# TODO: progress bar shouldn't block the main application
# !/bin/python
import uuid
import time
import pandas as pd
from threading import Thread
from threading import Event
import threading
from pyomrx.omr.omr_factory import OmrFactory
import json
import zipfile
import traceback
import sys
import wx
import webbrowser
from pathlib import Path
from pyomrx.omr.exceptions import *
import pyomrx
from pubsub import pub
from pyomrx.omr.meta import Abortable

EVT_SUCCESS_ID = wx.NewId()
EVT_NONFATAL_ID = wx.NewId()
EVT_PROCESSING_START_ID = wx.NewId()

DEBUG = True


class PyomrxMainFrame(wx.Frame, Abortable):
    def __init__(self, *args, **kw):
        super(PyomrxMainFrame, self).__init__(*args, **kw)
        Abortable.__init__(self, None)
        sys.excepthook = ExceptionHandler
        self.input_folder_path = Path(
            'pyomrx/tests/res/example_images_folder') if DEBUG else ''
        self.output_path = Path(
            'pyomrx/tests/res/temp_output_file') if DEBUG else ''
        self.template_path = Path(
            'pyomrx/tests/res/testing_form.omr') if DEBUG else ''
        self.buttons = []
        self.panel = wx.Panel(self)
        self.create_buttons()
        self.init_ui()
        self.Centre()
        self.batches_processing = 0
        self.statusbar.SetStatusText('ready')
        self.update_layout()
        self.Connect(-1, -1, EVT_NONFATAL_ID,
                     self.handle_processing_nonfatal_fail)
        self.Connect(-1, -1, EVT_PROCESSING_START_ID,
                     self.handle_processing_start)
        self.Connect(-1, -1, EVT_SUCCESS_ID, self.handle_processing_done)
        self.Bind(wx.EVT_CLOSE, self.handle_close)
        self.worker_abort_events = {}

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

        create_button("template", "Open template",
                      getattr(self, 'choose_template'))
        create_button("images", "Choose images folder",
                      getattr(self, 'choose_images_folder'))
        create_button("output", "Choose output path",
                      getattr(self, 'choose_output_path'))
        create_button(
            'process',
            'Process images',
            self.handle_process_images,
            with_text=False)

    def init_ui(self):
        border_width = 10
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add((-1, 20), proportion=0, border=border_width)

        # hbox = wx.BoxSizer(wx.HORIZONTAL)
        # hbox.Add(
        #     wx.StaticText(self.panel, label='Form type:'),
        #     proportion=0,
        #     flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL,
        #     border=border_width)
        # self.form_type_dropdown = wx.Choice(
        #     self.panel, choices=['exam marksheet', 'attendance register'])
        # self.form_type_dropdown.SetSelection(0)
        # hbox.Add(
        #     self.form_type_dropdown,
        #     proportion=0,
        #     flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL,
        #     border=border_width)
        # self.vbox.Add(
        #     hbox,
        #     proportion=0,
        #     flag=wx.ALIGN_CENTRE | wx.ALL | wx.ALIGN_CENTER_VERTICAL,
        #     border=border_width)
        # self.vbox.Add((-1, 5), proportion=0, border=border_width)

        for button_type, button_dict in self.buttons:
            hbox = wx.BoxSizer(wx.HORIZONTAL)
            hbox.Add(
                button_dict['button'],
                proportion=0,
                flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                border=border_width)
            if button_dict['text']:
                hbox.Add(
                    button_dict['text'],
                    proportion=0,
                    flag=wx.ALIGN_LEFT | wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                    border=border_width)
                self.vbox.Add(
                    hbox,
                    proportion=0,
                    flag=wx.ALIGN_LEFT | wx.ALIGN_BOTTOM | wx.ALL
                    | wx.ALIGN_CENTER_VERTICAL,
                    border=border_width)
            else:
                self.vbox.Add(
                    hbox,
                    proportion=0,
                    flag=wx.ALIGN_CENTRE | wx.ALL | wx.ALIGN_CENTER_VERTICAL,
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
            self.input_folder_path = Path(path)
            text_objext = next(
                (object[1]['text']
                 for object in self.buttons if object[0] == 'images'), None)
            text_objext.SetLabel('...{}'.format(str(path)[-30:]))
        self.update_layout()

    def choose_output_path(self, event):
        dialog = wx.FileDialog(
            self, 'Save output csv as...', '', style=wx.DD_DEFAULT_STYLE)
        try:
            if dialog.ShowModal() == wx.ID_CANCEL:
                return
            path = dialog.GetPath()
        except Exception:
            wx.LogError('Failed to choose desired path!')
            raise
        finally:
            dialog.Destroy()
        if len(path) > 0:
            self.output_path = Path(path)
            if self.output_path.suffix != '.csv':
                self.output_path = Path(f'{path}.csv')
            text_objext = next(
                (object[1]['text']
                 for object in self.buttons if object[0] == 'output'), None)
            text_objext.SetLabel('...{}'.format(str(path)[-30:]))
        self.update_layout()

    def choose_template(self, event):
        dialog = wx.FileDialog(
            self,
            'Choose template file',
            '',
            wildcard='*.omr',
            style=wx.DD_DEFAULT_STYLE)
        try:
            if dialog.ShowModal() == wx.ID_CANCEL:
                return
            path = dialog.GetPath()
        except Exception:
            wx.LogError('Failed to select file!')
            raise
        finally:
            dialog.Destroy()
        if len(path) > 0:
            self.template_path = Path(path)
            text_objext = next(
                (object[1]['text']
                 for object in self.buttons if object[0] == 'template'), None)
            text_objext.SetLabel(f'...{str(path)[-30:]}')
        self.update_layout()

    def update_layout(self):
        self.vbox.SetSizeHints(self)
        self.panel.SetSizer(self.vbox)
        self.Fit()
        self.Layout()

    def open_folder(self, path):
        if Path(path).is_file():
            path = path.parent
        webbrowser.open(str(path))

    def handle_process_images(self, event):
        input_folder_path = self.input_folder_path
        output_path = self.output_path
        template_path = self.template_path
        if not input_folder_path or not output_path or not template_path:
            wx.MessageDialog(
                self,
                'Please choose a template, input folder and output folder',
                style=wx.ICON_INFORMATION).ShowModal()
            return
        wx.PostEvent(self, ProcessingStartEvent())
        omr_template = zipfile.ZipFile(template_path, 'r')
        template_json = omr_template.read('omr_config.json')
        template_dict = json.loads(template_json.decode())
        worker_thread = FormProcessingWorker(
            self,
            template_dict=template_dict,
            input_folder_path=input_folder_path,
            output_folder_path=output_path)
        self.worker_abort_events[worker_thread.id] = worker_thread.abort_event
        num_files = len(list(Path(input_folder_path).iterdir()))
        progress_dialog = ProcessingProgressDialog(
            worker_id=worker_thread.id,
            num_files=num_files,
            input_path=input_folder_path,
            parent=self,
            style=wx.PD_SMOOTH | wx.PD_AUTO_HIDE | wx.PD_CAN_ABORT
            | wx.PD_REMAINING_TIME | wx.PD_ELAPSED_TIME | wx.PD_SMOOTH,
            abort_event=worker_thread.abort_event)
        worker_thread.start()

    def handle_processing_start(self, event):
        self.batches_processing += 1
        self.update_status_text()

    def update_status_text(self):
        if self.abort_event.is_set():
            self.statusbar.PushStatusText('quitting')
        elif self.batches_processing:
            self.statusbar.PushStatusText(
                f'processing {self.batches_processing} '
                f'folder{"s" if self.batches_processing > 1 else ""}')
        else:
            self.statusbar.PushStatusText('ready')

    def handle_processing_nonfatal_fail(self, event):
        self.batches_processing -= 1
        self.update_status_text()

    def handle_processing_done(self, event):
        self.batches_processing -= 1
        self.update_status_text()
        success_dialog = wx.MessageDialog(
            self.panel,
            message=
            f'Finished processing\n{event.input_path}\n\nOpen output folder?',
            style=wx.ICON_INFORMATION | wx.YES_NO | wx.NO_DEFAULT | wx.CENTRE,
            caption='Processing done').ShowModal()
        del self.worker_abort_events[event.worker_id]
        if success_dialog == 5103:
            self.open_folder(Path(event.output_path).parent)

    def handle_close(self, event):
        self.abort()
        self.update_status_text()
        while len(threading.enumerate()) > 1:
            time.sleep(0.5)
        self.Destroy()

    def abort(self):
        super().abort()
        for abort_event in self.worker_abort_events.values():
            abort_event.set()


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


class ProcessingSuccessEvent(wx.PyEvent):
    def __init__(self, data, input_path, output_path, worker_id):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_SUCCESS_ID)
        self.data = data
        self.input_path = input_path
        self.output_path = output_path
        self.worker_id = worker_id


