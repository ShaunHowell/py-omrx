#!/bin/python
import traceback
import sys
from pyomrx.omr.attendance_register import process_attendance_sheet_folder
from pyomrx.omr.exam_marksheet import process_exam_marksheet_folder
import wx
import webbrowser
from pathlib import Path
from pyomrx.omr.exceptions import EmptyFolderException
import pyomrx


class PyomrxMainFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(PyomrxMainFrame, self).__init__(*args, **kw)
        sys.excepthook = ExceptionHandler
        self.input_path = ''
        self.output_folder = ''
        self.buttons = []
        self.panel = wx.Panel(self)
        self.create_buttons()
        self.init_ui()
        self.Centre()
        self.statusbar.SetStatusText('ready')
        self.update_layout()

    def create_buttons(self):
        def create_button(button_type, label, function, with_text=True):
            button = wx.Button(self.panel, label=label)
            path_text = wx.StaticText(
                self.panel, label='_' * 30) if with_text else None
            self.buttons.append(
                [button_type, {
                    'button': button,
                    'text': path_text
                }])
            button.Bind(wx.EVT_BUTTON, function)

        font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
        font.SetPointSize(9)

        for button_type in ["images", "output"]:
            create_button(
                button_type, "Open {} folder".format(button_type),
                getattr(self, 'choose_{}_folder'.format(button_type)))
        create_button(
            'process', 'Process images', self.process_images, with_text=False)

    def init_ui(self):
        border_width = 10
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add((-1, 20), proportion=0, border=border_width)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(wx.StaticText(self.panel, label='Form type:'), proportion=0, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                 border=border_width)
        self.form_type_dropdown = wx.Choice(self.panel, choices=['exam marksheet', 'attendance register'])
        self.form_type_dropdown.SetSelection(0)
        hbox.Add(self.form_type_dropdown, proportion=0,
                 flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                 border=border_width)
        self.vbox.Add(hbox, proportion=0, flag=wx.ALIGN_CENTRE | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border_width)
        self.vbox.Add((-1, 5), proportion=0, border=border_width)

        for button_type, button_dict in self.buttons:
            hbox = wx.BoxSizer(wx.HORIZONTAL)
            hbox.Add(button_dict['button'], proportion=0, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border_width)
            if button_dict['text']:
                hbox.Add(button_dict['text'], proportion=0, flag=wx.ALIGN_LEFT | wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                         border=border_width)
                self.vbox.Add(
                    hbox, proportion=0,
                    flag=wx.ALIGN_LEFT | wx.ALIGN_BOTTOM | wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                    border=border_width)
            else:
                self.vbox.Add(hbox, proportion=0, flag=wx.ALIGN_CENTRE | wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                              border=border_width)
            self.vbox.Add((-1, 5), proportion=0, border=border_width)
        self.vbox.Add((-1, 20), proportion=0, border=border_width)

        self.update_layout()
        self.statusbar = self.CreateStatusBar(2)
        version_string = 'version: {}'.format(pyomrx.__version__)
        self.statusbar.SetStatusWidths([-1, len(version_string) * 5])
        self.statusbar.SetStatusText('UI created')
        self.statusbar.SetStatusText(version_string, 1)

    def choose_images_folder(self, event):
        dialog = wx.DirDialog(
            self, 'Choose images directory', '', style=wx.DD_DEFAULT_STYLE)
        try:
            if dialog.ShowModal() == wx.ID_CANCEL:
                return
            path = dialog.GetPath()
        except Exception:
            wx.LogError('Failed to open directory!')
            raise
        finally:
            dialog.Destroy()
        if len(path) > 0:
            self.input_path = Path(path)
            text_objext = next(
                (object[1]['text']
                 for object in self.buttons if object[0] == 'images'), None)
            text_objext.SetLabel('...{}'.format(str(path)[-30:]))
        self.update_layout()

    def choose_output_folder(self, event):
        dialog = wx.DirDialog(
            self, 'Choose output directory', '', style=wx.DD_DEFAULT_STYLE)
        try:
            if dialog.ShowModal() == wx.ID_CANCEL:
                return
            path = dialog.GetPath()
        except Exception:
            wx.LogError('Failed to open directory!')
            raise
        finally:
            dialog.Destroy()
        if len(path) > 0:
            self.output_folder = Path(path)
            text_objext = next(
                (object[1]['text']
                 for object in self.buttons if object[0] == 'output'), None)
            text_objext.SetLabel('...{}'.format(str(path)[-30:]))
        self.update_layout()

    def update_layout(self):
        self.vbox.SetSizeHints(self)
        self.panel.SetSizer(self.vbox)
        self.Fit()
        self.Layout()

    def open_output_folder(self):
        webbrowser.open(str(self.output_folder))

    def process_images(self, event):
        if not self.input_path or not self.output_folder:
            raise ValueError('need to set input path and output folder')
        form_type = self.form_type_dropdown.GetString(self.form_type_dropdown.GetSelection())
        self.statusbar.PushStatusText('processing {}s'.format(form_type))
        try:
            if form_type == 'attendance register':
                process_attendance_sheet_folder(
                    input_folder=str(self.input_path),
                    form_design_path=None,
                    output_folder=str(self.output_folder))
            elif form_type == 'exam marksheet':
                process_exam_marksheet_folder(
                    input_folder=str(self.input_path),
                    form_design_path=None,
                    output_folder=str(self.output_folder))
            else:
                raise ValueError('got form type: {}, not supported (check spelling?)'.format(form_type))
        except EmptyFolderException as e:
            # frame = wx.GetApp().GetTopWindow()
            print(e)
            self.statusbar.PushStatusText('error: empty folder')
            dlg = ExceptionDialog('No image files found in the selected folder', parent=None, fatal=False,
                                  title='Error')
            dlg.ShowModal()
            dlg.Destroy()
            self.statusbar.PushStatusText('ready')
            return

        success_dialog = wx.MessageDialog(
            self.panel,
            message='Processing finished: open output folder?',
            style=wx.ICON_INFORMATION | wx.YES_NO | wx.NO_DEFAULT | wx.CENTRE,
            caption='Attendance register processing done').ShowModal()
        if success_dialog == 5103:
            self.open_output_folder()
        self.statusbar.PushStatusText('ready')


