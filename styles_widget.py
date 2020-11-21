import matplotlib
matplotlib.use("Qt5Agg")
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QColor, QPainter, QFont, QImage, QPixmap
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
import globals


class StylesWidget(QWidget):
    signal_style_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super(StylesWidget, self).__init__(parent)
        self.is_mouse_pressed = False
        self.styles_pixmaps = {}
        image_selected = QImage()
        image_selected.load('res/selected_frame.png')
        self.pixmap_selected = QPixmap.fromImage(image_selected)
        self.styles_locations = {'blues': (60, 55),
                                 'classical': (190, 55),
                                 'country': (0, 145),
                                 'disco': (125, 145),
                                 'hiphop': (250, 145),
                                 'jazz': (0, 235),
                                 'metal': (125, 235),
                                 'pop': (250, 235),
                                 'reggae': (60, 325),
                                 'rock': (190, 325),
                                 'other': (125, 415)}

        self.style_size = (110, 75)
        self.styles_image_scale = [1, 1]
        self.selected_style = None

    def load_styles_images(self):
        self.styles_pixmaps = {}
        for style in globals.styles:
            image = QImage()
            image.load('res/%s.png' % style)
            pixmap = QPixmap.fromImage(image)
            self.styles_pixmaps[style] = pixmap

    def paintEvent(self, event):
        p = QPainter(self)
        for style in globals.styles:
            p.drawPixmap(self.styles_locations[style][0], self.styles_locations[style][1],
                         self.styles_pixmaps[style].scaled(self.style_size[0], self.style_size[1]))
            p.setPen(QColor('white'))
            chinese_style_name = globals.styles_chinese[globals.styles.index(style)]
            p.setFont(QFont('times', 18))
            p.drawText(self.styles_locations[style][0] + self.style_size[0] / 6,
                       self.styles_locations[style][1] + self.style_size[1] / 8,
                       self.style_size[0] / 3 * 2,
                       self.style_size[1] / 3 * 2,
                       Qt.AlignCenter,
                       chinese_style_name)

        if self.is_mouse_pressed and self.selected_style:
            p.drawPixmap(self.styles_locations[self.selected_style][0] + 1,
                         self.styles_locations[self.selected_style][1] + 1,
                         self.pixmap_selected.scaled(self.style_size[0] - 2, self.style_size[1] - 2))
        super(StylesWidget, self).paintEvent(event)

    def _get_selected_style(self, pos):
        # pos scale to original style image
        original_x = pos.x() * self.styles_image_scale[0]
        original_y = pos.y() * self.styles_image_scale[1]
        for style_name, style_location in self.styles_locations.items():
            if (style_location[0] <= original_x <= style_location[0] + self.style_size[0] and
                    style_location[1] <= original_y <= style_location[1] + self.style_size[1]):

                self.selected_style = style_name
                return
        self.selected_style = None

    def mousePressEvent(self, event):
        self._get_selected_style(event.pos())
        self.is_mouse_pressed = True
        self.update()

    def mouseReleaseEvent(self, event):
        self.is_mouse_pressed = False
        self.update()
        if self.selected_style:
            self.signal_style_clicked.emit(self.selected_style)
