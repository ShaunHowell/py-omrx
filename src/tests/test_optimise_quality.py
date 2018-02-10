from unittest import TestCase
import os
from pathlib import Path
from omr.preprocessing import optimise_quality
import hashlib


class TestOptimise_quality(TestCase):
    def test_optimise_quality(self):
        input_path = Path('tests/res/optimise_quality_in/good_1.png')
        reference_output_path = Path('tests/res/optimise_quality_out/good_1.png')
        temp_output_folder = Path('tests/out')
        temp_output_path = Path('tests/out/good_1_optimised.png')
        for file_path in temp_output_folder.iterdir():
            os.remove(str(file_path))
        optimise_quality(input_path, temp_output_path, overwrite=True)
        with open(str(reference_output_path), 'rb') as reference_output_file:
            reference_output_hash = hashlib.md5(reference_output_file.read()).hexdigest()
        with open(str(temp_output_path), 'rb') as created_output_file:
            created_output_hash = hashlib.md5(created_output_file.read()).hexdigest()
        self.assertEqual(len(list(temp_output_folder.iterdir())), 1, 'no output file created')
        self.assertEqual(reference_output_hash, created_output_hash, 'image not optimised correctly')
        for file_path in temp_output_folder.iterdir():
            os.remove(str(file_path))
