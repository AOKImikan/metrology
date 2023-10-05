#------------------------------------------------------------------------
# pmm: imageTool.py
#------------------------------------------------------------------------
import cv2
from PyQt5 import QtGui

class ImageTool:
    @staticmethod
    def arrayToQImage(arrayImage):
        h, w, nch = arrayImage.shape
        nbytes = nch * w
        image_rgb = cv2.cvtColor(arrayImage, cv2.COLOR_BGR2RGB)
        image = QtGui.QImage(image_rgb.data, w, h, nbytes,
                             QtGui.QImage.Format_RGB888)
        return image
    
    @staticmethod
    def arrayToQPixmap(arrayImage):
        image = ImageTool.arrayToQImage(arrayImage)
        pixmap = QtGui.QPixmap.fromImage(image)
        return pixmap
    
