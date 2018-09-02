import sys
from imutils.perspective import four_point_transform
import numpy as np
import imutils
import cv2
import pprint
import json
from PIL import Image
from pathlib import Path
from scipy.spatial import KDTree
import pandas as pd
from scipy.spatial.distance import euclidean
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans


class OmrException(Exception):
    pass


class OmrValidationException(OmrException):
    pass


def nearby_circle(x, y, circles, max_distance=np.inf):
    if len(circles) == 0:
        raise OmrValidationException('no more candidate circles available')
    circle_coords = np.array(circles)[:, :2]
    d, i = KDTree(circle_coords).query([x, y], distance_upper_bound=max_distance)
    if d != np.inf:
        return circles[i]
    else:
        return None


def expected_circle_locations(circles_per_header_row, circles_per_q_row, bubble_spacing,
                              top_left_position=None):
    exp_loc = []
    spacing_width = bubble_spacing[0]
    spacing_height = bubble_spacing[1]
    top_left_position = top_left_position if top_left_position is not None else [0, 0]
    y = top_left_position[1]
    for row, num_options in enumerate(circles_per_header_row):
        x = top_left_position[0]
        for column in range(num_options):
            exp_loc.append([int(x), int(y)])
            x += spacing_width
        y += spacing_height
    y += spacing_height
    for row, num_options in enumerate(circles_per_q_row):
        x = top_left_position[0]
        for column in range(num_options):
            exp_loc.append([int(x), int(y)])
            x += spacing_width
        y += spacing_height
    return exp_loc


def circles_from_grid(x_coords, y_coords, circles_per_header_row, circles_per_q_row):
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
    circle_size = x_box_size * 0.19
    # Make most likely circle locations
    for y_coord, circles_for_row in zip(y_coords, circles_per_header_row + circles_per_q_row):
        for x_coord, _ in zip(x_coords, range(circles_for_row)):
            circles.append([int(x_coord), int(y_coord), int(circle_size)])
    return circles


def get_good_circles(candidate_circles, circles_per_header_row, circles_per_q_row, inner_box_shape, debug_image):
    candidate_circles = sorted(candidate_circles.copy().tolist(), key=lambda circ: circ[0] + circ[1])
    assert len(np.array(candidate_circles).shape) == 2, 'shape must be (n,3), [} was passed'.format(
        np.array(candidate_circles).shape)
    bubble_box_width = inner_box_shape[1] / max(circles_per_q_row + circles_per_header_row)
    bubble_box_height = inner_box_shape[0] / (27) # number of rows in inner box
    max_circle_search_distance = max([bubble_box_height, bubble_box_width]) * 0.5
    bubble_spacing = [0.995 * bubble_box_width, 1.00 * bubble_box_height]
    top_left_position = [int(0.53 * bubble_box_width), int(0.65 * bubble_box_height)]
    # print('bubble box shape: w:{}, h:{}'.format(bubble_box_width, bubble_box_height))
    # print('bubble spacing: {}'.format(bubble_spacing))
    # print('top left pos: {}'.format(top_left_position))
    expected_locations = expected_circle_locations(circles_per_header_row,
                                                   circles_per_q_row,
                                                   bubble_spacing,
                                                   top_left_position)
    # temp_image = cv2.cvtColor(debug_image, cv2.COLOR_GRAY2RGB)
    # [cv2.circle(temp_image,tuple(loc),2,(255,0,0), -1) for loc in expected_locations]
    # [cv2.circle(temp_image,(circ[0],circ[1]),circ[2],(0,255,0), 2) for circ in candidate_circles]
    # plt.imshow(temp_image)
    # plt.show()
    filtered_circles = []
    for x, y in expected_locations:
        try:
            good_match = nearby_circle(x, y, candidate_circles, max_circle_search_distance)
            if good_match:
                filtered_circles.append(good_match)
                candidate_circles.remove(good_match)
        except OmrValidationException as e:
            print('WARNING: Found too few circles')
            break
    if len(filtered_circles) < len(circles_per_header_row + circles_per_q_row) * 0.5:
        raise OmrValidationException('less than half the expected circles found')
    y_coords = [circ[1] for circ in filtered_circles]
    x_coords = [circ[0] for circ in filtered_circles]
    try:
        # Cluster x & y coords
        x_km = KMeans(max(circles_per_header_row + circles_per_q_row))
        y_km = KMeans(len(circles_per_header_row + circles_per_q_row))
    except ValueError as e:
        print('error, could not find good circles, probably there wasn\'t at least one circle in each row and column')
        # TODO: this edge case doesn't have to raise: can fill in missing values if not enough circles found
        raise e
    x_km.fit(np.array(x_coords).reshape(-1, 1))
    x_cluster_centers = sorted(x_km.cluster_centers_.flatten().tolist())
    y_km.fit(np.array(y_coords).reshape(-1, 1))
    y_cluster_centers = sorted(y_km.cluster_centers_.flatten().tolist())
    good_circles = circles_from_grid(x_cluster_centers, y_cluster_centers, circles_per_header_row, circles_per_q_row)
    return good_circles


