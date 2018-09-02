import os
from unittest import TestCase

from omr.exam_marksheet.processing import *
from omr.core.metrics import *


class TestProcess_Exam_Mark_Sheet(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestProcess_Exam_Mark_Sheet, self).__init__(*args, **kwargs)
        print(os.getcwd())
    def test_process_exam_mark_sheet(self):
        input_path = Path('res/demo_2018_T2/data')
        output_folder = Path('out')
        for file_path in output_folder.iterdir():
            os.remove(str(file_path))
        process_images_folder(str(input_path / 'images'),
                              str(Path(input_path) / 'ext' / 'omr_form_designs.json'),
                              str(output_folder))
        accuracy_results = find_omr_accuracy(str(output_folder / 'omr_output.csv'),
                                             str(input_path / 'exam_results' / 'human_processed_exam_results.csv'),
                                             str(input_path / 'ext' / 'omr_form_designs.json'))
        print(accuracy_results)
        self.assertLess(accuracy_results['incorrect'], 2)
        self.assertLess(accuracy_results['abstentions'], 6)