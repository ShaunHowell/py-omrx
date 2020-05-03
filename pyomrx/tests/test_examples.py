import os
import pytest
from pathlib import Path
from pyomrx.core.form_maker import FormMaker
from pyomrx.core.omr_factory import OmrFactory
import pandas as pd
from pyomrx.utils.test_utils import *


def test_attendance_register_example(request, res_folder):
    attendance_example_folder = Path('examples/attendance_register/')
    excel_file_path = attendance_example_folder / 'example attendance register.xlsx'

    def delete_temp_files():
        for path in attendance_example_folder.iterdir():
            if str(path) == str(excel_file_path):
                continue
            os.remove(str(path))

    request.addfinalizer(delete_temp_files)
    omr_file_path = attendance_example_folder / 'example attendance register.omr'
    example_output_file_path = attendance_example_folder / 'example_output.csv'
    form_maker = FormMaker(str(excel_file_path), str(omr_file_path))
    form_maker.make_form()
    omr_factory = OmrFactory.from_omr_file(str(omr_file_path))
    omr_factory.process_images_folder(
        str(attendance_example_folder), str(example_output_file_path))
    correct_result_path = Path(
        res_folder
    ) / 'correct_examples_answers/correct_result_attendance_register.csv'
    correct_df = pd.read_csv(str(correct_result_path))
    df = pd.read_csv(str(example_output_file_path))
    assert_correct_result(df, correct_df)


def test_exam_form_example(request, res_folder):
    exam_example_folder = Path('examples/example_exam_score_form/')
    excel_file_path = exam_example_folder / 'example exam score form.xlsx'

    def delete_temp_files():
        for path in exam_example_folder.iterdir():
            if str(path) == str(excel_file_path):
                continue
            os.remove(str(path))

    request.addfinalizer(delete_temp_files)
    omr_file_path = exam_example_folder / 'example exam score form.omr'
    example_output_file_path = exam_example_folder / 'example_output.csv'
    form_maker = FormMaker(str(excel_file_path), str(omr_file_path))
    form_maker.make_form()
    omr_factory = OmrFactory.from_omr_file(str(omr_file_path))
    omr_factory.process_images_folder(
        str(exam_example_folder), str(example_output_file_path))
    correct_result_path = Path(
        res_folder) / 'correct_examples_answers/correct_result_exam_form.csv'
    correct_df = pd.read_csv(str(correct_result_path))
    df = pd.read_csv(str(example_output_file_path))
    assert_correct_result(df, correct_df)


if __name__ == '__main__':
    pytest.main(['-s'])
