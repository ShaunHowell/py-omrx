from pathlib import Path

import cv2

from omr.core import get_binary_code_from_outer_box, get_inner_boxes, process_images_folder, get_outer_box, process_boxes
from omr.exceptions import OmrException

def process_exam_marksheet_folder(input_folder,
                                  form_design_path,
                                  output_folder=None):
    process_images_folder(
        input_folder,
        form_design_path,
        omr_mode='exam',
        output_folder=output_folder)


def process_image(input_file_path, form_designs):
    assert Path(input_file_path).exists(), 'check input file path'
    image = cv2.imread(input_file_path)
    try:
        grey_outer_box, rgb_outer_box = get_outer_box(image)
    except OmrException as e:
        raise OmrException('no suitable outer contour found:\n{}'.format(e))
    try:
        paper_code = get_binary_code_from_outer_box(
            grey_outer_box,
            105 / 3507,
            175 / 3507,
            0.145,
            0.250,
            0.0042,
            0.0054,
            0.0114,
            num_circles=3)
    except OmrException as e:
        raise OmrException(
            'paper code not detected properly, please check file {}:\n{}'.
            format(Path(input_file_path).name, e))
    form_design = form_designs[str(paper_code)]
    # print('INFO: form design:')
    # pprint.pprint(form_design)
    try:
        left_edge_coord = 0.028
        bottom_left_corners = [[0.944, left_edge_coord],
                               [0.655, left_edge_coord],
                               [0.363, left_edge_coord]]
        inner_boxes = get_inner_boxes(
            grey_outer_box,
            height=0.229,
            width=0.945,
            bottom_left_corners=bottom_left_corners)
    except OmrException as e:
        raise OmrException(
            'couldn\'t find inner boxes correctly:\n{}'.format(e))
    answers = process_boxes(
        inner_boxes,
        form_design,
        rotate_boxes=False,
        num_boxes=3,
        omr_mode='exam')
    answers['paper_code'] = paper_code
    answers['file_name'] = Path(input_file_path).stem
    return answers
