import numpy as np
import pandas as pd
import pytest
from pyomrx.omr.circle_group import DataCircleGroup
from pathlib import Path
from pyomrx.omr.cv2_utils import load_and_check_image


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


def test_data_circles_1_values(attendance_data_circles):
    columns = [f'A{i:02}' for i in range(31)]
    correct_values = pd.DataFrame(
        np.zeros([25, 31]).astype(bool), columns=columns)
    for i in range(len(correct_values)):
        correct_values.iloc[i, i] = True
    correct_values.iloc[0, 30] = True
    correct_values.iloc[24, 30] = True
    correct_values.iloc[24, 0] = True
    assert isinstance(attendance_data_circles.values, pd.DataFrame)
    assert attendance_data_circles.values.equals(correct_values)


if __name__ == '__main__':
    pytest.main(['-k', 'test_data_circles', '-s'])