class ProcessingNonFatalEvent(wx.PyEvent):
    def __init__(self):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_NONFATAL_ID)


class ProcessingStartEvent(wx.PyEvent):
    def __init__(self):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_PROCESSING_START_ID)


class FormProcessingWorker(Thread, Abortable):
    def __init__(self,
                 parent_window,
                 template_dict,
                 input_folder_path,
                 output_folder_path,
                 abort_event=None):
        Thread.__init__(self)
        Abortable.__init__(self, abort_event)
        self.id = uuid.uuid4()
        self._parent_window = parent_window
        self.omr_factory = OmrFactory(
            template_dict, abort_event=self.abort_event, id=self.id)
        self.input_folder_path = input_folder_path
        self.output_folder_path = output_folder_path

    def run(self):
        try:
            df = self.omr_factory.process_images_folder(
                self.input_folder_path, self.output_folder_path)
            if df is None:
                wx.PostEvent(self._parent_window, ProcessingNonFatalEvent())
            elif isinstance(df, pd.DataFrame):
                wx.PostEvent(
                    self._parent_window,
                    ProcessingSuccessEvent(
                        data=df,
                        input_path=self.input_folder_path,
                        output_path=self.output_folder_path,
                        worker_id=self.id))
            else:
                raise TypeError(
                    f'got unexpected return type {type(df)} from omr factory')
        except EmptyFolderException as e:
            print(e)
            dlg = ExceptionDialog(
                'No image files found in the selected folder',
                parent=None,
                fatal=False,
                title='Error')
            dlg.ShowModal()
            dlg.Destroy()
            wx.PostEvent(self._parent_window, ProcessingNonFatalEvent())
        except AbortException:
            print(f'aborted processing worker {self.id}')
            wx.PostEvent(self._parent_window, ProcessingNonFatalEvent())


