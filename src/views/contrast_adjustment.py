from PIL import Image
import numpy as np
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QBoxLayout, QComboBox, QDialog, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QSpinBox

import SimpleITK as sitk

from services.get_slice import get_slice
from views.components.range_slider import RangeSlider

class ImageDialog(QDialog):
    valuesSelected = pyqtSignal(float, float, str)

    def __init__(self, parent, image_3d, window_center, window_width, orientation):
        super().__init__(parent)
        self.setWindowTitle("Adjust values")

        self.window_center = float(window_center)
        self.window_width = max(1.0, float(window_width))
        self.layer_transversal = image_3d.GetSize()[2] // 2
        self.layer_coronal = image_3d.GetSize()[1] // 2
        self.layer_sagittal = image_3d.GetSize()[0] // 2
        self.image_3d = image_3d
        self.image_preview_size = 500
        self.orientation = orientation

        # Contrast range components
        initial_min = int(self.window_center - self.window_width / 2)
        initial_max = int(self.window_center + self.window_width / 2)
        
        self.range_slider = RangeSlider()
        self.range_slider.setMinimum(-2000)
        self.range_slider.setMaximum(4000)
        
        self.min_spinbox = QSpinBox()
        self.min_spinbox.setRange(-2000, 4000)
        
        self.max_spinbox = QSpinBox()
        self.max_spinbox.setRange(-2000, 4000)
        
        self.range_slider.setLow(initial_min)
        self.range_slider.setHigh(initial_max)
        self.min_spinbox.setValue(initial_min)
        self.max_spinbox.setValue(initial_max)

        self.range_slider.valuesChanged.connect(self.range_slider_changed)
        self.min_spinbox.valueChanged.connect(self.spinbox_changed)
        self.max_spinbox.valueChanged.connect(self.spinbox_changed)

        self.image_preview_transversal = QLabel()
        self.image_preview_coronal = QLabel()
        self.image_preview_sagittal = QLabel()
        self.image_preview_transversal.setMinimumSize(500, 500)
        self.image_preview_coronal.setMinimumSize(500, 500)
        self.image_preview_sagittal.setMinimumSize(500, 500)
        self.update_pixmap_transversal()
        self.update_pixmap_coronal()
        self.update_pixmap_sagittal()

        self.layer_label_transversal = QLabel(f"Transversal: {self.layer_transversal}")
        self.layer_index_transversal = QSlider(Qt.Horizontal)
        self.layer_index_transversal.setRange(0, image_3d.GetSize()[2])
        self.layer_index_transversal.setValue(self.layer_transversal)

        self.layer_label_coronal = QLabel(f"Coronal: {self.layer_coronal}")
        self.layer_index_coronal = QSlider(Qt.Horizontal)
        self.layer_index_coronal.setRange(0, image_3d.GetSize()[1])
        self.layer_index_coronal.setValue(self.layer_transversal)

        self.layer_label_sagittal = QLabel(f"Sagittal: {self.layer_sagittal}")
        self.layer_index_sagittal = QSlider(Qt.Horizontal)
        self.layer_index_sagittal.setRange(0, image_3d.GetSize()[0])
        self.layer_index_sagittal.setValue(self.layer_transversal)

        self.layer_index_transversal.valueChanged.connect(self.layer_changed_transversal)
        self.layer_index_coronal.valueChanged.connect(self.layer_changed_coronal)
        self.layer_index_sagittal.valueChanged.connect(self.layer_changed_sagittal)

        self.orientation_combo = QComboBox()
        self.orientations = [
            "LPS", "RAS", "LAS", "RPS", "LPI", "RPI", "LAI", "RAI"
        ]
        self.orientation_combo.addItems(self.orientations)
        self.orientation_combo.setCurrentIndex(self.orientations.index(self.orientation))

        buttons = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)

        horizontal_layout = QHBoxLayout()
        transversal_layout = QVBoxLayout()
        transversal_layout.addWidget(self.image_preview_transversal)
        transversal_layout.addWidget(self.layer_label_transversal)
        transversal_layout.addWidget(self.layer_index_transversal)

        coronal_layout = QVBoxLayout()
        coronal_layout.addWidget(self.image_preview_coronal)
        coronal_layout.addWidget(self.layer_label_coronal)
        coronal_layout.addWidget(self.layer_index_coronal)

        sagittal_layout = QVBoxLayout()
        sagittal_layout.addWidget(self.image_preview_sagittal)
        sagittal_layout.addWidget(self.layer_label_sagittal)
        sagittal_layout.addWidget(self.layer_index_sagittal)

        horizontal_layout.addLayout(transversal_layout)
        horizontal_layout.addLayout(coronal_layout)
        horizontal_layout.addLayout(sagittal_layout)

        window_layout = QHBoxLayout()
        window_layout.addWidget(QLabel("Min:"))
        window_layout.addWidget(self.min_spinbox)
        window_layout.addWidget(self.range_slider)
        window_layout.addWidget(QLabel("Max:"))
        window_layout.addWidget(self.max_spinbox)

        layout = QVBoxLayout()
        layout.addLayout(horizontal_layout)
        layout.addWidget(self.orientation_combo)
        apply_btn = QPushButton("Apply Orientation")
        apply_btn.clicked.connect(self.orientation_applied)
        layout.addWidget(apply_btn)
        layout.addWidget(QLabel("Contrast Spectrum:"))
        layout.addLayout(window_layout)
        layout.addLayout(buttons)
        self.setLayout(layout)

    def range_slider_changed(self, min_val, max_val):
        self.min_spinbox.blockSignals(True)
        self.max_spinbox.blockSignals(True)
        self.min_spinbox.setValue(min_val)
        self.max_spinbox.setValue(max_val)
        self.min_spinbox.blockSignals(False)
        self.max_spinbox.blockSignals(False)
        self.update_window_parameters(min_val, max_val)

    def spinbox_changed(self):
        min_val = self.min_spinbox.value()
        max_val = self.max_spinbox.value()
        if min_val > max_val:
            min_val = max_val
            self.min_spinbox.setValue(min_val)
        self.range_slider.blockSignals(True)
        self.range_slider.setLow(min_val)
        self.range_slider.setHigh(max_val)
        self.range_slider.blockSignals(False)
        self.update_window_parameters(min_val, max_val)

    def update_window_parameters(self, min_val, max_val):
        self.window_width = max(1.0, float(max_val - min_val))
        self.window_center = float(min_val + self.window_width / 2.0)
        self.update_pixmap_transversal()
        self.update_pixmap_coronal()
        self.update_pixmap_sagittal()

    def layer_changed_transversal(self, value):
        self.layer_transversal = value
        self.update_pixmap_transversal()

    def layer_changed_coronal(self, value):
        self.layer_coronal = value
        self.update_pixmap_coronal()

    def layer_changed_sagittal(self, value):
        self.layer_sagittal = value
        self.update_pixmap_sagittal()

    def update_pixmap_transversal(self):
        try:
            slice = get_slice(self.image_3d, self.layer_transversal, 2)
            self.image_preview_transversal.setPixmap(self.sitk_to_qpixmap(slice, self.window_center, self.window_width))
        except Exception as e:
            print(f"Error opening slice: {e}")

    def update_pixmap_coronal(self):
        try:
            slice = get_slice(self.image_3d, self.layer_coronal, 1)
            self.image_preview_coronal.setPixmap(self.sitk_to_qpixmap(slice, self.window_center, self.window_width))
        except Exception as e:
            print(f"Error opening slice: {e}")

    def update_pixmap_sagittal(self):
        try:
            slice = get_slice(self.image_3d, self.layer_sagittal, 0)
            self.image_preview_sagittal.setPixmap(self.sitk_to_qpixmap(slice, self.window_center, self.window_width))
        except Exception as e:
            print(f"Error opening slice: {e}")

    def orientation_applied(self):
        self.orientation = self.orientation_combo.currentText()
        self.image_3d = sitk.DICOMOrient(self.image_3d, self.orientation)
        self.update_pixmap_transversal()
        self.update_pixmap_coronal()
        self.update_pixmap_sagittal()

    def accept(self):
        self.valuesSelected.emit(*self.get_values())
        super().accept()

    def get_values(self):
        return self.window_center, self.window_width, self.orientation

    def sitk_to_qpixmap(self, sitk_slice, window_center, window_width):
        sitk_slice = sitk.Cast(sitk_slice, sitk.sitkFloat32)
        window_min = float(window_center - window_width / 2.0)
        window_max = float(window_center + window_width / 2.0)
        img_255 = sitk.IntensityWindowing(
            sitk_slice, 
            window_min, 
            window_max, 
            0.0, 255.0
        )
        img_8bit = sitk.Cast(img_255, sitk.sitkUInt8)
        data = sitk.GetArrayFromImage(img_8bit)
        width = sitk_slice.GetWidth()
        height = sitk_slice.GetHeight()
        q_image = QImage(data.data, width,  height, width, QImage.Format.Format_Grayscale8).scaled(self.image_preview_size, self.image_preview_size,Qt.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        return QPixmap.fromImage(q_image.copy())
