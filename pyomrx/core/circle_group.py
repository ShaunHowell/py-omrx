import pandas as pd
from pyomrx.core.cv2_utils import *
from scipy.spatial import KDTree
from pyomrx.core.circle import Circle
from pyomrx.core.vis_utils import show_circles_on_image, show_image
from threading import Event
from pyomrx.core.meta import Abortable


class CircleGroup(Abortable):
    def __init__(self, image, config, abort_event=None):
        Abortable.__init__(self, abort_event)
        self.image = get_one_channel_grey_image(image)
        self.config = config
        self.name = config['name']
        self._value = None

    @property
    def value(self):
        if self._value is None:
            self._extract_value()
        return self._value

    def _extract_value(self):
        raise NotImplementedError()

    def extract_circles_grid(self,
                             image,
                             circles_per_row,
                             radius,
                             possible_columns=None,
                             radius_tolerance=0.2,
                             hough_param_1=60,
                             hough_param_2=5):
        # print(radius)
        debug_image = image.copy()
        possible_rows = len(circles_per_row)
        possible_columns = possible_columns or max(circles_per_row)
        assert len(
            image.shape
        ) == 2, f'must be 1 channel 2D grey image, image has shape {image.shape}'
        min_distance = get_min_distance(*image.shape, possible_rows,
                                        possible_columns)
        min_radius = int(radius * (1 - radius_tolerance))
        max_radius = int(radius * (1 + radius_tolerance))
        row_height = image.shape[0] / possible_rows
        # print(image.shape[0], possible_rows)
        column_width = image.shape[1] / possible_columns
        expected_locations = expected_circle_locations(
            circles_per_row, row_height, column_width)
        debug_expected_circles_min = [(x, y, min_radius)
                                      for x, y in expected_locations]
        # show_circles_on_image(
        #     debug_image,
        #     debug_expected_circles_min,
        #     'expected smallest circles',
        #     delayed_show=True,
        #     thickness=1)
        debug_expected_circles_max = [(x, y, max_radius)
                                      for x, y in expected_locations]
        # show_circles_on_image(
        #     debug_image,
        #     debug_expected_circles_max,
        #     'expected largest circles',
        #     delayed_show=False,
        #     thickness=1)
        self.raise_for_abort()
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
            candidate_circles.copy().tolist(),
            key=lambda circ: circ[0] + circ[1])
        self.raise_for_abort()
        assert len(np.array(candidate_circles).shape
                   ) == 2, 'shape must be (n,3), [} was passed'.format(
                       np.array(candidate_circles).shape)
        self.raise_for_abort()
        max_circle_search_distance = get_max_search_distance(
            *image.shape, possible_rows, possible_columns)
        filtered_circles = []
        good_x_coords, good_y_coords = {}, {}
        for x, y in expected_locations:
            self.raise_for_abort()
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
        self.raise_for_abort()
        # show_circles_on_image(debug_image, filtered_circles, 'filtered circles')
        CIRCLE_SHRINK_FACTOR = 1  # 0.85
        good_circles = list(
            map(lambda c: [c[0], c[1],
                           int(c[2] * CIRCLE_SHRINK_FACTOR)],
                filtered_circles.copy()))
        y_coord_options = np.unique(
            [coord[1] for coord in expected_locations]).tolist()
        x_coord_options = np.unique(
            [coord[0] for coord in expected_locations]).tolist()

        for x, y in expected_locations:
            self.raise_for_abort()
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
                    good_circles.append([good_x, good_y, radius])
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


class BinaryCircles(CircleGroup):
    def __init__(self, image, config, abort_event=None):
        # TODO: assert that the image is approximately the correct dimensions for the radius and number of circles
        CircleGroup.__init__(self, image, config, abort_event)
        # show_image(image, f'binary circles {config["name"]}')

    def _extract_value(self):
        # print(f'extracting for binary circles {self.name}')
        absolute_radius = self.config['radius'] * max(self.image.shape)
        bare_circles_list = self.extract_circles_grid(
            self.image, [self.config['quantity']], absolute_radius,
            self.config['quantity'])
        bare_circles_grid = circles_list_to_grid(bare_circles_list,
                                                 [self.config['quantity']])
        self.circles = init_circles_from_grid(self.image, bare_circles_grid)[0]
        # TODO: seems like form circles are above the row centerline
        # TODO: seems like expected circle size is still smaller than actual circles
        # print(self.circles)
        value = 0
        for i, circle in enumerate(reversed(self.circles)):
            if circle.is_filled:
                value = value + 2**i
        self._value = value


class DataCircleGroup(CircleGroup):
    def __init__(self, image, config, abort_event=None):
        CircleGroup.__init__(self, image, config, abort_event)
        self.raise_for_abort()
        self.row_filling = config['allowed_row_filling']
        self.circles = []
        if self.row_filling != 'many':
            raise NotImplementedError(
                'cant do single circle per row data circles yet (eg exam forms)'
            )

    def _extract_value(self):
        self.raise_for_abort()
        # show_image(self.image, 'data_circles')
        absolute_radius = self.config['radius'] * max(self.image.shape)
        bare_circles_list = self.extract_circles_grid(
            self.image, self.config['circles_per_row'], absolute_radius,
            self.config['possible_columns'])
        bare_circles_grid = circles_list_to_grid(
            bare_circles_list, self.config['circles_per_row'])
        self.circles = init_circles_from_grid(self.image, bare_circles_grid)
        # TODO: seems like form circles are above the row centerline
        # TODO: seems like expected circle size is still smaller than actual circles
        values = []
        for row in self.circles:
            values.append([])
            for circle in row:
                values[-1].append(circle.is_filled)
        if self.config['possible_columns'] == 1:
            columns = [self.config['column_prefix']]
        elif self.config['possible_columns'] > 1:
            columns = [
                f'{self.config["column_prefix"]}{i:02}'
                for i in range(self.config["possible_columns"])
            ]
        else:
            raise ValueError(
                f'possible columns of {self.config["possible_columns"]} not allowed'
            )
        self._value = pd.DataFrame(values, columns=columns)
        return True


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
    top_left_position = top_left_position or [row_height / 2, column_width / 2]
    # print(top_left_position)
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
