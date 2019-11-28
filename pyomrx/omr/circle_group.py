from pyomrx.omr.cv2_utils import *
from pyomrx.omr.core import *


class BinaryCircles:
    def __init__(self, image, config):
        # TODO: assert that the image is approximately the correct dimensions for the radius and number of circles
        self.image = get_one_channel_grey_image(image)
        self.config = config
        self._value = None
        # show_image(image, f'binary circles {config["name"]}')

    @property
    def value(self):
        if not self._value:
            self._extract_value()
        return self._value

    def _extract_value(self):
        absolute_radius = self.config['radius'] * max(self.image.shape)
        bare_circles_list = extract_circles_grid(self.image,
                                                 [self.config['quantity']],
                                                 absolute_radius,
                                                 self.config['quantity']
                                                 )
        bare_circles_grid = circles_list_to_grid(bare_circles_list, [self.config['quantity']])
        self.circles = init_circles_from_grid(self.image, bare_circles_grid)[0]
        # TODO: seems like form circles are above the row centerline
        # TODO: seems like expected circle size is still smaller than actual circles
        print(self.circles)
        value = 0
        for i, circle in enumerate(reversed(self.circles)):
            if circle.is_filled:
                value = value + 2 ** i
        self._value = value
