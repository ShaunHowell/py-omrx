import matplotlib.pyplot as plt

from omr_tool.omr.core.processing import *
from omr_tool.omr.core.processing import get_outer_box, process_boxes
from omr_tool.omr.exceptions import OmrException


def process_image(input_file_path, form_designs):
    assert Path(input_file_path).exists(), 'check input file path'
    image = cv2.imread(input_file_path)
    try:
        grey_outer_box, rgb_outer_box = get_outer_box(image)
    except OmrException as e:
        raise OmrException('no suitable outer contour found:\n{}'.format(e))
    try:
        paper_code = get_binary_code_from_outer_box(grey_outer_box,
                                                    105 / 3507, 175 / 3507,
                                                    0.145, 0.250,
                                                    0.0042, 0.0054,
                                                    0.0114, num_circles=3)
    except OmrException as e:
        raise OmrException(
            'paper code not detected properly, please check file {}:\n{}'.format(Path(input_file_path).name, e))
    form_design = form_designs[str(paper_code)]
    # print('INFO: form design:')
    # pprint.pprint(form_design)
    try:
        left_edge_coord = 0.028
        bottom_left_corners = [[0.944, left_edge_coord], [0.655, left_edge_coord], [0.363, left_edge_coord]]
        inner_boxes = get_inner_boxes(grey_outer_box, height=0.229, width=0.945,
                                      bottom_left_corners=bottom_left_corners)
    except OmrException as e:
        raise OmrException('couldn\'t find inner boxes correctly:\n{}'.format(e))
    answers = process_boxes(inner_boxes, form_design, num_boxes=3)
    answers['file_name'] = Path(input_file_path).stem
    answers['paper_code'] = paper_code
    return answers


def process_exam_marksheet_folder(input_folder, form_design_path, output_folder=None):
    process_images_folder(input_folder, form_design_path,
                          omr_mode='exam', output_folder=output_folder)

# if __name__ == '__main__' and sys.argv[1] == 'dev':
# form_design = json.load(open('demo/omr_data_extraction/data/ext/omr_form_designs.json'))
# answers, ok = answers_from_image('demo/omr_data_extraction/data/images/good_2.png', form_design)
# print(answers.to_string())

# temp_box = cv2.cvtColor(paper_code_box, cv2.COLOR_GRAY2RGB)
#     for i in code_circles:
#         cv2.circle(temp_box, (i[0], i[1]), i[2], (0, 255, 0), 2)
#         cv2.circle(temp_box, (i[0], i[1]), 2, (0, 0, 255), 3)
# Image.fromarray(temp_box).show()
