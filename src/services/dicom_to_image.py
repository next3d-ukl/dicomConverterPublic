import json
import os
from PyQt5.QtWidgets import QDialog
import numpy as np
import cv2 as cv

from typing import Tuple
from PIL import Image

from pydicom.pixel_data_handlers.util import apply_voi_lut
from pydicom.multival import MultiValue

from services.get_meta_data import get_meta_from_slice
from services.slice_loading import load_slices
from services.slice_orientation import get_slice_orientation
from views.contrast_adjustment import ContrastDialog


@staticmethod
def convert_dicom_to_images(parent, input_path: str, output_path: str) -> Tuple[str, float, float, float]:
    """
    Convert DICOM files to images and save metadata
    Returns: orientation, horizontal_spacing, vertical_spacing, depth_spacing
    """
    # Set Progress Bar
    total_dicom_images = str(len(os.listdir(input_path)))

    distance = 0

    # Step 1: Load DICOM slices
    slices = load_slices(input_path)

    # Check if we found any valid DICOM files
    if len(slices) == 0:
        print("No valid DICOM files found in the input directory.")
        print("Please check if the selected directory contains DICOM files.")
        print(f"Input directory: {input_path}")
        print(f"Files in directory: {os.listdir(input_path)}")
        raise ValueError("No valid DICOM files found in the input directory")

    data_json = {}
    orientation = "unknown"

    # Print Meta Data of First Slice for Debugging
    print(slices[0])


    # Step 1.5 Sortierung
    try:
        slices.sort(key=lambda s: float(s.ImagePositionPatient[2]))
    except AttributeError:
        print("⚠️ Keine Z-Position verfügbar – Sortierung nicht möglich.")

    # Step 2: Extract metadata

    if len(slices) > 1:
        try:
            distance = abs(slices[0].ImagePositionPatient[2] - slices[1].ImagePositionPatient[2])
            print(f"Calculated Spacing: {distance}")

            orientation = get_slice_orientation(slices[0].ImageOrientationPatient)
            data_json['sliceOrientation'] = orientation
            data_json["firstImage"] = get_meta_from_slice(slices[0], distance)
            data_json["lastImage"] = get_meta_from_slice(slices[len(slices) - 1], distance)
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            print("Using default orientation 'unknown'")
            orientation = "unknown"
            data_json['sliceOrientation'] = orientation

    # Step 3: create folders
    create_folders(output_path, orientation)

    # Step 4: Process and save each slice
    save_images(parent, slices, output_path, orientation, total_dicom_images)

    # Step 5: Save metadata JSON
    json.dump(data_json, open(output_path + '/data.json', 'w'), indent=5, sort_keys=True)

    # how the return is structured: orientation, horizontal_spacing, vertical_spacing, depth_spacing
    if len(slices) > 0:
        print(f"orientation: {orientation}, horizontal_spacing{slices[0].PixelSpacing[0]}, vertical_spacing{slices[0].PixelSpacing[1]}, depth_spacing{distance}")
        return orientation, slices[0].PixelSpacing[0], slices[0].PixelSpacing[1], distance
    else:
        print("DEFAULT VALUES")
        return "unknown", 1.0, 1.0, 1.0


@staticmethod
def save_images(parent, slices, output_path, orientation, total_dicom_images):
    print(f"Slices detected: {len(slices)}")
    print(f"Total dicom images given: {total_dicom_images}")
    # Initial progress indicator (0%)

    # Get Contrast from Dicom file
    window_center = slices[0].WindowCenter
    window_width = slices[0].WindowWidth
    intercept = slices[0].RescaleIntercept

    if isinstance(window_center, (list, tuple, MultiValue)):
        window_center = window_center[0]

    if isinstance(window_width, (list, tuple, MultiValue)):
        window_width = window_width[0]

    # Adjust Contrast

    contrast_object = ContrastObject(parent, slices, window_center, window_width, intercept)
    window_width = contrast_object.window_width
    window_center = contrast_object.window_center



    lower_bound = window_center - (window_width/2) - intercept


    print(f"Bounds: {window_center}, {window_width}")


    for idx, slice in enumerate(slices):
        try:
            output_image = slice.pixel_array


            output_image = output_image - lower_bound
            output_image = output_image * (255/window_width) * 0.95

            output_image = np.clip(
                output_image,
                    0,
                    255
                ).astype(np.uint8)


            # Stelle sicher, dass der Zielordner existiert
            save_dir = os.path.normpath(os.path.join(output_path, "images", orientation))
            os.makedirs(save_dir, exist_ok=True)

            filename = f'{idx:04d}.png'
            filepath = os.path.normpath(os.path.join(save_dir, filename))

            try:
                # Bild speichern mit OpenCV, Fallback auf PIL
                success = cv.imwrite(filepath, output_image)
                if not success:
                    try:
                        Image.fromarray(output_image).save(filepath)
                    except Exception as e:
                        print(f"❌ Fehler beim Speichern mit PIL: {e}")
            except Exception as e:
                print(f"Error saving image: {e}")
                continue

            # Show file progress
        except Exception as e:
            continue

@staticmethod
def create_folders(output_path, orientation):
    # Step 3.1: Create images folder
    filepathImages = os.path.normpath(os.path.join(output_path, "images"))

    if not os.path.exists(filepathImages):
        os.makedirs(filepathImages)
    # Step 3.2: Create orientation folder
    filepathOrientation = os.path.normpath(os.path.join(output_path, "images", orientation))

    if not os.path.exists(filepathOrientation):
        os.makedirs(filepathOrientation)


def detect_coordinate_system(iop) -> str:
    print(f"Cross Product: {np.cross(iop[0:3],iop[3:6])}")

    row_cosine = np.array(iop[0:3])
    col_cosine = np.array(iop[3:6])

    def direction_label(vec):
        label = ""
        label += "R" if vec[0] < 0 else "L"
        label += "A" if vec[1] < 0 else "P"
        label += "S" if vec[2] > 0 else "I"
        return label

    row_dir = direction_label(row_cosine)
    col_dir = direction_label(col_cosine)

    # Neue Heuristik erkennt RAS zuverlässiger
    if any(k in row_dir + col_dir for k in ["R", "A"]):
        return "RAS"
    return "LPS"


class ContrastObject():
    def __init__(self, parent, slices, window_center, window_width, intercept):
        self.window_center = window_center
        self.window_width = window_width
        self.open_contrast_adjustment_dialog(parent, slices, window_center, window_width, intercept)

    def update_contrast_values(self, v1,v2):
        self.window_center = v1
        self.window_width = v2

    def open_contrast_adjustment_dialog(self, parent, slices, window_center, window_width, intercept):
        dialog = ContrastDialog(parent, slices, window_center, window_width, intercept)
        dialog.valuesSelected.connect(self.update_contrast_values)
        dialog.exec_()

    def get_window_center(self):
        return self.window_center

    def get_window_width(self):
        return self.window_width
