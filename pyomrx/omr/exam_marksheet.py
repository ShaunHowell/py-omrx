from pathlib import Path

import cv2

from pyomrx.omr.core import get_binary_code_from_outer_box, get_inner_boxes, process_images_folder, get_outer_box, process_boxes
from pyomrx.omr.exceptions import OmrException
from pyomrx.omr.vis_utils import show_circles_on_image, show_image


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
    if image is None:
        raise OmrException('failed to load image: {}'.format(input_file_path))
    try:
        grey_outer_box, rgb_outer_box = get_outer_box(image)
        # show_image(grey_outer_box,title='outer box')
    except OmrException as e:
        raise OmrException('no suitable outer contour found:\n{}'.format(e))
    try:
        paper_code = get_binary_code_from_outer_box(
            grey_outer_box,
            127 / 2643,
            185 / 2643,
            304 / 2033,
            520 / 2033, (162 - 142) / (2 * 2643), (173 - 132) / (2 * 2643),
            (394 - 366) / (2 * 2033),
            num_circles=3)
    except OmrException as e:
        raise OmrException(
            'paper code not detected properly, please check file {}:\n{}'.
            format(Path(input_file_path).name, e))
    form_design = form_designs[str(paper_code)]
    # print('INFO: form design:')
    # pprint.pprint(form_design)
    try:
        left_edge_coord = 0.029  # when outer box is portrait
        inner_box_height = (
            2585 - 1840) / 2643  # the smaller dimension of the inner box
        inner_box_width = (1977 - 62) / 2033
        bottom_left_corners = [[2583 / 2643, left_edge_coord],
                               [1785 / 2643, left_edge_coord],
                               [989 / 2643, left_edge_coord]]
        inner_boxes = get_inner_boxes(
            grey_outer_box,
            height=inner_box_height,
            width=inner_box_width,
            bottom_left_corners=bottom_left_corners)
    except OmrException as e:
        raise OmrException(
            'couldn\'t find inner boxes correctly:\n{}'.format(e))
    answers = process_boxes(
        inner_boxes,
        form_design,
        rotate_boxes=True,
        num_boxes=3,
        omr_mode='exam')
    answers['paper_code'] = paper_code
    answers['file_name'] = Path(input_file_path).stem
    return answers
