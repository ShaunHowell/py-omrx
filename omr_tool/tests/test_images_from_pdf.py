import os
from pathlib import Path
from unittest import TestCase
import pytest

from omr_tool.omr.core.preprocessing import *


@pytest.mark.skip('no longer supported')
class TestImages_from_pdf(TestCase):
    def test_images_from_pdf(self):
        # run split_pdf then check that the correct number of pdf files have been produced
        input_path = Path('tests/res/images_from_pdf_in/good_1.pdf')
        output_folder = Path('tests/out')
        for file_path in output_folder.iterdir():
            os.remove(str(file_path))
        images_from_pdf(str(input_path), str(output_folder))
        num_files = len(list(output_folder.iterdir()))
        self.assertEqual(num_files, 4, 'incorrect number of image files made')
        for file_path in output_folder.iterdir():
            self.assertEqual(file_path.suffix,
                             '.png',
                             'wrong file type found res output folder: {}'.format(file_path.suffix))
        for file_path in output_folder.iterdir():
            os.remove(str(file_path))
