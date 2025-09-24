import os
import json
import numpy as np
from PIL import Image
from pydicom import dcmread
from typing import List, Dict, Tuple, Any, Optional

from models.dicom_data import DicomData

from services.dicom_to_image import convert_dicom_to_images


class DicomService:
    """
    Service class for DICOM related operations
    """
            
    @staticmethod
    def load_image_as_array(file_path: str) -> np.ndarray:
        print("load_image_as_array")
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
        print("++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("resize_input_images")
        """
        Resize input images for proper display
        """
        #TODO: shall not be 0
        print(f"depth_spacing: {depth_spacing}, horizontal_spacing: {horizontal_spacing}")
        multiplier = int(depth_spacing // horizontal_spacing)
        print(f"multiplier: {multiplier}")
        print("++++++++++++++++++++++++++++++++++++++++++++++++++")

        # Calculate the new dimensions
        print("Calculate the new dimensions")
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
        print("Write the updated JSON back to the file")
        print("QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ")
        print(f"data['firstImage']['cols']: {data['firstImage']['cols']}")
        print(f"data['firstImage']['rows']: {data['firstImage']['rows']}")
        print(f"data['firstImage']['spacing']: {data['firstImage']['spacing']}")
        print(f"data['lastImage']['cols']: {data['lastImage']['cols']}")
        print(f"data['lastImage']['rows']: {data['lastImage']['rows']}")
        print(f"data['lastImage']['spacing']: {data['lastImage']['spacing']}")
        print("QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ")

        with open(json_path, 'w') as file:
            json.dump(data, file, indent=4)

    @staticmethod
    def create_column_images(image_paths: List[str], multiplier: int, orientation: str) -> List[np.ndarray]:
        print("create_column_images")
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
        print("create_row_images")
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
        print("process_cross_sections")
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
        print("run_conversion")
        """
        Run the complete DICOM conversion process and return data model
        """
        # Step 1: Convert DICOM to images
        orientation, horizontal_spacing, vertical_spacing, depth_spacing = convert_dicom_to_images(input_path, output_path)
        print("RETURN VALUE convert_dicom_to_images(input_path, output_path)")
        print("-------------------------------------------------------------")
        print(f"orientation: {orientation}, horizontal_spacing: {horizontal_spacing}, vertical_spacing: {vertical_spacing}, depth_spacing: {depth_spacing}")
        print("-------------------------------------------------------------")
        
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
        print("get_orientation_names")
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