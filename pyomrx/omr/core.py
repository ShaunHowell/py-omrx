import copy
import datetime
import importlib
import json
import sys
from pathlib import Path
from pyomrx.omr.circle import Circle
from pyomrx.omr.circle_group import *
from pyomrx.omr.cv2_utils import load_and_check_image

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


def extract_circles_grid(image, circles_per_row, num_rows, num_columns, radius):
    # TODO: cv2 extract circles from image, estimate row & column widths, filter circles in wrong place,
    #  ...infill missing circles, return a grid of instantiated Circle objects
    return []


class DataCircleGroup:
    def __init__(self, image, config):
        self.image = image
        self.config = config
        # show_image(image, 'data_circles')


class OmrForm:
    def __init__(self, input_image_path, form_config):
        self.input_image_path = Path(input_image_path)
        self.id = form_config['id']
        self.author = form_config['author']
        self.created_on = form_config['created_on']
        self.template = form_config['template']
        self.data = None
        self.image = None
        # self.metadata_circle_groups = self.template['metadata_circles']
        self._metadata_values = {}
        self.sub_forms = []
        self._load_image()
        # show_image(self.image, 'omr form')
        self._init_sub_forms()
        self.metadata_circle_groups = []
        self._init_metadata_circles()

    @property
    def metadata_values(self):
        if not self.metadata_values:
            self._metadata_values = {m.name: m.value for m in self.metadata_circle_groups}
        return self._metadata_values

    def extract_data(self):

        pass

    def _load_image(self):
        load_and_check_image(self.input_image_path)
        try:
            grey_outer_box, rgb_outer_box = get_outer_box(
                self.image, desired_portrait=False)
            # show_image(rgb_outer_box, 'outer box')
        except OmrException as e:
            raise OmrException('no suitable outer contour found:\n{}'.format(e))
        self.image = grey_outer_box

    def _init_sub_forms(self):
        sub_form_config = self.template['sub_forms']
        template = sub_form_config['sub_form_templates'][0]
        for rectangle in sub_form_config['locations']:
            sub_form_image = extract_rectangle_image(self.image, rectangle)
            self.sub_forms.append(OmrSubForm(sub_form_image, template))

    def _init_metadata_circles(self):
        for metadata_circle_group_config in self.template['metadata_circles']:
            metadata_circles_image = extract_rectangle_image(self.image, metadata_circle_group_config['rectangle'])
            self.metadata_circle_groups.append(BinaryCircles(metadata_circles_image, metadata_circle_group_config))


class OmrSubForm:
    def __init__(self, image, template):
        self.image = image
        self.template = template
        # show_image(image, 'sub form')
        self.data_circle_groups = []
        self._init_circles()

    def _init_circles(self):
        # sub_form_config = self.template['sub_forms']
        # template = sub_form_config['sub_form_templates'][0]
        for data_circles_config in self.template['circles']:
            data_circles_image = extract_rectangle_image(self.image, data_circles_config['rectangle'])
            self.data_circle_groups.append(DataCircleGroup(data_circles_image, data_circles_config))


def extract_rectangle_image(image, rectangle):
    image_height, image_width = image.shape
    print(image.shape, rectangle)
    top = int(image_height * rectangle['top'])
    bottom = int(image_height * rectangle['bottom'])
    left = int(image_width * rectangle['left'])
    right = int(image_width * rectangle['right'])
    print(top, bottom, left, right)
    # TODO: add a buffer outside the specified rectangle to avoid cropping circles if there's skew
    return image[top:bottom, left:right]


def process_form(
        input_image_path,
        form_config):
    assert Path(input_image_path).exists(), 'check input file path'
    form = OmrForm(input_image_path, form_config)
    form.extract_data()
    return form.data


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
        raise ImportError(
            'must have opencv version 3 or 4, yours is {}'.format(
                cv2.__version__))

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
    min_acceptable_perim = image_perim * 0.5
    if type(docCnt) != np.ndarray or perim < min_acceptable_perim:
        temp_image = cv2.cvtColor(edged_image, cv2.COLOR_GRAY2RGB)
        cv2.drawContours(temp_image, [docCnt], -1, (255, 0, 0), 3)
        # show_image(temp_image)
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
            print(
                'DEBUG: image was not correct orientation, rotating counter-cw 90 degrees'
            )
            original_image = np.array(
                Image.fromarray(original_image).rotate(90, expand=True))
        i += 1
    if not portrait == desired_portrait:
        raise OmrValidationException(
            'outer box not found with correct orientation')
    return grey_cropped, original_cropped


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


def expected_circle_locations(circles_per_row,
                              row_height,
                              column_width,
                              top_left_position=None):
    expected_locations = []
    top_left_position = top_left_position or [
        row_height / 2, column_width / 2
    ]
    print(top_left_position)
    y = top_left_position[0]
    for row, num_circles in enumerate(circles_per_row):
        x = top_left_position[1]
        for column in range(num_circles):
            expected_locations.append([int(x), int(y)])
            x += column_width
        y += row_height
    return expected_locations


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


