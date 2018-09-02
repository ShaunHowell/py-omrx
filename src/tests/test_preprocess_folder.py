import os
from pathlib import Path
from unittest import TestCase

from omr.core.preprocessing import preprocess_folder


# @pytest.mark.skipif(bool(os.environ.get('TRAVIS')) == True,
#                     reason="cannot test parts with GraphicsMagick dependency on TRAVIS yet")
class TestPreprocess_folder(TestCase):
    def test_preprocess_folder(self):
        input_folder = Path('tests/res/preprocess_folder_in')
        output_folder = Path('tests/out')
        for file_path in output_folder.iterdir():
            os.remove(str(file_path))
        preprocess_folder(str(input_folder), str(output_folder))
        num_files = len(list(output_folder.iterdir()))
        self.assertEqual(num_files, 8, 'incorrect number of image files made')
        for file_path in output_folder.iterdir():
            self.assertEqual(file_path.suffix,
                             '.png',
                             'wrong file type found res output folder: {}'.format(file_path.suffix))
        for file_path in output_folder.iterdir():
            os.remove(str(file_path))
