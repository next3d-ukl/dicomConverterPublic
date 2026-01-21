import numpy as np

@staticmethod
def get_slice_orientation(orientation) -> str:
    row = orientation[:3]
    column = orientation[3:]
    cross = np.cross(row,column)
    if cross.argmax() == 0:
        return "sagittal"
    elif cross.argmax() == 1:
        return "coronal"
    elif cross.argmax() == 2:
        return "transversal"
    return "unknown"
