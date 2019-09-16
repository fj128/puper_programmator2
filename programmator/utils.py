import tkinter as tk
import tkinter.font
import logging
from typing import Callable


def set_high_DPI_awareness():
    'Avoid blurry text on Win10 with nonstandard DPI. Must be called before initializing tk'
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)


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
    if lines > max_lines:
        lines = lines - max_lines + 2 # adjust to 1-based index, exclusive
        text_widget.delete('1.0', '%d.0' % lines)
    text_widget.see(tk.END)
    text_widget.configure(state=tk.DISABLED)


def tk_set_list_maxwidth(element, lst):
    f = tk.font.nametofont(element.cget("font"))
    zerowidth=f.measure('0')
    w=max([f.measure(i) for i in lst])/zerowidth
    element.config(width=round(w + 0.5))


class CallbackLogHandler(logging.Handler):
    '''Just call the callback method with formatted log message'''
    def __init__(self, callback: Callable[[str], None]):
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
