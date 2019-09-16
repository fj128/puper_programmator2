import re, string, threading, queue, time

import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

import logging
log = logging.getLogger(__name__)

from programmator.utils import tk_append_readonly_text, set_high_DPI_awareness, CallbackLogHandler
from programmator.port_monitor import PortMonitor
from programmator.comms import compose
from programmator import panel


class Application:
    def __init__(self, root=None):
        self.buffer_line_count = 2000
        self.stopping = False

        self.create_widgets(root)

        # generic mechanism for worker threads to safely execute code on the main thread.
        self.invoke_queue = queue.Queue()
        self.start_polling_invoke_queue()

        self.main_thread_id = threading.get_ident()
        self.log_handler = CallbackLogHandler(lambda s:
            self.invoke_on_main_thread(self.log, s))

        self.log_handler.setFormatter(logging.Formatter('{levelname}: {message}', style='{'))
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)
        root_logger.setLevel(logging.DEBUG) # use INFO in production. And add full logging to a file.

        self.port_monitor = PortMonitor()
        self.start_scanning_ports()

        # self.receiver_thread = threading.Thread(target=self.receiver_thread_func)
        # self.receiver_thread.start()


    def create_widgets(self, root):
        padding = {'padx': 1, 'pady': 1}

        frame = self.frame = tk.Frame(root)
        root = self.root = self.frame.master

        root.title('Puper Programmator')
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)
        frame.grid(sticky='nesw')

        button_panel = tk.Frame(frame)
        button_panel.pack(fill=tk.X)

        button_read = tk.Button(button_panel, text='Считать')
        button_read.pack(side=tk.LEFT)

        button_compare = tk.Button(button_panel, text='Сравнить')
        button_compare.pack(side=tk.LEFT)

        button_write = tk.Button(button_panel, text='Записать')
        button_write.pack(side=tk.LEFT)

        button_settings = tk.Button(button_panel, text='Настройки')
        button_settings.pack(side=tk.RIGHT)

        separator = tk.Frame(frame, height=3, bd=1) #, relief=tk.SUNKEN
        separator.pack(fill=tk.X)

        tabs = ttk.Notebook(frame)

        # create log_text page ASAP to enable logging, but actually add it last
        log_page = ttk.Frame(tabs)
        self.log_text = log_text = ScrolledText(log_page)
        log_text.pack(expand=1, fill="both")

        panel.create_widgets(tabs)

        # tabs.add(ttk.Frame(tabs), text=' ' * 10, state=tk.DISABLED) # separator
        tabs.add(log_page, text='-- Журнал')

        tabs.pack(expand=True, fill=tk.BOTH)
        # tabs.select(tabs.index(tk.END) - 1)

        # self.set_initial_window_position()


    def log(self, s):
        print(s)
        if self.stopping:
            return
        tk_append_readonly_text(self.log_text, s, self.buffer_line_count, True)


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



    def run(self):
        self.root.mainloop()
        self.stopping = True
        self.port_monitor.disconnect()
        log.debug('Stopping receiver thread')
        # self.receiver_thread.join()


def main():
    set_high_DPI_awareness()
    app = Application()
    app.run()


if __name__ == '__main__':
    main()

