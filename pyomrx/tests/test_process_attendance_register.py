import pytest
from pyomrx.omr.attendance_register import process_attendance_sheet_folder
from pyomrx.tests.fixtures import *
from pyomrx.omr.accuracy import *


def test_process_attendance_register(clean_out_folder,
                                     example_attendance_data_path):
    input_path = Path(example_attendance_data_path)
    output_folder = Path(clean_out_folder)
    for file_path in output_folder.iterdir():
        os.remove(str(file_path))
    process_attendance_sheet_folder(
        str(input_path / 'images'),
        str(Path(input_path) / 'ext' / 'omr_form_designs.json'),
        str(output_folder))
    accuracy_results = find_omr_accuracy(
        str(output_folder / 'attendance_omr_output.csv'),
        str(input_path / 'ext' / 'human_processed_attendance_register.csv'),
        str(input_path / 'ext' / 'omr_form_designs.json'),
        omr_mode='attendance')
    print('INFO: accuracy results:\n{}'.format(accuracy_results))
    assert accuracy_results[
        'incorrect'] < accuracy_results['total_responses'] * 0.01
    assert accuracy_results[
        'abstentions'] < accuracy_results['total_responses'] * 0.05


def test_process_attendance_register_three_sheets(
        clean_out_folder, example_attendance_data_path_three_sheets):
    input_path = Path(example_attendance_data_path_three_sheets)
    output_folder = Path(clean_out_folder)
    for file_path in output_folder.iterdir():
        os.remove(str(file_path))
    process_attendance_sheet_folder(
        str(input_path / 'images'),
        str(Path(input_path) / 'ext' / 'omr_form_designs.json'),
        str(output_folder))
    accuracy_results = find_omr_accuracy(
        str(output_folder / 'attendance_omr_output.csv'),
        str(input_path / 'ext' / 'human_processed_attendance_register.csv'),
        str(input_path / 'ext' / 'omr_form_designs.json'),
        omr_mode='attendance')
    print('INFO: accuracy results:\n{}'.format(accuracy_results))
    assert accuracy_results[
        'incorrect'] < accuracy_results['total_responses'] * 0.01
    assert accuracy_results[
        'abstentions'] < accuracy_results['total_responses'] * 0.05


if __name__ == '__main__':
    pytest.main(['-k', 'test_process_attendance_register_three_sheets', '-sx'])
