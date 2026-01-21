@staticmethod
def get_slice_orientation(slice) -> str:
    """
    Determine the orientation of a DICOM slice

    Uses a more tolerant approach to handle small deviations in orientation values
    """
    orientation = slice.ImageOrientationPatient
    row_cosines = orientation[:3]
    column_cosines = orientation[3:]

    # Helper function to check if vectors are approximately equal
    def is_approx_equal(vec1, vec2, threshold=0.1):
        """Check if two vectors are approximately equal"""
        if len(vec1) != len(vec2):
            return False
        return all(abs(a - b) < threshold for a, b in zip(vec1, vec2))

    # Define standard orientation vectors
    transversal_row = [1, 0, 0]
    transversal_col = [0, 1, 0]

    sagittal_row = [0, 1, 0]
    sagittal_col = [0, 0, 1]

    coronal_row = [1, 0, 0]
    coronal_col = [0, 0, 1]

    # Check for approximate matches using the helper function
    if is_approx_equal(row_cosines, transversal_row) and is_approx_equal(column_cosines, transversal_col):
        return "transversal"
    elif is_approx_equal(row_cosines, sagittal_row) and is_approx_equal(column_cosines, sagittal_col):
        return "sagittal"
    elif is_approx_equal(row_cosines, coronal_row) and is_approx_equal(column_cosines, coronal_col):
        return "coronal"

    # If no approximate match, try using the dot product to determine the best match
    # These represent the standard basis vectors X, Y, Z
    standard_vectors = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]

    # Check which standard vector has the highest alignment with row and column cosines
    def find_closest_axis(vector):
        """Find the axis that the vector is most closely aligned with"""
        max_dot = -1
        max_idx = -1
        for i, standard in enumerate(standard_vectors):
            dot = abs(sum(v * s for v, s in zip(vector, standard)))
            if dot > max_dot:
                max_dot = dot
                max_idx = i
        return max_idx

    # Get the most aligned axes
    row_axis = find_closest_axis(row_cosines)
    col_axis = find_closest_axis(column_cosines)

    # Determine orientation based on which axes the vectors align with
    if row_axis == 0 and col_axis == 1:  # X and Y
        return "transversal"
    elif row_axis == 1 and col_axis == 2:  # Y and Z
        return "sagittal"
    elif row_axis == 0 and col_axis == 2:  # X and Z
        return "coronal"

    # If still not determined, the orientation is unknown
    print(f"Unknown orientation. Row cosines: {row_cosines}, Column cosines: {column_cosines}")
    return "unknown"