from pathlib import Path

import cv2

from omr.core import get_binary_code_from_outer_box, get_inner_boxes, process_images_folder, get_outer_box, \
    process_boxes
from omr.exceptions import OmrException
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
    try:
        grey_outer_box, rgb_outer_box = get_outer_box(
            image, desired_portrait=True)
    except OmrException as e:
        raise OmrException('no suitable outer contour found:\n{}'.format(e))
    form_design = form_designs[str(1)]
    try:
        bottom_left_corners = [[1.0, 0.005]]
        inner_boxes = get_inner_boxes(
            grey_outer_box,
            height=0.98,
            width=0.995,
            bottom_left_corners=bottom_left_corners)
    except OmrException as e:
        raise OmrException(
            'couldn\'t find inner boxes correctly:\n{}'.format(e))
    # plt.imshow(Image.fromarray(inner_boxes[0]))
    # plt.show()
    school_number = get_binary_code_from_outer_box(
        inner_boxes[0],
        6 / 2021,
        40 / 2021,
        478 / 1424,
        710 / 1424,
        12 / 2021,
        22 / 2021,
        55 / 3166,
        num_circles=5)
    class_number = get_binary_code_from_outer_box(
        inner_boxes[0],
        6 / 2021,
        40 / 2021,
        1014 / 1424,
        1204 / 1424,
        12 / 2021,
        22 / 2021,
        55 / 3166,
        num_circles=4)
    sheet_number = get_binary_code_from_outer_box(
        inner_boxes[0],
        1991 / 2021,
        2020 / 2021,
        383 / 1424,
        496 / 1424,
        12 / 2021,
        22 / 2021,
        55 / 3166,
        num_circles=2)
    answers = process_boxes(
        inner_boxes,
        form_design,
        rotate_boxes=False,
        num_boxes=1,
        omr_mode='attendance')
    answers['student_number'] = answers['student_number'].astype(
        np.int) + len(form_design["questions"]) * (sheet_number - 1)
    answers['school_code'] = school_number
    answers['class_code'] = class_number
    answers['sheet_number'] = sheet_number
    answers['file_name'] = Path(input_file_path).stem
    return answers
