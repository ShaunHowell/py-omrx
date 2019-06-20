import os
from pyomrx.omr.exam_marksheet import process_exam_marksheet_folder
from pyomrx.omr.accuracy import *
import pytest
from pathlib import Path
from pyomrx.tests.fixtures import *
from pyomrx.omr.core import response_from_darknesses


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
        str(output_folder / 'exam_omr_output.csv'),
        str(input_path / 'exam_results' / 'human_processed_exam_results.csv'),
        str(input_path / 'ext' / 'omr_form_designs.json'))
    print('INFO: accuracy results:\n{}'.format(accuracy_results))
    assert accuracy_results['incorrect'] < 2
    assert accuracy_results['abstentions'] < 6


def test_process_exam_mark_sheet_may_2019(clean_out_folder,
                                          example_exam_data_path_2):
    input_path = Path(example_exam_data_path_2)
    output_folder = Path(clean_out_folder)
    process_exam_marksheet_folder(
        str(input_path / 'images'),
        str(Path(input_path) / 'ext' / 'omr_form_designs.json'),
        str(output_folder))
    accuracy_results = find_omr_accuracy(
        str(output_folder / 'exam_omr_output.csv'),
        str(input_path / 'exam_results' / 'human_processed_exam_results.csv'),
        str(input_path / 'ext' / 'omr_form_designs.json'))
    print('INFO: accuracy results:\n{}'.format(accuracy_results))
    assert accuracy_results['total_responses'] == 225
    assert accuracy_results['incorrect'] == 0
    assert accuracy_results['abstentions'] == 0


def test_handles_broken_border(clean_out_folder,
                               example_exam_data_path_broken_outer_box):
    input_path = Path(example_exam_data_path_broken_outer_box)
    output_folder = Path(clean_out_folder)
    for file_path in output_folder.iterdir():
        os.remove(str(file_path))
    process_exam_marksheet_folder(
        str(input_path / 'images'),
        str(Path(input_path) / 'ext' / 'omr_form_designs.json'),
        str(output_folder))
    accuracy_results = find_omr_accuracy(
        str(output_folder / 'exam_omr_output.csv'),
        str(input_path / 'exam_results' / 'human_processed_exam_results.csv'),
        str(input_path / 'ext' / 'omr_form_designs.json'))
    print('INFO: accuracy results:\n{}'.format(accuracy_results))
    assert accuracy_results['total_responses'] == 171
    assert accuracy_results['incorrect'] == 0
    assert accuracy_results['abstentions'] == 0


def test_good_response_from_darknesses():
    example = [
        0.17548420642142207, 0.21935525802677758, 0.20798128168464836,
        0.15436110750032495, 0.180358767710906, 0.20473157415832574,
        0.9960353568178864, 0.18523332900038994, 0.32288229793390616,
        0.20960613544780968
    ]
    assert response_from_darknesses(example) == 6


def test_no_response_from_darknesses():
    example = [0.1706096451319381, 0.2915782024062279]
    assert response_from_darknesses(example) == -1


def test_double_response_from_darknesses():
    example = [
        0.17548420642142207, 0.21935525802677758, 0.9960353568178864,
        0.15436110750032495, 0.180358767710906, 0.20473157415832574,
        0.9960353568178864, 0.18523332900038994, 0.32288229793390616,
        0.20960613544780968
    ]
    assert response_from_darknesses(example) == -2


def test_middle_ground_abstention_response_from_darknesses():
    example = [0.5, 0.5, 0.5, 0.5, 0.32288229793390616, 0.20960613544780968]
    assert response_from_darknesses(example) == -3


def test_closeness_abstention_response_from_darknesses():
    example = [0.59, 0.7, 0.5, 0.5, 0.32288229793390616, 0.20960613544780968]
    assert response_from_darknesses(example) == -3


if __name__ == '__main__':
    pytest.main(['-sxk', 'broken_border'])
