from omr.core.processing import *
import matplotlib.pyplot as plt


def process_attendance_sheet_folder(input_folder, form_design_path, output_folder=None):
    process_images_folder(input_folder, form_design_path,
                          image_type='attendance_register', output_folder=output_folder)


def process_image(input_file_path, form_designs):
    assert Path(input_file_path).exists(), 'check input file path'
    image = cv2.imread(input_file_path)
    try:
        grey_outer_box, rgb_outer_box = get_outer_box(image, desired_portrait=True)
    except OmrException as e:
        raise OmrException('no suitable outer contour found:\n{}'.format(e))
    form_design = form_designs[str(1)]
    # plt.imshow(Image.fromarray(grey_outer_box))
    # plt.show()
    try:
        school_number = get_binary_code_from_outer_box(grey_outer_box,
                                                       73 / 3116, 120 / 3116,
                                                       341 / 2165, 738 / 2165,
                                                       12 / 3116, 22 / 3116,
                                                       55 / 3166,
                                                       num_circles=6)
        class_number = get_binary_code_from_outer_box(grey_outer_box,
                                                      74 / 3116, 120 / 3116,
                                                      1290 / 2165, 1555 / 2165,
                                                      12 / 3116, 22 / 3116,
                                                      55 / 3166,
                                                      num_circles=4)
    except ZeroCodeFoundException:
        pass
    try:
        bottom_left_corners = [[0.99, 0]]
        inner_boxes = get_inner_boxes(grey_outer_box, height=0.97, width=1,
                                      bottom_left_corners=bottom_left_corners)


    except OmrException as e:
        raise OmrException('couldn\'t find inner boxes correctly:\n{}'.format(e))
    answers = process_boxes(inner_boxes, form_design, rotate_boxes=False)
    answers['file_name'] = Path(input_file_path).stem
    return answers
