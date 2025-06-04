from PyQt5.QtWidgets import QApplication
import sys

from views.main_window import MainWindow
from viewmodels.main_viewmodel import MainViewModel

def main():
    """
    Application entry point
    """
    app = QApplication(sys.argv)
    
    # Create the view model
    view_model = MainViewModel()
    
    # Create the main window, passing the view model
    window = MainWindow(view_model)
    window.show()
    
    # Start the application event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()