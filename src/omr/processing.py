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


class OmrException(Exception):
    pass


class OmrValidationException(OmrException):
    pass


def closest_circle(x, y, circles):
    circle_coords = np.array(circles)[:, :2]
    d, i = KDTree(circle_coords).query([x, y], )
    return circles[i]


def expected_circle_locations(circles_per_header_row, circles_per_q_row, pixels_per_box):
    exp_loc = []
    y = 0
    w = pixels_per_box
    for row, num_options in enumerate(circles_per_header_row):
        x = 0
        for column in range(num_options):
            exp_loc.append([x + w / 2, y + w / 2])
            x += w
        y += w
    y += w
    for row, num_options in enumerate(circles_per_q_row):
        x = 0
        for column in range(num_options):
            exp_loc.append([x + w / 2, y + w / 2])
            x += w
        y += w
    return exp_loc


def filter_circles(circles, circles_per_header_row, circles_per_q_row, pixels_per_box=64):
    circles = circles.copy().tolist()
    assert len(np.array(circles).shape) == 2, 'shape must be (n,3), [} was passed'.format(np.array(circles).shape)
    expected_locations = expected_circle_locations(circles_per_header_row, circles_per_q_row, pixels_per_box)
    filtered_circles = []
    for x, y in expected_locations:
        best_match = closest_circle(x, y, circles)

        if best_match:
            filtered_circles.append(best_match)
            circles.remove(best_match)
    return filtered_circles


def get_outer_box_contour(edged_image, original_image=None, debug=False):
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
    if type(docCnt) != np.ndarray or perim < 9500:
        if debug:
            Image.fromarray(edged_image).show()
            for i, c in enumerate(sorted(cnts, key=cv2.contourArea, reverse=True)):
                cv2.drawContours(original_image, [c], -1, color=(0, 0, 100 + (155) * i / len(cnts)), thickness=1)
            cv2.drawContours(original_image, sorted(cnts, key=cv2.contourArea, reverse=True), 0, color=(0, 255, 0),
                             thickness=4)
            Image.fromarray(original_image).show()
        raise OmrException('no suitable outer contour found')
    return docCnt


def get_outer_box(original_image, debug=False):
    portrait = False
    i = 0
    while not portrait and i<2:
        gray = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, threshold1=75, threshold2=200, L2gradient=True)
        outer_box_contour = get_outer_box_contour(edged, original_image, debug)
        tl, bl, br, tr = outer_box_contour[0], outer_box_contour[1], outer_box_contour[2], outer_box_contour[3]
        heights = sorted([euclidean(bl,tl), euclidean(br,tr)])
        widths = sorted([euclidean(tr,tl),euclidean(br,bl)])
        try:
            assert heights[1] / heights[0] < 1.05
            assert widths[1] / widths[0] < 1.05
        except:
            # print('outer contour: {}'.format(outer_box_contour.tolist()))
            # cv2.drawContours(original_image, [outer_box_contour], -1, (0, 0, 255), 3)
            # Image.fromarray(original_image).show()
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


