from PIL import Image
import numpy as np
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout


class ContrastDialog(QDialog):
    valuesSelected = pyqtSignal(int, int)


    def __init__(self, parent, slices, window_center, window_width, intercept):
        super().__init__(parent)
        self.setWindowTitle("Adjust values")

        self.window_center = window_center
        self.window_width = window_width
        self.layer = len(slices) // 2
        self.slices = slices
        self.intercept = intercept

        self.layer_label = QLabel(f"Layer: {self.layer}")
        self.layer_index = QSlider(Qt.Horizontal)
        self.layer_index.setRange(0, len(slices))
        self.layer_index.setValue(self.layer)

        self.window_center_label = QLabel(f"Window Center: {window_center}")
        self.window_center_slider = QSlider(Qt.Horizontal)
        self.window_center_slider.setRange(-1024, 3000)
        self.window_center_slider.setValue(int(window_center))

        self.window_width_label = QLabel(f"Window Width: {window_width}")
        self.window_width_slider = QSlider(Qt.Horizontal)
        self.window_width_slider.setRange(1, 2000)
        self.window_width_slider.setValue(int(window_width))

        self.intercept_label = QLabel(f"Intercept: {intercept}")
        self.intercept_slider = QSlider(Qt.Horizontal)
        self.intercept_slider.setRange(-1000, 1000)
        self.intercept_slider.setValue(int(intercept))


        self.layer_index.valueChanged.connect(self.layer_changed)
        self.window_center_slider.valueChanged.connect(self.window_center_changed)
        self.window_width_slider.valueChanged.connect(self.window_width_changed)
        self.intercept_slider.valueChanged.connect(self.intercept_changed)

        self.image_preview = QLabel()
        self.image_preview.setMinimumSize(500, 500)
        self.update_pixmap()


        buttons = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)

        layout = QVBoxLayout()
        layout.addWidget(self.image_preview)
        layout.addWidget(self.layer_label)
        layout.addWidget(self.layer_index)
        layout.addWidget(self.window_center_label)
        layout.addWidget(self.window_center_slider)
        layout.addWidget(self.window_width_label)
        layout.addWidget(self.window_width_slider)
        layout.addLayout(buttons)
        self.setLayout(layout)

    def layer_changed(self, value):
        self.layer = value
        self.update_pixmap()

    def window_center_changed(self, value):
        self.window_center_label.setText(f"Window Center: {value}")
        self.window_center = value
        self.update_pixmap()
                                   
    def window_width_changed(self, value):
        self.window_width_label.setText(f"Window Width: {value}")
        self.window_width = value
        self.update_pixmap()

    def intercept_changed(self, value):
        self.intercept_label.setText(f"Intercept: {value}")
        self.intercept = value
        self.update_pixmap()

    def update_pixmap(self):
        try:
            image = self.slices[self.layer].pixel_array


            lower_bound = self.window_center - (self.window_width/2) - self.intercept

            image = image - lower_bound
            image = image * (255/self.window_width) * 0.95

            image = np.clip(
                image,
                    0,
                    255
                ).astype(np.uint8)

            image = Image.fromarray(image)

            if image.mode != "RGBA":
                image = image.convert("RGBA")

            data = image.tobytes("raw", "RGBA")
            w, h = image.size

            qimg = QImage(data, w, h, QImage.Format_RGBA8888)

            pixmap = QPixmap.fromImage(qimg.copy())

            pixmap = pixmap.scaled(
                500, 500,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            self.image_preview.setPixmap(pixmap)
        except Exception as e:
            print(f"Error opening slice: {e}")
            image = None


    def accept(self):
        self.valuesSelected.emit(*self.get_values())
        super().accept()

    def get_values(self):
        return self.window_center_slider.value(), self.window_width_slider.value()

