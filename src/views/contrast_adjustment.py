from PIL import Image
import numpy as np
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QBoxLayout, QDialog, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout

import SimpleITK as sitk




class ImageDialog(QDialog):
    valuesSelected = pyqtSignal(int, int)


    def __init__(self, parent, image_3d, window_center, window_width):
        super().__init__(parent)
        self.setWindowTitle("Adjust values")

        self.window_center = window_center
        self.window_width = window_width
        self.layer_transversal = image_3d.GetSize()[2] // 2
        self.layer_coronal = image_3d.GetSize()[1] // 2
        self.layer_sagittal = image_3d.GetSize()[0] // 2
        self.image_3d = image_3d
        self.image_preview_size = 500

        # Sliders
        self.window_center_label = QLabel(f"Window Center: {window_center}")
        self.window_center_slider = QSlider(Qt.Horizontal)
        self.window_center_slider.setRange(-1024, 3000)
        self.window_center_slider.setValue(int(window_center))

        self.window_width_label = QLabel(f"Window Width: {window_width}")
        self.window_width_slider = QSlider(Qt.Horizontal)
        self.window_width_slider.setRange(1, 2000)
        self.window_width_slider.setValue(int(window_width))


        self.window_center_slider.valueChanged.connect(self.window_center_changed)
        self.window_width_slider.valueChanged.connect(self.window_width_changed)

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


        layout = QVBoxLayout()
        layout.addLayout(horizontal_layout)
        layout.addWidget(self.layer_label_coronal)
        layout.addWidget(self.layer_index_coronal)
        layout.addWidget(self.window_center_label)
        layout.addWidget(self.window_center_slider)
        layout.addWidget(self.window_width_label)
        layout.addWidget(self.window_width_slider)
        layout.addLayout(buttons)
        self.setLayout(layout)

    def layer_changed_transversal(self, value):
        self.layer_transversal = value
        self.update_pixmap_transversal()

    def layer_changed_coronal(self, value):
        self.layer_coronal = value
        self.update_pixmap_coronal()

    def layer_changed_sagittal(self, value):
        self.layer_sagittal = value
        self.update_pixmap_sagittal()

    def window_center_changed(self, value):
        self.window_center_label.setText(f"Window Center: {value}")
        self.window_center = value
        self.update_pixmap_transversal()
        self.update_pixmap_coronal()
        self.update_pixmap_sagittal()
                                   
    def window_width_changed(self, value):
        self.window_width_label.setText(f"Window Width: {value}")
        self.window_width = value
        self.update_pixmap_transversal()
        self.update_pixmap_coronal()
        self.update_pixmap_sagittal()


    def update_pixmap_transversal(self):
        try:
            slice = get_slice(sitk.Flip(self.image_3d, [False, False, True]), self.layer_transversal, 2)
            self.image_preview_transversal.setPixmap(self.sitk_to_qpixmap(slice, self.window_center, self.window_width))
        except Exception as e:
            print(f"Error opening slice: {e}")

    def update_pixmap_coronal(self):
        try:
            slice = get_slice(sitk.Flip(self.image_3d, [False, True, False]), self.layer_coronal, 1)
            self.image_preview_coronal.setPixmap(self.sitk_to_qpixmap(slice, self.window_center, self.window_width))
        except Exception as e:
            print(f"Error opening slice: {e}")

    def update_pixmap_sagittal(self):
        try:
            slice = get_slice(self.image_3d, self.layer_sagittal, 0)
            self.image_preview_sagittal.setPixmap(self.sitk_to_qpixmap(slice, self.window_center, self.window_width))
        except Exception as e:
            print(f"Error opening slice: {e}")


    def accept(self):
        self.valuesSelected.emit(*self.get_values())
        super().accept()

    def get_values(self):
        return self.window_center_slider.value(), self.window_width_slider.value()

    def sitk_to_qpixmap(self, sitk_slice, window_center=40, window_width=400):
        """
        Converts a 2D SimpleITK slice to a QPixmap.
        """
        # 1. Intensity Windowing (Medical values -> 0-255)
        img_255 = sitk.IntensityWindowing(
            sitk_slice, 
            max(0, window_center - window_width / 2), 
            min(3000, window_center + window_width / 2), 
            0.0, 255.0
        )
        
        img_8bit = sitk.Cast(img_255, sitk.sitkUInt8)
        
        data = sitk.GetArrayFromImage(img_8bit)
        
        width = sitk_slice.GetWidth()
        height = sitk_slice.GetHeight()
        
        q_image = QImage(data.data, width,  height, width, QImage.Format.Format_Grayscale8).scaled(self.image_preview_size, self.image_preview_size,Qt.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        return QPixmap.fromImage(q_image.copy())

def get_slice(volume, index, axis=2):
    extract = sitk.ExtractImageFilter()
    
    size = list(volume.GetSize())
    size[axis] = 0 
    extract.SetSize(size)
    
    start_index = [0, 0, 0]
    start_index[axis] = index
    extract.SetIndex(start_index)
    
    return extract.Execute(volume)

