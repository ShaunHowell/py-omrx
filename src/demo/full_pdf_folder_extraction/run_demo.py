from omr.preprocessing import preprocess_folder
from omr.processing import answers_from_images
import os
from pathlib import Path


for file_path in Path('data/images').iterdir():
    os.remove(str(file_path))

preprocess_folder('data/scans', 'data/images')

answers = answers_from_images('data/images','data/ext/omr_form_designs.json','data/exam_results')

print(answers.to_string())
print('output csv should be in data/exam_results.csv')