import pytest
from pyomrx.core import *
from pyomrx.tests.fixtures import *
from pyomrx.core.form import process_form
import json


def test_blank_form_doesnt_crash(example_attendance_data_path, res_folder):
    input_image_path = Path(
        res_folder) / 'attendance_form_config/blank_omr_form.png'
    form_config = json.load(
        open(Path(res_folder) / 'attendance_form_config/omr_config.json'))
    process_form(str(input_image_path), form_config)
    # print(form_data)
    # accuracy_results = find_omr_accuracy(
    #     str(output_folder / 'attendance_omr_output.csv'),
    #     str(input_path / 'ext' / 'human_processed_attendance_register.csv'),
    #     str(input_path / 'ext' / 'omr_form_designs.json'),
    #     omr_mode='attendance')
    # print('INFO: accuracy results:\n{}'.format(accuracy_results))
    # assert accuracy_results[
    #     'incorrect'] < accuracy_results['total_responses'] * 0.01
    # assert accuracy_results[
    #     'abstentions'] < accuracy_results['total_responses'] * 0.05


if __name__ == '__main__':
    pytest.main(['-k', 'test_blank_form', '-sx'])
