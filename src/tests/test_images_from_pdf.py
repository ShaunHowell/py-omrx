from unittest import TestCase
from omr.preprocessing import *
import os


class TestImages_from_pdf(TestCase):
    def test_images_from_pdf(self):
        # run split_pdf then check that the correct number of pdf files have been produced
        input_path = 'tests/in/split_pdf_in.pdf'
        output_folder = 'tests/out'
        for file_path in os.listdir(output_folder):
            os.remove('{}/{}'.format(output_folder, file_path))
        images_from_pdf(input_path, output_folder)
        num_files = os.listdir(output_folder)
        self.assertEqual(len(num_files), 4, 'incorrect number of image files made')
        for file_path in os.listdir(output_folder):
            self.assertEqual(file_path.split('.')[-1],
                             'png',
                             'wrong file type found in output folder: {}'.format(file_path.split('.')[-1]))
