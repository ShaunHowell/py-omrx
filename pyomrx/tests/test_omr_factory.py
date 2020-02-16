import pandas as pd
from pyomrx.core.omr_factory import OmrFactory
import pytest
import json
from pathlib import Path


@pytest.fixture
def attendance_omr_factory_1(res_folder):
    config = json.load(
        open(
            str(
                Path(res_folder) / 'attendance_form_config' /
                'omr_config.json')))
    return OmrFactory(config)


class TestAttendanceForms:
    def test_process_images_folder(self, res_folder, attendance_omr_factory_1):
        image_folder_path = str(Path(res_folder) / 'example_images_folder')
        df = attendance_omr_factory_1.process_images_folder(image_folder_path)
        trues = [(0, 'A01'), (-1, 'A01'), (0, 'dropout'), (-1, 'dropout')]
        for i, j in trues:
            assert df[j].iloc[i] == True

    def test_process_example_folder(self, res_folder):
        config = json.load(
            open(str(Path(res_folder) / 'feb_example' / 'omr_config.json')))
        omr_factory = OmrFactory(config)
        image_folder_path = str(Path(res_folder) / 'feb_example' / 'images')
        df = omr_factory.process_images_folder(image_folder_path)
        correct_result = pd.read_csv(
            str(Path(res_folder) / 'feb_example' / 'correct_result.csv'),
            index_col=0)
        print(df.to_string())
        assert df.to_dict() == correct_result.to_dict()

    def test_process_example_scan_folder(self, res_folder):
        config = json.load(
            open(str(Path(res_folder) / 'scan_example' / 'omr_config.json')))
        omr_factory = OmrFactory(config)
        image_folder_path = str(Path(res_folder) / 'scan_example' / 'images')
        df = omr_factory.process_images_folder(image_folder_path)
        correct_result = pd.read_csv(
            str(Path(res_folder) / 'scan_example' / 'correct_result.csv'),
            index_col=0)
        print(df.to_string())
        assert df.to_dict() == correct_result.to_dict()


class TestExamForms:
    def test_process_exam_images_folder(self, res_folder,
                                        attendance_omr_factory_1):
        config = json.load(
            open(
                str(
                    Path(res_folder) / 'exam_form' / 'full_form' /
                    'omr_config.json')))
        omr_factory = OmrFactory(config)
        image_folder_path = str(
            Path(res_folder) / 'exam_form' / 'full_form' / 'images')
        df = omr_factory.process_images_folder(image_folder_path)
        correct_result = pd.read_csv(
            str(
                Path(res_folder) / 'exam_form' / 'full_form' /
                'correct_result.csv'),
            index_col=0)
        print('extracted data:')
        print(df.to_string())
        assert df.to_dict() == correct_result.to_dict()


if __name__ == '__main__':
    pytest.main(['-k', 'test_process_exam_images_folder', '-s'])
