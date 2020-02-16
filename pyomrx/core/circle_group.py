from scipy.spatial import distance
from scipy.optimize import minimize
import pandas as pd
from pyomrx.core.cv2_utils import *
from pyomrx.core.circle import Circle
from pyomrx.core.meta import Abortable
from pyomrx.core.vis_utils import show_circles_on_image, show_image


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
                             circles_per_row,
                             radius,
                             possible_columns=None,
                             radius_tolerance=0.2,
                             hough_param_1=60,
                             hough_param_2=5):
        image = self.image
        possible_rows = len(circles_per_row)
        possible_columns = possible_columns or max(circles_per_row)
        assert len(
            image.shape
        ) == 2, f'must be 1 channel 2D grey image, image has shape {image.shape}'
        row_height = image.shape[0] / possible_rows
        column_width = image.shape[1] / possible_columns
        expected_circles = get_expected_circles(
            circles_per_row, row_height, column_width, radius=radius)
        self.raise_for_abort()
        # show_circles_on_image(image, expected_circles.astype(int).tolist(),
        #                       'expected circles', thickness=2)
        min_distance = get_min_distance(*image.shape, possible_rows,
                                        possible_columns)
        min_radius = int(radius * (1 - radius_tolerance))
        max_radius = int(radius * (1 + radius_tolerance))
        seen_circles = cv2.HoughCircles(
            image,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=min_distance,
            param1=hough_param_1,
            param2=hough_param_2,
            minRadius=min_radius,
            maxRadius=max_radius)
        if seen_circles is None:
            raise OmrException('failed to identify any circles from image')
        seen_circles = seen_circles[0]
        # show_circles_on_image(image, seen_circles,
        #                       'seen circles', thickness=2)
        good_circles = get_best_fitting_grid(
            circles_grid=expected_circles, seen_circles=seen_circles)
        good_circles = good_circles.astype(int).tolist()
        # show_circles_on_image(image, good_circles,
        #                       'good circles', thickness=2)
        good_circles_grid = circles_list_to_grid(good_circles, circles_per_row)
        return good_circles_grid


class BinaryCircles(CircleGroup):
    def __init__(self, image, config, abort_event=None):
        # TODO: assert that the image is approximately the correct dimensions for the radius and number of circles
        CircleGroup.__init__(self, image, config, abort_event)
        # show_image(image, f'binary circles {config["name"]}')

    def _extract_value(self):
        # print(f'extracting for binary circles {self.name}')
        absolute_radius = self.config['radius'] * max(self.image.shape)
        bare_circles_grid = self.extract_circles_grid(
            [self.config['quantity']], absolute_radius,
            self.config['quantity'])
        # bare_circles_grid = circles_list_to_grid(bare_circles_list,
        #                                          [self.config['quantity']])
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

    def _extract_value(self):
        self.raise_for_abort()
        # show_image(self.image, 'data_circles')
        absolute_radius = self.config['radius'] * max(self.image.shape)
        bare_circles_grid = self.extract_circles_grid(
            self.config['circles_per_row'], absolute_radius,
            self.config['possible_columns'])
        # bare_circles_grid = circles_list_to_grid(
        #     bare_circles_grid, self.config['circles_per_row'])
        # print(bare_circles_grid)
        self.circles = init_circles_from_grid(self.image, bare_circles_grid)
        if self.row_filling == 'many':
            values = self._get_value_many_per_row()
        elif self.row_filling == 'one':
            values = self._get_value_one_per_row()
        else:
            raise ValueError(f'row_filling of {self.row_filling} not allowed')

        if self.config['possible_columns'] == 1:
            if self.config['column_prefix'] == None:
                print(
                    'WARNING: found a column prefix of None and only 1 columns: will set column name to "1"'
                )
                columns = ['1']
            else:
                columns = [self.config['column_prefix']]
        elif self.config['possible_columns'] > 1:
            prefix = self.config["column_prefix"] or ''
            if self.row_filling == 'many':
                columns = [
                    f'{prefix}{i:02}'
                    for i in range(1, self.config["possible_columns"] + 1)
                ]
            else:
                columns = [
                    f'{prefix}{i:02}' for i in range(1,
                                                     len(self.circles) + 1)
                ]
        else:
            raise ValueError(
                f'possible columns of {self.config["possible_columns"]} not allowed'
            )
        self._value = pd.DataFrame(values, columns=columns)
        return True

    def _get_value_one_per_row(self):
        values = []
        for row in self.circles:
            if not row:
                # skip if no circles on this row
                continue
            response = single_response_from_darknesses(
                [circle.relative_fill for circle in row])
            values.append(response)
        return [values]

    def _get_value_many_per_row(self):
        values = []
        for row in self.circles:
            values.append([])
            for circle in row:
                values[-1].append(circle.is_filled)
        return values


