# from dataclasses import dataclass

import re, string, threading, queue, time

import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

import logging
log = logging.getLogger(__name__)

from programmator.utils import tk_append_readonly_text, set_high_DPI_awareness, CallbackLogHandler
from programmator.port_monitor import PortMonitor
from programmator.comms import compose


class ParseError(Exception):
    def __init__(self, msg, column, column_end):
        super().__init__(msg)
        self.column = column
        self.column_end = column_end


def parse_hex_input(s: str):
    def check_hex_digit(c, pos):
        if c not in string.hexdigits:
            raise ParseError(f'Invalid hex digit {c!r} at {pos}', pos, pos + 1)
    res = bytearray()
    for match in re.finditer(r'[^\s]+', s):
        group = match.group(0)
        if len(group) & 1:
            raise ParseError(f'Odd length group at {match.start()}', match.start(), match.end())
        for i in range(0, len(group), 2):
            check_hex_digit(group[i], i + match.start())
            check_hex_digit(group[i + 1], i + 1 + match.start())
            res.append(int(group[i : i + 2], 16))
    return res


class Application:
    def __init__(self, root=None):
        self.buffer_line_count = 2000
        self.stopping = False

        self.createWidgets(root)

        # generic mechanism for worker threads to execute code on the main thread.
        self.invoke_queue = queue.Queue()
        self.start_polling_invoke_queue()

        self.main_thread_id = threading.get_ident()
        self.log_handler = CallbackLogHandler(lambda s:
            self.invoke_on_main_thread(self.append_main_text_line, s))

        self.log_handler.setFormatter(logging.Formatter('{levelname}: {message}', style='{'))
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)
        root_logger.setLevel(logging.DEBUG) # use INFO in production. And add full logging to a file.

        self.port_monitor = PortMonitor()
        self.start_scanning_ports()

        self.receiver_thread = threading.Thread(target=self.receiver_thread_func)
        self.receiver_thread.start()


    def createWidgets(self, root):
        padding = {'padx': 1, 'pady': 1}

        frame = self.frame = tk.Frame(root)
        root = self.root = self.frame.master

        root.title('HexTerminal')
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)
        root.bind('<Return>', self.send)

        frame.grid(sticky='nesw')
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=0)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=0)

        self.main_text = ScrolledText(frame, state=tk.DISABLED)
        self.main_text.grid(columnspan=3, sticky='NSWE', **padding)

        v = tk.StringVar()
        self.commandline = tk.Entry(frame, textvariable=v)
        self.commandline.grid(row=1, column=0, sticky='NSWE', **padding)

        self.send_button = tk.Button(frame, text='Send (ENTER)',
            command=self.send)
        self.send_button.grid(row=1, column=1, **padding)

        size_grip = ttk.Sizegrip(frame)
        size_grip.grid(row=1, column=2, sticky='NSWE')

        self.append_main_text_line('# Enter space separated hex bytes below, press ENTER')
        self.append_main_text_line('# Alternatively, "!" followed by hex data is interpreted as a programmator command')
        self.append_main_text_line('# first byte must be the command, then two byte address, then payload')
        self.set_initial_window_position()
        self.commandline.focus_set()


    def send(self, event=None):
        if not self.port_monitor.port:
            log.error(f'Not connected to device')

        cmd = self.commandline.get().strip()

        programmator_mode = False
        if cmd.startswith('!'):
            programmator_mode = True
            cmd = cmd[1:]
            # todo: fixup positions in error message

        arr = None
        try:
            arr = parse_hex_input(cmd)
        except ParseError as exc:
            log.error(f'{exc}')
            log.error('Input should be a hexadecimal string optionally space-separated on byte boundaries')

        if not arr:
            return

        if programmator_mode:
            if len(arr) < 3:
                log.error('Command too short, must contain at least 3 bytes (command, address)')
                return
            if arr[0] not in (0, 1):
                log.error('Command must be 00 or 01')
                return
            tmp = compose(arr[0], arr[1] * 256 + arr[2], arr[3:])
            self.append_main_text_line('! ' + ' '.join(f'{c:02X}' for c in arr))
            arr = tmp

        self.port_monitor.port.write(arr)
        self.append_main_text_line('> ' + ' '.join(f'{c:02X}' for c in arr))


    def append_main_text(self, s):
        if self.stopping:
            return
        tk_append_readonly_text(self.main_text, s, self.buffer_line_count, False)


    def append_main_text_line(self, s):
        if self.stopping:
            return
        tk_append_readonly_text(self.main_text, s, self.buffer_line_count, True)


    def set_initial_window_position(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w = int(sw * 0.75)
        h = int(sh * 0.75) # this doesn't include the window title apparently, so the result is kinda fucky
        y = (sh - h * 1.05) // 2
        x = (sw - w) // 2
        self.root.geometry('%dx%d+%d+%d' % (w, h, x, y))


    def invoke_on_main_thread(self, f, *args, **kwargs):
        if self.main_thread_id != threading.get_ident():
            self.invoke_queue.put((f, args, kwargs))
        else:
            # invoke directly, probably should swallow exceptions like the above
            f(*args, **kwargs)


    def start_polling_invoke_queue(self):
        try:
            while not self.invoke_queue.empty():
                f, args, kwargs = self.invoke_queue.get(block=False)
                f(*args, **kwargs)
        finally:
            # 20 ms should be enough for everyone
            self.root.after(20, self.start_polling_invoke_queue)


    def start_scanning_ports(self):
        try:
            self.port_monitor.scan_and_connect()
        finally:
            self.root.after(1000, self.start_scanning_ports)


    def receiver_thread_func(self):
        # all other output is line based, this is the only thing that appends data to current line
        has_message = False
        while not self.stopping:
            port = self.port_monitor.port
            if port is None:
                time.sleep(0.1)
                continue
            try:
                size = port.in_waiting
                data = port.read(max(size, 1))
                if len(data):
                    s = ' '.join(f'{b:02X}' for b in data) + ' '
                    has_message = True
                    self.invoke_on_main_thread(self.append_main_text, s)
                elif has_message:
                    self.invoke_on_main_thread(self.append_main_text_line, '\n')
                    has_message = False
            except Exception as exc:
                log.error('Exception while reading: ' + str(exc))
                if self.stopping:
                    return
                time.sleep(1)


    def run(self):
        self.root.mainloop()
        self.stopping = True
        self.port_monitor.disconnect()
        log.debug('Stopping receiver thread')
        self.receiver_thread.join()


def main():
    set_high_DPI_awareness()
    app = Application()
    app.run()


if __name__ == '__main__':
    main()
