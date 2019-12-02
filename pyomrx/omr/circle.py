from matplotlib import pyplot as plt
import cv2
import numpy as np
from pyomrx.omr.cv2_utils import *
from pyomrx.omr.vis_utils import show_image, show_circles_on_image


class Circle:
    def __init__(self, image, fill_threshold=0.3):
        self.image = get_one_channel_grey_image(image)
        assert np.isclose(*self.image.shape, rtol=0.04), 'image must be square'
        self.fill_threshold = fill_threshold
        self.radius = int(np.mean(self.image.shape) / 2) - 1
        self.area = np.pi * self.radius**2
        self._is_filled = None
        # show_image(self.image, str(self.is_filled), delayed_show=True)
        plt.show()

    @property
    def is_filled(self):
        if self._is_filled is None:
            binary_image = cv2.threshold(
                self.image, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
            mask = np.zeros(self.image.shape, dtype="uint8")
            cv2.circle(
                img=mask,
                center=(int(self.image.shape[0] / 2),
                        int(self.image.shape[1] / 2)),
                radius=self.radius,
                color=255,
                thickness=-1)
            mask = cv2.bitwise_and(binary_image, binary_image, mask=mask)
            # show_image(mask, 'final circle image')
            relative_fill = cv2.countNonZero(mask) / self.area
            self._is_filled = True if relative_fill >= 0.3 else False
        return self._is_filled
