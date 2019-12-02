import random
import numpy as np
import cv2
from pathlib import Path
from pyomrx.omr.exceptions import *
from itertools import product


def load_and_check_image(path):
    assert Path(path).exists(), 'check input file path'
    image = cv2.imread(str(path))
    if image is None:
        raise OmrException('failed to load image: {}'.format(path))
    return image


def is_colour_image(image):
    if len(image.shape) == 3:
        channels = image.shape[2]
        assert channels == 3, f'3D image must be 3-channel, got {channels} channels'
        h_sample = random.sample(list(range(image.shape[0])), 10)
        w_sample = random.sample(list(range(image.shape[1])), 10)
        for i, j in product(h_sample, w_sample):
            pixel = image[i, j, :]
            if not pixel[0] == pixel[1] == pixel[2]:
                return True
    else:
        assert len(image.shape) == 2, 'images must be either 2D (grey) or 3D'
    return False


def get_one_channel_grey_image(image):
    new_image = image.copy()
    if is_colour_image(image) or len(image.shape) == 3:
        new_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    assert not is_colour_image(
        new_image), 'failed to convert colour image to grey'
    return new_image


def extract_rectangle_image(image, rectangle):
    image_height, image_width = image.shape
    print(image.shape, rectangle)
    top = int(image_height * rectangle['top'])
    bottom = int(image_height * rectangle['bottom'])
    left = int(image_width * rectangle['left'])
    right = int(image_width * rectangle['right'])
    print(top, bottom, left, right)
    # TODO: add a buffer outside the specified rectangle to avoid cropping circles if there's skew
    return image[top:bottom, left:right]
