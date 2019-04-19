import os
from omr.exam_marksheet import process_exam_marksheet_folder
from omr.accuracy import *
import pytest
from pathlib import Path
from tests.fixtures import clean_out_folder, example_exam_data_path


def test_process_exam_mark_sheet(clean_out_folder, example_exam_data_path):
    input_path = Path(example_exam_data_path)
    output_folder = Path(clean_out_folder)
    for file_path in output_folder.iterdir():
        os.remove(str(file_path))
    process_exam_marksheet_folder(
        str(input_path / 'images'),
        str(Path(input_path) / 'ext' / 'omr_form_designs.json'),
        str(output_folder))
    accuracy_results = find_omr_accuracy(
        str(output_folder / 'human_processed_attendance_register.csv'),
        str(input_path / 'exam_results' / 'human_processed_exam_results.csv'),
        str(input_path / 'ext' / 'omr_form_designs.json'))
    print('INFO: accuracy results:\n{}'.format(accuracy_results))
    assert accuracy_results['incorrect'] < 2
    assert accuracy_results['abstentions'] < 6
