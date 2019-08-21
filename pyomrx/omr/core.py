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

IMAGE_SUFFIXES = ['.png', '.jpg', 'jpeg', '.PNG', '.JPG', '.JPEG']


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
    # plt.imshow(temp_image)
    # plt.show()
    # for temp_image in inner_boxes:
    #     plt.figure()
    #     plt.imshow(Image.fromarray(temp_image))
    #     plt.show()
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
    # temp_image = image.copy()
    # [cv2.circle(temp_image, (c[0],c[1]),c[2], thickness=4, color=(255,0,0)) for c in code_circles]
    # plt.imshow(Image.fromarray(temp_image))
    # plt.show()
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


def process_images_folder(input_folder,
                          form_design=None,
                          omr_mode='attendance',
                          output_folder=None):
    if omr_mode == 'exam':
        temp_module = importlib.import_module('pyomrx.omr.exam_marksheet')
    elif omr_mode == 'attendance':
        temp_module = importlib.import_module('pyomrx.omr.attendance_register')
    else:
        print(
            'ERROR: image_type must be exam_marksheet or attendance_register, {} passed'
            .format(omr_mode))
        raise ValueError('invalid image_type')
    process_image = getattr(temp_module, 'process_image')
    if isinstance(form_design, str):
        form_design = json.load(open(form_design))
    elif isinstance(form_design, dict):
        form_design = form_design
    elif omr_mode == 'attendance' and form_design is None:
        print('using default attendance template')
        form_design = attendance_register.default_config()
    elif omr_mode == 'exam' and form_design is None:
        form_design = exam_marksheet.default_config()
        print('using default attendance template')
    else:
        raise TypeError(
            'form design passed is of typ {} but must be either str or dict'.
            format(type(form_design)))
    answers_df = pd.DataFrame()
    print(list(Path(input_folder).iterdir()))
    img_files = [
        img_file for img_file in Path(input_folder).iterdir()
        if img_file.suffix in IMAGE_SUFFIXES
    ]
    if not img_files:
        raise EmptyFolderException(
            'no image files found in {}'.format(input_folder))
    error_files = []
    print('{} files to process in folder {}'.format(
        len(img_files), input_folder))
    for i, file_path in enumerate(img_files):
        print('INFO: processing image {} {}'.format(i, file_path.name))
        try:
            im_answers = process_image(str(file_path), form_design)
            answers_df = answers_df.append(im_answers)
        except OmrException as e:
            error_files.append(str(file_path.stem))
            print(
                'couldn\'t extract data from {}: check input file'.format(
                    Path(file_path).name),
                file=sys.stderr)
            print('error message: ', e, file=sys.stderr)
            if output_folder:
                now = datetime.datetime.now()
                make_folder_if_not_exists(output_folder)
                with (Path(output_folder) / 'errors.txt').open('a') as f:
                    f.write('{}:{}:{}:{}\n'.format(now, file_path, type(e), e))
    if len(answers_df) == 0:
        raise OmrException('could not extract any data from the images')
    error_df = pd.DataFrame(
        index=error_files, columns=answers_df.columns.tolist())
    error_df = pd.concat([error_df] * 3, axis=0).sort_index()
    error_df['omr_error'] = True
    error_df['box_no'] = [1, 2, 3] * int(len(error_df) / 3)
    error_df['file_name'] = error_df.index.tolist()
    error_df['marker_error'] = np.nan
    error_df.loc[:, ~error_df.columns.isin(
        ['file_name', 'omr_error', 'box_no', 'marker_error'])] = -3
    answers_df = pd.concat([answers_df, error_df], axis=0)
    if output_folder:
        if not Path(output_folder).exists():
            Path(output_folder).mkdir(parents=True)
        answers_df.to_csv(
            str(Path(output_folder) / '{}_omr_output.csv'.format(omr_mode)),
            index=False)
    return answers_df


def nearby_circle(x, y, circles, max_distance=np.inf):
    if len(circles) == 0:
        raise OmrValidationException('no more candidate circles available')
    circle_coords = np.array(circles)[:, :2]
    d, i = KDTree(circle_coords).query([x, y],
                                       distance_upper_bound=max_distance)
    if d != np.inf:
        return circles[i]
    else:
        return None


