import os
from unittest import TestCase
from pathlib import Path
from omr_tool.omr.attendance_register.processing import *
from omr_tool.omr.core.metrics import *
import pytest

class TestProcess_Attendance_Register(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestProcess_Attendance_Register, self).__init__(*args, **kwargs)
    def test_process_attendance_register(self):
        input_path = Path('omr_tool/tests/res/attendance_register_demo/data')
        output_folder = Path('omr_tool/tests/out')
        for file_path in output_folder.iterdir():
            os.remove(str(file_path))
        process_attendance_sheet_folder(str(input_path / 'images'),
                                        str(Path(input_path) / 'ext' / 'omr_form_designs.json'),
                                        str(output_folder))
        accuracy_results = find_omr_accuracy(str(output_folder / 'omr_output.csv'),
                                             str(input_path / 'attendance_results' / 'human_processed_attendance_register.csv'),
                                             str(input_path / 'ext' / 'omr_form_designs.json'),
                                             omr_mode='attendance')
        print('INFO: accuracy results:\n{}'.format(accuracy_results))
        self.assertLess(accuracy_results['incorrect'], accuracy_results['total_responses']*0.01)
        self.assertLess(accuracy_results['abstentions'], accuracy_results['total_responses']*0.05)