def get_paper_code(greyscale_outer_box, debug=False):
    # binarise
    binary_outer_box = cv2.threshold(greyscale_outer_box, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    paper_code_box = binary_outer_box[105:165, 280:500]
    code_circles = cv2.HoughCircles(paper_code_box, cv2.HOUGH_GRADIENT, 1, 50,
                                    param1=50,
                                    param2=8,
                                    minRadius=14,
                                    maxRadius=25)
    code_circles = np.uint16(np.around(code_circles))[0]
    code_circles = np.array(sorted(code_circles, key=lambda circle: circle[0], reverse=True))
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
        if debug:
            blurred = cv2.GaussianBlur(greyscale_outer_box, (5, 5), 0)
            edged = cv2.Canny(blurred, threshold1=75, threshold2=200, L2gradient=True)
            cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            cnts = cnts[0] if imutils.is_cv2() else cnts[1]
            temp_code_box = cv2.cvtColor(paper_code_box, cv2.COLOR_GRAY2RGB)
            for i in code_circles:
                cv2.circle(temp_code_box, (i[0], i[1]), i[2], (0, 255, 0), 2)
                cv2.circle(temp_code_box, (i[0], i[1]), 2, (0, 0, 255), 3)
            Image.fromarray(temp_code_box).show()
            cv2.drawContours(greyscale_outer_box, cnts, -1, color=(0, 0, 255), thickness=2)
            cv2.drawContours(greyscale_outer_box, cnts, 0, color=(0, 255, 0), thickness=4)
            Image.fromarray(greyscale_outer_box).show()
        raise OmrException('paper code not detected properly, please check file')
    return paper_code


def get_inner_boxes(greyscale_outer_box):
    box_1_cnt = [[[42, 2102]], [[46, 2775]], [[1978, 2773]], [[1976, 2101]]]
    box_2_cnt = [[[44, 1257]], [[46, 1925]], [[1979, 1923]], [[1977, 1253]]]
    box_3_cnt = [[[42, 412]], [[42, 1077]], [[1979, 1074]], [[1979, 410]]]
    # binary_outer_box = cv2.threshold(greyscale_outer_box, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    # candidate_cnts = cv2.findContours(binary_outer_box.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # candidate_cnts = candidate_cnts[0] if imutils.is_cv2() else candidate_cnts[1]
    # candidate_cnts = sorted(candidate_cnts, key=cv2.contourArea, reverse=True)
    # inner_boxes = []
    inner_box_cnts = [np.array(box_1_cnt), np.array(box_2_cnt), np.array(box_3_cnt)]
    # for c in sorted(candidate_cnts[:3], key=lambda cnt: cv2.boundingRect(cnt.copy())[1], reverse=True):
    #     perim = cv2.arcLength(c, True)
    #     approx = cv2.approxPolyDP(c, 0.02 * perim, True)
    #     if len(approx) == 4:
    #         inner_box_cnt = approx
    #         inner_boxes.append(four_point_transform(binary_outer_box.copy(), inner_box_cnt.reshape(4, 2)))
    #         inner_box_cnts.append(inner_box_cnt)
    inner_boxes = [four_point_transform(greyscale_outer_box.copy(), cnt.reshape(4, 2)) for cnt in inner_box_cnts]
    temp_box = cv2.cvtColor(greyscale_outer_box, cv2.COLOR_GRAY2RGB)
    # cv2.drawContours(temp_box, candidate_cnts, -1, (0, 255, 0), 3)
    cv2.drawContours(temp_box, inner_box_cnts, -1, (0, 0, 255), 3)
    Image.fromarray(temp_box).show()
    return inner_boxes


def get_answers_from_inner_box(inner_box, circles_per_header_row, circles_per_q_row):
    # Find circles
    inner_box = cv2.threshold(inner_box, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    circles = cv2.HoughCircles(inner_box, cv2.HOUGH_GRADIENT, 1, 50,
                               param1=50,
                               param2=8,
                               minRadius=14,
                               maxRadius=24)
    circles = np.uint16(np.around(circles))[0]
    circles = filter_circles(circles, circles_per_header_row, circles_per_q_row, pixels_per_box=64)

    # Draw circles for visualisation
    temp = cv2.cvtColor(inner_box, cv2.COLOR_GRAY2RGB)
    [cv2.circle(temp, (circ[0], circ[1]), circ[2], (0, 255, 0), thickness=2) for circ in circles]
    # Image.fromarray(temp).show()


    # Check region outside of circles doesn't have too many marks, or image quality is probably poor
    mask = np.ones(inner_box.shape, dtype="uint8")
    [cv2.circle(mask, (circ[0], circ[1]), int(circ[2]*1.3), 0, -1) for circ in circles]
    mask = cv2.bitwise_and(inner_box, inner_box, mask=mask)
    noise = sum((mask/255).flatten().tolist())*100/mask.size
    if noise > 13: # FIXME: needs manual calibration for each new excel form change
        print('mask mark percentage: ', sum((mask / 255).flatten().tolist()) * 100 / mask.size)
        raise OmrValidationException('too many marks found outside of circles')

    # sort circles top-to-bottom
    circles = np.array(sorted(circles, key=lambda circle: circle[1]))
    inner_box_answers = {}
    # bubbles_per_row = 2
    bubbles_processed = 0
    for question_number, num_bubbles in enumerate(circles_per_header_row + circles_per_q_row):
        question_circles = np.array(
            sorted(circles[bubbles_processed:bubbles_processed + num_bubbles], key=lambda circle: circle[0]))
        filled_circle = None
        best_confidence = 0
        for option_number, circle in enumerate(question_circles):
            # mask outside current bubble
            mask = np.zeros(inner_box.shape, dtype="uint8")
            cv2.circle(mask, (circle[0], circle[1]), circle[2], 255, -1)
            mask = cv2.bitwise_and(inner_box, inner_box, mask=mask)
            average = cv2.countNonZero(mask) / (circle[2] * circle[2] * 3.14)
            # check if best positive detection
            if filled_circle is None or average > filled_circle[0]:
                filled_circle = (average, option_number)
                if question_number < len(circles_per_header_row):
                    inner_box_answers.update({'c_{}'.format(question_number + 1): option_number})
                else:
                    inner_box_answers.update(
                        {'q_{}'.format(question_number - len(circles_per_header_row) + 1): option_number})
                best_confidence = average
            bubbles_processed += 1
        if best_confidence < 0.5:
            print('low confidence: row {}'.format(question_number + 1), file=sys.stderr)
            if question_number < len(circles_per_header_row):
                inner_box_answers.update({'c_{}'.format(question_number + 1): np.nan})
            else:
                inner_box_answers.update({'q_{}'.format(question_number - len(circles_per_header_row) + 1): np.nan})
    return pd.DataFrame(inner_box_answers, index=[0])


def get_answers_from_inner_boxes(inner_boxes, form_design):
    circles_per_row = form_design['code'] + form_design['questions']
    left_margin = 60
    top_margin = 130
    pixels_per_row = 65
    height = (len(circles_per_row) + 1) * pixels_per_row + 5  # plus 1 for middle buffer
    answers = pd.DataFrame(columns=['file_name', 'paper_code', 'box_no'])
    for box_no, inner_box in enumerate(inner_boxes):
        inner_box = np.array(Image.fromarray(inner_box).rotate(-90, expand=True))
        inner_box = inner_box[top_margin:top_margin + height, left_margin:]
        inner_box_answers = get_answers_from_inner_box(inner_box, form_design['code'], form_design['questions'])
        inner_box_answers['box_no'] = box_no + 1
        answers = answers.append(inner_box_answers)
    ok = True  # TODO: make this raise instead of returning ok, and handle it at the next function up
    if answers.isnull().sum().sum() > 0 or len(answers) < 3:
        ok = False
    return answers


def answers_from_image(input_file_path, form_designs, debug=False):
    assert Path(input_file_path).exists(), 'check input file path'
    image = cv2.imread(input_file_path)
    try:
        grey_outer_box, rgb_outer_box = get_outer_box(image, debug)
    except OmrException as e:
        raise OmrException('no suitable outer contour found:\n{}'.format(e))
    try:
        paper_code = get_paper_code(grey_outer_box)
    except OmrException as e:
        raise OmrException(
            'paper code not detected properly, please check file {}:\n{}'.format(Path(input_file_path).name, e))
    form_design = form_designs[str(paper_code)]
    try:
        inner_boxes = get_inner_boxes(grey_outer_box)
    except OmrException as e:
        raise OmrException('couldn\'t find inner boxes correctly:\n{}'.format(e))
    answers = get_answers_from_inner_boxes(inner_boxes, form_design)
    answers['file_name'] = Path(input_file_path).stem
    answers['paper_code'] = paper_code
    return answers


def answers_from_images(input_folder, form_design_path, output_folder=None):
    form_design = json.load(open(form_design_path))
    answers = pd.DataFrame(columns=['file_name', 'paper_code', 'box_no'])
    for file_path in Path(input_folder).iterdir():
        print('INFO: processing image {}'.format(file_path.name))
        try:
            im_answers = answers_from_image(str(file_path), form_design)
            # if not ok:
            #     print('problem with {}, please see above'.format(Path(file_path).name), file=sys.stderr)
            answers = answers.append(im_answers)
        except OmrException as e:
            print('couldn\'t extract data from {}: check input file'.format(Path(file_path).name), file=sys.stderr)
            print('error message: ', e, file=sys.stderr)
    if output_folder:
        if not Path(output_folder).exists():
            Path(output_folder).mkdir(parents=True)
        answers.to_csv(str(Path(output_folder) / 'omr_output.csv'), index=False)
    return answers


if __name__ == '__main__' and sys.argv[1] == 'dev':
    form_design = json.load(open('demo/omr_data_extraction/data/ext/omr_form_designs.json'))
    answers, ok = answers_from_image('demo/omr_data_extraction/data/images/good_2.png', form_design)
    print(answers.to_string())

    # temp_box = cv2.cvtColor(paper_code_box, cv2.COLOR_GRAY2RGB)
    #     for i in code_circles:
    #         cv2.circle(temp_box, (i[0], i[1]), i[2], (0, 255, 0), 2)
    #         cv2.circle(temp_box, (i[0], i[1]), 2, (0, 0, 255), 3)
    # Image.fromarray(temp_box).show()
