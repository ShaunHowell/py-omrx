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


class OmrException(Exception):
    pass


def closest_circle(x, y, circles):
    circle_coords = np.array(circles)[:, :2]
    d, i = KDTree(circle_coords).query([x, y], )
    return circles[i]


def expected_circle_locations(form_design, pixels_per_box):
    exp_loc = []
    y = 0
    w = pixels_per_box
    for row, num_options in enumerate(form_design['code']):
        x = 0
        for column in range(num_options):
            exp_loc.append([x + w / 2, y + w / 2])
            x += w
        y += w
    y += w
    for row, num_options in enumerate(form_design['questions']):
        x = 0
        for column in range(num_options):
            exp_loc.append([x + w / 2, y + w / 2])
            x += w
        y += w
    return exp_loc


def filter_circles(circles, form_design, pixels_per_box=64):
    circles = circles.copy().tolist()
    assert len(np.array(circles).shape) == 2, 'shape must be (n,3), [} was passed'.format(np.array(circles).shape)
    expected_locations = expected_circle_locations(form_design, pixels_per_box)
    filtered_circles = []
    for x, y in expected_locations:
        best_match = closest_circle(x, y, circles)

        if best_match:
            filtered_circles.append(best_match)
            circles.remove(best_match)
    return filtered_circles


def answers_from_image(input_file_path, form_design, debug = False):
    assert Path(input_file_path).exists(), 'check input file path'
    answers = pd.DataFrame(columns=['file_name', 'paper_code', 'box_no'])

    # prep image
    image = cv2.imread(input_file_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, threshold1=75, threshold2=200, L2gradient=True)

    # find outer bounding box
    cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
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
            Image.fromarray(edged).show()
            for i, c in enumerate(sorted(cnts, key=cv2.contourArea, reverse=True)):
                cv2.drawContours(image, [c], -1, color=(0, 0, 100 + (155) * i / len(cnts)), thickness=1)
            cv2.drawContours(image, sorted(cnts, key=cv2.contourArea, reverse=True), 0, color=(0, 255, 0), thickness=4)
            Image.fromarray(image).show()
        raise OmrException('no suitable outer contour found')

    # perspective transform
    shrink = 20
    # original_cropped = four_point_transform(image, docCnt.reshape(4, 2))
    # original_cropped = original_cropped[shrink:-shrink, shrink:-shrink]
    grey_cropped = four_point_transform(gray, docCnt.reshape(4, 2))
    grey_cropped = grey_cropped[shrink:-shrink, shrink:-shrink]

    # binarise
    thresh = cv2.threshold(grey_cropped, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

    # find the paper code
    paper_code_box = thresh[105:165, 280:500]
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
            temp_box = cv2.cvtColor(paper_code_box, cv2.COLOR_GRAY2RGB)
            for i in code_circles:
                cv2.circle(temp_box, (i[0], i[1]), i[2], (0, 255, 0), 2)
                cv2.circle(temp_box, (i[0], i[1]), 2, (0, 0, 255), 3)
            Image.fromarray(temp_box).show()
            cv2.drawContours(image, cnts, -1, color=(0, 0, 255), thickness=2)
            cv2.drawContours(image, cnts, 0, color=(0, 255, 0), thickness=4)
            Image.fromarray(image).show()
        raise OmrException('paper code not detected properly, please check file {}'.format(Path(input_file_path).name))

    # set variables for main omr processes
    form_design = form_design[str(paper_code)]
    bubbles_per_row = form_design['code'] + form_design['questions']
    left_margin = 60
    top_margin = 130
    pixels_per_row = 65
    height = (len(bubbles_per_row) + 1) * pixels_per_row + 5  # plus 1 for middle buffer

    # find inner bounding boxes
    innerBoxCnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    innerBoxCnts = innerBoxCnts[0] if imutils.is_cv2() else innerBoxCnts[1]
    innerBoxCnts = sorted(innerBoxCnts, key=cv2.contourArea, reverse=True)
    inner_boxes = []
    for c in sorted(innerBoxCnts[:3], key=lambda cnt: cv2.boundingRect(cnt.copy())[1], reverse=True):
        perim = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * perim, True)
        if len(approx) == 4:
            inner_box_cnt = approx
            inner_boxes.append(four_point_transform(thresh.copy(), inner_box_cnt.reshape(4, 2)))

    # extract data from inner boxes
    for box_no, inner_box in enumerate(inner_boxes):
        # rotate 90 via Pillow
        inner_box = np.array(Image.fromarray(inner_box).rotate(-90, expand=True))
        inner_box = inner_box[top_margin:top_margin + height, left_margin:]
        # find bubbles
        circles = cv2.HoughCircles(inner_box, cv2.HOUGH_GRADIENT, 1, 50,
                                   param1=50,
                                   param2=8,
                                   minRadius=14,
                                   maxRadius=24)
        circles = np.uint16(np.around(circles))[0]
        circles = filter_circles(circles, form_design, pixels_per_box=64)
        # sort circles top-to-bottom
        circles = np.array(sorted(circles, key=lambda circle: circle[1]))
        inner_box_answers = {}
        # bubbles_per_row = 2
        bubbles_processed = 0
        for question_number, num_bubbles in enumerate(bubbles_per_row):
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
                    if question_number < len(form_design['code']):
                        inner_box_answers.update({'c_{}'.format(question_number + 1): option_number})
                    else:
                        inner_box_answers.update(
                            {'q_{}'.format(question_number - len(form_design['code']) + 1): option_number})
                    best_confidence = average
                bubbles_processed += 1
            if best_confidence < 0.5:
                print('low confidence: q {}, box {}, file {}'.format(question_number + 1, box_no + 1,
                                                                     Path(input_file_path).name), file=sys.stderr)
                if question_number < len(form_design['code']):
                    inner_box_answers.update({'c_{}'.format(question_number + 1): np.nan})
                else:
                    inner_box_answers.update({'q_{}'.format(question_number - len(form_design['code']) + 1): np.nan})
        inner_box_answers.update({'file_name': Path(input_file_path).stem,
                                  'paper_code': paper_code,
                                  'box_no': box_no + 1})
        answers = answers.append(pd.Series(inner_box_answers), ignore_index=True)
    ok = True  # TODO: make this raise instead of returning ok, and handle it at the next function up
    if answers.isnull().sum().sum() > 0 or len(answers) < 3:
        ok = False
    return answers, ok


def answers_from_images(input_folder, form_design_path, output_folder=None):
    form_design = json.load(open(form_design_path))
    answers = pd.DataFrame(columns=['file_name', 'paper_code', 'box_no'])
    for file_path in Path(input_folder).iterdir():
        print('INFO: processing image {}'.format(file_path.name))
        try:
            im_answers, ok = answers_from_image(str(file_path), form_design)
            if not ok:
                print('problem with {}, please see above'.format(Path(file_path).name), file=sys.stderr)
            answers = answers.append(im_answers)
        except Exception as e:
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
