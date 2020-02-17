# !/bin/python
import os
import time
import threading
import json
import zipfile
import sys
from pathlib import Path
import pyomrx
from pyomrx.core.meta import Abortable
from collections import defaultdict
from pyomrx.gui.events import *
from pyomrx.gui.dialogs import *
from pyomrx.gui.utils import handle_exception, open_folder
from pyomrx.gui.workers import *
from pyomrx import IMAGE_SUFFIXES
import wx

DEBUG = True


class PyomrxMainFrame(wx.Frame, Abortable):
    def __init__(self, *args, **kw):
        super(PyomrxMainFrame, self).__init__(*args, **kw)
        Abortable.__init__(self, None)
        sys.excepthook = handle_exception
        self.input_folder_path = Path(
            'pyomrx/tests/res/example_images_folder') if DEBUG else ''
        self.omr_data_output_path = Path(
            'pyomrx/tests/res/temp_output_file') if DEBUG else ''
        self.omr_config_path = Path(
            'pyomrx/tests/res/testing_form.omr') if DEBUG else ''
        self.excel_file_path = Path(
            'pyomrx/tests/res/Absence register v31.xlsx') if DEBUG else ''
        self.convert_output_folder_path = Path(
            'pyomrx/temp/forms') if DEBUG else ''
        self.buttons = defaultdict(lambda: dict())
        self.tabs = {}
        self.dialogs = []
        self.sizers = {}
        self.init_tabs()
        self.init_extract_data_tab()
        self.init_generate_forms_tab()
        self.init_statusbar()
        self.update_layout()
        self.Centre()
        self.batches_processing = 0
        self.forms_generating = 0
        self.statusbar.SetStatusText('ready')
        self.update_layout()
        self.Connect(-1, -1, EVT_DATA_EXT_NONFATAL_ID,
                     self.handle_data_extract_nonfatal_fail)
        self.Connect(-1, -1, EVT_DATA_EXT_START_ID,
                     self.handle_data_extract_start)
        self.Connect(-1, -1, EVT_DATA_EXT_SUCCESS_ID,
                     self.handle_data_extract_done)
        self.Connect(-1, -1, EVT_FORM_GEN_SUCCESS_ID,
                     self.handle_form_gen_done)
        self.Connect(-1, -1, EVT_FATAL_ID, self.handle_worker_exception)
        self.Connect(-1, -1, EVT_FORM_GEN_START_ID, self.handle_form_gen_start)
        self.Bind(wx.EVT_CLOSE, self.handle_close)
        self.worker_abort_events = {}

    def init_tabs(self):
        self.top_panel = wx.Panel(self)
        self.tab_holder = wx.Notebook(self.top_panel)
        self.tabs['extract_data'] = wx.Panel(self.tab_holder)
        self.tabs['generate_forms'] = wx.Panel(self.tab_holder)
        self.tab_holder.AddPage(self.tabs['extract_data'], "Extract data")
        self.tab_holder.AddPage(self.tabs['generate_forms'],
                                "Generate template")
        sizer = wx.BoxSizer()
        sizer.Add(self.tab_holder, 1, wx.EXPAND)
        self.top_panel.SetSizer(sizer)

    def add_button(self, tab, button_name, label, function, with_text=True):
        button = wx.Button(self.tabs[tab], label=label)
        button.SetMinSize((160, 40))
        path_text = wx.StaticText(
            self.tabs[tab], label='_' * 30) if with_text else None
        self.buttons[tab][button_name] = {'button': button, 'text': path_text}
        button.Bind(wx.EVT_BUTTON, function)

    def init_extract_data_tab(self):
        font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
        font.SetPointSize(9)

        self.add_button("extract_data", "template", "Open template",
                        self.choose_template)
        self.add_button("extract_data", "images", "Choose images folder",
                        self.choose_images_folder)
        self.add_button("extract_data", "output", "Choose output path",
                        self.choose_output_path)
        self.add_button(
            'extract_data',
            'process',
            'Process',
            self.extract_data_from_folder,
            with_text=False)

        border_width = 10
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.sizers['extract_data'] = vbox
        vbox.Add((-1, 20), proportion=0, border=border_width)

        for button_type, button_dict in self.buttons['extract_data'].items():
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
                vbox.Add(
                    hbox,
                    proportion=0,
                    flag=wx.ALIGN_LEFT | wx.ALIGN_BOTTOM | wx.ALL
                    | wx.ALIGN_CENTER_VERTICAL,
                    border=border_width)
            else:
                vbox.Add(
                    hbox,
                    proportion=0,
                    flag=wx.ALIGN_CENTRE | wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                    border=border_width)
            vbox.Add((-1, 5), proportion=0, border=border_width)
        vbox.Add((-1, 20), proportion=0, border=border_width)

    def init_generate_forms_tab(self):
        font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
        font.SetPointSize(9)

        self.add_button("generate_forms", "excel_file", "Choose template file",
                        self.choose_excel_file)
        self.add_button("generate_forms", "output", "Choose output folder",
                        self.choose_convert_output_folder)
        self.add_button(
            'generate_forms',
            'process',
            'Process',
            self.generate_forms,
            with_text=False)

        border_width = 10
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.sizers['generate_forms'] = vbox
        vbox.Add((-1, 20), proportion=0, border=border_width)

        text_hbox = wx.BoxSizer(wx.HORIZONTAL)
        text_hbox.Add(
            wx.StaticText(
                self.tabs['generate_forms'],
                label='OMR template description:'),
            proportion=0,
            flag=wx.ALIGN_LEFT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL,
            border=border_width)
        vbox.Add(
            text_hbox,
            proportion=0,
            flag=wx.ALIGN_LEFT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL,
            border=border_width)

        description_widget_hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.new_form_description_widget = wx.TextCtrl(
            self.tabs['generate_forms'],
            -1,
            '',
            wx.DefaultPosition,
            wx.Size(300, 30),
            style=wx.TE_BESTWRAP)
        description_widget_hbox.Add(
            self.new_form_description_widget,
            # proportion=0,
            flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND,
            border=border_width)
        vbox.Add(
            description_widget_hbox,
            # proportion=0,
            flag=wx.ALIGN_CENTRE | wx.ALL | wx.ALIGN_CENTER_VERTICAL
            | wx.EXPAND,
            border=border_width)
        vbox.Add((-1, 5), proportion=0, border=border_width)
        for button_type, button_dict in self.buttons['generate_forms'].items():
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
                vbox.Add(
                    hbox,
                    proportion=0,
                    flag=wx.ALIGN_LEFT | wx.ALIGN_BOTTOM | wx.ALL
                    | wx.ALIGN_CENTER_VERTICAL,
                    border=border_width)
            else:
                vbox.Add(
                    hbox,
                    proportion=0,
                    flag=wx.ALIGN_CENTRE | wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                    border=border_width)
            vbox.Add((-1, 5), proportion=0, border=border_width)

        vbox.Add((-1, 20), proportion=0, border=border_width)

    def init_statusbar(self):
        self.statusbar = self.CreateStatusBar(2)
        version_string = 'version: {}'.format(pyomrx.__version__)
        self.statusbar.SetStatusWidths([-1, len(version_string) * 5])
        self.statusbar.SetStatusText(version_string, 1)

    def choose_convert_output_folder(self, event):
        dialog = wx.DirDialog(
            self, 'Choose output folder', '', style=wx.DD_DEFAULT_STYLE)
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
            self.convert_output_folder_path = Path(path)
            text_objext = self.buttons['generate_forms']['output']['text']
            text_objext.SetLabel('...{}'.format(str(path)[-20:]))

    def choose_excel_file(self, event):
        dialog = wx.FileDialog(
            self,
            'Choose template file',
            '',
            wildcard='*.xls|*xlsx',
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
            self.excel_file_path = Path(path)
            text_objext = self.buttons['generate_forms']['excel_file']['text']
            text_objext.SetLabel(f'...{str(path)[-30:]}')
        self.update_layout()

    def choose_images_folder(self, event):
        dialog = wx.DirDialog(
            self, 'Choose images folder', '', style=wx.DD_DEFAULT_STYLE)
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
            text_objext = self.buttons['extract_data']['images']['text']
            text_objext.SetLabel('...{}'.format(str(path)[-20:]))
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
            self.omr_data_output_path = Path(path)
            if self.omr_data_output_path.suffix != '.csv':
                self.omr_data_output_path = Path(f'{path}.csv')
            text_objext = self.buttons['extract_data']['output']['text']
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
            self.omr_config_path = Path(path)
            text_objext = self.buttons['extract_data']['template']['text']
            text_objext.SetLabel(f'...{str(path)[-30:]}')
        self.update_layout()

    def extract_data_from_folder(self, event):
        input_folder_path = self.input_folder_path
        output_path = self.omr_data_output_path
        template_path = self.omr_config_path
        if not input_folder_path or not output_path or not template_path:
            wx.MessageDialog(
                self,
                'Please choose a template, input folder and output folder',
                style=wx.ICON_INFORMATION).ShowModal()
            return
        wx.PostEvent(self, DataExtractionStartEvent())
        omr_template = zipfile.ZipFile(template_path, 'r')
        template_json = omr_template.read('omr_config.json')
        template_dict = json.loads(template_json.decode())
        worker_thread = DataExtractionWorker(
            self,
            template_dict=template_dict,
            input_folder_path=input_folder_path,
            output_file_path=output_path)
        self.worker_abort_events[worker_thread.id] = worker_thread.abort_event
        num_files = len([
            path for path in Path(input_folder_path).iterdir()
            if path.suffix in IMAGE_SUFFIXES
        ])
        progress_dialog = DataExtractProgressDialog(
            worker_id=worker_thread.id,
            num_files=num_files,
            input_path=input_folder_path,
            parent=self,
            style=wx.PD_SMOOTH | wx.PD_AUTO_HIDE | wx.PD_CAN_ABORT
            | wx.PD_REMAINING_TIME | wx.PD_ELAPSED_TIME | wx.PD_SMOOTH,
            abort_event=worker_thread.abort_event)
        self.dialogs.append(progress_dialog)
        worker_thread.start()

    def generate_forms(self, event):
        excel_file_path = self.excel_file_path
        convert_output_folder_path = self.convert_output_folder_path
        description = self.new_form_description_widget.GetValue()
        if not excel_file_path or not convert_output_folder_path:
            wx.MessageDialog(
                self,
                'Please choose an input file, name, description and output folder',
                style=wx.ICON_INFORMATION).ShowModal()
            return
        output_omr_file_path = Path(
            f'{convert_output_folder_path}/{excel_file_path.stem}.omr')
        if output_omr_file_path.exists():
            replace_file = wx.MessageDialog(
                self,
                f'{output_omr_file_path} already exists, replace?',
                style=wx.ICON_INFORMATION | wx.YES | wx.NO).ShowModal()
            if replace_file == 5103:
                # YES
                os.remove(output_omr_file_path)
            else:
                return

        wx.PostEvent(self, FormGenerationStartEvent())
        worker_thread = FormGenerationWorker(
            self,
            excel_file_path=excel_file_path,
            output_folder_path=convert_output_folder_path,
            description=description)
        self.worker_abort_events[worker_thread.id] = worker_thread.abort_event
        progress_dialog = FormGenerationProgressDialog(
            worker_id=worker_thread.id,
            input_path=excel_file_path,
            parent=self,
            style=wx.PD_SMOOTH | wx.PD_AUTO_HIDE | wx.PD_CAN_ABORT
            | wx.PD_REMAINING_TIME | wx.PD_ELAPSED_TIME | wx.PD_SMOOTH,
            abort_event=worker_thread.abort_event)
        self.dialogs.append(progress_dialog)
        worker_thread.start()

    def handle_data_extract_start(self, event):
        self.batches_processing += 1
        self.update_status_text()

    def handle_form_gen_start(self, event):
        self.forms_generating += 1
        self.update_status_text()

    def handle_data_extract_nonfatal_fail(self, event):
        self.batches_processing -= 1
        self.update_status_text()

    def handle_data_extract_done(self, event):
        self.batches_processing -= 1
        self.update_status_text()
        success_dialog = wx.MessageDialog(
            self.tabs['extract_data'],
            message=
            f'Finished processing\n{event.input_path}\n\nOpen output folder?',
            style=wx.ICON_INFORMATION | wx.YES_NO | wx.NO_DEFAULT | wx.CENTRE,
            caption='Processing done').ShowModal()
        del self.worker_abort_events[event.worker_id]
        if success_dialog == 5103:
            open_folder(Path(event.output_path).parent)

    def handle_form_gen_done(self, event):
        self.forms_generating -= 1
        self.update_status_text()
        success_dialog = wx.MessageDialog(
            self.tabs['generate_forms'],
            message=
            f'Finished generating form from\n{event.input_path}\n\nOpen output folder?',
            style=wx.ICON_INFORMATION | wx.YES_NO | wx.NO_DEFAULT | wx.CENTRE,
            caption='Processing done').ShowModal()
        del self.worker_abort_events[event.worker_id]
        if success_dialog == 5103:
            open_folder(Path(event.output_path))

    def handle_worker_exception(self, event):
        raise event.exception

    def handle_close(self, event):
        self.abort()
        self.update_status_text()
        while len(threading.enumerate()) > 1:
            time.sleep(0.5)
        self.Destroy()

    def update_status_text(self):
        if self.abort_event.is_set():
            self.statusbar.PushStatusText('quitting')
        elif self.forms_generating:
            self.statusbar.PushStatusText(
                f'generating {self.forms_generating} '
                f'form{"s" if self.forms_generating > 1 else ""}')
        elif self.batches_processing:
            self.statusbar.PushStatusText(
                f'processing {self.batches_processing} '
                f'folder{"s" if self.batches_processing > 1 else ""}')
        else:
            self.statusbar.PushStatusText('ready')

    def update_layout(self):
        for tab in ['generate_forms', 'extract_data']:
            vbox = self.sizers[tab]
            vbox.SetSizeHints(self)
            self.tabs[tab].SetSizer(vbox)
        self.Fit()
        self.Layout()

    def abort(self):
        super().abort()
        for abort_event in self.worker_abort_events.values():
            abort_event.set()


def main():
    app = wx.App()
    frm = PyomrxMainFrame(
        None,
        wx.ID_ANY,
        title='OMR Tool',
        style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
    frm.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
