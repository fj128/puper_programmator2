import os
import tkinter as tk
import tkinter.font
import logging
from typing import Callable
from contextlib import contextmanager
import pyaes


import logging
log = logging.getLogger(__name__)


def pretty_hexlify(data):
    return ' '.join(f'{b:02X}' for b in data)


def enumerate_first_last(lst):
    'Use like `for is_first, is_last, it in enumerate_first_last(lst):`'
    last = len(lst) - 1
    for i, it in enumerate(lst):
        yield i == 0, i == last, it


# use the dumbest possible encryption scheme that still completely mangles the file
_encryption_key = b'super secret key, 32 bytes, asdf'

def encrypt_string(s: str):
    b = s.encode('utf-8')
    iv = os.urandom(16)
    encrypter = pyaes.Encrypter(pyaes.AESModeOfOperationCBC(_encryption_key, iv))
    res = iv
    res += encrypter.feed(s)
    res += encrypter.feed()
    return res


def decrypt_string(s: bytes):
    iv, s = s[:16], s[16:]
    decrypter = pyaes.Decrypter(pyaes.AESModeOfOperationCBC(_encryption_key, iv))
    res = decrypter.feed(s)
    res += decrypter.feed()
    return res.decode('utf-8')


@contextmanager
def timeit_block(what='Something'):
    import timeit
    t = timeit.default_timer()
    yield
    t2 = timeit.default_timer()
    log.debug(f'{what} took {t2 - t:0.3f} seconds')


def set_high_DPI_awareness():
    'Avoid blurry text on Win10 with nonstandard DPI. Must be called before initializing tk'
    from ctypes import windll
    try:
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        # no Windows 10 then.
        pass


def tk_append_readonly_text(text_widget, s, max_lines=None, line_mode=False):
    '''Append text to a readonly text widget.
    if max_lines is not None, delete lines from the start to maintain the line count.
    if line_mode is True, add newlines before and after inserted text, if necessary.
    if s is empty and line_mode is true, add a single newline if necessary'''

    text_widget.configure(state=tk.NORMAL)
    if line_mode and not text_widget.index(tk.END + '-1c').endswith('.0'):
        text_widget.insert(tk.END, '\n')
    if s:
        text_widget.insert(tk.END, s)
        if line_mode and not s.endswith('\n'):
            text_widget.insert(tk.END, '\n')

    lines = int(text_widget.index(tk.END).split('.')[0])
    if max_lines is not None and lines > max_lines:
        lines = lines - max_lines + 2 # adjust to 1-based index, exclusive
        text_widget.delete('1.0', '%d.0' % lines)
    text_widget.see(tk.END)
    text_widget.configure(state=tk.DISABLED)


def tk_set_list_maxwidth(element, lst):
    f = tk.font.nametofont(element.cget("font"))
    zerowidth=f.measure('0')
    w=max([f.measure(i) for i in lst])/zerowidth
    element.config(width=round(w + 0.5))


def tk_center_window(self, resize=False):
    '''Warning: calls update_idletasks to force computing all geometry and actual width/height values.

    Unfortunately we need to use the blackest magic to prevent the window from getting actually
    drawn (at an unadjusted position) as a result, and it still kinda flickers.

    https://wiki.tcl-lang.org/page/Centering+a+window
    https://github.com/tcltk/tk/blob/master/library/tk.tcl#L72
    '''
    # self.eval('tk::PlaceWindow . center')
    # could use the above but we also optionally resize the window.
    self.withdraw()
    self.update_idletasks()
    sw = self.winfo_screenwidth()
    sh = self.winfo_screenheight()
    w = self.winfo_width()
    h = self.winfo_height()
    if resize:
        w = max(w, int(sw * 0.75))
        h = max(h, int(sh * 0.75))

    y = (sh - h * 1.05) // 2  # height doesn't include the window title, hackily adjust
    x = (sw - w) // 2
    self.geometry('%dx%d+%d+%d' % (w, h, x, y))
    self.deiconify()


class CallbackLogHandler(logging.Handler):
    '''Just call the callback method with formatted log message'''
    def __init__(self, callback: Callable[[str, int], None]):
        super().__init__()
        self.callback = callback

    def emit(self, record):
        self.callback(self.format(record))


class VerticalScrolledFrame(tk.Frame):
    'An abomination constructed from several pieces found on the internet'

    def __init__(self, parent, *args, **kw):
        super().__init__(parent, *args, **kw)

        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        vscrollbar.pack(fill=tk.Y, side=tk.RIGHT, expand=False)
        canvas = tk.Canvas(self, bd=0, highlightthickness=0,
                        yscrollcommand=vscrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vscrollbar.config(command=canvas.yview)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = tk.Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor='nw')

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())
        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())

        canvas.bind('<Configure>', _configure_canvas)

        def _on_mousewheel(event):
            """Linux uses event.num; Windows / Mac uses event.delta"""
            if event.num == 4 or event.delta > 0:
                canvas.yview_scroll(-1, "units" )
            elif event.num == 5 or event.delta < 0:
                canvas.yview_scroll(1, "units" )

        def _bind_mouse(event=None):
            canvas.bind_all("<4>", _on_mousewheel)
            canvas.bind_all("<5>", _on_mousewheel)
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_mouse(event=None):
            canvas.unbind_all("<4>")
            canvas.unbind_all("<5>")
            canvas.unbind_all("<MouseWheel>")

        canvas.bind("<Enter>", _bind_mouse)
        canvas.bind("<Leave>", _unbind_mouse)


# based on https://effbot.org/tkinterbook/tkinter-dialog-windows.htm
# todo: inherit from tkinter.simpledialog.Dialog
class Dialog(tk.Toplevel):
    def __init__(self, parent, title=None):
        tk.Toplevel.__init__(self, parent)
        self.transient(parent)
        if title:
            self.title(title)
        self.parent = parent
        self.result = None
        body = tk.Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)
        self.buttonbox()
        self.grab_set()
        if not self.initial_focus:
            self.initial_focus = self
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        tk_center_window(self)
        self.resizable(False, False)
        self.initial_focus.focus_set()
        self.wait_window(self)


    #
    # construction hooks

    def body(self, master):
        # create dialog body.  return widget that should have
        # initial focus.  this method should be overridden
        pass


    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons

        box = tk.Frame(self)

        w = tk.Button(box, text="OK", width=10, command=self.ok, default=tk.ACTIVE)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        w = tk.Button(box, text="Отмена", width=10, command=self.cancel)
        w.pack(side=tk.LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()


    #
    # standard button semantics

    def ok(self, event=None):
        if not self.validate():
            self.initial_focus.focus_set() # put focus back
            return
        self.withdraw()
        self.update_idletasks()
        self.apply()
        self.cancel()


    def cancel(self, event=None):
        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()

    #
    # command hooks

    def validate(self):
        return True # override

    def apply(self):
        pass # override


if __name__ == '__main__':
    from programmator.main import main
    main()
    # s = encrypt_string('some string')
    # print(s)
    # print(decrypt_string(s))
