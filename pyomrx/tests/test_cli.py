import pandas as pd
from pyomrx.utils.test_utils import *
from pathlib import Path
import pytest
import subprocess
import zipfile
import json
import os
import sys


def test_cli_round_trip(tmpdir, res_folder):
    config_output_path = Path(tmpdir) / 'example exam score form.omr'
    env = os.environ
    env['PYTHONPATH'] = ';'.join(sys.path)
    subprocess.check_call(
        f'python ./bin/omrx.py make '
        f'--input "examples/example_exam_score_form/example exam score form.xlsx" '
        f'--output "{config_output_path}"',
        env=env)
    omr_template = zipfile.ZipFile(config_output_path, 'r')
    config_json = omr_template.read('omr_config.json')
    config_dict = json.loads(config_json.decode())
    correct_config = json.load(
        open(Path(res_folder) / 'exam_form/example_exam_form.json'))
    assert config_dict['template'] == correct_config['template']
    csv_output_path = Path(tmpdir) / 'example_output.csv'
    subprocess.check_call(
        f'python ./bin/omrx.py extract '
        f'--template "{config_output_path}" '
        f'--input "{tmpdir}" '
        f'--output "{csv_output_path}"',
        env=env)

    extracted_df = pd.read_csv(csv_output_path)
    correct_df = pd.read_csv(
        Path(res_folder) /
        'correct_examples_answers/correct_result_exam_form.csv')
    assert_correct_result(extracted_df, correct_df)


if __name__ == '__main__':
    pytest.main(['-svvk', 'test_cli_round_trip'])
