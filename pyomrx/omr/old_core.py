import datetime
import importlib
import json
import sys
from pathlib import Path

import cv2
import imutils
import numpy as np
import pandas as pd
from PIL import Image
from imutils.perspective import four_point_transform
from scipy.spatial import KDTree
from scipy.spatial.distance import euclidean

from pyomrx.default_configs import attendance_register, exam_marksheet
from pyomrx.omr.exceptions import ZeroCodeFoundException, OmrException, OmrValidationException, EmptyFolderException
from pyomrx.omr.vis_utils import show_circles_on_image, show_image
import matplotlib.pyplot as plt
from pyomrx.omr.file_utils import make_folder_if_not_exists


def get_binary_code_from_outer_box(greyscale_outer_box,
                                   h1,
                                   h2,
                                   w1,
                                   w2,
                                   r1,
                                   r2,
                                   min_dist,
                                   num_circles=None):
    height, width = greyscale_outer_box.shape
    h1, h2 = int(height * h1), int(height * h2)
    w1, w2 = int(width * w1), int(width * w2)
    r1, r2 = int(height * r1), int(height * r2)
    min_dist = int(height * min_dist)
    binary_outer_box = cv2.threshold(
        greyscale_outer_box, 0, 255,
        cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    code_box = binary_outer_box[h1:h2, w1:w2]
    # show_image(code_box, title='code box')
    code = get_code_from_binary_circles(
        code_box, min_dist, r1, r2, num_circles=num_circles)
    print('INFO: code: {}'.format(code))
    return code


def get_inner_boxes(greyscale_outer_box, height, width, bottom_left_corners):
    h, w = greyscale_outer_box.shape
    box_height, box_width = height * h, width * w  # height & width of inner boxes with outer box viewed portrait
    inner_box_cnts = []
    for corner_h, corner_w in bottom_left_corners:
        corner_w_abs = corner_w * w
        corner_h_abs = corner_h * h
        box_cnt = {
            'h1': int(corner_h_abs - box_height),
            'h2': int(corner_h_abs),
            'w1': int(corner_w_abs),
            'w2': int(corner_w_abs + box_width)
        }
        inner_box_cnts.append(box_cnt)
    inner_boxes = [
        greyscale_outer_box[cnt['h1']:cnt['h2'], cnt['w1']:cnt['w2']]
        for cnt in inner_box_cnts
    ]
    # temp_image = cv2.cvtColor(greyscale_outer_box, cv2.COLOR_GRAY2RGB)
    # # cv2.drawContours(temp_image, inner_box_cnts, -1, (255, 0, 0), 3)
    return inner_boxes


def get_code_from_binary_circles(image,
                                 min_dist,
                                 min_radius,
                                 max_radius,
                                 num_circles=None):
    code_circles = cv2.HoughCircles(
        image,
        cv2.HOUGH_GRADIENT,
        1,
        min_dist,
        param1=150,
        param2=5,
        minRadius=min_radius,
        maxRadius=max_radius)
    if code_circles is None:
        raise OmrValidationException('could not find code circles from image')
    code_circles = np.uint16(np.around(code_circles))[0].tolist()
    sorted_circles = sorted(
        code_circles,
        key=lambda circle: circle[0]**2 + circle[1]**2,
        reverse=True)
    code_circles = np.array(sorted_circles)  # read left to right
    if num_circles:
        if len(code_circles) != num_circles:
            raise OmrException('found {} circles whilst trying ' \
                               'to find paper code, should be {}'.format(len(code_circles),
                                                                         num_circles))
    paper_code = 0
    for i, circle in enumerate(code_circles):
        mask = np.zeros(image.shape, dtype="uint8")
        cv2.circle(mask, (circle[0], circle[1]), circle[2], 255, -1)
        mask = cv2.bitwise_and(image, image, mask=mask)
        average = cv2.countNonZero(mask) / (circle[2] * circle[2] * 3.14)
        # check if positive detection
        if average > 0.5:
            paper_code = paper_code + 2**i
    if paper_code < 0:
        raise ZeroCodeFoundException(
            'paper code not detected properly, please check file')
    return paper_code


def process_boxes(inner_boxes,
                  form_design,
                  num_boxes,
                  rotate_boxes=True,
                  omr_mode='exam'):
    # circles_per_row = form_design['code'] + form_design['questions']
    if omr_mode == 'exam':
        answers = pd.DataFrame(
            columns=['file_name', 'box_no', 'omr_error', 'marker_error'])
    elif omr_mode == 'attendance':
        answers = pd.DataFrame(columns=[
            'file_name', 'school_code', 'class_code', 'sheet_number', 'box_no',
            'omr_error', 'marker_error'
        ])
    for box_no, inner_box in enumerate(inner_boxes):
        # pixels_per_row = int(0.085 * h)
        # height = (len(circles_per_row) + 1) * pixels_per_row  # plus 2 for middle buffer and top buffer
        if rotate_boxes:
            inner_box = np.array(
                Image.fromarray(inner_box).rotate(-90, expand=True))
        h, w = inner_box.shape
        left_margin = int(form_design['inner_box_margins']['left'] * w)
        top_margin = int(form_design['inner_box_margins']['top'] * h)
        bottom_margin = int(
            form_design['inner_box_margins'].get('bottom', 0) * w)
        print('bottom margin: {}'.format(bottom_margin))
        inner_box = inner_box[top_margin:h - bottom_margin, left_margin:]
        inner_box = cv2.copyMakeBorder(
            inner_box,
            right=5,
            top=0,
            bottom=0,
            left=0,
            borderType=cv2.BORDER_CONSTANT,
            value=[255, 255, 255])
        # show_image(inner_box,title='cropped inner box')
        try:
            circle_details = form_design['circle_details']
            inner_box_answers = process_inner_box(
                inner_box,
                form_design['code'],
                form_design['questions'],
                r_min=circle_details['r_min'],
                r_max=circle_details['r_max'],
                min_dist=circle_details['min_spacing'],
                omr_mode=omr_mode,
                blank_rows=form_design['blank_rows'])
            # print('INFO: box no {}, answers:\n{}'.format(box_no, inner_box_answers.to_string()))
            inner_box_answers['box_no'] = box_no + 1
        except OmrException as e:
            print(
                'Couldn\'t extract answers from box {}\nerror: {}'.format(
                    box_no + 1, e),
                file=sys.stderr)
            print('error: {}'.format(e))
            inner_box_answers = pd.DataFrame([[box_no + 1, True]],
                                             columns=['box_no', 'omr_error'])
        answers = answers.append(inner_box_answers)
    if answers.loc[:, ~answers.columns.isin(['omr_error', 'marker_error', 'file_name', 'sheet_number',
                                             'paper_code', 'school_code', 'class_code'])].isnull().sum().sum() > 0 \
            or len(answers) < num_boxes:
        raise OmrException(
            'Must be no nulls in answers and must be {} boxes processed'.
            format(num_boxes))
    return answers


def response_from_darknesses(darknesses):
    if len(darknesses) < 2:
        return -3  # omr error because it didn't get enough circles
    if max(darknesses) < 0.4:  # was 0.09
        return -1  # -1 means the row doesn't have a response
    filled_circles = list(filter(lambda d: d > 0.6,
                                 darknesses))  # was 0.25 cutoff
    if len(filled_circles) > 1:
        return -2  # -2 means more than one response detected
    if len(filled_circles) < 1:
        return -3  # -3 means the omr algorithm couldn't work out the filled in box (abstention)
    darknesses = enumerate(darknesses)
    darknesses = sorted(darknesses, key=lambda circle: circle[1])
    if darknesses[-1][1] / darknesses[-2][1] < 1.6:
        return -3  # -3 because there wasn't enough difference between the 1st and 2nd darkest circles
    return darknesses[-1][0]


def darknesses_to_binary(darknesses):
    return list(map(lambda d: 1 if (d > 0.3) else 0, darknesses))


def process_inner_box(inner_box,
                      circles_per_header_row,
                      circles_per_q_row,
                      r_min,
                      r_max,
                      min_dist,
                      omr_mode='exam',
                      blank_rows=0):
    # show_image(inner_box, 'inner box')
    assert omr_mode in ['exam', 'attendance'
                        ], 'omr_mode {} not supported'.format(omr_mode)
    h, w = inner_box.shape
    min_dist = int(min_dist * h)
    r1, r2 = int(r_min * h), int(r_max * h)
    inner_box = cv2.threshold(inner_box, 0, 255,
                              cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # show_circles_on_image(inner_box, circles, 'initial candidate circles')
    circles = get_good_circles(
        inner_box,
        circles_per_header_row,
        circles_per_q_row,
        inner_box_shape=inner_box.shape,
        debug_image=inner_box,
        blank_rows=blank_rows,
        omr_mode=omr_mode)
    # show_circles_on_image(inner_box, circles, 'final circles')
    # Check region outside of circles doesn't have too many marks, or image quality is probably poor
    mask = np.ones(inner_box.shape, dtype="uint8")
    [
        cv2.circle(mask, (circ[0], circ[1]), int(circ[2] * 1.3), 0, -1)
        for circ in circles
    ]
    mask = cv2.bitwise_and(inner_box, inner_box, mask=mask)
    noise = sum((mask / 255).flatten().tolist()) * 100 / mask.size
    if noise > 30:  # FIXME: needs manual calibration for each new excel form change
        raise OmrValidationException('too many marks found outside of circles')
    # sort circles top-to-bottom
    circles = np.array(sorted(circles, key=lambda circle: circle[1]))
    inner_box_answers = {}
    bubbles_processed = 0
    for question_number, num_bubbles in enumerate(circles_per_header_row +
                                                  circles_per_q_row):
        if num_bubbles == 0:
            continue
        question_circles = np.array(
            sorted(
                circles[bubbles_processed:bubbles_processed + num_bubbles],
                key=lambda circle: circle[0]))
        darknesses = []
        # get circle darknesses
        for circle in question_circles:
            darknesses.append(process_circle(inner_box, circle))
            bubbles_processed += 1
        # print('INFO: q{} darknesses: {}'.format(question_number, darknesses))
        # determine response based on circle darknesses
        if omr_mode == 'exam':
            response = response_from_darknesses(darknesses)
        elif omr_mode == 'attendance':
            response = darknesses_to_binary(darknesses)
        print('Row {}, darknesses: {}, response: {}'.format(
            question_number, darknesses, response))
        if response == -3:
            inner_box_answers.update({'omr_error': True})
        if response in [-1, -2]:
            inner_box_answers.update({'marker_error': True})
        if question_number < len(circles_per_header_row):
            inner_box_answers.update(
                {'c_{:0>2}'.format(question_number + 1): response})
        else:
            inner_box_answers.update({
                'q_{:0>2}'.format(question_number - len(circles_per_header_row) + 1):
                response
            })
    if omr_mode == 'exam':
        inner_box_df = pd.DataFrame(inner_box_answers, index=[0])
    elif omr_mode == 'attendance':
        inner_box_df = pd.DataFrame.from_dict(
            inner_box_answers, orient='index')
        inner_box_df.columns = range(1, inner_box_df.shape[1] + 1)
        inner_box_df['student_number'] = inner_box_df.index.str.lstrip('q_')
    return inner_box_df