def expected_circle_locations(circles_per_header_row,
                              circles_per_q_row,
                              bubble_spacing,
                              top_left_position=None):
    exp_loc = []
    spacing_width = bubble_spacing[0]
    spacing_height = bubble_spacing[1]
    top_left_position = top_left_position if top_left_position is not None else [
        spacing_width / 2, spacing_height / 2
    ]
    y = top_left_position[1]
    for row, num_options in enumerate(circles_per_header_row):
        x = top_left_position[0]
        for column in range(num_options):
            exp_loc.append([int(x), int(y)])
            x += spacing_width
        y += spacing_height
    if len(exp_loc) > 0:
        y += spacing_height
    for row, num_options in enumerate(circles_per_q_row):
        x = top_left_position[0]
        for column in range(num_options):
            exp_loc.append([int(x), int(y)])
            x += spacing_width
        y += spacing_height
    return exp_loc


def circles_from_grid(x_coords, y_coords, circles_per_header_row,
                      circles_per_q_row):
    # print('x coords: {},\ny coords: {}'.format(x_coords, y_coords))
    # print('len x: {}, len y: {}'.format(len(x_coords), len(y_coords)))
    circles = []
    x_coords = sorted(x_coords)
    y_coords = sorted(y_coords)
    try:
        assert len(x_coords) == max(circles_per_header_row + circles_per_q_row)
        assert len(y_coords) == len(circles_per_header_row + circles_per_q_row)
    except:
        raise OmrValidationException('wrong number of x or y clusters made')
    # Find average circle size
    x_deltas = list(map(lambda el: el[1] - el[0], zip(x_coords, x_coords[1:])))
    x_box_size = sum(x_deltas) / len(x_deltas)
    circle_size = x_box_size * 0.20
    # Make most likely circle locations
    for y_coord, circles_for_row in zip(
            y_coords, circles_per_header_row + circles_per_q_row):
        for x_coord, _ in zip(x_coords, range(circles_for_row)):
            circles.append([int(x_coord), int(y_coord), int(circle_size)])
    return circles