def get_outer_box_contour(edged_image):
    cnts = cv2.findContours(edged_image.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if imutils.is_cv2() else cnts[1]
    docCnt = None
    assert len(cnts) > 0, 'no contours found when looking for outer box'
    for c in sorted(cnts, key=cv2.contourArea, reverse=True):
        perim = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.05 * perim, True)
        if len(approx) == 4:
            docCnt = approx
            break
    if type(docCnt) != np.ndarray or perim < 7400:
        # temp_image = cv2.cvtColor(edged_image, cv2.COLOR_GRAY2RGB)
        # cv2.drawContours(temp_image, [docCnt], -1, (255, 0, 0), 3)
        # plt.imshow(temp_image)
        # plt.show()
        raise OmrException('no suitable outer contour found, '
                           'biggest outer contour had perim of {}'.format(perim))
    return docCnt


def get_outer_box(original_image):
    portrait = False
    i = 0
    while not portrait and i < 2:
        gray = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.medianBlur(gray, 7)
        blurred = cv2.blur(blurred, ksize=(7, 7))
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        edged = cv2.Canny(thresh, threshold1=180, threshold2=230, L2gradient=True, apertureSize=3)
        outer_box_contour = get_outer_box_contour(edged)
        tl, bl, br, tr = outer_box_contour[0], outer_box_contour[1], outer_box_contour[2], outer_box_contour[3]
        heights = sorted([euclidean(bl, tl), euclidean(br, tr)])
        widths = sorted([euclidean(tr, tl), euclidean(br, bl)])
        try:
            assert heights[1] / heights[0] < 1.05
            assert widths[1] / widths[0] < 1.05
        except:
            raise OmrValidationException('good outer box not found')
        shrink = 20
        original_cropped = four_point_transform(original_image, outer_box_contour.reshape(4, 2))
        original_cropped = original_cropped[shrink:-shrink, shrink:-shrink]
        grey_cropped = four_point_transform(gray, outer_box_contour.reshape(4, 2))
        grey_cropped = grey_cropped[shrink:-shrink, shrink:-shrink]
        height, width, = grey_cropped.shape
        if height > width:
            portrait = True
        else:
            original_image = np.array(Image.fromarray(original_image).rotate(90, expand=True))
        i += 1
    if not portrait:
        raise OmrValidationException('portrait outer box not found')
    return grey_cropped, original_cropped


