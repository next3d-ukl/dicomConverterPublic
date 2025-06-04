import os
import json
import cv2 as cv
import numpy as np
from PIL import Image
from pydicom import dcmread
from pydicom.pixel_data_handlers.util import apply_voi_lut
from typing import List, Dict, Tuple, Any, Optional

from models.dicom_data import DicomData

class DicomService:
    """
    Service class for DICOM related operations
    """
    
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
    
    @staticmethod
    def get_meta_from_slice(slice) -> Dict[str, Any]:
        """
        Extract metadata from a DICOM slice
        """
        def multivalue_to_list(multivalue):
            lst = []
            for element in multivalue:
                lst.append(element)
            return lst
        
        data_json = {}
        
        modality = slice.get(0x00080060).value
        
        if modality != 'PR' and modality != 'SR':
            if modality == 'MR':
                if 'DERIVED' in slice.get(0x00080008).value:
                    try:
                        spacing = multivalue_to_list(slice.get(0x00280030).value)
                        data_json = {'spacing': spacing}
                    except:
                        pass
                else:
                    rows = slice.get(0x00280010).value
                    cols = slice.get(0x00280011).value
                    try:
                        thickness = slice.get(0x00180050).value
                    except:
                        thickness = ''
                    if slice.get(0x00200032).value is None:
                        pos = ''
                    else:
                        pos = multivalue_to_list(slice.get(0x00200032).value)
                    if slice.get(0x00200037).value is None:
                        direction = ''
                    else:
                        direction = multivalue_to_list(slice.get(0x00200037).value)
                    spacing = multivalue_to_list(slice.get(0x00280030).value)
                    data_json = {'rows': rows, 'cols': cols, 'pos': pos, 'direction': direction, 'spacing': spacing, 'slice_thickness': thickness}
            elif modality == 'CT':
                if 'DERIVED' in slice.get(0x00080008).value:
                    try:
                        spacing = multivalue_to_list(slice.get(0x00280030).value)
                        data_json = {'spacing': spacing}
                    except:
                        pass
                else:
                    rows = slice.get(0x00280010).value
                    cols = slice.get(0x00280011).value
                    try:
                        thickness = slice.get(0x00180050).value
                    except:
                        thickness = ''
                    if slice.get(0x00200032).value is None:
                        pos = ''
                    else:
                        pos = multivalue_to_list(slice.get(0x00200032).value)
                    if slice.get(0x00200037).value is None:
                        direction = ''
                    else:
                        direction = multivalue_to_list(slice.get(0x00200037).value)
                    spacing = multivalue_to_list(slice.get(0x00280030).value)
                    data_json = {'rows': rows, 'cols': cols, 'pos': pos, 'direction': direction, 'spacing': spacing, 'slice_thickness': thickness}
        return data_json
    
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
        slices = DicomService.load_slices(input_path)

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
                orientation = DicomService.get_slice_orientation(slices[0])
                data_json['sliceOrientation'] = orientation
                data_json["firstImage"] = DicomService.get_meta_from_slice(slices[0])
                data_json["lastImage"] = DicomService.get_meta_from_slice(slices[len(slices) - 1])
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
                print(f"PROGRESS: {int(progress_counter/2)} / {total_dicom_images}")                
            except Exception as e:
                print(f"Error processing slice: {e}")
                continue

        # Step 5: Save metadata JSON
        json.dump(data_json, open(output_path + '/data.json', 'w'), indent=5, sort_keys=True)

        if len(slices) > 0:
            return orientation, slices[0].PixelSpacing[0], slices[0].PixelSpacing[1], slices[0].SliceThickness
        else:
            return "unknown", 1.0, 1.0, 1.0
            
    @staticmethod
    def load_image_as_array(file_path: str) -> np.ndarray:
        """
        Load image as a NumPy array
        """
        img = Image.open(file_path).convert('L')  # Convert to grayscale
        img_array = np.array(img)
        return img_array

    @staticmethod
    def resize_input_images(json_path: str, image_paths: List[str], 
                          horizontal_spacing: float, vertical_spacing: float, 
                          depth_spacing: float) -> None:
        """
        Resize input images for proper display
        """
        multiplier = int(depth_spacing // horizontal_spacing)

        # Calculate the new dimensions
        old_width, old_height = 0, 0
        new_width = 0
        new_height = 0

        for path in image_paths:
            with Image.open(path) as img:
                # Calculate the new dimensions
                old_width, old_height = img.size

                new_width = int(old_width * (horizontal_spacing * multiplier / depth_spacing))
                new_height = int(old_height * (vertical_spacing * multiplier / depth_spacing))

                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                resized_img.save(path)

        with open(json_path, 'r') as file:
            data = json.load(file)

        data['firstImage']['cols'] = new_width
        data['firstImage']['rows'] = new_height
        data['firstImage']['spacing'] = [old_width / new_width * horizontal_spacing, old_height / new_height * vertical_spacing]
        data['lastImage']['cols'] = new_width
        data['lastImage']['rows'] = new_height
        data['lastImage']['spacing'] = [old_width / new_width * horizontal_spacing, old_height / new_height * vertical_spacing]

        # Write the updated JSON back to the file
        with open(json_path, 'w') as file:
            json.dump(data, file, indent=4)

    @staticmethod
    def create_column_images(image_paths: List[str], multiplier: int, orientation: str) -> List[np.ndarray]:
        """
        Create column-based cross-sectional images
        
        Args:
            image_paths: List of paths to input images
            multiplier: Scaling factor for image creation
            orientation: The orientation of the input images ('transversal', 'sagittal', or 'coronal')
            
        Returns:
            List of cross-sectional images as NumPy arrays
        """
        # Determine sort order based on orientation
        sort_reverse = True
        if orientation == "sagittal":
            # For sagittal inputs, we need forward order for proper results
            sort_reverse = False
            
        # Sort image paths according to orientation needs
        image_paths.sort(reverse=sort_reverse)

        # Load and resize all input images
        images = [Image.open(path).convert('L') for path in image_paths]
        images = [np.array(img) for img in images]
        
        # Ensure all images are of identical size
        for img in images:
            if img.shape != images[0].shape:
                raise ValueError("All images must be of the same size")
        
        # Get the dimensions of the images
        height, width = images[0].shape
        
        # Create a list to store the result images
        result_images = []
        
        # Create result images for each column index
        for col_index in range(width):
            # Create an empty array for the new image
            new_img = np.zeros((height, len(images) * multiplier), dtype=images[0].dtype)
            
            # Populate the new image array with the specific column from each input image
            for img_index in range(len(images) * multiplier):
                img = images[img_index // multiplier]
                new_img[:, img_index] = img[:, col_index]
            
            # Transpose the new image to swap rows and columns
            new_img = np.transpose(new_img, (1, 0))
            
            # Apply orientation-specific transformations
            if orientation == "coronal":
                # For coronal inputs, rotate sagittal output 90 degrees clockwise
                new_img = np.rot90(new_img, k=3)  # k=3 is 270 degrees = 90 degrees clockwise
            elif orientation == "sagittal":
                # For sagittal inputs, rotate coronal output 90 degrees clockwise
                new_img = np.rot90(new_img, k=3)  # k=3 is 270 degrees = 90 degrees clockwise
            
            # Add the new image to the result list
            result_images.append(new_img)
        
        # Apply orientation-specific result order
        if orientation in ["transversal", "coronal"]:
            result_images.reverse()
        
        return result_images

    @staticmethod
    def create_row_images(image_paths: List[str], multiplier: int, orientation: str) -> List[np.ndarray]:
        """
        Create row-based cross-sectional images
        
        Args:
            image_paths: List of paths to input images
            multiplier: Scaling factor for image creation
            orientation: The orientation of the input images ('transversal', 'sagittal', or 'coronal')
            
        Returns:
            List of cross-sectional images as NumPy arrays
        """
        # Determine sort order based on orientation
        sort_reverse = False  # Default is standard order
        
        # Sort image paths according to orientation needs
        # For coronal inputs, transversal output should be in default order
        image_paths.sort(reverse=sort_reverse)
        
        # Load and resize all input images
        images = [Image.open(path).convert('L') for path in image_paths]
        images = [np.array(img) for img in images]
        
        # Ensure all images are of identical size
        for img in images:
            if img.shape != images[0].shape:
                raise ValueError("All images must be of the same size")
        
        # Get the dimensions of the images
        height, width = images[0].shape
        
        # Create a list to store the result images
        result_images = []
        
        # Create result images for each row index
        for row_index in range(height):
            # Create an empty array for the new image
            new_img = np.zeros((len(images) * multiplier, width), dtype=images[0].dtype)
            
            # Populate the new image array with the specific row from each input image
            for img_index in range(len(images) * multiplier):
                img = images[img_index // multiplier]
                new_img[img_index, :] = img[row_index, :]
            
            # Apply orientation-specific transformations
            if orientation == "transversal":
                # For transversal inputs, flip coronal output vertically
                new_img = np.flipud(new_img)
            elif orientation == "sagittal":
                new_img = np.rot90(new_img, k=3)  # k=3 is 270 degrees = 90 degrees clockwise

            # Add the new image to the result list
            result_images.append(new_img)
        
        # Reverse the result order for specific orientations
        if orientation == "coronal":
            # For coronal inputs, reverse the order of transversal images
            result_images.reverse()
        elif orientation == "sagittal":
            # For sagittal inputs, reverse the order of transversal images
            result_images.reverse()
            
        return result_images

    @staticmethod
    def process_cross_sections(output_folder: str, base_orientation: str, columns_folder: str, 
                              rows_folder: str, horizontal_spacing: float, 
                              vertical_spacing: float, depth_spacing: float) -> None:
        """
        Process images to create cross-sectional views
        """
        # Get all image paths from the input folder and sort them alphabetically
        image_paths = sorted([
            os.path.normpath(os.path.join(output_folder, "images", base_orientation, f))
            for f in os.listdir(os.path.normpath(os.path.join(output_folder, "images", base_orientation)))
            if f.endswith(('png', 'jpg', 'jpeg'))
        ])

        # Step 1: Resize images (70% to 75%)
        DicomService.resize_input_images(
            output_folder + "/data.json", 
            image_paths, 
            horizontal_spacing, 
            vertical_spacing, 
            depth_spacing
        )
        print(f"Resized {base_orientation} images")
        print(f"PROGRESS: 75 / 100")  # Signal 75% progress after resizing

        # Step 2: Create column images (75% to 80%)
        column_result_images = DicomService.create_column_images(
            image_paths, 
            int(depth_spacing // vertical_spacing),
            base_orientation  # Pass the orientation for proper transformations
        )
        print(f"Calculated {columns_folder} images (column)")
        print(f"PROGRESS: 80 / 100")  # Signal 80% progress

        # Step 3: Create row images (80% to 85%)
        row_result_images = DicomService.create_row_images(
            image_paths, 
            int(depth_spacing // horizontal_spacing),
            base_orientation  # Pass the orientation for proper transformations
        )
        print(f"Calculated {rows_folder} images (row)")
        print(f"PROGRESS: 85 / 100")  # Signal 85% progress
        
        # Ensure output directories exist
        os.makedirs(output_folder + "/images/" + columns_folder, exist_ok=True)
        os.makedirs(output_folder + "/images/" + rows_folder, exist_ok=True)

        # Step 4: Save column images (85% to 90%)
        for i, result_image in enumerate(column_result_images):
            result_img_pil = Image.fromarray(result_image)
            result_img_pil.save(os.path.normpath(os.path.join(output_folder + "/images/" + columns_folder, f'{i:04d}.png')))
        print(f"Saved {columns_folder} images")
        print(f"PROGRESS: 90 / 100")  # Signal 90% progress

        # Step 5: Save row images (90% to 95%)
        for i, result_image in enumerate(row_result_images):
            result_img_pil = Image.fromarray(result_image)
            result_img_pil.save(os.path.normpath(os.path.join(output_folder + "/images/" + rows_folder, f'{i:04d}.png')))
        print(f"Saved {rows_folder} images")
        print(f"PROGRESS: 95 / 100")  # Signal 95% progress at the end
        
        print("Conversion finished!")

    @staticmethod
    def run_conversion(input_path: str, output_path: str) -> DicomData:
        """
        Run the complete DICOM conversion process and return data model
        """
        # Step 1: Convert DICOM to images
        orientation, horizontal_spacing, vertical_spacing, depth_spacing = DicomService.convert_dicom_to_images(
            input_path, output_path
        )
        
        # Get derived orientation names
        columns_folder = DicomService.get_orientation_names(orientation)['columns']
        rows_folder = DicomService.get_orientation_names(orientation)['rows']

        # Step 2: Process cross sections
        DicomService.process_cross_sections(
            output_path, orientation, columns_folder, rows_folder, 
            horizontal_spacing, vertical_spacing, depth_spacing
        )
        
        # Step 3: Create and populate data model
        model = DicomData(
            slice_orientation=orientation,
            spacing=(horizontal_spacing, vertical_spacing, depth_spacing),
            input_folder=input_path,
            output_folder=output_path
        )
        
        # Load metadata
        try:
            with open(output_path + '/data.json', 'r') as f:
                data = json.load(f)
                if "firstImage" in data:
                    model.first_image_metadata = data["firstImage"]
                if "lastImage" in data:
                    model.last_image_metadata = data["lastImage"]
        except (FileNotFoundError, json.JSONDecodeError):
            print("Error loading metadata from data.json")
        
        return model
        
    @staticmethod
    def get_orientation_names(slice_orientation: str) -> Dict[str, str]:
        """
        Get names of derived orientations based on slice orientation
        """
        direction_map = {
            "transversal": {"rows": "coronal", "columns": "sagittal"},
            "sagittal": {"rows": "transversal", "columns": "coronal"},
            "coronal": {"rows": "transversal", "columns": "sagittal"}
        }
        
        if slice_orientation in direction_map:
            return direction_map[slice_orientation]
        else:
            return {"rows": "rows", "columns": "columns"}
    
    @staticmethod
    def get_dicom_metadata(directory_path: str) -> Dict[str, Any]:
        """
        Extract all metadata from the first DICOM file in a directory
        
        Args:
            directory_path: Path to directory containing DICOM files
            
        Returns:
            Dictionary containing all metadata from the DICOM file
        """
        if not os.path.exists(directory_path):
            return {}
            
        # Find first DICOM file
        for file_name in os.listdir(directory_path):
            file_path = os.path.normpath(os.path.join(directory_path, file_name))
            if not os.path.isfile(file_path):
                continue
                
            try:
                # Try to read as DICOM
                dicom_data = dcmread(file_path, force=True)
                
                # Create a dictionary with all metadata
                metadata = {}

                # Add file information
                metadata["File Information"] = {
                    "File Path": file_path,
                    "File Size": f"{os.path.getsize(file_path) / 1024:.2f} KB"
                }
                
                # Add DICOM metadata by categories
                metadata["Patient Information"] = {}
                metadata["Study Information"] = {}
                metadata["Series Information"] = {}
                metadata["Image Information"] = {}
                metadata["Other Attributes"] = {}
                
                # Process each DICOM attribute
                for elem in dicom_data:
                    # Skip pixel data (too large)
                    if elem.tag == 0x7FE00010:  # PixelData
                        metadata["Image Information"]["Pixel Data"] = f"[Array of {len(elem.value)} bytes]"
                        continue
                        
                    # Get element name and value
                    try:
                        name = elem.name
                        if elem.VR == "SQ":  # Sequence
                            if elem.value:
                                value = f"Sequence with {len(elem.value)} item(s)"
                            else:
                                value = "Empty sequence"
                        else:
                            value = str(elem.value)
                    except Exception as e:
                        name = f"Unknown ({elem.tag})"
                        value = f"Error: {str(e)}"
                    
                    # Categorize by group
                    tag_group = elem.tag.group
                    
                    if tag_group == 0x0010:  # Patient
                        metadata["Patient Information"][name] = value
                    elif tag_group == 0x0020:  # Study
                        metadata["Study Information"][name] = value
                    elif tag_group == 0x0008:  # Series
                        metadata["Series Information"][name] = value
                    elif tag_group in (0x0028, 0x7FE0):  # Image
                        metadata["Image Information"][name] = value
                    else:
                        metadata["Other Attributes"][name] = value
                
                return metadata
                
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue
        
        return {}
