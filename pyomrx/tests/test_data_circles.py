import pytest
from pyomrx.core.circle_group import *
from pathlib import Path
from pyomrx.core.cv2_utils import load_and_check_image
from pyomrx.core.circle_group import single_response_from_darknesses


@pytest.fixture
def attendance_data_circles(res_folder):
    image_path = str(Path(res_folder) / 'attendance_data_circles.png')
    image = load_and_check_image(image_path)
    config = {
        "allowed_row_filling":
            "many",
        "column_prefix":
            "A",
        "radius":
            0.007119021134593994,
        "circles_per_row": [
            31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31,
            31, 31, 31, 31, 31, 31, 31, 31
        ],
        "possible_columns":
            31,
        "name":
            "attendance"
    }
    return DataCircleGroup(image, config)


def test_attendance_data_circles_1_values(attendance_data_circles):
    columns = [f'A{i:02}' for i in range(1, 32)]
    correct_values = pd.DataFrame(
        np.zeros([25, 31]).astype(bool), columns=columns)
    for i in range(len(correct_values)):
        correct_values.iloc[i, i] = True
    correct_values.iloc[0, 30] = True
    correct_values.iloc[24, 30] = True
    correct_values.iloc[24, 0] = True
    assert isinstance(attendance_data_circles.value, pd.DataFrame)
    if not attendance_data_circles.value.equals(correct_values):
        print(correct_values.to_string())
        print(attendance_data_circles.value.to_string())
        assert attendance_data_circles.value.equals(correct_values)


class TestExamCircleGrid:
    def test_example_exam_data_circles(self):
        assert False


