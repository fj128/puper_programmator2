import tkinter as tk
from tkinter import Toplevel, Label, Entry, Button
from tkinter.ttk import Progressbar
from tkinter.scrolledtext import ScrolledText

from programmator.utils import tk_append_readonly_text

import logging
log = logging.getLogger(__name__)


class ProgressWindow:
    def __init__(self, parent, title):
        self.parent = parent
        self.title = title
        self.on_abort = None
        self.status = None
        self.autoclose = True

        try:
            top = self.top = Toplevel(parent)
            self.create_widgets()
            self.set_initial_window_position()
            top.transient(parent)
            top.grab_set()
            top.focus_set()
        except:
            # make sure we don't create orphan windows
            self.top.destroy()
            raise

    def create_widgets(self):
        top = self.top
        self.label = Label(top, text=self.title)
        self.label.pack()

        self.progressbar = Progressbar(top)
        self.progressbar.pack(fill=tk.X)

        self.log_text = log_text = ScrolledText(top, height=10)
        log_text.pack(expand=1, fill=tk.BOTH)

        button_panel = tk.Frame(top)
        button_panel.pack(fill=tk.X)

        '''control flow:
        Initially: abort enabled, cancel disabled

        self.abort -> parent tells and waits for the thread to stop

        thread terminates (forced or successfully) -> calls report_status()

        report_status() -> enable cancel button or autoclose on success
        '''

        self.btn_close = Button(top, text='Закрыть', command=self.close, state=tk.DISABLED)
        self.btn_close.pack(side=tk.RIGHT, pady=(5, 5), padx=(5, 5))

        self.btn_abort = Button(top, text='Прервать', command=self.abort, state=tk.NORMAL)
        self.btn_abort.pack(side=tk.RIGHT, pady=(5, 5), padx=(5, 5))

        self.top.protocol("WM_DELETE_WINDOW", self.abort)
        self.top.bind("<Escape>", self.abort)


    def set_initial_window_position(self):
        sw = self.parent.winfo_width()
        sh = self.parent.winfo_height()
        w = int(sw * 0.85)
        h = int(sh * 0.6)
        y = (sh - h * 1.05) // 2 + self.parent.winfo_y()
        x = (sw - w) // 2 + self.parent.winfo_x()
        self.top.geometry('%dx%d+%d+%d' % (w, h, x, y))


    def log(self, s):
        tk_append_readonly_text(self.log_text, s, line_mode=True)


    def abort(self, *args):
        log.debug('abort')
        self.on_abort()


    def close(self, *args):
        log.debug('close')
        self.top.destroy()


    def report_status(self, status):
        self.status = status

        if status and self.autoclose:
            self.close()
            return

        self.label.configure(text=self.title + '. Операция завершена ' + ('успешно.' if status else 'с ошибкой.'))
        self.btn_abort.configure(state=tk.DISABLED)
        self.btn_close.configure(state=tk.NORMAL)

        self.top.protocol("WM_DELETE_WINDOW", self.close)
        self.top.bind("<Escape>", self.close)
        self.top.bind("<Return>", self.close)
        self.btn_close.focus_set()


    def update_progress(self, current, total):
        p = self.progressbar
        if p.cget('maximum') != total:
            p.configure(value=current, maximum=total)
        else:
            p.configure(value=current)


    def run(self):
        self.parent.wait_window(self.top)
        return self.status


if __name__ == '__main__':
    from programmator.main import main
    main()
