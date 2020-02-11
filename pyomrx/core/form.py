import pandas as pd
from PIL import Image
from imutils.perspective import four_point_transform
from scipy.spatial.distance import euclidean

from pyomrx.core.exceptions import OmrException, OmrValidationException
import cv2
from pathlib import Path
from pyomrx.core.cv2_utils import load_and_check_image, extract_rectangle_image, get_one_channel_grey_image
from pyomrx.core.circle_group import BinaryCircles, DataCircleGroup
import imutils
import numpy as np
from pyomrx.core.vis_utils import show_image
from threading import Event
from pyomrx.core.meta import Abortable


class OmrForm(Abortable):
    def __init__(self, input_image_path, form_config, abort_event=None):
        Abortable.__init__(self, abort_event)
        self.input_image_path = Path(input_image_path)
        self.id = form_config['id']
        self.author = form_config['author']
        self.created_on = form_config['created_on']
        self.template = form_config['template']
        self._df = None
        self._data_values = None
        self._metadata_values = None
        self.image = None
        # self.metadata_circle_groups = self.template['metadata_circles']
        self.sub_forms = []
        self._load_image()
        # show_image(self.image, 'omr form')
        self._init_sub_forms()
        self.metadata_circle_groups = []
        self._init_metadata_circles()

    @property
    def metadata_values(self):
        if self._metadata_values is None:
            self._metadata_values = {
                m.name: m.value
                for m in self.metadata_circle_groups
            }
        return self._metadata_values

    @property
    def data(self):
        if self._data_values is None:
            self.extract_data()
        return self._data_values

    @property
    def df(self):
        if self._df is None:
            self.extract_df()
        return self._df

    def extract_data(self):
        dfs = [sub_form.values for sub_form in self.sub_forms]
        self._data_values = pd.concat(dfs, axis=0)
        return True

    def extract_df(self):
        df = self.data.copy()
        for metadata_name, metadata_value in self.metadata_values.items():
            df.loc[:, metadata_name] = metadata_value
        if 'page' in df.columns.tolist():
            df.index = df.index + len(df) * (df['page'] - 1) + 1
        # TODO: add an optional field in the sub form comments whereby the index can be given a column heading
        self._df = df
        return True

    def _load_image(self):
        self.image = load_and_check_image(self.input_image_path)
        try:
            grey_outer_box, rgb_outer_box = get_outer_box(
                self.image, desired_portrait=False)
            # show_image(rgb_outer_box, 'outer box')
        except OmrException as e:
            raise OmrException(
                'no suitable outer contour found:\n{}'.format(e))
        self.image = grey_outer_box

    def _init_sub_forms(self):
        sub_form_config = self.template['sub_forms']
        template = sub_form_config['sub_form_templates'][0]
        for rectangle in sub_form_config['locations']:
            sub_form_image = extract_rectangle_image(self.image, rectangle)
            # print('template')
            # print(template)
            self.sub_forms.append(
                OmrSubForm(
                    sub_form_image, template, abort_event=self.abort_event))

    def _init_metadata_circles(self):
        for metadata_circle_group_config in self.template['metadata_circles']:
            metadata_circles_image = extract_rectangle_image(
                self.image, metadata_circle_group_config['rectangle'])
            self.metadata_circle_groups.append(
                BinaryCircles(
                    metadata_circles_image,
                    metadata_circle_group_config,
                    abort_event=self.abort_event))


class OmrSubForm(Abortable):
    def __init__(self, image, template, abort_event=None):
        Abortable.__init__(self, abort_event)
        self.image = get_one_channel_grey_image(image)
        self.template = template
        # show_image(image, 'sub form')
        self.data_circle_groups = []
        self._init_circle_groups()
        self._values = None

    def _init_circle_groups(self):
        # sub_form_config = self.template['sub_forms']
        # template = sub_form_config['sub_form_templates'][0]
        for data_circles_config in self.template['circles']:
            data_circles_image = extract_rectangle_image(
                self.image, data_circles_config['rectangle'])
            self.data_circle_groups.append(
                DataCircleGroup(
                    data_circles_image,
                    data_circles_config,
                    abort_event=self.abort_event))

    @property
    def values(self):
        if self._values is None:
            self.extract_values()
        return self._values

    def extract_values(self):
        dfs = [circle_group.value for circle_group in self.data_circle_groups]
        # TODO: configurably allow different types of joins
        assert all([len(df) == len(dfs[0]) for df in dfs])
        df = pd.concat(dfs, axis=1)
        df = df.sort_index(axis=1)
        self._values = df
        # print(self._values.to_string())


def process_form(input_image_path, form_config):
    assert Path(input_image_path).exists(), 'check input file path'
    form = OmrForm(input_image_path, form_config)
    return form.df


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
    # show_image(dilated, title='after erosion-dilation', delayed_show=True)

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

    contour_image = edged_image.copy()
    cv2.drawContours(contour_image, cnts, -1, (255, 0, 0), 3)
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
        show_image(temp_image)
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