def single_response_from_darknesses(darknesses):
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
    if darknesses[-2][1] > 0:
        if darknesses[-1][1] / darknesses[-2][1] < 1.6:
            return -3  # -3 because there wasn't enough difference between the 1st and 2nd darkest circles
    return darknesses[-1][0]


def get_expected_circles(circles_per_row, row_height, column_width, radius):
    expected_locations = []
    top_left_position = [row_height / 2, column_width / 2]
    # print(top_left_position)
    y = top_left_position[0]
    for row, num_circles in enumerate(circles_per_row):
        x = top_left_position[1]
        for column in range(num_circles):
            expected_locations.append([x, y, radius])
            x += column_width
        y += row_height
    expected_circles = np.array(expected_locations).astype(float)
    return expected_circles


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
        if not row_length:
            continue
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


def get_best_fitting_grid(circles_grid, seen_circles):
    result = minimize(
        circle_adjustment_scipy_objective_function_wrapper,
        method='powell',
        tol=1e-4,
        x0=np.array([0.0, 0.0, 1.0, 1.0, 0.0]),
        args=(circles_grid, seen_circles),
        # bounds=((-10, 10), (-10, 10), (0.85, 1.15), (-5, 5))
    )
    new_grid = adjust_grid_circles(circles_grid, *result.x)
    return new_grid


def circle_adjustment_scipy_objective_function_wrapper(x, *args):
    x_shift, y_shift, grow_x, grow_y, rotation = x
    circles_grid, seen_circles = args
    loss = evaluate_circle_adjustment(circles_grid, seen_circles, x_shift,
                                      y_shift, grow_x, grow_y, rotation)
    # print(f'calling objective func: {x} -> loss = {loss}')
    return loss


def evaluate_circle_adjustment(circles_grid, seen_circles, x_shift, y_shift,
                               grow_x, grow_y, rotation):
    new_grid = adjust_grid_circles(circles_grid, x_shift, y_shift, grow_x,
                                   grow_y, rotation)
    return evaluate_circles_distance(new_grid, seen_circles)


def rotate_points_around_origin(points, origin, angle):
    """
    Rotate a 2D array of points counterclockwise by a given angle around a given origin.

    The angle should be given in degrees.
    """
    angle = angle * np.pi / 180
    ox, oy = origin.tolist()
    new_points = np.copy(points)

    new_points[:, 0] = ox + np.cos(angle) * (
        points[:, 0] - ox) - np.sin(angle) * (points[:, 1] - oy)
    new_points[:, 1] = oy + np.sin(angle) * (
        points[:, 0] - ox) + np.cos(angle) * (points[:, 1] - oy)
    return new_points


def adjust_grid_circles(circles_grid, x_shift, y_shift, grow_x, grow_y,
                        rotation):
    new_grid = np.copy(circles_grid).astype(float)
    new_grid[:, 0] += x_shift
    new_grid[:, 1] += y_shift
    grid_centre = np.mean(new_grid[:, :2], axis=0)
    # print(new_grid)
    # print(grid_centre)
    # plt.plot(*grid_centre.tolist(), 'o')
    new_grid[:, 0] = (
        new_grid[:, 0] - grid_centre[0]) * grow_x + grid_centre[0]
    new_grid[:, 1] = (
        new_grid[:, 1] - grid_centre[1]) * grow_y + grid_centre[1]
    new_grid = rotate_points_around_origin(
        new_grid, grid_centre, angle=rotation)
    return new_grid


def evaluate_circles_distance(candidate_circles, seen_circles):
    candidate_points = np.array(candidate_circles)[:, :2]
    hough_points = np.array(seen_circles)[:, :2]
    distances = find_closest_point_distances(candidate_points, hough_points)
    return np.sum(distances)


def find_closest_point_distances(candidate_points, seen_points):
    dists = distance.cdist(candidate_points, seen_points).min(axis=1)
    return dists