class ProcessingProgressDialog(wx.GenericProgressDialog, Abortable):
    def __init__(self,
                 parent,
                 worker_id,
                 num_files,
                 input_path,
                 abort_event=None,
                 *args,
                 **kwargs):
        self.parent = parent
        wx.GenericProgressDialog.__init__(
            self,
            parent=parent,
            title='OMR progress',
            message=f'Processing {num_files} forms in\n{input_path}',
            maximum=num_files,
            *args,
            **kwargs)
        Abortable.__init__(self, abort_event)
        self.Bind(wx.EVT_CLOSE, self.close)
        self.Connect(-1, -1, wx.ID_CANCEL, self.close)
        pub.subscribe(self.increment_files_processed,
                      f'{worker_id}.file_processed')
        self.num_files_processed = 0
        self.recursive_close_if_aborted()

    def increment_files_processed(self):
        self.num_files_processed += 1
        self.Update(self.num_files_processed)
        self.close_if_cancelled()

    def close_if_cancelled(self):
        if self.abort_event.is_set():
            # already been closed
            return True
        if self.WasCancelled():
            self.close('')
            return True
        return False

    def recursive_close_if_aborted(self):
        if not self.close_if_cancelled():
            wx.CallLater(250, self.recursive_close_if_aborted)

    def close(self, event):
        # will need multiple abort events to be able to abort for individual folders
        self.abort()
        self.Destroy()


def main():
    app = wx.App()
    frm = PyomrxMainFrame(None, wx.ID_ANY, title='OMR Tool')
    frm.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
