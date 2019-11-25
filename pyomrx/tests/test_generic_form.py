import pytest
from pyomrx.omr.core import *
from pyomrx.tests.fixtures import *
from pyomrx.omr.accuracy import *


def test_blank_form(clean_out_folder,
                    example_attendance_data_path):
    input_image_path = Path(f'{__file__}/../res/form_config/omr_form.png')
    form_config = json.load(open(f'{__file__}/../res/form_config/omr_config.json'))
    # output_folder = Path(clean_out_folder)
    form_data = process_form(
        str(input_image_path),
        form_config)
    print(form_data)
    sys.exit(1)
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
    pytest.main(['-k', 'test_blank_form', '-sx'])
