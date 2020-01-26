from pathlib import Path

import cv2

from pyomrx.omr.core import get_binary_code_from_outer_box, get_inner_boxes, process_images_folder, get_outer_box, \
    process_boxes
from pyomrx.omr.vis_utils import show_image
from pyomrx.omr.exceptions import OmrException
import numpy as np


def process_attendance_sheet_folder(input_folder,
                                    form_design_path,
                                    output_folder=None):
    process_images_folder(
        input_folder,
        form_design_path,
        omr_mode='attendance',
        output_folder=output_folder)


def process_image(input_file_path, form_designs):
    assert Path(input_file_path).exists(), 'check input file path'
    image = cv2.imread(input_file_path)
    if image is None:
        raise OmrException('failed to load image: {}'.format(input_file_path))
    try:
        grey_outer_box, rgb_outer_box = get_outer_box(
            image, desired_portrait=False)
        # show_image(rgb_outer_box,'outer box')
    except OmrException as e:
        raise OmrException('no suitable outer contour found:\n{}'.format(e))
    form_design = form_designs[str(1)]
    school_number = get_binary_code_from_outer_box(
        grey_outer_box,
        13 / 2021,
        70 / 2021,
        660 / 1424,
        890 / 1424,
        form_design['circle_details']['r_min'],
        form_design['circle_details']['r_max'],
        form_design['circle_details']['min_spacing'],
        num_circles=7)
    class_number = get_binary_code_from_outer_box(
        grey_outer_box,
        13 / 2021,
        70 / 2021,
        1085 / 1424,
        1235 / 1424,
        form_design['circle_details']['r_min'],
        form_design['circle_details']['r_max'],
        form_design['circle_details']['min_spacing'],
        num_circles=5)
    sheet_number = get_binary_code_from_outer_box(
        grey_outer_box,
        1930 / 2021,
        2000 / 2021,
        1295 / 1424,
        1400 / 1424,
        form_design['circle_details']['r_min'],
        form_design['circle_details']['r_max'],
        form_design['circle_details']['min_spacing'],
        num_circles=3)
    try:
        bottom_left_corners = [[1.0, 0.01]]
        inner_boxes = get_inner_boxes(
            grey_outer_box,
            height=0.98,
            width=0.967,
            bottom_left_corners=bottom_left_corners)
    except OmrException as e:
        raise OmrException(
            'couldn\'t find inner boxes correctly:\n{}'.format(e))
    # show_image(inner_boxes[0], 'inner box')
    answers = process_boxes(
        inner_boxes,
        form_design,
        rotate_boxes=False,
        num_boxes=1,
        omr_mode='attendance')
    if not all([
            col in answers.columns for col in [
                'student_number', 'school_code', 'class_code', 'sheet_number',
                'file_name'
            ]
    ]):
        raise OmrException(
            'data extracted from inner box malformed, missing a column heading'
        )
    answers['student_number'] = answers['student_number'].astype(
        np.int) + len(form_design["questions"]) * (sheet_number - 1)
    answers['school_code'] = school_number
    answers['class_code'] = class_number
    answers['sheet_number'] = sheet_number
    answers['file_name'] = Path(input_file_path).stem
    return answers
