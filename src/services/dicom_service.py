import json
import os

import SimpleITK as sitk
import numpy as np

from models.dicom_data import DicomData

from services.get_slice import get_slice
from views.contrast_adjustment import ImageDialog


class DicomService:
    """
    Service class for DICOM related operations
    """
    @staticmethod
    def run_conversion(parent, input_path: str, output_path: str) -> DicomData:
        print("run_conversion")
        """
        Run the complete DICOM conversion process and return data model
        """


        file_reader = sitk.ImageSeriesReader()

        file_reader.MetaDataDictionaryArrayUpdateOn()
        file_reader.LoadPrivateTagsOn()

        dicom_names = file_reader.GetGDCMSeriesFileNames(input_path)
        file_reader.SetFileNames(dicom_names)
        image_3d = file_reader.Execute()
        orientation = "RAS"
        image_3d = sitk.DICOMOrient(image_3d, orientation)
        image_3d = resample_to_isotropic(image_3d)
        image_3d = sitk.Flip(image_3d, [False, False, False])


        window_width = [float(x.strip()) for x in file_reader.GetMetaData(0, "0028|1051").strip().split('\\')][0]
        window_center = [float(x.strip()) for x in file_reader.GetMetaData(0, "0028|1050").strip().split('\\')][0]
        image_dialog = ImageWindowObject(parent, image_3d, window_center, window_width, orientation)
        window_width = image_dialog.window_width
        window_center = image_dialog.window_center
        orientation = image_dialog.orientation

        image_3d = sitk.DICOMOrient(image_3d, orientation)


        window_min = float(window_center - window_width / 2.0)
        window_max = float(window_center + window_width / 2.0)

        # Count Images to Display Progess Bar
        counter = 0
        max_count = image_3d.GetSize()[0] + image_3d.GetSize()[1] + image_3d.GetSize()[2]

        counter = safe_axis(image_3d, output_path, "coronal", 1, window_min, window_max, parent, counter, max_count)
        counter = safe_axis(image_3d, output_path, "sagittal", 0, window_min, window_max, parent, counter, max_count)
        counter = safe_axis(image_3d, output_path, "transversal", 2, window_min, window_max, parent, counter, max_count)

        # Get Orientation
        direction = np.array(image_3d.GetDirection()).tolist()

        spacing = np.array(image_3d.GetSpacing()).tolist()

        # Save Info to Json
        data_json = {}


        firstPosition = [float(x.strip()) for x in file_reader.GetMetaData(0, "0020|0032").split('\\')]
        lastPosition = [float(x.strip()) for x in file_reader.GetMetaData(len(dicom_names)- 1, "0020|0032").split('\\')]
        
        data_json = {
            "size": image_3d.GetSize(),
            "direction": image_3d.GetDirection(),
            "origin": image_3d.GetOrigin(),
            "spacing": image_3d.GetSpacing(),
            "orientation": orientation, # LAS, LPS, RAS Auch in direction gespeichert
        }


        json.dump(data_json, open(output_path + '/data.json', 'w'), indent=5, sort_keys=True)

        model = DicomData(
            slice_orientation=direction,
            spacing=(spacing[0], spacing[1], spacing[2]),
            input_folder=input_path,
            output_folder=output_path
        )
        
        return model

def safe_axis(image_3d, filepath, axis_name, axis, window_min, window_max, parent, counter, max_count):
    folder = os.path.join(filepath, "images", axis_name)
    os.makedirs(folder,exist_ok=True)
    for i in range(image_3d.GetSize()[axis]):

        counter += 1
        parent.progress_bar.setValue(int(counter/max_count * 100))

        slice = get_slice(image_3d,i,axis)
        slice = sitk.Cast(slice, sitk.sitkFloat32)
        img_255 = sitk.IntensityWindowing(slice, window_min, window_max, 0.0, 255.0)
        img_8bit = sitk.Cast(img_255, sitk.sitkUInt8)
        out_filepath = os.path.normpath(os.path.join(folder, f"image{i}.png"))
        sitk.WriteImage(img_8bit, out_filepath)
    return counter

    

def resample_to_isotropic(image):
    # Aktuelles Spacing und Größe 
    original_spacing = image.GetSpacing()
    original_size = image.GetSize()
    
    # Neues Spacing festlegen (1.0 mm in alle Richtungen)
    new_spacing = [1.0, 1.0, 1.0]
    
    # Neue Größe berechnen, damit das physische Volumen gleich bleibt
    new_size = [
        int(round(original_size[0] * (original_spacing[0] / new_spacing[0]))),
        int(round(original_size[1] * (original_spacing[1] / new_spacing[1]))),
        int(round(original_size[2] * (original_spacing[2] / new_spacing[2])))
    ]
    
    resampler = sitk.ResampleImageFilter()
    resampler.SetSize(new_size)
    resampler.SetOutputSpacing(new_spacing)
    resampler.SetOutputOrigin(image.GetOrigin())
    resampler.SetOutputDirection(image.GetDirection())
    resampler.SetInterpolator(sitk.sitkLinear) # Linear für schnell & gut
    
    return resampler.Execute(image)

class ImageWindowObject():
    def __init__(self, parent, slices, window_center, window_width, orientation):
        self.window_center = window_center
        self.window_width = window_width
        self.orientation = orientation
        self.open_contrast_adjustment_dialog(parent, slices, window_center, window_width, orientation)

    def update_contrast_values(self, v1,v2,v3):
        self.window_center = v1
        self.window_width = v2
        self.orientation = v3

    def open_contrast_adjustment_dialog(self, parent, slices, window_center, window_width, orientation):
        dialog = ImageDialog(parent, slices, window_center, window_width, orientation)
        dialog.valuesSelected.connect(self.update_contrast_values)
        dialog.exec_()

    def get_window_center(self):
        return self.window_center

    def get_window_width(self):
        return self.window_width


