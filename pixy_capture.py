import cv2
import numpy
import pixy
from ctypes import *

vectors = VectorArray(1)

def initialize():
    pixy.init()
    pixy.change_prog("line")

def get_pixy_image():
    line_get_all_features()
    line_get_vectors(1, vectors)

    image = numpy.zeros((480, 680, 1), dtype=numpy.uint8)
    cv2.line(image, (vectors[0].m_y0,vectors[0].m_x0), (vectors[0].m_y1, vectors[0].m_x1), 256, thickness=5)
    return image

if __name__ == "__main__":
    initialize()
    cv2.namedWindow("image", cv2.WINDOW_NORMAL)
    while True:
        cv2.imshow("image", get_pixy_image())
        if cv2.waitKey(1) & 0xFF == ord('q')
            break
    cv2.destroyAllWindows()
