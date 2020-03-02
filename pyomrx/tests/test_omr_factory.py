import numpy as np
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
        df = df.sort_values(by=['file', 'sub_form'])
        df = df.sort_index(axis=1)

        correct_result = pd.read_csv(
            str(Path(res_folder) / 'feb_example' / 'correct_result.csv'),
            index_col=0)
        correct_result = correct_result.sort_values(by=['file', 'sub_form'])
        correct_result = correct_result.sort_index(axis=1)

        print(df.to_string())
        assert df.equals(correct_result)

    def test_process_example_scan_folder(self, res_folder):
        config = json.load(
            open(str(Path(res_folder) / 'scan_example' / 'omr_config.json')))
        omr_factory = OmrFactory(config)
        image_folder_path = str(Path(res_folder) / 'scan_example' / 'images')
        df = omr_factory.process_images_folder(image_folder_path)
        df = df.sort_values(by=['file', 'sub_form'])
        df = df.sort_index(axis=1)

        correct_result = pd.read_csv(
            str(Path(res_folder) / 'scan_example' / 'correct_result.csv'),
            index_col=0)
        correct_result = correct_result.sort_values(by=['file', 'sub_form'])
        correct_result = correct_result.sort_index(axis=1)

        print(df.to_string())
        assert df.equals(correct_result)


class TestExamForms:
    def test_process_exam_images_folder(self, res_folder):
        config = json.load(
            open(
                str(
                    Path(res_folder) / 'exam_form' / 'full_form' /
                    'omr_config.json')))
        omr_factory = OmrFactory(config)
        image_folder_path = str(
            Path(res_folder) / 'exam_form' / 'full_form' / 'images')
        df = omr_factory.process_images_folder(image_folder_path)
        df = df.sort_values(by=['file', 'sub_form'])
        df = df.sort_index(axis=1)

        correct_result = pd.read_csv(
            str(
                Path(res_folder) / 'exam_form' / 'full_form' /
                'correct_result.csv'),
            index_col=0)
        correct_result = correct_result.sort_values(by=['file', 'sub_form'])
        correct_result = correct_result.sort_index(axis=1)

        print('extracted data:')
        print(df.to_string())
        assert df.to_dict() == correct_result.to_dict()

    def test_process_old_forms(self, res_folder):
        config = json.load(
            open(
                str(
                    Path(res_folder) / 'exam_form' / 'old_full_form' /
                    'omr_config.json')))
        omr_factory = OmrFactory(config)
        image_folder_path = str(
            Path(res_folder) / 'exam_form' / 'old_full_form' / 'images')
        df = omr_factory.process_images_folder(image_folder_path)
        correct_result = pd.read_csv(
            str(
                Path(res_folder) / 'exam_form' / 'old_full_form' /
                'correct_result.csv'),
            index_col=0)
        print('extracted data:')
        df = df.sort_values(by=['file', 'sub_form'])
        df = df.sort_index(axis=1)
        print(df.to_string())
        print('correct data:')
        correct_result = correct_result.sort_values(by=['file', 'sub_form'])
        correct_result = correct_result.sort_index(axis=1)
        print(correct_result.to_string())
        assert df.equals(correct_result)

    def test_process_problem_old_forms_math_l2(self, res_folder):
        config = json.load(
            open(
                str(
                    Path(res_folder) / 'exam_form' / 'problem_scans' /
                    'omr_config.json')))
        omr_factory = OmrFactory(config)
        image_folder_path = str(
            Path(res_folder) / 'exam_form' / 'problem_scans' / 'images')
        df = omr_factory.process_images_folder(image_folder_path)
        correct_result = pd.read_csv(
            str(
                Path(res_folder) / 'exam_form' / 'problem_scans' /
                'correct_result.csv'),
            index_col=0)
        print('extracted data:')
        df = df.sort_values(by=['file', 'sub_form'])
        df = df.sort_index(axis=1)
        print(df.to_string())
        print('correct data:')
        correct_result = correct_result.sort_values(by=['file', 'sub_form'])
        correct_result = correct_result.sort_index(axis=1)
        print(correct_result.to_string())
        for df_row, correct_row in zip(df.iterrows(),
                                       correct_result.iterrows()):
            df_row = df_row[1]
            correct_row = correct_row[1]
            df_cells = df_row.iteritems()
            correct_cells = correct_row.iteritems()
            for df_cell, correct_cell in zip(df_cells, correct_cells):
                if df_cell != correct_cell:
                    raise ValueError(
                        f'{df_cell} != {correct_cell}\nRow: {df_row}')
        # assert correct_result.select_dtypes(exclude=[np.number]) == df.select_dtypes(exclude=[np.number])
        # assert correct_result.select_dtypes(include=[np.number]).astype(np.float()) == \
        #        df.select_dtypes(include=[np.number]).astype(np.float())

    def test_process_problem_old_forms_lang_l2(self, res_folder):
        config = json.load(
            open(
                str(
                    Path(res_folder) / 'exam_form' / 'problem_scans_lang_L2' /
                    'omr_config.json')))
        omr_factory = OmrFactory(config)
        image_folder_path = str(
            Path(res_folder) / 'exam_form' / 'problem_scans_lang_L2' /
            'images')
        df = omr_factory.process_images_folder(image_folder_path)
        correct_result = pd.read_csv(
            str(
                Path(res_folder) / 'exam_form' / 'problem_scans_lang_L2' /
                'correct_result.csv'),
            index_col=0)
        print('extracted data:')
        df = df.sort_values(by=['file', 'sub_form'])
        df = df.sort_index(axis=1)
        print(df.to_string())
        print('correct data:')
        correct_result = correct_result.sort_values(by=['file', 'sub_form'])
        correct_result = correct_result.sort_index(axis=1)
        print(correct_result.to_string())
        for df_row, correct_row in zip(df.iterrows(),
                                       correct_result.iterrows()):
            df_row = df_row[1]
            correct_row = correct_row[1]
            df_cells = df_row.iteritems()
            correct_cells = correct_row.iteritems()
            for df_cell, correct_cell in zip(df_cells, correct_cells):
                if df_cell != correct_cell:
                    df_row.name = 'observed'
                    correct_row.name = 'correct'
                    raise ValueError(
                        f'{df_cell} != {correct_cell}\n{pd.concat([df_row, correct_row], axis=1)}'
                    )


if __name__ == '__main__':
    pytest.main(['-k', 'test_process_problem_old_forms_lang_l2', '-s'])
