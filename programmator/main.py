import sys, threading, queue, traceback, functools
from contextlib import contextmanager

import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

import logging
log = logging.getLogger(__name__)

from programmator.utils import (OkCancelDialog, tk_append_readonly_text, tk_center_window, set_high_DPI_awareness,
        CallbackLogHandler, encrypt_string, decrypt_string)
from programmator.port_monitor import PortMonitor
from programmator.progress_window import ProgressWindow
from programmator.comms import ThreadController
from programmator import panel, device_memory
from programmator.pinmanager import pinmanager
from programmator.version import __version__


class Application:
    def __init__(self, root=None):
        self.buffer_line_count = 2000
        self.stopping = False
        self.progress_window = None

        self.create_widgets(root)

        # generic mechanism for worker threads to safely execute code on the main thread.
        self.invoke_queue = queue.Queue()
        self.start_polling_invoke_queue()

        # configure logging
        formatter = logging.Formatter('{asctime}|{levelname}| {message}',
                style='{')
        formatter.default_time_format='%H:%M:%S'
        formatter.default_msec_format='%s.%03d'

        # log to visible journal
        self.main_thread_id = threading.get_ident()
        self.log_handler = CallbackLogHandler(lambda s:
            self.invoke_on_main_thread(self.log, s))
        self.log_handler.setFormatter(formatter)
        self.log_handler.setLevel(logging.INFO)

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(self.log_handler)

        # also log to stderr (unsynchronized at the IO level, but should be OK)
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.DEBUG)
        stderr_handler.setFormatter(formatter)
        root_logger.addHandler(stderr_handler)

        tk.Tk.report_callback_exception = self.report_callback_exception

        log.info(self.root.title())

        tk_center_window(self.root, True)

        self.on_connection_status_changed(False)
        self.port_monitor = PortMonitor(self.on_connection_status_changed)
        self.start_scanning_ports()


    def create_widgets(self, root):
        frame = self.frame = tk.Frame(root)
        root = self.root = self.frame.master

        root.title('Puper Programmator ' + __version__)
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

        self.button_reset = tk.Button(button_panel, text='Сбросить', command=self.cmd_reset)
        if False:
            # fixme: implement settings already
            self.button_reset.pack(side=tk.LEFT)

        self.button_loadfile = tk.Button(button_panel, text='Из файла', command=self.cmd_loadfile)
        self.button_loadfile.pack(side=tk.LEFT, padx=(5, 0))

        self.button_savefile = tk.Button(button_panel, text='Сохранить', command=self.cmd_savefile)
        self.button_savefile.pack(side=tk.LEFT)

        self.button_write_factory_settings = tk.Button(button_panel,
            text='Записать фабричные настройки', command=self.cmd_write_factory_settings)
        self.button_write_factory_settings.pack(side=tk.LEFT, padx=(5, 0))

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

        tabs.add(log_page, text='-- Журнал')

        tabs.pack(expand=True, fill=tk.BOTH)
        # tabs.select(tabs.index(tk.END) - 1)


    def on_connection_status_changed(self, connected: bool):
        if self.stopping:
            return
        log.debug(f'connection status changed, connected={connected}')
        # forget device memory after swapping devices!
        device_memory.memory_map.clear()

        def configure(button, enabled: bool):
            button.configure(state=(tk.NORMAL if enabled else tk.DISABLED))

        configure(self.button_read, connected)
        configure(self.button_write, connected)
        configure(self.button_reset, True)
        configure(self.button_loadfile, True)
        configure(self.button_savefile, True)
        configure(self.button_write_factory_settings, connected)


    def log(self, s):
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
            while not self.invoke_queue.empty():
                f, args, kwargs = self.invoke_queue.get(block=False)
                f(*args, **kwargs)
        finally:
            self.root.after(50, self.start_polling_invoke_queue)


    class AlreadyReported(Exception):
        pass


    def report_callback_exception(self, etype, value, tb):
        if etype == self.AlreadyReported:
            return
        log.exception('Произошла ошибка!')
        tk.messagebox.showerror('Произошла ошибка!', traceback.format_exception_only(etype, value))


    # for reporting exceptions about specific situations
    @contextmanager
    def try_and_report_exception(self, msg):
        try:
            yield
        except:
            log.exception(msg)
            tk.messagebox.showerror('Произошла ошибка!', msg)
            raise self.AlreadyReported()


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
            log.info(f'{title} памяти устройства')
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
            log.info('Загрузка данных в интерфейс')
            device_memory.populate_controls_from_memory_map()
            log.info(f'Настройки считаны из устройства')


    def cmd_write(self):
        if not self.port_monitor.port:
            log.error('Not connected')
            return
        try:
            log.info('Выгрузка данных из интерфейса в образ памяти')
            device_memory.populate_memory_map_from_controls()
            # FIXME: dirty hack, if device type == keyboard then input 9 must be enabled
            if device_memory.memory_map[3] & 0x07 == 6:
                device_memory.memory_map[111] |= 0x80
            # read back rounded values
            device_memory.populate_controls_from_memory_map()
            op = functools.partial(device_memory.write_from_memory_map)
            self.readwrite_in_thread('Запись', op)
        except Exception as exc:
            log.error(exc)
            raise # tkinter will print it to stdout
        log.info(f'Настройки записаны в устройство')


    def cmd_reset(self):
        device_memory.set_default_values()
        pinmanager.clear_pin()
        log.info(f'Настройки сброшены')


    def cmd_loadfile(self):
        file = filedialog.askopenfile(parent=self.root,
                filetypes=[('hex', '*.hex')],
                defaultextension='hex',
                mode='rb')

        if file is None:
            return

        with self.try_and_report_exception(f'Не удалось открыть файл {file.name!r}!'):
            s = file.read()

        with self.try_and_report_exception(f'Неправильные данные в файле {file.name!r}!'):
            # TODO: implement special processing for invalid version
            s = decrypt_string(s)
            pin_protected = device_memory.memory_map_from_str(s)

        pinmanager.update_status_after_loading_file(pin_protected)
        device_memory.populate_controls_from_memory_map()
        log.info(f'Файл {file.name!r} загружен')


    def cmd_savefile(self):
        # do this first to avoid creating corrupted files
        device_memory.populate_memory_map_from_controls()

        file = filedialog.asksaveasfile(parent=self.root,
                filetypes=[('hex', '*.hex')],
                defaultextension='hex',
                mode='wb')
        if file is None:
            return

        pin_protected = False
        if pinmanager.status == pinmanager.OPEN:
            # always save open data
            pin_protected = True
        elif pinmanager.status == pinmanager.VALID:
            res = tk.messagebox.askquestion('Сохранить закрытые данные?', 'Сохранить в файл пин и закрытые им данные?', icon = 'warning')
            if res == 'yes':
                pin_protected = True
        s = device_memory.memory_map_to_str(pin_protected)
        file.write(encrypt_string(s))
        log.info(f'Файл {file.name!r} записан')


    def cmd_write_factory_settings(self):
        if not self.port_monitor.port:
            log.error('Not connected')
            return

        d = OkCancelDialog(self.frame, 'Подтверждение сброса на заводсткие установки',
            'Вы уверены что хотите сбросить всю память устройства?')
        if not d.result:
            return

        try:
            log.info('Запись фабричных настроек')
            op = functools.partial(device_memory.write_from_memory_map, do_factory_reset=True)
            self.readwrite_in_thread('Запись', op)
            if self.readwrite_in_thread('Считывание', device_memory.read_into_memory_map):
                pinmanager.check_pin(self.root)
                log.info('Загрузка данных в интерфейс')
                device_memory.populate_controls_from_memory_map()
                log.info(f'Настройки считаны из устройства')
        except Exception as exc:
            log.error(exc)
            raise # tkinter will print it to stdout
        log.info(f'Настройки записаны в устройство')


    def cmd_unbrick(self):
        # here I used to put custom one-time code.
        assert False


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

