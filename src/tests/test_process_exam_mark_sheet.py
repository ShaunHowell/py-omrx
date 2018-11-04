import os
from unittest import TestCase, skip

from omr.exam_marksheet.processing import *
from omr.core.metrics import *

@skip("no longer supported")
class TestProcess_Exam_Mark_Sheet(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestProcess_Exam_Mark_Sheet, self).__init__(*args, **kwargs)
    def test_process_exam_mark_sheet(self):
        input_path = Path('tests/res/demo_2018_T2/data')
        output_folder = Path('tests/out')
        for file_path in output_folder.iterdir():
            os.remove(str(file_path))
        process_exam_marksheet_folder(str(input_path / 'images'),
                                      str(Path(input_path) / 'ext' / 'omr_form_designs.json'),
                                      str(output_folder))
        accuracy_results = find_omr_accuracy(str(output_folder / 'omr_output.csv'),
                                             str(input_path / 'exam_results' / 'human_processed_exam_results.csv'),
                                             str(input_path / 'ext' / 'omr_form_designs.json'))
        print('INFO: accuracy results:\n{}'.format(accuracy_results))
        self.assertLess(accuracy_results['incorrect'], 2)
        self.assertLess(accuracy_results['abstentions'], 6)