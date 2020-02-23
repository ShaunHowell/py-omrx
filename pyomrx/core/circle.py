import os
from matplotlib import pyplot as plt
import cv2
import numpy as np
from pyomrx.core.cv2_utils import *
from pyomrx.core.vis_utils import show_image, show_circles_on_image


class Circle:
    def __init__(self,
                 image,
                 radius,
                 fill_threshold=0.4,
                 not_filled_threshold=0.2):
        self.image = get_one_channel_grey_image(image)
        assert np.isclose(*self.image.shape, rtol=0.04, atol=1), \
            f'image must be square, got image with shape {self.image.shape}'
        self.fill_threshold = fill_threshold
        self.not_filled_threshold = not_filled_threshold
        self.radius = radius
        self.area = np.pi * self.radius**2
        self._is_filled = None
        self._relative_fill = None

    @property
    def is_filled(self):
        if self._is_filled is None:
            blurred_image = cv2.blur(self.image, (5, 5))
            sharp_image = cv2.addWeighted(self.image, 1.9, blurred_image, -0.1,
                                          0)
            binary_image = cv2.threshold(
                sharp_image, 0, 255,
                cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
            mask = np.zeros(self.image.shape, dtype="uint8")
            circle_shrink_factor = 0.9
            cv2.circle(
                img=mask,
                center=(int(self.image.shape[0] / 2),
                        int(self.image.shape[1] / 2)),
                radius=int(self.radius * circle_shrink_factor),
                color=255,
                thickness=-1)
            mask = cv2.bitwise_and(binary_image, mask)
            relative_fill_in_circle = cv2.countNonZero(mask) / (
                self.area * circle_shrink_factor**2)
            relative_fill_total = cv2.countNonZero(binary_image) / self.area
            if relative_fill_in_circle >= self.fill_threshold or relative_fill_total > 0.9:
                self._is_filled = True
            elif self.not_filled_threshold <= relative_fill_in_circle < self.fill_threshold:
                self._is_filled = None
            else:
                self._is_filled = False

            if self._is_filled is None and os.environ.get('debug').lower() == 'true':
                print(f'total area relative fill: {relative_fill_total}')
                print(f'radius: {self.radius}')
                debug_image = cv2.cvtColor(self.image, cv2.COLOR_GRAY2RGB)
                cv2.circle(
                    img=debug_image,
                    center=(int(self.image.shape[0] / 2),
                            int(self.image.shape[1] / 2)),
                    radius=int(self.radius),
                    color=(0, 255, 0),
                    thickness=1)
                show_image(
                    self.image,
                    f'fill:{self.relative_fill}, filled: {self.is_filled}',
                    delayed_show=True)
                show_image(
                    debug_image,
                    f'fill:{self.relative_fill}, filled: {self.is_filled}',
                    delayed_show=True)
                show_image(binary_image, 'binary boi', delayed_show=True)
                show_image(
                    mask,
                    f'final circle image, relative fill: {self._relative_fill}',
                    delayed_show=False)

        return self._is_filled
