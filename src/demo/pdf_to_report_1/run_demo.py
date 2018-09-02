import os

from analysis.preprocessing import preprocess
from analysis.processing import *
from omr.core.preprocessing import preprocess_folder
from omr.exam_marksheet.processing import process_exam_marksheet_folder

images_path = 'data/images'
results_path = 'data/exam_results'
scans_path = 'data/scans'
metadata_path = 'data/ext'
reports_folder = 'data/reports'

if Path(images_path).exists():
    for file_path in Path(images_path).iterdir():
        os.remove(str(file_path))

preprocess_folder(scans_path, images_path)

process_exam_marksheet_folder(images_path, str(Path(metadata_path) / 'omr_form_designs.json'), results_path)
print('INFO: raw data extracted from scans')

df = preprocess(str(Path(results_path) / 'omr_output.csv'), metadata_path, results_path)
print('INFO: data extracted:\n',df.head().to_string())

make_auto_report(str(Path(results_path) / 'full_dataset.csv'),reports_folder,metadata_path)


print('outputs should be in reports folder')
