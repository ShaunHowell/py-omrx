import pytest
import os
import shutil
from pathlib import Path


@pytest.fixture
def example_attendance_data_path():
    tests_folder = Path(__file__).parent
    assert str(tests_folder.parts[-1]) == 'tests'
    res_folder = str(tests_folder / 'res')
    return str(Path(res_folder) / 'attendance_register' / 'sub_form_data')


@pytest.fixture
def example_attendance_data_path_three_sheets():
    tests_folder = Path(__file__).parent
    assert str(tests_folder.parts[-1]) == 'tests'
    res_folder = str(tests_folder / 'res')
    return str(Path(res_folder) / 'attendance_register' / 'data_three_sheets')


@pytest.fixture
def example_exam_data_path(res_folder):
    return str(Path(res_folder) / 'exam_marksheet' / 'sub_form_data')


@pytest.fixture
def res_folder():
    tests_folder = Path(__file__).parent
    assert str(tests_folder.parts[-1]) == 'tests'
    res_folder = str(tests_folder / 'res')
    return res_folder
