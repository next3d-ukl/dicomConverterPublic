# DICOM Converter UI

This project is a user-friendly application for converting DICOM files into image formats. It utilizes PyQt for the graphical user interface and provides functionalities to select input and output folders, toggle console output, and initiate the conversion process.

## Project Structure

The project follows the Model-View-ViewModel (MVVM) pattern:

```
dicomConverterPublic
├── Blender                         # Blender portable 4.4
├── src                             # Sourcecode
│   ├── models                      # Data models
│   │   ├── color_list_class.py     # List of colors for objects
│   │   └── dicom_data.py           # Core data model for DICOM information
│   ├── services                    # Services for data processing
│   │   ├── dicom_service.py        # DICOM processing service
│   │   └── stl_service.py          # STL file processing service
│   ├── utils                       # Utility classes
│   │   └── console_redirect.py     # Console redirection utilities
│   ├── viewmodels                  # View models (business logic)
│   │   └── main_viewmodel.py       # Main view model connecting views and services
│   ├── views                       # UI views
│   │   ├── folder_tree_widget.py   # UI component
│   │   ├── main_window.py          # Main application window
│   │   └── metadata_window.py      # Metadata window
│   ├── main.py                     # Application entry point
├── README.md                       # Documentation
├── requirements.txt                # Project dependencies
├── start.bat                       # Start-script for Windows
└── start.command                   # Start-script for MacOS
```

## MVVM Architecture

- **Models**: Represent the data and business objects. They don't know about views or view models.
- **Views**: The user interface components. They bind to view models and respond to user interaction.
- **ViewModels**: Act as intermediaries between the models and views, containing the presentation logic.
- **Services**: Contain business logic and data processing functionality.

## Requirements

To run this project you need:

- Python 3.10 
- Blender (only on MacOS)

The following dependencies will be installed for you on start:

- PyQt5
- pydicom
- opencv-python
- Pillow
- numpy
- pyqtgraph
- numpy-stl
- PyOpenGL
- bpy==4.0.0

## Running the Application

1. Clone the repository or download the project files.
2. Navigate to the Folder in your filesytem.
3. Doubleclick the start.bat (Windows) or start.command (MacOS)
4. Only for MacOS: If the start.command doesn't work open the terminal, navigate to the projekt folder and type "chmod +x start_env.command"

## Usage Workflow

1. **Choose Output Location**: Click "Select Output Folder" to specify where the converted files should be saved. Note that the output folder must be empty.

### DICOM Convertion

1. **Select DICOM Folder**: Click "Select DICOM Import Folder" and navigate to a directory containing DICOM files. The application will automatically scan and display folders with relevant files.

2. **Browse and Select Input**: The folder browser will show folders containing files, with the folder having the most files automatically selected. You can select a different folder if needed.

3. **Start Conversion**: Click "Start Conversion" to begin the process. A progress bar will show the conversion status.

4. **View Results**: Upon completion, the output folder will automatically open.

### Object Convertion

1. **Load STL Files**: Use the "Select OBJ/STL Import Folder" and navigate to a directory containing OBJ or STL files.

2. **Browse and Select Input**: The folder browser will show folders containing files, with the folder having the most files automatically selected. You can select a different folder if needed (select the one with your OBJ or STL).

3. **Start Conversion**: Click "Start Conversion" to begin the process. This can take a while.

4. **View Results**: Upon completion, the output folder will automatically open.

## Features

- Select input and output folders for DICOM files
- Intelligent folder browser with automatic file counting
- Auto-selection of folders containing DICOM files
- Progress tracking during conversion with visual feedback
- Automatic output folder opening upon completion
- Load STL/OBJ and convert to USDZ
- Toggle console output to view detailed logs and messages

## Troubleshooting

### Import Errors
- **Error: "cannot import name 'mesh' from 'stl'"**: This usually means the numpy-stl package is not installed. Run `pip install numpy-stl` to fix this issue.

- **OpenGL Context Errors**: If you encounter OpenGL context errors, make sure you have appropriate graphics drivers installed. The application uses OpenGL for 3D rendering.

- **Empty Folder Browser**: If the folder browser appears empty after selecting a directory, try choosing a folder that contains valid DICOM files. The browser filters out folders with fewer than 2 files by default.

## License

This project is licensed under the MIT License. Feel free to modify and distribute as needed.