class ExceptionDialog(wx.Dialog):
    def __init__(self, msg, fatal=True, *args, **kw):
        super(ExceptionDialog, self).__init__(*args, **kw, style=wx.CAPTION)
        self.msg = msg
        self.init_ui(fatal=fatal)

    def init_ui(self, fatal=True):
        exception_vertical_sizer = wx.BoxSizer(wx.VERTICAL)

        message_panel = wx.Panel(self)
        message_box_sizer = wx.StaticBoxSizer(
            parent=message_panel, orient=wx.VERTICAL)
        if fatal:
            message_header = 'Sorry, something went wrong.'
        else:
            message_header = 'Oops'
        message_text_object = wx.StaticText(
            message_panel,
            label=message_header,
            style=wx.ALIGN_CENTRE_HORIZONTAL)
        font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        message_text_object.SetFont(font)
        message_box_sizer.Add(message_text_object,
                              proportion=1,
                              flag=wx.EXPAND,
                              border=5)
        message_box_sizer.Add((-1, 10), proportion=0)
        msg_text = self.msg if not fatal else '1. Click below to copy the error details to the clipboard,' \
                                              '\n 2. Email the error details to Shaun for support'
        message_box_sizer.Add(
            wx.StaticText(
                message_panel,
                label=msg_text,
                style=wx.ALIGN_LEFT),
            proportion=1,
            flag=wx.EXPAND,
            border=5)
        message_panel.SetSizer(message_box_sizer)
        exception_vertical_sizer.Add(
            message_panel, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)
        button_container_sizer = wx.BoxSizer(wx.HORIZONTAL)
        if fatal:
            clipboardButton = wx.Button(self, label='Copy to clipboard')
            exitButton = wx.Button(self, label='Exit')
            button_container_sizer.Add(clipboardButton)
            button_container_sizer.Add(exitButton, flag=wx.LEFT, border=5)
            clipboardButton.Bind(
                wx.EVT_BUTTON,
                lambda evt, temp=self.msg: self.OnCopyToClipboard(evt, temp))
            exitButton.Bind(wx.EVT_BUTTON, self.OnClose)
        else:
            okButton = wx.Button(self, label='Ok')
            okButton.Bind(wx.EVT_BUTTON, self.OnOk)
            button_container_sizer.Add(okButton)
        exception_vertical_sizer.Add(
            button_container_sizer,
            flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM,
            border=10)

        exception_vertical_sizer.SetSizeHints(self)
        self.SetSizer(exception_vertical_sizer)
        self.Fit()
        self.Layout()

    def OnClose(self, e):
        self.Destroy()
        sys.exit(1)

    def OnOk(self, e):
        self.Destroy()

    def OnCopyToClipboard(self, e, message):
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(str(message)))
            wx.TheClipboard.Close()
            wx.TheClipboard.Flush()
        else:
            wx.MessageBox(message='failed to copy', style=wx.ICON_ERROR)


def ExceptionHandler(etype, value, trace):
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


def main():
    app = wx.App()
    frm = PyomrxMainFrame(None, wx.ID_ANY, title='OMR Tool')
    frm.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
