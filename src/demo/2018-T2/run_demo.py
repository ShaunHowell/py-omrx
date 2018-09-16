from pathlib import Path

from analysis.preprocessing import preprocess
from omr.exam_marksheet.processing import *
from omr.core.preprocessing import *
from omr.core.metrics import *

images_path = 'data/images'
results_path = 'data/exam_results'
scans_path = 'data/scans'
metadata_path = 'data/ext'
reports_folder = 'data/reports'

# if Path(images_path).exists():
#     for file_path in Path(images_path).iterdir():
#         os.remove(str(file_path))
#
# preprocess_folder(scans_path, images_path)

process_images_folder(images_path, str(Path(metadata_path) / 'omr_form_designs.json'),
                      omr_mode='exam',
                      output_folder=results_path)
print('INFO: raw data extracted from scans')
print('output csv should be in data/exam_results.csv')

find_omr_accuracy(os.path.join(results_path, 'omr_output.csv'),
                  os.path.join(results_path, 'human_processed_exam_results.csv'),
                  os.path.join(metadata_path, 'omr_form_designs.json'))

# df = preprocess(str(Path(results_path) / 'omr_output.csv'), metadata_path, results_path)
# print('INFO: data extracted:\n', df.head().to_string())

# make_auto_report(str(Path(results_path) / 'full_dataset.csv'),reports_folder,metadata_path)


print('outputs should be in reports folder')
