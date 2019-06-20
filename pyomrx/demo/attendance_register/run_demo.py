import os

from pyomrx.omr.attendance_register import process_attendance_sheet_folder
from pyomrx.omr.accuracy import *

input_path = Path('data')
output_folder = Path('data/out')
for file_path in output_folder.iterdir():
    os.remove(str(file_path))
process_attendance_sheet_folder(
    str(input_path / 'images'),
    str(Path(input_path) / 'ext' / 'omr_form_designs.json'),
    str(output_folder))
accuracy_results = find_omr_accuracy(
    str(output_folder / 'human_processed_attendance_register.csv'),
    str(input_path / 'attendance_results' /
        'human_processed_attendance_register.csv'),
    str(input_path / 'ext' / 'omr_form_designs.json'),
    omr_mode='attendance')
print('INFO: accuracy results:\n{}'.format(accuracy_results))
