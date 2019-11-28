import pytest
from pyomrx.omr.circle_group import BinaryCircles
from pyomrx.omr.core import *


@pytest.fixture
def binary_circles_1(res_folder):
    image_path = str(Path(res_folder) / 'binary_circles_1.png')
    image = load_and_check_image(image_path)
    config = {
        "name": "institution",
        "decides_sub_form": False,
        "quantity": 7,
        "radius": 0.03152709359605912

    }
    return BinaryCircles(image, config)


def test_binary_circles_1_has_value_1(binary_circles_1):
    assert binary_circles_1.value == 1
