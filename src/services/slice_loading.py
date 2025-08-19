import os
from typing import List

from pydicom import dcmread


@staticmethod
def load_slices(path: str) -> List:
    """
    Load DICOM slices from the specified directory
    """
    slices = []
    for s in os.listdir(path):
        file_path = os.path.normpath(os.path.join(path, s))

        # Skip directories and non-file items
        if not os.path.isfile(file_path):
            print(f"Skipping directory or special file: {file_path}")
            continue

        try:
            file = dcmread(file_path, force=True)
            slices.append(file)
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            continue

    if len(slices) > 1:
        try:
            slices.sort(key=lambda slice: ((slice.get(0x00200100).value), slice.SliceLocation))
        except AttributeError:
            try:
                slices.sort(key=lambda slice: slice.InstanceNumber)
            except (AttributeError, TypeError) as e:
                print(f"Warning: Could not sort slices by InstanceNumber: {e}")
                # Just keep them in the original order if we can't sort

    return slices