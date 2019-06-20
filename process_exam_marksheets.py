import sys
import os
from pyomrx.omr.exam_marksheet import process_exam_marksheet_folder
from pyomrx.omr.accuracy import *
import pytest
from pathlib import Path
from pyomrx.tests.fixtures import clean_out_folder, example_exam_data_path, example_exam_data_path_2
from pyomrx.omr.core import response_from_darknesses
from pyomrx.omr.exceptions import OmrException

input_input_folder = 'C:/Users/Shaun/Downloads/SCUK_may_2019_exams'
for input_path in Path(input_input_folder).iterdir():
    # if input_path.parts[-1] != 'Photo scans root folder':
    #     continue
    if 'output' in input_path.parts[-1]:
        continue
    input_path = Path(input_path)
    output_folder = Path(input_input_folder) / 'output' / input_path.parts[-1]
    try:
        process_exam_marksheet_folder(
            str(input_path),
            str(
                Path(
                    'C:/Users/Shaun/PycharmProjects/py-omrx/exam_omr_form_designs.json'
                )), str(output_folder))
    except OmrException as e:
        print(e, file=sys.stderr)