def get_good_circles(candidate_circles,
                     circles_per_header_row,
                     circles_per_q_row,
                     inner_box_shape,
                     debug_image,
                     blank_rows=0,
                     omr_mode='exam'):
    if omr_mode == 'exam':
        blank_rows = 22 - len(
            circles_per_q_row)  # 22 is the max that fits in the box currently
    debug_candidate_circles = candidate_circles.copy()
    # show_circles_on_image(
    #     debug_image, candidate_circles, 'candidate_circles', delayed_show=True)
    candidate_circles = sorted(
        candidate_circles.copy().tolist(), key=lambda circ: circ[0] + circ[1])
    assert len(np.array(candidate_circles).shape
               ) == 2, 'shape must be (n,3), [} was passed'.format(
                   np.array(candidate_circles).shape)
    bubble_box_width = inner_box_shape[1] / max(circles_per_q_row +
                                                circles_per_header_row)
    number_of_rows = len(circles_per_q_row +
                         circles_per_header_row) + blank_rows
    number_of_rows = number_of_rows + 1 if len(
        circles_per_header_row) > 0 else number_of_rows
    bubble_box_height = inner_box_shape[0] / number_of_rows
    max_circle_search_distance = max([bubble_box_height, bubble_box_width
                                      ]) * 0.6
    bubble_spacing = [bubble_box_width, bubble_box_height]
    print('number_of_rows: {}, bubble_box_height:{}'.format(
        number_of_rows, bubble_box_height))
    expected_locations = expected_circle_locations(
        circles_per_header_row, circles_per_q_row, bubble_spacing)
    debug_expected_locations = [(x, y, 3) for x, y in expected_locations]
    # show_circles_on_image(
    #     debug_image,
    #     debug_expected_locations,
    #     'expected locations',
    #     delayed_show=True)
    filtered_circles = []
    good_x_coords, good_y_coords = {}, {}
    for x, y in expected_locations:
        try:
            good_match = nearby_circle(x, y, candidate_circles,
                                       max_circle_search_distance)
            if good_match:
                filtered_circles.append(good_match)
                if good_x_coords.get(x) == None:
                    good_x_coords[x] = []
                if good_y_coords.get(y) == None:
                    good_y_coords[y] = []
                good_x_coords[x].append(good_match[0])
                good_y_coords[y].append(good_match[1])
                candidate_circles.remove(good_match)
        except OmrValidationException as e:
            print('WARNING: Found too few circles')
            break
    if len(filtered_circles
           ) < len(circles_per_header_row + circles_per_q_row) * 0.5:
        raise OmrValidationException(
            'less than half the expected circles found')
    # show_circles_on_image(debug_image, filtered_circles, 'filtered circles')

    good_circles = list(
        map(lambda c: [c[0], c[1], int(c[2] * 0.85)], filtered_circles.copy()))
    y_coord_options = np.unique(
        [coord[1] for coord in expected_locations]).tolist()
    x_coord_options = np.unique(
        [coord[0] for coord in expected_locations]).tolist()

    for x, y in expected_locations:
        if not nearby_circle(x, y, filtered_circles,
                             max_circle_search_distance):
            try:
                if good_x_coords.get(x):
                    good_x = int(np.mean(good_x_coords.get(x)))
                else:
                    prev_x_expected_coord = x_coord_options[
                        x_coord_options.index(x) - 1]
                    next_x_expected_coord = x_coord_options[
                        x_coord_options.index(x) + 1]
                    prev_x_mean = np.mean(
                        good_x_coords.get(prev_x_expected_coord))
                    next_x_mean = np.mean(
                        good_x_coords.get(next_x_expected_coord))
                    good_x = int(np.mean([prev_x_mean, next_x_mean]))
                if good_y_coords.get(y):
                    good_y = int(np.mean(good_y_coords.get(y)))
                else:
                    prev_y_expected_coord = y_coord_options[
                        y_coord_options.index(y) - 1]
                    next_y_expected_coord = y_coord_options[
                        y_coord_options.index(y) + 1]
                    prev_y_mean = np.mean(
                        good_y_coords.get(prev_y_expected_coord))
                    next_y_mean = np.mean(
                        good_y_coords.get(next_y_expected_coord))
                    good_y = int(np.mean([prev_y_mean, next_y_mean]))
                assert good_x
                assert good_y
                good_circles.append(
                    [good_x, good_y,
                     int(bubble_box_height * 0.3)])
            except:
                expected_location_circles = np.concatenate([
                    np.array(expected_locations),
                    np.array([[3] * len(expected_locations)]).T
                ],
                                                           axis=1)
                show_circles_on_image(
                    debug_image,
                    expected_location_circles,
                    'expected circle locations',
                    delayed_show=True)
                show_circles_on_image(
                    debug_image,
                    debug_candidate_circles,
                    'ERROR (candidate circles)',
                    delayed_show=True)
                show_circles_on_image(debug_image, filtered_circles,
                                      'ERROR (filtered circles)')
                raise OmrException('could not fill missing circles')

    # y_coords = [circ[1] for circ in filtered_circles]
    # x_coords = [circ[0] for circ in filtered_circles]
    # try:
    #     # Cluster x & y coords
    #     x_km = KMeans(max(circles_per_header_row + circles_per_q_row))
    #     y_km = KMeans(len(circles_per_header_row + circles_per_q_row))
    # except ValueError as e:
    #     print('error, could not find good circles, probably there wasn\'t at least one circle in each row and column')
    #     raise e
    # x_km.fit(np.array(x_coords).reshape(-1, 1))
    # x_cluster_centers = np.array(sorted(x_km.cluster_centers_.flatten().tolist()))
    # mean_x_delta = np.mean(x_cluster_centers[1:] - x_cluster_centers[:-1])
    # grid_x_coords = (mean_x_delta *
    #                  np.array(range(0, max(circles_per_q_row + circles_per_header_row)))
    #                  + x_cluster_centers[0]).tolist()
    # y_km.fit(np.array(y_coords).reshape(-1, 1))
    # y_cluster_centers = np.array(sorted(y_km.cluster_centers_.flatten().tolist()))
    # print('x centres: {}, len: {}\ny centres: {}, len: {}'.format(x_cluster_centers, len(x_cluster_centers),
    #                                                               y_cluster_centers, len(y_cluster_centers)))
    # median_y_delta = np.median(y_cluster_centers[1:] - y_cluster_centers[:-1])
    # code_y_coords = (median_y_delta *
    #                  np.array(range(0, len(circles_per_header_row)))
    #                  + y_cluster_centers[0]).tolist()
    # if code_y_coords:
    #     question_y_coords = (median_y_delta *
    #                          np.array(range(0, len(circles_per_q_row))) +
    #                          bubble_box_height * 2 +
    #                          code_y_coords[-1]).tolist()
    # else:
    #     question_y_coords = (median_y_delta *
    #                          np.array(range(0, len(circles_per_q_row))) +
    #                          y_cluster_centers[0]).tolist()
    # print('median_y_delta:{}'.format(median_y_delta))

    # good_circles = circles_from_grid(grid_x_coords, code_y_coords + question_y_coords,
    #                                  circles_per_header_row, circles_per_q_row)
    return good_circles


