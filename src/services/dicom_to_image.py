import json
import os
import numpy as np
import cv2 as cv

from typing import Tuple
from PIL import Image

from pydicom.pixel_data_handlers.util import apply_voi_lut

from services.get_meta_data import get_meta_from_slice
from services.slice_loading import load_slices
from services.slice_orientation import get_slice_orientation


@staticmethod
def convert_dicom_to_images(input_path: str, output_path: str) -> Tuple[str, float, float, float]:
    """
    Convert DICOM files to images and save metadata
    Returns: orientation, horizontal_spacing, vertical_spacing, depth_spacing
    """
    # Set Progress Bar
    total_dicom_images = str(len(os.listdir(input_path)))
    # Initial progress indicator (0%)
    progress_counter = 0

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

    # Step 2: Extract metadata
    if len(slices) > 0:
        try:
            pos1 = np.array([float(x) for x in slices[0].ImagePositionPatient])
            pos2 = np.array([float(x) for x in slices[1].ImagePositionPatient])
            distance = np.linalg.norm(pos2 - pos1)
            print(f"Calculated Spacing: {distance}")

            orientation = get_slice_orientation(slices[0])
            data_json['sliceOrientation'] = orientation
            data_json["firstImage"] = get_meta_from_slice(slices[0], distance)
            data_json["lastImage"] = get_meta_from_slice(slices[len(slices) - 1], distance)
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            print("Using default orientation 'unknown'")
            orientation = "unknown"
            data_json['sliceOrientation'] = orientation

    # Step 3.1: Create images folder
    filepathImages = os.path.normpath(os.path.join(output_path, "images"))

    if not os.path.exists(filepathImages):
        os.makedirs(filepathImages)
    # Step 3.2: Create orientation folder
    filepathOrientation = os.path.normpath(os.path.join(output_path, "images", orientation))

    if not os.path.exists(filepathOrientation):
        os.makedirs(filepathOrientation)

    # Step 4: Process and save each slice
    for idx, slice in enumerate(slices):
        try:
            Output_Image = slice.pixel_array

            # Apply VOI LUT for proper display
            Output_Image = apply_voi_lut(Output_Image, slice)

            # Find the pixel values below which 1% and 99% of the data fall, respectively
            p1, p99 = np.percentile(Output_Image, (1, 99))

            # Perform contrast stretching if possible
            if p99 != p1:
                Output_Image = np.clip((Output_Image - p1) / (p99 - p1) * 255, 0, 255).astype(np.uint8)
            else:
                Output_Image = np.clip(Output_Image, 0, 255).astype(np.uint8)

            # Stelle sicher, dass der Zielordner existiert
            save_dir = os.path.normpath(os.path.join(output_path, "images", orientation))
            os.makedirs(save_dir, exist_ok=True)

            filename = f'{slices.index(slice):04d}.png'
            filepath = os.path.normpath(os.path.join(save_dir, filename))

            try:
                # Bild speichern mit OpenCV, Fallback auf PIL
                success = cv.imwrite(filepath, Output_Image)
                if not success:
                    try:
                        Image.fromarray(Output_Image).save(filepath)
                    except Exception as e:
                        print(f"❌ Fehler beim Speichern mit PIL: {e}")
            except Exception as e:
                print(f"Error saving image: {e}")
                continue

            # Update progress counter
            progress_counter += 1

            # Show file progress
            print(f"PROGRESS: {int(progress_counter / 2)} / {total_dicom_images}")
        except Exception as e:
            print(f"Error processing slice: {e}")
            continue

    # Step 5: Save metadata JSON
    json.dump(data_json, open(output_path + '/data.json', 'w'), indent=5, sort_keys=True)

    if len(slices) > 0:
        return orientation, slices[0].PixelSpacing[0], slices[0].PixelSpacing[1], slices[0].SliceThickness
    else:
        return "unknown", 1.0, 1.0, 1.0