def get_min_distance(height, width, rows, columns, tolerance=0.1):
    row_height = height / rows
    column_width = width / columns
    min_distance = min(row_height, column_width) * (1 - tolerance)
    return min_distance


def get_max_search_distance(height, width, rows, columns, tolerance=0.3):
    row_height = height / rows
    column_width = width / columns
    max_distance = max(row_height, column_width) * tolerance
    return max_distance


def extract_circles_grid(image,
                         circles_per_row,
                         radius,
                         possible_columns=None,
                         radius_tolerance=0.2,
                         hough_param_1=60,
                         hough_param_2=5):
    print(radius)
    debug_image = image.copy()
    possible_rows = len(circles_per_row)
    possible_columns = possible_columns or max(circles_per_row)
    assert len(image.shape) == 2, f'must be 1 channel 2D grey image, image has shape {image.shape}'
    min_distance = get_min_distance(*image.shape, possible_rows, possible_columns)
    min_radius = int(radius * (1 - radius_tolerance))
    max_radius = int(radius * (1 + radius_tolerance))
    row_height = image.shape[0] / possible_rows
    print(image.shape[0], possible_rows)
    column_width = image.shape[1] / possible_columns
    expected_locations = expected_circle_locations(circles_per_row, row_height, column_width)
    debug_expected_circles_min = [(x, y, min_radius) for x, y in expected_locations]
    # show_circles_on_image(
    #     debug_image,
    #     debug_expected_circles_min,
    #     'expected smallest circles',
    #     delayed_show=True,
    #     thickness=1)
    debug_expected_circles_max = [(x, y, max_radius) for x, y in expected_locations]
    # show_circles_on_image(
    #     debug_image,
    #     debug_expected_circles_max,
    #     'expected largest circles',
    #     delayed_show=False,
    #     thickness=1)
    candidate_circles = cv2.HoughCircles(
        image,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=min_distance,
        param1=hough_param_1,
        param2=hough_param_2,
        minRadius=min_radius,
        maxRadius=max_radius)
    if candidate_circles is None:
        raise OmrException('failed to get any circles from image')
    candidate_circles = np.uint16(np.around(candidate_circles))[0]
    # debug_candidate_circles = copy.deepcopy(candidate_circles)
    # show_circles_on_image(
    #     debug_image, candidate_circles, 'candidate_circles', delayed_show=True,
    #     thickness=1)
    candidate_circles = sorted(
        candidate_circles.copy().tolist(), key=lambda circ: circ[0] + circ[1])
    assert len(np.array(candidate_circles).shape
               ) == 2, 'shape must be (n,3), [} was passed'.format(
        np.array(candidate_circles).shape)
    max_circle_search_distance = get_max_search_distance(*image.shape, possible_rows, possible_columns)
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
    if len(filtered_circles) < sum(circles_per_row) * 0.5:
        raise OmrValidationException(
            'less than half the expected circles found')
    # show_circles_on_image(debug_image, filtered_circles, 'filtered circles')
    CIRCLE_SHRINK_FACTOR = 1 #0.85
    good_circles = list(
        map(lambda c: [c[0], c[1], int(c[2] * CIRCLE_SHRINK_FACTOR)], filtered_circles.copy()))
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
                    [good_x, good_y, radius])
            except:
                expected_location_circles = np.concatenate([
                    np.array(expected_locations),
                    np.array([[3] * len(expected_locations)]).T
                ],
                    axis=1)
                show_circles_on_image(
                    image,
                    expected_location_circles,
                    'expected circle locations',
                    delayed_show=True)
                show_circles_on_image(
                    image,
                    candidate_circles,
                    'ERROR (candidate circles)',
                    delayed_show=True)
                show_circles_on_image(image, filtered_circles,
                                      'ERROR (filtered circles)')
                raise OmrException('could not fill missing circles')
    # show_circles_on_image(image, good_circles,
    #                       'good circles', thickness=1)

    return good_circles


def circles_list_to_grid(circles, circles_per_row):
    circles_grid = []
    for row_length in circles_per_row:
        circles_grid.append([])
        for circle_index in range(row_length):
            circles_grid[-1].append(circles.pop(0))
    return circles_grid


def init_circles_from_grid(image, circle_grid):
    circles = []
    for circle_row in circle_grid:
        circles.append([])
        for bare_circle in circle_row:
            x = bare_circle[0]
            y = bare_circle[1]
            radius = bare_circle[2]
            x_lim_low = int(x - radius)
            x_lim_high = int(x + radius)
            y_lim_low = int(y - radius)
            y_lim_high = int(y + radius)
            circle_image = image[y_lim_low:y_lim_high, x_lim_low:x_lim_high]
            circles[-1].append(Circle(circle_image))
    return circles
