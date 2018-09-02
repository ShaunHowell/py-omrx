import os
from unittest import TestCase
from pathlib import Path
from omr.attendance_register.processing import *
from omr.core.metrics import *


class TestProcess_Attendance_Register(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestProcess_Attendance_Register, self).__init__(*args, **kwargs)
    def test_process_attendance_register(self):
        input_path = Path('tests/res/attendance_register_demo/data')
        output_folder = Path('tests/out')
        for file_path in output_folder.iterdir():
            os.remove(str(file_path))
        process_attendance_sheet_folder(str(input_path / 'images'),
                              str(Path(input_path) / 'ext' / 'omr_form_designs.json'),
                              str(output_folder))
        accuracy_results = find_omr_accuracy(str(output_folder / 'omr_output.csv'),
                                             str(input_path / 'exam_results' / 'human_processed_attendance_register.csv'),
                                             str(input_path / 'ext' / 'omr_form_design.json'))
        print(accuracy_results)
        self.assertLess(accuracy_results['incorrect'], 2)
        self.assertLess(accuracy_results['abstentions'], 6)