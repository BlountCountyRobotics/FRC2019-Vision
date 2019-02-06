import cv2
import numpy
from pixy import *
from ctypes import *

#vectors = VectorArray(1)

def initialize():
    pixy.init()
    pixy.change_prog("line")

def get_pixy_image():
    line_get_all_features()
    line_get_vectors(1, vectors)

    image = numpy.zeros((480, 680, 1), dtype=numpy.uint8)
    cv2.line(image, (vectors[0].m_y0,vectors[0].m_x0), (vectors[0].m_y1, vectors[0].m_x1), 256, thickness=5)
    cv2.imshow("image", image)
    cv2.waitKey(0)

if __name__ == "__main__":
    get_pixy_image()
