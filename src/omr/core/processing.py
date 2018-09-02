import json
import pandas as pd
from pathlib import Path
import numpy as np
import importlib
from omr.exceptions import *
import sys

def process_images_folder(input_folder, form_design_path, image_type, output_folder=None):
    if image_type == 'exam_marksheet':
        temp_module = importlib.import_module('omr.exam_marksheet.processing')
    elif image_type == 'attendance_register':
        temp_module = importlib.import_module('omr.attendance_register.processing')
    else:
        print('ERROR: image_type must be exam_marksheet or attendance_register, {} passed'.format(image_type))
        raise ValueError('invalid image_type')
    process_image = getattr(temp_module, 'process_image')
    form_design = json.load(open(form_design_path))
    answers_df = pd.DataFrame()
    img_files = list(Path(input_folder).iterdir())
    error_files = []
    print('{} files to process'.format(len(img_files)))
    for i , file_path in enumerate(img_files):
        print('INFO: processing image {} {}'.format(i, file_path.name))
        try:
            im_answers = process_image(str(file_path), form_design)
            answers_df = answers_df.append(im_answers)
        except OmrException as e:
            error_files.append(str(file_path.stem))
            print('couldn\'t extract data from {}: check input file'.format(Path(file_path).name), file=sys.stderr)
            print('error message: ', e, file=sys.stderr)
    assert len(answers_df) > 0, 'could not extract any data from the images'
    error_df = pd.DataFrame(index=error_files,columns=answers_df.columns.tolist())
    error_df = pd.concat([error_df]*3, axis=0).sort_index()
    error_df['omr_error'] = True
    error_df['box_no'] = [1,2,3] * int(len(error_df)/3)
    error_df['file_name'] = error_df.index.tolist()
    error_df['marker_error'] = np.nan
    error_df.loc[:, ~error_df.columns.isin(['file_name', 'omr_error', 'box_no', 'marker_error'])] = -3
    answers_df = pd.concat([answers_df,error_df],axis=0)
    if output_folder:
        if not Path(output_folder).exists():
            Path(output_folder).mkdir(parents=True)
        answers_df.to_csv(str(Path(output_folder) / 'omr_output.csv'), index=False)
    return answers_df
