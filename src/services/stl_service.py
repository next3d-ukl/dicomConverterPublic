from typing import Tuple
import numpy as np
from stl import mesh

class StlService:
    """
    Service for handling STL model files
    """
    
    @staticmethod
    def load_stl_mesh(file_path: str, scale: float = 0.1) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load an STL mesh file and return vertices and faces
        
        Args:
            file_path: Path to the STL file
            scale: Scaling factor for the vertices
            
        Returns:
            Tuple containing:
                - vertices: numpy array of vertex coordinates
                - faces: numpy array of face indices
        """
        stl_mesh = mesh.Mesh.from_file(file_path)
        vertices = stl_mesh.vectors.reshape(-1, 3) * scale
        faces = np.arange(len(vertices)).reshape(-1, 3)
        
        return vertices, faces