def get_outer_box_contour(original_image):
    original_image_copy = original_image.copy()
    # show_image(original_image_copy , title='original_image', delayed_show=True)

    gray = cv2.cvtColor(original_image_copy, cv2.COLOR_BGR2GRAY)
    blurred = cv2.medianBlur(gray, 7)
    blurred = cv2.blur(blurred, ksize=(7, 7))
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    # show_image(thresh, title='thresh', delayed_show=True)

    kernel = np.ones((13, 13), np.uint8)
    eroded = cv2.erode(thresh, kernel, iterations=1)
    dilated = cv2.dilate(eroded, kernel, iterations=1)
    # show_image(dilated, title='after erosion-dilation', delayed_show=False)

    edged_image = cv2.Canny(
        dilated,
        threshold1=180,
        threshold2=230,
        L2gradient=True,
        apertureSize=3)

    # show_image(edged_image, title='edged_image', delayed_show=True)
    cnts = cv2.findContours(edged_image.copy(), cv2.RETR_LIST,
                            cv2.CHAIN_APPROX_SIMPLE)
    if imutils.is_cv3():
        cnts = cnts[1]
    elif imutils.is_cv4():
        cnts = cnts[0]
    else:
        raise ImportError('must have opencv version 3 or 4, yours is {}'.format(cv2.__version__))

    # contour_image = edged_image.copy()
    # cv2.drawContours(contour_image, cnts, -1, (255, 0, 0), 3)
    # show_image(contour_image, title='contoured_image', delayed_show=False)

    # validate
    image_perim = 2 * sum(edged_image.shape)
    docCnt = None
    assert len(cnts) > 0, 'no contours found when looking for outer box'
    for c in sorted(cnts, key=cv2.contourArea, reverse=True):
        perim = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.05 * perim, True)
        if len(approx) == 4:
            docCnt = approx
            break
    min_acceptable_perim = image_perim * 0.7
    if type(docCnt) != np.ndarray or perim < min_acceptable_perim:
        temp_image = cv2.cvtColor(edged_image, cv2.COLOR_GRAY2RGB)
        cv2.drawContours(temp_image, [docCnt], -1, (255, 0, 0), 3)
        # plt.imshow(temp_image)
        # plt.show()
        raise OmrException(
            'no suitable outer contour found, '
            'biggest outer contour had perim of {}, needs to be bigger than {}'
            .format(perim, min_acceptable_perim))
    return docCnt


def get_outer_box(original_image, desired_portrait=True):
    portrait = not desired_portrait
    i = 0
    while not portrait == desired_portrait and i < 2:
        outer_box_contour = get_outer_box_contour(original_image)
        tl, bl, br, tr = outer_box_contour[0], outer_box_contour[
            1], outer_box_contour[2], outer_box_contour[3]
        heights = sorted([euclidean(bl, tl), euclidean(br, tr)])
        widths = sorted([euclidean(tr, tl), euclidean(br, bl)])
        try:
            assert heights[1] / heights[0] < 1.05
            assert widths[1] / widths[0] < 1.05
        except:
            raise OmrValidationException('good outer box not found')
        shrink = 5
        original_cropped = four_point_transform(
            original_image, outer_box_contour.reshape(4, 2))
        original_cropped = original_cropped[shrink:-shrink, shrink:-shrink]
        gray = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
        grey_cropped = four_point_transform(gray,
                                            outer_box_contour.reshape(4, 2))
        grey_cropped = grey_cropped[shrink:-shrink, shrink:-shrink]
        height, width, = grey_cropped.shape
        portrait = True if height >= width else False
        if portrait != desired_portrait:
            original_image = np.array(
                Image.fromarray(original_image).rotate(90, expand=True))
        i += 1
    if not portrait == desired_portrait:
        raise OmrValidationException(
            'outer box not found with correct orientation')
    return grey_cropped, original_cropped


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


def process_circle(inner_box, circle):
    mask = np.zeros(inner_box.shape, dtype="uint8")
    cv2.circle(mask, (circle[0], circle[1]), circle[2], 255, -1)
    mask = cv2.bitwise_and(inner_box, inner_box, mask=mask)
    return cv2.countNonZero(mask) / (circle[2] * circle[2] * 3.14)


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
    circles = cv2.HoughCircles(
        inner_box,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=min_dist,
        param1=60,
        param2=5,
        minRadius=r1 - 2,
        maxRadius=r2)
    if circles is None:
        raise OmrException('failed to get any circles from inner box')
    circles = np.uint16(np.around(circles))[0]
    # show_circles_on_image(inner_box, circles, 'initial candidate circles')
    circles = get_good_circles(
        circles,
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
