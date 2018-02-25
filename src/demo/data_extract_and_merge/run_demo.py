from omr.preprocessing import preprocess_folder
from omr.processing import answers_from_images
from analysis.preprocessing import preprocess
import os
from pathlib import Path

images_path = 'data/images'
results_path = 'data/exam_results'
scans_path = 'data/scans'
metadata_path = 'data/ext'


if Path(images_path).exists():
    for file_path in Path(images_path).iterdir():
        os.remove(str(file_path))

preprocess_folder(scans_path, images_path)

answers_from_images(images_path, str(Path(metadata_path)/'omr_form_designs.json'), results_path)
data = preprocess(str(Path(results_path)/'omr_output.csv'), metadata_path, results_path)

print(data.head(10).to_string())
print('outputs should be in data folder')