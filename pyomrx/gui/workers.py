import uuid
from threading import Thread

import pandas as pd
import wx

from pyomrx.core.exceptions import EmptyFolderException, AbortException
from pyomrx.core.form_maker import FormMaker
from pyomrx.core.meta import Abortable
from pyomrx.core.omr_factory import OmrFactory
from pyomrx.gui.events import DataExtractionNonFatalEvent, DataExtractionSuccessEvent, \
    FormGenerationSuccessEvent, FormGenerationNonFatalEvent
from pyomrx.gui.dialogs import ExceptionDialog


class DataExtractionWorker(Thread, Abortable):
    def __init__(self,
                 parent_window,
                 template_dict,
                 input_folder_path,
                 output_file_path,
                 abort_event=None):
        Thread.__init__(self)
        Abortable.__init__(self, abort_event)
        self.id = uuid.uuid4()
        self._parent_window = parent_window
        self.omr_factory = OmrFactory(
            template_dict, abort_event=self.abort_event, id=self.id)
        self.input_folder_path = input_folder_path
        self.output_file_path = output_file_path

    def run(self):
        try:
            df = self.omr_factory.process_images_folder(
                self.input_folder_path, self.output_file_path)
            if df is None:
                wx.PostEvent(self._parent_window,
                             DataExtractionNonFatalEvent())
            elif isinstance(df, pd.DataFrame):
                wx.PostEvent(
                    self._parent_window,
                    DataExtractionSuccessEvent(
                        data=df,
                        input_path=self.input_folder_path,
                        output_path=self.output_file_path,
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
            wx.PostEvent(self._parent_window, DataExtractionNonFatalEvent())
        except AbortException:
            print(f'aborted processing worker {self.id}')
            wx.PostEvent(self._parent_window, DataExtractionNonFatalEvent())


class FormGenerationWorker(Thread, Abortable):
    def __init__(self,
                 parent_window,
                 excel_file_path,
                 output_folder_path,
                 description,
                 abort_event=None):
        Thread.__init__(self)
        Abortable.__init__(self, abort_event)
        self.id = uuid.uuid4()
        self._parent_window = parent_window
        self.form_maker = FormMaker(
            excel_file_path=excel_file_path,
            output_folder=output_folder_path,
            description=description,
            abort_event=abort_event,
            id=self.id)
        self.excel_file_path = excel_file_path
        self.output_folder_path = output_folder_path

    def run(self):
        try:
            self.form_maker.make_form()
            wx.PostEvent(
                self._parent_window,
                FormGenerationSuccessEvent(
                    input_path=self.excel_file_path,
                    output_path=self.output_folder_path,
                    worker_id=self.id))
        except AbortException:
            print(f'aborted form generation worker {self.id}')
            wx.PostEvent(self._parent_window, FormGenerationNonFatalEvent())
