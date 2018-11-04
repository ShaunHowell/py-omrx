import cv2
from PIL import Image
import matplotlib.pyplot as plt

def show_circles_on_image(image, circles, title=None):
    temp_image = cv2.cvtColor(image.copy(), cv2.COLOR_GRAY2RGB)
    [cv2.circle(temp_image, (c[0],c[1]),c[2], thickness=4, color=(255,0,0)) for c in circles]
    if title:
        plt.title(title)
    plt.imshow(Image.fromarray(temp_image))
    plt.show()

def show_image(image):
    temp_image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    plt.imshow(image)
    plt.show()
