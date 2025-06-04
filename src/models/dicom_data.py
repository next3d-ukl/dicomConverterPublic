from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import os

@dataclass
class DicomData:
    """
    Data model representing DICOM dataset information
    """
    slice_orientation: str = "unknown"
    spacing: Tuple[float, float, float] = (1.0, 1.0, 1.0)  # horizontal, vertical, depth
    first_image_metadata: Dict[str, Any] = field(default_factory=dict)
    last_image_metadata: Dict[str, Any] = field(default_factory=dict)
    input_folder: str = ""
    output_folder: str = ""
    
    def get_derived_orientation_names(self) -> Dict[str, str]:
        """
        Get names of derived orientations based on slice orientation
        """
        direction_map = {
            "transversal": {"rows": "coronal", "columns": "sagittal"},
            "sagittal": {"rows": "coronal", "columns": "transversal"},
            "coronal": {"rows": "transversal", "columns": "sagittal"}
        }
        
        if self.slice_orientation in direction_map:
            return direction_map[self.slice_orientation]
        else:
            return {"rows": "rows", "columns": "columns"}

    
    def get_center_image_path(self) -> Optional[str]:
        """
        Get path to center image for the specified orientation
        """
        image_paths = os.path.join(self.output_folder, "images")
        if not image_paths:
            return None
            
        return image_paths[len(image_paths) // 2]