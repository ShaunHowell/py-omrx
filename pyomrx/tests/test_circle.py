import pytest
from pathlib import Path
from pyomrx.core.cv2_utils import *
import numpy as np
from pyomrx.core.circle import Circle


@pytest.fixture
def empty_circle(res_folder):
    image_path = str(Path(res_folder) / 'empty_circle.png')
    image = load_and_check_image(image_path)
    return Circle(image)


def test_empty_circle_is_not_filled(empty_circle):
    assert not empty_circle.is_filled


@pytest.fixture
def filled_circle(res_folder):
    image_path = str(Path(res_folder) / 'filled_circle.png')
    image = load_and_check_image(image_path)
    return Circle(image)


def test_filled_circle_is_filled(filled_circle):
    assert filled_circle.is_filled


if __name__ == '__main__':
    pytest.main(['-k', 'test_circle', '-svv'])
