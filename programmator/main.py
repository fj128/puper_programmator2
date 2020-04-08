import re, string, threading, queue, time

import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

import logging
log = logging.getLogger(__name__)

from programmator.utils import tk_append_readonly_text, tk_center_window, set_high_DPI_awareness, CallbackLogHandler
from programmator.port_monitor import PortMonitor
from programmator.progress_window import ProgressWindow
from programmator.comms import ThreadController
from programmator import panel, device_memory
from programmator.pinmanager import pinmanager


class Application:
    def __init__(self, root=None):
        self.buffer_line_count = 2000
        self.stopping = False
        self.progress_window = None

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

        tk_center_window(self.root, True)

        self.port_monitor = PortMonitor(self.on_connection_status_changed)
        self.start_scanning_ports()


    def create_widgets(self, root):
        frame = self.frame = tk.Frame(root)
        root = self.root = self.frame.master

        root.title('Puper Programmator')
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)
        frame.grid(sticky='nesw')

        button_panel = tk.Frame(frame)
        button_panel.pack(fill=tk.X)

        self.button_read = tk.Button(button_panel, text='Считать', command=self.cmd_read, state=tk.DISABLED)
        self.button_read.pack(side=tk.LEFT)

        self.button_compare = tk.Button(button_panel, text='Сравнить', state=tk.DISABLED)
        self.button_compare.pack(side=tk.LEFT)

        self.button_write = tk.Button(button_panel, text='Записать', command=self.cmd_write, state=tk.DISABLED)
        self.button_write.pack(side=tk.LEFT)

        self.button_reset = tk.Button(button_panel, text='Сбросить', command=self.cmd_reset, state=tk.DISABLED)
        self.button_reset.pack(side=tk.LEFT)

        self.button_loadfile = tk.Button(button_panel, text='Из файла', command=self.cmd_loadfile, state=tk.DISABLED)
        self.button_loadfile.pack(side=tk.LEFT, padx=(5, 0))

        self.button_savefile = tk.Button(button_panel, text='Сохранить', command=self.cmd_savefile, state=tk.DISABLED)
        self.button_savefile.pack(side=tk.LEFT)

        button_settings = tk.Button(button_panel, text='Настройки', state=tk.DISABLED)
        button_settings.pack(side=tk.RIGHT)

        # button_emergency_unbrick = tk.Button(button_panel, text='Emergency Unbrick Write', command=self.cmd_unbrick)
        # button_emergency_unbrick.pack(side=tk.RIGHT)

        separator = tk.Frame(frame, height=3, bd=1) #, relief=tk.SUNKEN
        separator.pack(fill=tk.X)

        tabs = self.tabs = ttk.Notebook(frame)

        # create log_text page ASAP to enable logging, but actually add it last
        log_page = ttk.Frame(tabs)
        self.log_text = log_text = ScrolledText(log_page)
        log_text.pack(expand=1, fill="both")

        panel.create_widgets(tabs)

        # disable for now
        # tabs.add(log_page, text='-- Журнал')

        tabs.pack(expand=True, fill=tk.BOTH)
        # tabs.select(tabs.index(tk.END) - 1)


    def on_connection_status_changed(self, connected: bool):
        if self.stopping:
            return
        if connected:
            self.button_read.configure(state=tk.NORMAL)
            self.button_write.configure(state=tk.DISABLED)
            self.button_compare.configure(state=tk.DISABLED)
        else:
            self.button_read.configure(state=tk.DISABLED)
            self.button_write.configure(state=tk.DISABLED)
            self.button_compare.configure(state=tk.DISABLED)


    def log(self, s):
        print(s)
        if self.stopping:
            return
        tk_append_readonly_text(self.log_text, s, self.buffer_line_count, True)
        if self.progress_window:
            self.progress_window.log(s)


    def invoke_on_main_thread(self, f, *args, **kwargs):
        if self.main_thread_id != threading.get_ident():
            self.invoke_queue.put((f, args, kwargs))
        else:
            # invoke directly, probably should swallow exceptions like the above
            f(*args, **kwargs)


    def start_polling_invoke_queue(self):
        try:
            invoked_any = False
            while not self.invoke_queue.empty():
                f, args, kwargs = self.invoke_queue.get(block=False)
                f(*args, **kwargs)
                invoked_any = True
            # if invoked_any:
            #     self.root.update_idletasks()
        finally:
            self.root.after(50, self.start_polling_invoke_queue)


    def start_scanning_ports(self):
        try:
            self.port_monitor.scan_and_connect()
        finally:
            self.root.after(1000, self.start_scanning_ports)


    def readwrite_in_thread(self, title, op):
        pw = ProgressWindow(self.root, title)
        self.progress_window = pw # for logging

        def report_progress(current, total):
            self.invoke_on_main_thread(pw.update_progress, current, total)

        controller = ThreadController(report_progress)

        def worker_function():
            success = False
            try:
                success = op(self.port_monitor.port, controller)
            except:
                log.exception(f'{title} failed')
            finally:
                self.invoke_on_main_thread(pw.report_status, success)

        worker = threading.Thread(target=worker_function)

        def abort():
            log.debug('Operation interrupted. Stopping worker thread')
            controller.abort = True
            worker.join()
            log.debug('worker thread stopped')

        pw.on_abort = abort

        try:
            worker.start()
            if pw.run():
                return True
        except Exception as exc:
            log.error(exc)
            # TODO: proper exception handling
            raise # tkinter will print it to stdout
        finally:
            self.progress_window = None


    def cmd_read(self):
        if not self.port_monitor.port:
            log.error('Not connected')
            return
        if self.readwrite_in_thread('Считывание', device_memory.read_into_memory_map):
            pinmanager.check_pin(self.root)
            device_memory.populate_controls_from_memory_map()
            self.button_write.configure(state=tk.NORMAL)


    def cmd_write(self):
        if not self.port_monitor.port:
            log.error('Not connected')
            return
        try:
            if device_memory.populate_memory_map_from_controls():
                # read back rounded values
                device_memory.populate_controls_from_memory_map()
                self.readwrite_in_thread('Запись', device_memory.write_from_memory_map)
        except Exception as exc:
            log.error(exc)
            raise # tkinter will print it to stdout


    def cmd_reset(self):
        'reset to factory settings'


    def cmd_loadfile(self):
        ''


    def cmd_savefile(self):
        ''


    def cmd_unbrick(self):
        self.cmd_write()


    def run(self):
        self.root.mainloop()
        self.stopping = True
        self.port_monitor.disconnect()


def main():
    set_high_DPI_awareness()
    app = Application()
    app.run()



if __name__ == '__main__':
    main()

