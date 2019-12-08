import sys

import wx
from pubsub import pub

from pyomrx.core.meta import Abortable
from pyomrx.gui import DATA_EXTRACTION_TOPIC, FORM_GENERATION_TOPIC


class WorkerProgressDialog(wx.GenericProgressDialog, Abortable):
    def __init__(self, parent, worker_id, title, message, pubsub_topic, maximum=100, abort_event=None, *args, **kwargs):
        self.parent = parent
        wx.GenericProgressDialog.__init__(
            self,
            parent=parent,
            title=title,
            message=message,
            maximum=maximum,
            *args,
            **kwargs)
        Abortable.__init__(self, abort_event)
        self.Bind(wx.EVT_CLOSE, self.close)
        self.Connect(-1, -1, wx.ID_CANCEL, self.close)
        pub.subscribe(self.update_progress,
                      f'{worker_id}.{pubsub_topic}')
        self.progress = 0
        self.recursive_update()

    def update_progress(self, progress=None):
        if progress:
            self.progress = progress
        else:
            self.progress += 1

    def close_if_cancelled(self):
        if self.abort_event.is_set():
            # already been closed
            return True
        if self.WasCancelled():
            self.close('')
            return True
        return False

    def recursive_update(self):
        if not self.close_if_cancelled():
            self.Update(self.progress)
            wx.CallLater(250, self.recursive_update)

    def close(self, event):
        self.abort()
        self.Destroy()


class DataExtractProgressDialog(WorkerProgressDialog):
    def __init__(self,
                 parent,
                 worker_id,
                 num_files,
                 input_path,
                 abort_event=None,
                 *args,
                 **kwargs):
        WorkerProgressDialog.__init__(self, parent, worker_id, 'Data extraction progress',
                                      f'Processing {num_files} forms in\n{input_path}',
                                      pubsub_topic=DATA_EXTRACTION_TOPIC,
                                      maximum=num_files,
                                      abort_event=abort_event, *args, **kwargs)


class FormGenerationProgressDialog(WorkerProgressDialog):
    def __init__(self,
                 parent,
                 worker_id,
                 input_path,
                 abort_event=None,
                 *args,
                 **kwargs):
        WorkerProgressDialog.__init__(self,
                                      parent,
                                      worker_id,
                                      'Form generation progress',
                                      f'Generating OMR forms from \n{input_path}',
                                      pubsub_topic=FORM_GENERATION_TOPIC,
                                      abort_event=abort_event, *args, **kwargs)


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
        message_box_sizer.Add(
            message_text_object, proportion=1, flag=wx.EXPAND, border=5)
        message_box_sizer.Add((-1, 10), proportion=0)
        msg_text = self.msg if not fatal else '1. Click below to copy the error details to the clipboard,' \
                                              '\n 2. Email the error details to Shaun for support'
        message_box_sizer.Add(
            wx.StaticText(message_panel, label=msg_text, style=wx.ALIGN_LEFT),
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
