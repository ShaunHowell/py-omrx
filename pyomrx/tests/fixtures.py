import pytest
import os
import shutil
from pathlib import Path


@pytest.fixture
def clean_out_folder(request):
    out_folder_path = Path(__file__).parent / 'out'

    def delete_folder():
        shutil.rmtree(str(out_folder_path))

    if out_folder_path.exists():
        delete_folder()
    os.mkdir(str(out_folder_path))
    request.addfinalizer(delete_folder)
    return str(out_folder_path)


@pytest.fixture
def example_attendance_data_path():
    tests_folder = Path(__file__).parent
    assert str(tests_folder.parts[-1]) == 'tests'
    res_folder = str(tests_folder / 'res')
    return str(Path(res_folder) / 'attendance_register' / 'data')


@pytest.fixture
def example_attendance_data_path_three_sheets():
    tests_folder = Path(__file__).parent
    assert str(tests_folder.parts[-1]) == 'tests'
    res_folder = str(tests_folder / 'res')
    return str(Path(res_folder) / 'attendance_register' / 'data_three_sheets')


@pytest.fixture
def example_exam_data_path():
    tests_folder = Path(__file__).parent
    assert str(tests_folder.parts[-1]) == 'tests'
    res_folder = str(tests_folder / 'res')
    return str(Path(res_folder) / 'exam_marksheet' / 'data')


@pytest.fixture
def example_exam_data_path_2():
    tests_folder = Path(__file__).parent
    assert str(tests_folder.parts[-1]) == 'tests'
    res_folder = str(tests_folder / 'res')
    return str(Path(res_folder) / 'exam_marksheet' / 'data_2')


@pytest.fixture
def example_exam_data_path_broken_outer_box():
    tests_folder = Path(__file__).parent
    assert str(tests_folder.parts[-1]) == 'tests'
    res_folder = str(tests_folder / 'res')
    return str(Path(res_folder) / 'exam_marksheet' / 'data_broken_outer_box')
