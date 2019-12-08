import traceback
import webbrowser
from pathlib import Path

import wx

from pyomrx.gui.dialogs import ExceptionDialog


def handle_exception(etype, value, trace):
    """
    Handler for all unhandled exceptions.

    :param `etype`: the exception type (`SyntaxError`, `ZeroDivisionError`, etc...);
    :type `etype`: `Exception`
    :param string `value`: the exception error message;
    :param string `trace`: the traceback header, if any (otherwise, it prints the
     standard Python header: ``Traceback (most recent call last)``.
    """
    frame = wx.GetApp().GetTopWindow()
    tmp = traceback.format_exception(etype, value, trace)
    exception = "".join(tmp)
    print(exception)
    dlg = ExceptionDialog(exception, parent=None, fatal=True, title='Error')
    dlg.ShowModal()
    dlg.Destroy()


def open_folder(path):
    if Path(path).is_file():
        path = path.parent
    webbrowser.open(str(path))
