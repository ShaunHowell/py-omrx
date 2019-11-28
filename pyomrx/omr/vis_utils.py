import cv2
from PIL import Image
from matplotlib import pyplot as plt


def show_circles_on_image(image, circles, title=None, delayed_show=False, thickness=4):
    temp_image = cv2.cvtColor(image.copy(), cv2.COLOR_GRAY2RGB)
    [
        cv2.circle(
            temp_image, (c[0], c[1]), c[2], thickness=thickness, color=(255, 0, 0))
        for c in circles
    ]
    plt.figure()
    if title:
        plt.title(title)
    plt.imshow(Image.fromarray(temp_image))
    if not delayed_show:
        plt.show()


def show_image(image, title=None, delayed_show=False):
    if len(image.shape) < 3:
        temp_image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    else:
        temp_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    plt.figure()
    plt.imshow(temp_image)
    if title:
        plt.title(title)
    if not delayed_show:
        plt.show()
