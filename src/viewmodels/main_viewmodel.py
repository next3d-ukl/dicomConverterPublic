from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import threading
from typing import Optional
import os
import numpy as np

from models.dicom_data import DicomData
from services.dicom_service import DicomService
from services.stl_service import StlService

class MainViewModel(QObject):
    """
    ViewModel for the main window, handles business logic
    """
    # Signals
    conversion_started = pyqtSignal()
    conversion_completed = pyqtSignal(DicomData)
    conversion_failed = pyqtSignal(str)
    stl_loaded = pyqtSignal(np.ndarray, np.ndarray)
    metadata_loaded = pyqtSignal(dict)
    clear_gl_view_requested = pyqtSignal()  # Signal to clear the 3D view before starting conversion
    
    def __init__(self):
        super().__init__()
        self.dicom_data: Optional[DicomData] = None
        self.input_folder: str = ""
        self.output_folder: str = ""
        
    @pyqtSlot(str, str)
    def start_conversion(self, input_folder: str, output_folder: str) -> None:
        """
        Start DICOM conversion in a separate thread
        """
        if not input_folder or not output_folder:
            self.conversion_failed.emit("Please select both input and output folders.")
            return
        
        # Check if the input folder exists
        if not os.path.exists(input_folder):
            self.conversion_failed.emit(f"Input folder does not exist: {input_folder}")
            return
            
        # Check if the output folder is empty
        if os.path.exists(output_folder) and os.listdir(output_folder):
            self.conversion_failed.emit("Output folder must be empty. Please select an empty folder.")
            return
            
        # Validate that the input folder has files (not just directories)
        has_files = False
        for item in os.listdir(input_folder):
            item_path = os.path.join(input_folder, item)
            if os.path.isfile(item_path):
                has_files = True
                break
                
        if not has_files:
            self.conversion_failed.emit("Input folder doesn't contain any files. Please select a folder with DICOM files.")
            return
        
        # Store the input and output folders
        self.input_folder = input_folder
        self.output_folder = output_folder
        
        # Clear any existing GL view items to prevent OpenGL thread issues
        self.clear_gl_view_requested.emit()
        
        # Signal that conversion has started
        self.conversion_started.emit()
        
        # Run conversion in a separate thread
        thread = threading.Thread(
            target=self._run_conversion_thread,
            args=(input_folder, output_folder)
        )
        thread.daemon = True
        thread.start()
    
    def _run_conversion_thread(self, input_folder: str, output_folder: str) -> None:
        """
        Thread function to run conversion
        """
        try:
            self.dicom_data = DicomService.run_conversion(input_folder, output_folder)
            self.conversion_completed.emit(self.dicom_data)
        except Exception as e:
            self.conversion_failed.emit(f"Conversion failed: {str(e)}")
    
    @pyqtSlot(str)
    def load_stl(self, file_path: str) -> None:
        """
        Load STL file
        """
        # Clear the 3D view first to prevent OpenGL context issues
        self.clear_gl_view_requested.emit()
        
        # Run STL loading in a separate thread
        thread = threading.Thread(
            target=self._load_stl_thread,
            args=(file_path,)
        )
        thread.daemon = True
        thread.start()
        
    def _load_stl_thread(self, file_path: str) -> None:
        """
        Thread function to load STL file
        """
        try:
            vertices, faces = StlService.load_stl_mesh(file_path)
            self.stl_loaded.emit(vertices, faces)
        except Exception as e:
            self.conversion_failed.emit(f"Failed to load STL: {str(e)}")
    
    @pyqtSlot()
    def load_dicom_metadata(self) -> None:
        """
        Load and emit metadata from the input DICOM folder
        """
        if not self.input_folder:
            self.metadata_loaded.emit({})
            return
            
        # Run in a separate thread to avoid UI freezing
        thread = threading.Thread(
            target=self._load_metadata_thread
        )
        thread.daemon = True
        thread.start()
        
    def _load_metadata_thread(self) -> None:
        """
        Thread function to load DICOM metadata
        """
        try:
            metadata = DicomService.get_dicom_metadata(self.input_folder)
            self.metadata_loaded.emit(metadata)
        except Exception as e:
            print(f"Error loading metadata: {e}")
            self.metadata_loaded.emit({})
    
    def has_input_folder(self) -> bool:
        """
        Check if an input folder has been selected
        """
        return bool(self.input_folder)
    
    def get_center_cross_section_images(self) -> dict:
        """
        Get the center cross-section images for all orientations
        
        Returns:
            dict with keys 'transversal', 'coronal', 'sagittal' containing 
            paths to the center images
        """
        if not self.dicom_data:
            return {}
            
        result = {}
        
        orientations = [
            self.dicom_data.slice_orientation,
            self.dicom_data.get_derived_orientation_names()["rows"],
            self.dicom_data.get_derived_orientation_names()["columns"]
        ]
        
        for orientation in orientations:
            center_image_path = self.dicom_data.get_center_image_path()
            if center_image_path:
                result[orientation] = center_image_path
                
        return result