class TestFittingCircleGrid:

    def test_optimise_grid_fit_x_translate(self):
        candidate_circles = [(9, 11, 3), (9, 11, 3)]
        hough_circles = [(1, 3, 3), (100, 12, 3), (11, 11, 3), (20, 11, 3)]
        new_grid_circles = get_best_fitting_grid(candidate_circles, hough_circles)
        correct_grid_circles = [(11, 11, 3), (11, 11, 3)]
        print(new_grid_circles)
        closeness = evaluate_circles_distance(new_grid_circles,
                                              correct_grid_circles)
        assert abs(closeness) < 0.001

    def test_optimise_grid_fit_x_y_translate(self):
        candidate_circles = [(9, 10, 3), (9, 10, 3)]
        hough_circles = [(1, 3, 3), (100, 12, 3), (11, 11, 3), (20, 11, 3)]
        new_grid_circles = get_best_fitting_grid(candidate_circles, hough_circles)
        correct_grid_circles = [(11, 11, 3), (11, 11, 3)]
        closeness = evaluate_circles_distance(new_grid_circles,
                                              correct_grid_circles)
        print(new_grid_circles)
        assert abs(closeness) < 0.001

    def test_optimise_grid_fit_x_y_translate_rotate_grow(self):
        candidate_circles = [(9, 10, 3), (9, 10, 3)]
        candidate_circles = adjust_grid_circles(candidate_circles, 2, 2, 1.1, 1.1,
                                                3.2)
        hough_circles = [(1, 3, 3), (100, 12, 3), (11, 11, 3), (20, 11, 3)]
        new_grid_circles = get_best_fitting_grid(candidate_circles, hough_circles)
        correct_grid_circles = [(11, 11, 3), (11, 11, 3)]
        closeness = evaluate_circles_distance(new_grid_circles,
                                              correct_grid_circles)
        print(new_grid_circles)
        assert abs(closeness) < 0.001

    def test_find_closest_distance(self):
        candidate_points = [(10, 10), (12, 12)]
        hough_points = [(1, 3), (100, 12), (11, 11), (20, 11)]
        dists = find_closest_point_distances(candidate_points, hough_points)
        assert np.all(np.equal(dists, np.array([np.sqrt(2), np.sqrt(2)])))

    def test_find_closest_distance_misordered(self):
        circles = np.array([(0, 0, 3), (0, 1, 3), (1, 1, 3), (1, 0, 3)])
        other_circles = np.array([(0, 1, 3), (1, 1, 3), (1, 0, 3), (0, 0, 3)])
        assert evaluate_circles_distance(circles, other_circles) < 1e-5

    def test_evaluate_circle_fit(self):
        candidate_circles = [(10, 10, 3), (12, 12, 3)]
        hough_circles = [(1, 3, 3), (100, 12, 3), (11, 11, 3), (20, 11, 3)]
        total_dist = evaluate_circles_distance(candidate_circles, hough_circles)
        assert np.equal(total_dist, np.sqrt(2) * 2)

    def test_adjust_grid_grow_double(self):
        circles = np.array([(0, 0, 3), (0, 1, 3), (1, 1, 3), (1, 0, 3)])
        new_circles = adjust_grid_circles(circles, 0, 0, 2, 2, 0)
        # plt.plot(circles[:, 0], circles[:, 1], 'o')
        # plt.plot(new_circles[:, 0], new_circles[:, 1], 'o')
        # plt.show()
        correct_circles = np.array([[-0.5, -0.5, 3], [-0.5, 1.5, 3], [1.5, 1.5, 3],
                                    [1.5, -0.5, 3]])
        closeness = evaluate_circles_distance(new_circles, correct_circles)
        assert closeness < 1e-5

    def test_rotate_points_around_origin(self):
        circles = np.array([(0, 0, 3), (0, 1, 3), (1, 1, 3), (1, 0, 3)])
        new_circles = adjust_grid_circles(circles, 0, 0, 1, 1, 45)
        new_new_circles = adjust_grid_circles(new_circles, 0, 0, 1, 1, 45)
        # plt.plot(circles[:, 0], circles[:, 1], 'o')
        # plt.plot(new_circles[:, 0], new_circles[:, 1], 'o')
        # plt.plot(new_new_circles[:, 0], new_new_circles[:, 1], 'o')
        # plt.gca().set_aspect('equal', 'box')
        # plt.show()
        # print(circles)
        # print(new_circles)
        # print(np.round(new_new_circles, 3))
        closeness_after_one_rotate = evaluate_circles_distance(
            circles, new_circles)
        closeness_after_two_rotate = evaluate_circles_distance(
            circles, new_new_circles)
        assert closeness_after_one_rotate > 0.1
        assert closeness_after_two_rotate < 1e-5


class TestResponseFromDarknesses:
    def test_good_response_from_darknesses(self):
        example = [
            0.17548420642142207, 0.21935525802677758, 0.20798128168464836,
            0.15436110750032495, 0.180358767710906, 0.20473157415832574,
            0.9960353568178864, 0.18523332900038994, 0.32288229793390616,
            0.20960613544780968
        ]
        assert single_response_from_darknesses(example) == 6

    def test_no_response_from_darknesses(self):
        example = [0.1706096451319381, 0.2915782024062279]
        assert single_response_from_darknesses(example) == -1

    def test_double_response_from_darknesses(self):
        example = [
            0.17548420642142207, 0.21935525802677758, 0.9960353568178864,
            0.15436110750032495, 0.180358767710906, 0.20473157415832574,
            0.9960353568178864, 0.18523332900038994, 0.32288229793390616,
            0.20960613544780968
        ]
        assert single_response_from_darknesses(example) == -2

    def test_middle_ground_abstention_response_from_darknesses(self):
        example = [0.5, 0.5, 0.5, 0.5, 0.32288229793390616, 0.20960613544780968]
        assert single_response_from_darknesses(example) == -3

    def test_closeness_abstention_response_from_darknesses(self):
        example = [0.59, 0.7, 0.5, 0.5, 0.32288229793390616, 0.20960613544780968]
        assert single_response_from_darknesses(example) == -3


if __name__ == '__main__':
    pytest.main(['-s', '-k', 'test_data_circles_1_values'])
