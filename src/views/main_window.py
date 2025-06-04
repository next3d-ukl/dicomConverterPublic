from PIL import Image
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QPushButton, QHBoxLayout, QVBoxLayout, 
    QWidget, QFileDialog, QLabel, QMessageBox, QTextEdit, QAction,
    QSplitter, QFrame
)
from PyQt5.QtCore import pyqtSlot, Qt
import sys
import os
import numpy as np
import pyqtgraph.opengl as gl

from viewmodels.main_viewmodel import MainViewModel
from models.dicom_data import DicomData
from utils.console_redirect import ConsoleRedirect
from views.metadata_window import MetadataWindow
from views.folder_tree_widget import FolderTreeWidget

import math
import subprocess
import os
import bpy
import glob

from models.color_list_class import ColorList

class MainWindow(QMainWindow):
    """
    Main application window
    """
    def __init__(self, view_model: MainViewModel):
        super().__init__()

        self.view_model = view_model
        self.setWindowTitle("DICOM Converter")
        self.adjustSize()

        self.input_folder = ""
        self.objstl_input_folder = ""
        self.output_folder = ""
        self.console_output_enabled = False
        self.metadata_window = None
        
        # Connect signals
        self.view_model.conversion_started.connect(self.on_conversion_started)
        self.view_model.conversion_completed.connect(self.on_conversion_completed)
        self.view_model.conversion_failed.connect(self.on_conversion_failed)
        self.view_model.stl_loaded.connect(self.on_stl_loaded)
        self.view_model.metadata_loaded.connect(self.on_metadata_loaded)
        self.view_model.clear_gl_view_requested.connect(self.clear_gl_view)

        self.init_ui()
        self.init_menu()

        # Redirect stdout and stderr with progress bar support
        sys.stdout = ConsoleRedirect(self.console_output, sys.stdout, self.progress_bar)
        sys.stderr = ConsoleRedirect(self.console_output, sys.stderr, self.progress_bar)

    def init_ui(self):
        """Initialize the UI components"""
        # Create a splitter for the main layout
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel with controls and folder tree
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(10)  # Add spacing between sections

        # SECTION 1: Output Folder Selection
        output_frame = QFrame()
        output_frame.setFrameShape(QFrame.StyledPanel)
        output_layout = QVBoxLayout(output_frame)

        output_header = QLabel("<b>Output Selection</b>")
        output_layout.addWidget(output_header)

        self.output_label = QLabel("Output Folder: Not Selected")
        output_layout.addWidget(self.output_label)

        self.select_output_button = QPushButton("Select Output Folder")
        self.select_output_button.clicked.connect(self.select_output_folder)
        output_layout.addWidget(self.select_output_button)

        left_layout.addWidget(output_frame)

        # SECTION 2: DICOM Conversion
        input_frame = QFrame()
        input_frame.setFrameShape(QFrame.StyledPanel)
        input_frame.setMinimumHeight(300)
        input_layout = QVBoxLayout(input_frame)
        
        input_header = QLabel("<b>DICOM Conversion</b>")
        input_layout.addWidget(input_header)
        
        self.input_label = QLabel("Input Folder: Not Selected")
        input_layout.addWidget(self.input_label)

        self.select_input_button = QPushButton("Select DICOM Import Folder")
        self.select_input_button.clicked.connect(self.select_input_folder)
        input_layout.addWidget(self.select_input_button)
        
        # Folder tree (no label)
        tree_layout = QVBoxLayout()
        
        self.folder_tree = FolderTreeWidget()
        self.folder_tree.folder_selected.connect(self.on_dicom_folder_selected)
        tree_layout.addWidget(self.folder_tree)
        self.folder_tree.setMinimumHeight(100)
        self.folder_tree.setMinimumWidth(400)
        
        input_layout.addLayout(tree_layout)



        conversion_header = QLabel("<b>Conversion</b>")
        input_layout.addWidget(conversion_header)

        self.start_button = QPushButton("Start Conversion")
        self.start_button.clicked.connect(self.start_conversion)
        self.start_button.setEnabled(False)  # Disabled until input and output folders are selected
        input_layout.addWidget(self.start_button)

        # Add progress bar
        from PyQt5.QtWidgets import QProgressBar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        input_layout.addWidget(self.progress_bar)

        left_layout.addWidget(input_frame)
        
        # SECTION 4: USDZ Converter
        stl_frame = QFrame()
        stl_frame.setFrameShape(QFrame.StyledPanel)
        stl_frame.setMinimumHeight(250)
        stl_layout = QVBoxLayout(stl_frame)
        
        stl_header = QLabel("<b>USDZ Conversion</b>")
        stl_layout.addWidget(stl_header)

        self.usdz_input_label = QLabel("Input Folder: Not Selected")
        stl_layout.addWidget(self.usdz_input_label)

        self.select_objstl_input_button = QPushButton("Select OBJ/STL Import Folder")
        self.select_objstl_input_button.clicked.connect(self.select_objstl_input_folder)
        stl_layout.addWidget(self.select_objstl_input_button)


        # usdz Folder tree (no label)
        usdz_tree_layout = QVBoxLayout()

        self.usdz_folder_tree = FolderTreeWidget()
        self.usdz_folder_tree.folder_selected.connect(self.on_usdz_folder_selected)
        usdz_tree_layout.addWidget(self.usdz_folder_tree)
        self.folder_tree.setMinimumHeight(100)
        self.folder_tree.setMinimumWidth(400)

        stl_layout.addLayout(usdz_tree_layout)



        self.button_usdz_converter = QPushButton("Start Conversion")
        self.button_usdz_converter.clicked.connect(self.run)
        stl_layout.addWidget(self.button_usdz_converter)

        left_layout.addWidget(stl_frame)
        
        # Add the console output (hidden by default)
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.hide()  # Initially hide the console
        left_layout.addWidget(self.console_output)
        
        # Add expanding spacer at the bottom
        left_layout.addStretch(1)
        
        # Add the left panel to the splitter
        main_splitter.addWidget(left_panel)

        # Set size
        #self.setFixedSize(400,600)

        # Set the splitter as the central widget
        self.setCentralWidget(main_splitter)

    def init_menu(self):
        """Initialize the application menu"""
        menubar = self.menuBar()
        
        # View menu
        view_menu = menubar.addMenu('View')
        self.console_action = QAction('Toggle Console Output', self, checkable=True)
        self.console_action.triggered.connect(self.toggle_console_output)
        view_menu.addAction(self.console_action)
        
        # DICOM menu
        dicom_menu = menubar.addMenu('DICOM')
        self.metadata_action = QAction('Show Metadata', self)
        self.metadata_action.triggered.connect(self.show_metadata)
        self.metadata_action.setEnabled(False)  # Disabled by default
        dicom_menu.addAction(self.metadata_action)

    def select_objstl_input_folder(self):
        """Open dialog to select base folder and populate folder tree"""
        base_folder = QFileDialog.getExistingDirectory(self, "Select STL/OBJ Folder")
        if not base_folder:
            return

        # Set the root path for the folder tree
        try:
            # Show the folder tree
            self.usdz_folder_tree.show()

            # Print debug message
            print(f"Selected base folder: {base_folder}")

            # Set the root path for the folder tree
            result = self.usdz_folder_tree.set_root_path(base_folder)

            if not result:
                QMessageBox.warning(self, "Error",
                                    f"Could not access folder: {base_folder}\n\nPlease check the console output for details.")
                # Hide the folder tree if there was an error
                self.usdz_folder_tree.hide()
                return

            # Check if the tree is empty after filtering
            if self.usdz_folder_tree.tree_widget.topLevelItemCount() == 0:
                QMessageBox.information(self, "No Suitable Folders",
                                        "No folders with at least 2 files were found in the selected directory.\n\n"
                                        "Try selecting a different directory that contains DICOM files.")

            # Update the input folder label with just the folder name
            folder_name = os.path.basename(base_folder)
            self.usdz_input_label.setText(f"Input Folder: {folder_name}")

            # Automatically check if this folder already has DICOM files to enable metadata action
            self.metadata_action.setEnabled(False)  # Disable until a DICOM folder is selected
        except Exception as e:
            QMessageBox.warning(self, "Error", f"An error occurred: {str(e)}")
            # Hide the folder tree if there was an error
            self.usdz_folder_tree.hide()

    def select_input_folder(self):
        """Open dialog to select base folder and populate folder tree"""
        base_folder = QFileDialog.getExistingDirectory(self, "Select DICOM Folder")
        if not base_folder:
            return
            
        # Set the root path for the folder tree
        try:
            # Show the folder tree
            self.folder_tree.show()
            
            # Print debug message
            print(f"Selected base folder: {base_folder}")
            
            # Set the root path for the folder tree
            result = self.folder_tree.set_root_path(base_folder)
            
            if not result:
                QMessageBox.warning(self, "Error", f"Could not access folder: {base_folder}\n\nPlease check the console output for details.")
                # Hide the folder tree if there was an error
                self.folder_tree.hide()
                return
            
            # Check if the tree is empty after filtering
            if self.folder_tree.tree_widget.topLevelItemCount() == 0:
                QMessageBox.information(self, "No Suitable Folders", 
                    "No folders with at least 2 files were found in the selected directory.\n\n"
                    "Try selecting a different directory that contains DICOM files.")
            
            # Update the input folder label with just the folder name
            folder_name = os.path.basename(base_folder)
            self.input_label.setText(f"Input Folder: {folder_name}")
            
            # Automatically check if this folder already has DICOM files to enable metadata action
            self.metadata_action.setEnabled(False)  # Disable until a DICOM folder is selected
        except Exception as e:
            QMessageBox.warning(self, "Error", f"An error occurred: {str(e)}")
            # Hide the folder tree if there was an error
            self.folder_tree.hide()
        
    def on_dicom_folder_selected(self, folder_path):
        """Handle DICOM folder selection from the folder tree"""
        if not folder_path:
            return
            
        # Update the input folder
        self.input_folder = folder_path
        self.view_model.input_folder = folder_path
        
        # Update UI - show only the folder name
        folder_name = os.path.basename(folder_path)
        self.input_label.setText(f"Input Folder: {folder_name}")
        self.metadata_action.setEnabled(True)
        
        # Enable the start button if output folder is also selected
        self.update_start_button_state()

    def on_usdz_folder_selected(self, folder_path):
        """Handle DICOM folder selection from the folder tree"""
        if not folder_path:
            return

        # Update the input folder
        self.objstl_input_folder = folder_path

        # Update UI - show only the folder name
        folder_name = os.path.basename(folder_path)
        self.usdz_input_label.setText(f"Input Folder: {folder_name}")
        self.metadata_action.setEnabled(True)

        # Enable the start button if output folder is also selected
        self.update_start_button_state()

    def select_output_folder(self):
        """Open dialog to select output folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder = folder
            self.view_model.output_folder = folder  # Set in view model too
            
            # Display only the folder name instead of the full path
            folder_name = os.path.basename(folder)
            self.output_label.setText(f"Output Folder: {folder_name}")
            
            # Update start button state
            self.update_start_button_state()
            
    def update_start_button_state(self):
        """Update the state of the start button based on input and output folders"""
        has_input = bool(self.input_folder)
        has_output = bool(self.output_folder)
        
        self.start_button.setEnabled(has_input and has_output)

    def toggle_console_output(self):
        """Toggle the visibility of the console output"""
        self.console_output_enabled = not self.console_output_enabled
        if self.console_output_enabled:
            self.console_output.show()
        else:
            self.console_output.hide()
            
    def open_output_folder(self):
        """Open the output folder in the file explorer"""
        if not self.output_folder:
            return
            
        # Use platform-specific command to open folder
        import platform
        import subprocess
        
        try:
            if platform.system() == "Windows":
                # Windows
                os.startfile(self.output_folder)
            elif platform.system() == "Darwin":
                # macOS
                subprocess.Popen(["open", self.output_folder])
            else:
                # Linux
                subprocess.Popen(["xdg-open", self.output_folder])
                
            print(f"Opening output folder: {self.output_folder}")
        except Exception as e:
            print(f"Error opening output folder: {e}")

    def start_conversion(self):
        """Start the DICOM conversion process"""
        self.view_model.start_conversion(self.input_folder, self.output_folder)

    def load_stl(self):
        """Load an STL file for 3D visualization"""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open STL File", "", "STL Files (*.stl);;All Files (*)",
            options=options
        )
        if file_name:
            self.view_model.load_stl(file_name)
    
    def show_metadata(self):
        """Show the DICOM metadata window"""
        if not self.view_model.has_input_folder():
            QMessageBox.warning(self, "Warning", "Please select an input folder first.")
            return
            
        # Load metadata from the selected DICOM folder
        self.view_model.load_dicom_metadata()
    
    @pyqtSlot(dict)
    def on_metadata_loaded(self, metadata):
        """Handle metadata loaded event"""
        if not metadata:
            QMessageBox.warning(self, "Warning", "No DICOM metadata found in the selected folder.")
            return
            
        # Create and show the metadata window
        if not self.metadata_window:
            self.metadata_window = MetadataWindow()
            
        self.metadata_window.set_metadata(metadata)
        self.metadata_window.show()
        self.metadata_window.raise_()  # Bring to front
    
    @pyqtSlot()
    def on_conversion_started(self):
        """Handle conversion started event"""
        self.start_button.setEnabled(False)
        self.start_button.setText("Converting...")
        
        # Reset progress bar to 0
        self.progress_bar.setValue(0)
        
        # Reset the progress bar style to default with visible text
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                text-align: center;
                color: black;  /* Ensure text is visible during conversion */
            }
        """)
        
        print("Starting conversion...")
    
    @pyqtSlot(DicomData)
    def on_conversion_completed(self, dicom_data: DicomData):
        """Handle conversion completed event"""
        from PyQt5.QtCore import QTimer
        from PyQt5.QtGui import QColor

        self.start_button.setEnabled(True)
        self.start_button.setText("Start Conversion")
        
        # Set progress bar to 100% and hide text
        self.progress_bar.setValue(100)
        
        # Set the progress bar style to green and hide the text
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                text-align: center;
                color: transparent;  /* Hide the text */
            }
            QProgressBar::chunk {
                background-color: #4CAF50;  /* Material Design Green */
            }
        """)
        
        print("Conversion completed!")
        
        # Open the output folder automatically
        self.open_output_folder()
        
        # Clear any existing GL items first
        self.clear_gl_view()
        
        # Use QTimer to delay the display of cross-section images
        # This ensures it happens after the conversion thread has finished 
        # and any OpenGL context issues are resolved
        QTimer.singleShot(500, self.display_cross_section_images)
    
    @pyqtSlot(str)
    def on_conversion_failed(self, error_message: str):
        """Handle conversion failure event"""
        self.start_button.setEnabled(True)
        self.start_button.setText("Start Conversion")
        self.progress_bar.setValue(0)  # Reset progress bar
        
        error_box = QMessageBox.critical(self, "Error", error_message)
        
        # If the error was about the output folder not being empty, open folder picker
        if "Output folder must be empty" in error_message:
            self.select_output_folder()
    
    @pyqtSlot(np.ndarray, np.ndarray)
    def on_stl_loaded(self, vertices: np.ndarray, faces: np.ndarray):
        """Handle STL loaded event"""
        from PyQt5.QtCore import QTimer
        
        # Store the vertices and faces for later use
        self._stl_vertices = vertices
        self._stl_faces = faces
        
        # Clear current items first
        self.clear_gl_view()
        
        # Schedule the actual GL operations to happen in the main thread
        QTimer.singleShot(100, self._display_stl)
        
    def _display_stl(self):
        """Display the loaded STL file in the 3D view (called in main thread)"""
        try:
            # Make sure we have vertices and faces
            if not hasattr(self, '_stl_vertices') or not hasattr(self, '_stl_faces'):
                print("No STL data available to display")
                return
            
            # Create mesh data
            mesh_data = gl.MeshData(vertexes=self._stl_vertices, faces=self._stl_faces)
            mesh_item = gl.GLMeshItem(
                meshdata=mesh_data, 
                smooth=False, 
                drawEdges=True, 
                edgeColor=(1, 1, 1, 1)
            )
            
            self.gl_view.addItem(mesh_item)
            print("STL loaded successfully")
        except Exception as e:
            print(f"Error displaying STL: {e}")

    def _init_gl_view(self):
        """Initialize the GL view widget on the main thread"""
        # Create the GL view widget
        self.gl_view = gl.GLViewWidget()
        
        # Add it to the container
        self.gl_view_container_layout.addWidget(self.gl_view)
        
    def clear_gl_view(self):
        """Clear the 3D view of all items"""
        # Run in the main thread to avoid OpenGL context issues
        if hasattr(self, 'gl_view'):
            self.gl_view.clear()
            print("3D view cleared")
        
    def display_cross_section_images(self):
        """Display the center cross-section images in the 3D view"""
        # Clear current items
        self.clear_gl_view()
        
        # Get center image paths from viewmodel
        image_paths = self.view_model.get_center_cross_section_images()
        
        if not image_paths:
            print("No cross-section images available to display")
            return
            
        # Log the image paths
        for orientation, path in image_paths.items():
            print(f"{orientation} image path: {path}")
        
        # Process and add images to the 3D view (all done on the main thread)
        images = {}
        
        # First load all images on the main thread
        try:
            for orientation, path in image_paths.items():
                try:
                    # Load the image
                    image = Image.open(path).convert("L")
                    # Convert to numpy array and normalize to [0, 1]
                    array = np.array(image) / 255.0
                    # Convert to RGBA
                    rgba = np.stack((array,) * 3 + (np.ones_like(array),), axis=-1) * 255
                    rgba = rgba.astype(np.ubyte)
                    
                    # Store processed image
                    images[orientation] = rgba
                    print(f"{orientation} image shape: {rgba.shape}")
                except Exception as e:
                    print(f"Error loading image for {orientation}: {e}")
        except Exception as e:
            print(f"Error processing images: {e}")
            return
            
        # Now add the images to the GL view
        try:
            # Transversal
            if "transversal" in images:
                transversal_gl_image = gl.GLImageItem(images["transversal"])
                transversal_gl_image.translate(-0.5, -0.5, 0)
                self.gl_view.addItem(transversal_gl_image)
                print("Transversal image added")
                
            # Coronal
            if "coronal" in images:
                coronal_gl_image = gl.GLImageItem(images["coronal"])
                coronal_gl_image.rotate(90, 0, 1, 0)
                coronal_gl_image.translate(0, -0.5, -0.5)
                self.gl_view.addItem(coronal_gl_image)
                print("Coronal image added")
                
            # Sagittal
            if "sagittal" in images:
                sagittal_gl_image = gl.GLImageItem(images["sagittal"])
                sagittal_gl_image.rotate(90, 1, 0, 0)
                sagittal_gl_image.translate(-0.5, 0, -0.5)
                self.gl_view.addItem(sagittal_gl_image)
                print("Sagittal image added")
                
        except Exception as e:
            print(f"Error displaying cross-section images: {e}")
            
        print("Cross-section images displayed")


    def run(self):
        print("converter_model.py: run()")
        # Blender-Pfad (absolut)
        blender_path = ""
        if os.name == 'nt':  # Windows
            blender_path = r"..\..\Blender\blender-launcher.exe"
        elif os.name == 'posix':  # macOS und Linux
            blender_path = "/Applications/Blender.app/Contents/MacOS/Blender"

        # Ermittlung des aktuellen Skript-Verzeichnisses und Aufbau des relativen Pfads zum Konverter-Skript
        current_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.normpath(os.path.join(current_dir, self.convert()))

        # Blender im Hintergrund mit dem Python-Skript starten
        subprocess.call([blender_path, '--background', '--python', script_path])

    def convert(self):
        print("convert!")

        current_dir = os.path.dirname(os.path.abspath(__file__))
        import_path = self.objstl_input_folder
        export_path = self.output_folder

        print(f"import path: {import_path}")
        print(f"export path: {export_path}")

        if not os.path.exists(export_path):
            os.makedirs(export_path)

        bpy.context.scene.unit_settings.system = 'METRIC'
        bpy.context.scene.unit_settings.scale_length = 0.001

        # 🔹 Alle unterstützten Dateitypen sammeln
        model_files = glob.glob(os.path.normpath(os.path.join(import_path, "*.obj"))) + glob.glob(os.path.normpath(os.path.join(import_path, "*.stl")))

        for model_file in model_files:
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete()

            model_name = os.path.splitext(os.path.basename(model_file))[0]
            extension = os.path.splitext(model_file)[1].lower()

            print(f"extension: {extension}")

            self.import_model_file(model_file, extension)

            mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']

            if not mesh_objects:
                print(f"⚠️ Keine Mesh-Objekte gefunden für {model_name}, Überspringe...")
                continue

            for model in mesh_objects:
                bpy.context.view_layer.objects.active = model
                model.select_set(True)
                self.find_and_set_material(model)
                self.reduce_vertices(model)
                self.remove_vertex_duplicates(model)
                self.export_model(model, export_path, model_name)

        print("🚀 Alle Dateien wurden importiert und exportiert!")

        if os.name == 'nt':  # Windows
            os.startfile(export_path)
        elif os.name == 'posix':  # macOS und Linux
            subprocess.run(['open', export_path])

    def import_obj(self, filepath):
        bpy.ops.wm.obj_import(filepath=filepath)

    def import_stl(self, filepath):
        bpy.ops.import_mesh.stl(filepath=filepath)

    def get_or_create_material(self, name, color, alpha):
        if name in bpy.data.materials:
            return bpy.data.materials[name]

        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = color
            bsdf.inputs["Alpha"].default_value = alpha
        return mat

    def open_import_dir(self):
        print("______________________")
        print(self.objstl_input_folder)
        print("________________________________")
        import_path = self.objstl_input_folder
        if os.name == 'nt':  # Windows
            os.startfile(import_path)
        elif os.name == 'posix':  # macOS und Linux
            subprocess.run(['open', import_path])

    def reduce_vertices(self, model):
        vertex_count = len(model.data.vertices)
        if vertex_count > 100000:
            target_ratio = 100000 / vertex_count
            print(f"🔧 Reduziere '{model.name}' von {vertex_count} auf ~100000 Vertices (Ratio: {target_ratio:.4f})")
            decimate_mod = model.modifiers.new(name='Decimate', type='DECIMATE')
            decimate_mod.ratio = target_ratio
            bpy.ops.object.modifier_apply(modifier=decimate_mod.name)
        else:
            print(f"✅ '{model.name}' hat nur {vertex_count} Vertices – keine Reduktion notwendig.")

    def remove_vertex_duplicates(self, model):
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.0001)
        bpy.ops.object.editmode_toggle()

    def export_model(self, model, export_path, model_name):
        model_export_path = os.path.normpath(os.path.join(export_path, f"{model_name}.usdz"))
        bpy.ops.wm.usd_export(
            filepath=model_export_path,
            selected_objects_only=True
        )

        print(f"✅ Exportiert: {model_export_path}")
        model.select_set(False)

    def import_model_file(self, model_file, extension):
        print(f"📥 Importiere: {model_file}")

        if extension == ".stl":
            self.import_stl(model_file)

            # Rotate all mesh objects 90° around the X axis
            for obj in bpy.context.scene.objects:
                if obj.type == 'MESH':
                    obj.rotation_euler[0] += math.radians(90)

        elif extension == ".obj":
            self.import_obj(model_file)
        else:
            print(f"❌ Nicht unterstütztes Format: {extension}")

    def find_and_set_material(self, model):
        print("🔍 update material")
        name_lower = model.name.lower()
        print(f"looking for {name_lower}")

        colorList = ColorList()
        colors = colorList.getColorList()
        print("colorList loaded")
        color_count = len(colors)
        print("color_count set")
        color_not_found = True
        print("color finder setup ready")

        for i in range(color_count):
            for clue in colors[i].clues:
                if clue in name_lower:
                    color = colors[i].color
                    alpha = colors[i].alpha
                    mat = self.get_or_create_material(f"{clue}_material", color, alpha)
                    print(f"Identified as {clue}")
                    color_not_found = False
                    break
            if not color_not_found:
                break

        if color_not_found:
            if "transparent" in name_lower:
                color = colorList.defaultColor_transparent()
                alpha = colorList.defaultAlpha_transparent()
            else:
                color = colorList.defaultColor_opaque()
                alpha = colorList.defaultAlpha_opaque()
            mat = self.get_or_create_material("default", color, alpha)
            print("couldn't identify, setting default color")

        if model.data.materials:
            model.data.materials[0] = mat
        else:
            model.data.materials.append(mat)