def get_paper_code(greyscale_outer_box):
    height, width = greyscale_outer_box.shape
    h1, h2 = int(height * 105 / 3507), int(height * 175 / 3057)
    w1, w2 = int(width * 0.145), int(width * 0.250)
    r1, r2 = int(height * 0.0042), int(height * 0.0054)
    min_dist = int(height * 0.0114)
    binary_outer_box = cv2.threshold(greyscale_outer_box, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    paper_code_box = binary_outer_box[h1:h2, w1:w2]
    # temp_image = Image.fromarray(paper_code_box)
    # plt.imshow(temp_image)
    # plt.show()
    code_circles = cv2.HoughCircles(paper_code_box, cv2.HOUGH_GRADIENT, 1,
                                    min_dist,
                                    param1=150,
                                    param2=5,
                                    minRadius=r1,
                                    maxRadius=r2)
    code_circles = np.uint16(np.around(code_circles))[0]
    code_circles = np.array(sorted(code_circles, key=lambda circle: circle[0], reverse=True))  # read left to right
    assert len(code_circles) == 3, 'found {} circles whilst trying ' \
                                   'to find paper code, should be 3'.format(len(code_circles))
    paper_code = 0
    for i, circle in enumerate(code_circles):
        mask = np.zeros(paper_code_box.shape, dtype="uint8")
        cv2.circle(mask, (circle[0], circle[1]), circle[2], 255, -1)
        mask = cv2.bitwise_and(paper_code_box, paper_code_box, mask=mask)
        average = cv2.countNonZero(mask) / (circle[2] * circle[2] * 3.14)
        # check if positive detection
        if average > 0.5:
            paper_code = paper_code + 2 ** i
    if paper_code <= 0:
        raise OmrException('paper code not detected properly, please check file')
    # print('INFO: paper code: {}'.format(paper_code))
    return paper_code


def get_inner_boxes(greyscale_outer_box):
    h, w = greyscale_outer_box.shape
    box_height, box_width = 0.96 * w, 0.234 * h  # height & width of inner boxes when they're portrait
    bl_1, bl_2, bl_3 = [0.017 * w, 0.948 * h], [0.017 * w, 0.655 * h], [0.017 * w,
                                                                        0.363 * h]  # bottom left corner coords with page portrait
    box_1_cnt = [[bl_1], [[bl_1[0], bl_1[1] - box_width]], [[bl_1[0] + box_height, bl_1[1] - box_width]],
                 [[bl_1[0] + box_height, bl_1[1]]]]
    box_2_cnt = [[bl_2], [[bl_2[0], bl_2[1] - box_width]], [[bl_2[0] + box_height, bl_2[1] - box_width]],
                 [[bl_2[0] + box_height, bl_2[1]]]]
    box_3_cnt = [[bl_3], [[bl_3[0], bl_3[1] - box_width]], [[bl_3[0] + box_height, bl_3[1] - box_width]],
                 [[bl_3[0] + box_height, bl_3[1]]]]
    inner_box_cnts = [np.array(box_1_cnt), np.array(box_2_cnt), np.array(box_3_cnt)]
    inner_boxes = [four_point_transform(greyscale_outer_box.copy(), cnt.reshape(4, 2)) for cnt in inner_box_cnts]

    # temp_image = cv2.cvtColor(greyscale_outer_box, cv2.COLOR_GRAY2RGB)
    # cv2.drawContours(temp_image, inner_box_cnts, -1, (255, 0, 0), 3)
    # [plt.imshow(temp_image) for temp_image in inner_boxes]
    plt.show()
    return inner_boxes


def process_boxes(inner_boxes, form_design):
    circles_per_row = form_design['code'] + form_design['questions']
    answers = pd.DataFrame(columns=['file_name', 'paper_code', 'box_no', 'omr_error', 'marker_error'])
    for box_no, inner_box in enumerate(inner_boxes):
        h, w = inner_box.shape
        left_margin = int(0.101 * h)
        top_margin = int(0.1 * w)
        # pixels_per_row = int(0.085 * h)
        # height = (len(circles_per_row) + 1) * pixels_per_row  # plus 2 for middle buffer and top buffer

        inner_box = np.array(Image.fromarray(inner_box).rotate(-90, expand=True))
        inner_box = inner_box[top_margin:, left_margin:]
        # plt.imshow(inner_box)
        # plt.show()
        try:
            inner_box_answers = process_inner_box(inner_box, form_design['code'], form_design['questions'])
            inner_box_answers['box_no'] = box_no + 1
        except OmrException as e:
            print('Couldn\'t extract answers from box {}'.format(box_no + 1), file=sys.stderr)
            print('error: {}'.format(e))
            inner_box_answers = pd.DataFrame([[box_no + 1, True]], columns=['box_no', 'omr_error'])
        answers = answers.append(inner_box_answers)
    if answers.drop(['omr_error', 'marker_error', 'file_name', 'paper_code'], axis=1).isnull().sum().sum() > 0 or len(
            answers) < 3:
        raise OmrException('Must be no nulls in answers and must be 3 boxes processed')
    return answers


def process_circle(inner_box, circle):
    mask = np.zeros(inner_box.shape, dtype="uint8")
    cv2.circle(mask, (circle[0], circle[1]), circle[2], 255, -1)
    mask = cv2.bitwise_and(inner_box, inner_box, mask=mask)
    return cv2.countNonZero(mask) / (circle[2] * circle[2] * 3.14)


def response_from_darknesses(darknesses):
    if max(darknesses) < 0.09:
        return -1 # -1 means the row doesn't have a response
    filled_circles = list(filter(lambda d: d > 0.25, darknesses))
    if len(filled_circles) > 1:
        return -2 # -2 means more than one response detected
    if len(filled_circles) < 1:
        return -3 # -3 means the omr algorithm couldn't work out the filled in box (abstention)
    darknesses = enumerate(darknesses)
    darknesses = sorted(darknesses, key=lambda circle: circle[1])
    if darknesses[-1][1] / darknesses[-2][1] < 1.6:
        return -3 # -3 because there wasn't enough difference between the 1st and 2nd darkest circles
    return darknesses[-1][0]


def process_inner_box(inner_box, circles_per_header_row, circles_per_q_row):
    h, w = inner_box.shape
    min_dist = int(0.036 * h)
    r1, r2 = int(0.008 * h), int(0.011 * h)
    inner_box = cv2.threshold(inner_box, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    circles = cv2.HoughCircles(inner_box, cv2.HOUGH_GRADIENT,
                               dp=1,
                               minDist=min_dist,
                               param1=50,
                               param2=8,
                               minRadius=r1,
                               maxRadius=r2)
    circles = np.uint16(np.around(circles))[0]
    circles = get_good_circles(circles, circles_per_header_row, circles_per_q_row,
                               inner_box_shape=inner_box.shape, debug_image=inner_box)
    # Check region outside of circles doesn't have too many marks, or image quality is probably poor
    mask = np.ones(inner_box.shape, dtype="uint8")
    [cv2.circle(mask, (circ[0], circ[1]), int(circ[2] * 1.3), 0, -1) for circ in circles]
    mask = cv2.bitwise_and(inner_box, inner_box, mask=mask)
    noise = sum((mask / 255).flatten().tolist()) * 100 / mask.size
    if noise > 11:  # FIXME: needs manual calibration for each new excel form change
        raise OmrValidationException('too many marks found outside of circles')
    # sort circles top-to-bottom
    circles = np.array(sorted(circles, key=lambda circle: circle[1]))
    inner_box_answers = {}
    bubbles_processed = 0
    for question_number, num_bubbles in enumerate(circles_per_header_row + circles_per_q_row):
        question_circles = np.array(
            sorted(circles[bubbles_processed:bubbles_processed + num_bubbles], key=lambda circle: circle[0]))
        darknesses = []
        # get circle darknesses
        for circle in question_circles:
            darknesses.append(process_circle(inner_box, circle))
            bubbles_processed += 1
        # determine response based on circle darknesses
        response = response_from_darknesses(darknesses)
        # print('Row {}, darknesses: {}, response: {}'.format(question_number, list(enumerate(darknesses)), response))
        if response == -3:
            inner_box_answers.update({'omr_error': True})
        if response in [-1, -2]:
            inner_box_answers.update({'marker_error': True})
        if question_number < len(circles_per_header_row):
            inner_box_answers.update({'c_{:0>2}'.format(question_number + 1): response})
        else:
            inner_box_answers.update(
                {'q_{:0>2}'.format(question_number - len(circles_per_header_row) + 1): response})
    return pd.DataFrame(inner_box_answers, index=[0])


def process_image(input_file_path, form_designs):
    assert Path(input_file_path).exists(), 'check input file path'
    # if 'L2' not in input_file_path: return
    image = cv2.imread(input_file_path)
    try:
        grey_outer_box, rgb_outer_box = get_outer_box(image)
    except OmrException as e:
        raise OmrException('no suitable outer contour found:\n{}'.format(e))
    try:
        paper_code = get_paper_code(grey_outer_box)
    except OmrException as e:
        raise OmrException(
            'paper code not detected properly, please check file {}:\n{}'.format(Path(input_file_path).name, e))
    form_design = form_designs[str(paper_code)]
    # print('INFO: form design:')
    # pprint.pprint(form_design)
    try:
        inner_boxes = get_inner_boxes(grey_outer_box)
    except OmrException as e:
        raise OmrException('couldn\'t find inner boxes correctly:\n{}'.format(e))
    answers = process_boxes(inner_boxes, form_design)
    answers['file_name'] = Path(input_file_path).stem
    answers['paper_code'] = paper_code
    return answers


def process_images_folder(input_folder, form_design_path, output_folder=None):
    form_design = json.load(open(form_design_path))
    answers_df = pd.DataFrame(columns=['file_name', 'paper_code', 'box_no'])
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

# if __name__ == '__main__' and sys.argv[1] == 'dev':
# form_design = json.load(open('demo/omr_data_extraction/data/ext/omr_form_designs.json'))
# answers, ok = answers_from_image('demo/omr_data_extraction/data/images/good_2.png', form_design)
# print(answers.to_string())

# temp_box = cv2.cvtColor(paper_code_box, cv2.COLOR_GRAY2RGB)
#     for i in code_circles:
#         cv2.circle(temp_box, (i[0], i[1]), i[2], (0, 255, 0), 2)
#         cv2.circle(temp_box, (i[0], i[1]), 2, (0, 0, 255), 3)
# Image.fromarray(temp_box).show()