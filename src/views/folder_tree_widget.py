from PyQt5.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal
import os
from queue import Queue
import threading

class FolderTreeWidget(QWidget):
    """
    Widget that displays a custom folder tree with file counts
    """
    folder_selected = pyqtSignal(str)
    
    def __init__(self, parent=None, default_depth=4):
        super().__init__(parent)
        self.folder_items = {}  # Maps folder paths to tree items
        self.file_counts = {}   # Maps folder paths to file counts
        self.selected_folder = None
        self.root_path = None
        self.update_queue = Queue()
        self.default_depth = default_depth  # Default depth to expand folders
        
        # Start a timer to process UI updates from the queue
        from PyQt5.QtCore import QTimer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.process_ui_updates)
        self.update_timer.start(100)  # Process updates every 100ms
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Tree widget instead of tree view with model
        self.tree_widget = QTreeWidget()
        self.tree_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree_widget.setHeaderHidden(True)  # Hide the header
        self.tree_widget.setColumnCount(1)
        layout.addWidget(self.tree_widget)
            
        # Connect signals
        self.tree_widget.itemClicked.connect(self.on_item_clicked)
        self.tree_widget.itemExpanded.connect(self.on_item_expanded)
        self.tree_widget.itemSelectionChanged.connect(self.on_selection_changed)
    
    def process_ui_updates(self):
        """Process any pending UI updates from the queue"""
        while not self.update_queue.empty():
            try:
                folder_path, file_count = self.update_queue.get_nowait()
                self._update_folder_display(folder_path, file_count)
                self.update_queue.task_done()
            except Exception as e:
                print(f"Error processing UI update: {e}")
                break
        
    def set_root_path(self, path):
        """
        Set the root path and populate the tree
        """
        if not path or not os.path.isdir(path):
            print(f"Invalid directory: {path}")
            return False
            
        try:
            print(f"Setting root path to: {path}")
            
            # Make sure the path is a proper absolute path
            self.root_path = os.path.abspath(path)
            print(f"Absolute path: {self.root_path}")
            
            # Check if the path exists and is accessible
            if not os.access(self.root_path, os.R_OK):
                print(f"Path not readable: {self.root_path}")
                return False
                
            # Clear all existing items
            self.tree_widget.clear()
            self.folder_items = {}
            self.file_counts = {}
            self.selected_folder = None
            
            # Create and add the root item
            root_name = os.path.basename(self.root_path)
            root_item = QTreeWidgetItem(self.tree_widget, [root_name])
            root_item.setData(0, Qt.UserRole, self.root_path)
            self.folder_items[self.root_path] = root_item
            
            # Count files and load subfolders (recursively)
            self._load_folder_children(self.root_path, root_item)
            
            # First load all folders to the default depth
            self._expand_to_depth(root_item, 1, self.default_depth)
            
            # Then recursively count files in each visible folder
            # This ensures file counts are shown for all expanded folders
            all_paths = [path for path in self.folder_items.keys()]
            for path in all_paths:
                if path not in self.file_counts:
                    self._count_files_in_folder(path)
            
            # Apply filter to hide folders with fewer than 2 files
            # and no subfolders with at least 2 files
            self._apply_min_file_filter(root_item, 2)
            
            # Find and select best folder directly (without a thread)
            self._find_and_select_best_folder()
            
            print("Root path set successfully")
            return True
        except Exception as e:
            print(f"Error setting root path: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def _expand_to_depth(self, item, current_depth, max_depth):
        """
        Recursively expand all items to a specified depth
        
        Args:
            item: The current tree item
            current_depth: The current depth
            max_depth: The maximum depth to expand to
        """
        if current_depth > max_depth:
            return
            
        # Get the folder path for this item
        folder_path = item.data(0, Qt.UserRole)
        if not folder_path:
            return
                
        # First expand this item
        self.tree_widget.expandItem(item)
        
        # Force loading of children by handling the dummy items
        if item.childCount() == 1 and item.child(0).text(0) == "Loading...":
            # This will replace the dummy item with actual children
            self._load_folder_children(folder_path, item)
        
        # Now expand all children
        for i in range(item.childCount()):
            child = item.child(i)
            # Skip dummy or error items
            if child.text(0) in ["Loading...", "Error: Access Denied"]:
                continue
                
            # Process this child to the next depth
            self._expand_to_depth(child, current_depth + 1, max_depth)
    
    def _apply_min_file_filter(self, item, min_files):
        """
        Recursively filter folders with fewer than the minimum number of files
        and without any subfolders that meet the criteria
        
        Args:
            item: The current tree item
            min_files: Minimum number of files required to show a folder
        
        Returns:
            bool: Whether this folder or any of its subfolders meet the criteria
        """
        # Skip the root item (always visible)
        if item.parent() is None:
            # Process children of root
            has_valid_child = False
            
            # Check each child
            for i in range(item.childCount()-1, -1, -1):  # Iterate in reverse to safely remove items
                child = item.child(i)
                child_has_enough = self._apply_min_file_filter(child, min_files)
                if child_has_enough:
                    has_valid_child = True
                else:
                    # Remove child if it doesn't meet criteria
                    item.removeChild(child)
            
            return True  # Root is always visible
            
        # Get folder path and file count
        folder_path = item.data(0, Qt.UserRole)
        if not folder_path or folder_path not in self.file_counts:
            return False
            
        file_count = self.file_counts.get(folder_path, 0)
        
        # Check if this folder has enough files
        has_enough_files = file_count >= min_files
        
        # Check if any children have enough files
        has_valid_child = False
        
        # Process all children recursively
        for i in range(item.childCount()-1, -1, -1):  # Iterate in reverse to safely remove items
            child = item.child(i)
            # Skip dummy or error items
            if child.text(0) in ["Loading...", "Error: Access Denied"]:
                continue
                
            child_has_enough = self._apply_min_file_filter(child, min_files)
            if child_has_enough:
                has_valid_child = True
            else:
                # Remove child if it doesn't meet criteria
                item.removeChild(child)
        
        # Return true if either this folder has enough files or any child does
        return has_enough_files or has_valid_child
        
    def on_item_clicked(self, item, column):
        """
        Handle tree item click
        """
        if not item:
            return
            
        # Get the full path from the item's data
        folder_path = item.data(0, Qt.UserRole)
        if not folder_path:
            return
            
        # Count files in this folder if not already counted
        if folder_path not in self.file_counts:
            self._count_files_in_folder(folder_path)
        
    def on_selection_changed(self):
        """
        Handle selection change in the tree
        """
        items = self.tree_widget.selectedItems()
        if not items:
            return
            
        item = items[0]
        folder_path = item.data(0, Qt.UserRole)
        if not folder_path:
            return
            
        # Update the selected folder and emit the signal
        self.selected_folder = folder_path
        self.folder_selected.emit(folder_path)
                
    def on_item_expanded(self, item):
        """
        Handle item expansion - load children when a folder is expanded
        """
        if not item:
            return
            
        folder_path = item.data(0, Qt.UserRole)
        if not folder_path:
            return
            
        # Check if we need to replace the "Loading..." dummy item
        if item.childCount() == 1 and item.child(0).text(0) == "Loading...":
            # Remove the "Loading..." item
            item.takeChild(0)
            # Load the actual children
            self._load_folder_children(folder_path, item)
        elif item.childCount() == 0:
            # Load children if there are none
            self._load_folder_children(folder_path, item)
    
    def _load_folder_children(self, folder_path, parent_item):
        """
        Load children for a folder item
        """
        try:
            # List all subdirectories
            subdirs = []
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                if os.path.isdir(item_path):
                    subdirs.append(item_path)
                    
            # Sort alphabetically
            subdirs.sort()
            
            # Add each subdirectory as a child item
            for subdir in subdirs:
                dir_name = os.path.basename(subdir)
                child_item = QTreeWidgetItem(parent_item, [dir_name])
                child_item.setData(0, Qt.UserRole, subdir)
                self.folder_items[subdir] = child_item
                
                # Add a dummy child item to show the expand arrow if there are subdirectories
                try:
                    if any(os.path.isdir(os.path.join(subdir, d)) for d in os.listdir(subdir)):
                        dummy = QTreeWidgetItem(child_item, ["Loading..."])
                except (PermissionError, OSError):
                    pass
                
                # Files will be counted in _count_files_recursive later
                
        except (PermissionError, OSError) as e:
            # Skip folders we can't access
            print(f"Error accessing {folder_path}: {e}")
            error_item = QTreeWidgetItem(parent_item, ["Error: Access Denied"])
            error_item.setDisabled(True)
    
    def _count_files_recursive(self, folder_path):
        """
        Count files in all folders recursively and update the UI synchronously
        """
        # Count files in the base folder
        self._count_files_in_folder(folder_path)
        
        # Now count files in all subfolders
        try:
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                if os.path.isdir(item_path) and item_path in self.folder_items:
                    self._count_files_in_folder(item_path)
        except (PermissionError, OSError) as e:
            print(f"Error accessing subfolders in {folder_path}: {e}")
    
    def _count_files_in_folder(self, folder_path):
        """
        Count files in a single folder and update UI
        """
        # Skip if we've already counted files in this folder
        if folder_path in self.file_counts:
            return
            
        try:
            # Count files in this folder (only actual files, not subfolders or hidden files)
            file_count = 0
            
            # List all items in this folder
            try:
                for item in os.listdir(folder_path):
                    # Skip hidden files (starting with .)
                    if item.startswith('.'):
                        continue
                        
                    item_path = os.path.join(folder_path, item)
                    
                    # Only count actual files, not directories
                    if os.path.isfile(item_path):
                        # Make extra sure it's not a directory
                        if not os.path.isdir(item_path):
                            # Count this file
                            file_count += 1
                            
            except (PermissionError, OSError):
                # Skip folders we can't access
                print(f"Permission error accessing {folder_path}")
                self.file_counts[folder_path] = 0
                return
            
            # Store the results
            self.file_counts[folder_path] = file_count
            
            # Debug output
            print(f"Counted {file_count} files in {os.path.basename(folder_path)}")
            
            # Update UI directly
            self._update_folder_display(folder_path, file_count)
            
        except Exception as e:
            print(f"Error counting files in {folder_path}: {e}")
            self.file_counts[folder_path] = 0
    
    def _update_folder_display(self, folder_path, file_count):
        """
        Update the folder display in the tree widget (called in the UI thread)
        """
        # Get the item for this folder
        if folder_path not in self.folder_items:
            return
            
        item = self.folder_items[folder_path]
        
        # Update the item text
        folder_name = os.path.basename(folder_path)
        
        # Only show file count if it's greater than 0
        if file_count > 0:
            item.setText(0, f"{folder_name} ({file_count} files)")
        else:
            item.setText(0, folder_name)
        
        # If this item is currently selected, emit the selection signal
        if item.isSelected():
            self.selected_folder = folder_path
            self.folder_selected.emit(folder_path)
    
    def _find_and_select_best_folder(self):
        """
        Find and select the folder with the most files
        If no subfolders have files, select the base folder itself
        Also directly emit the folder_selected signal to update the input folder
        """
        if not self.root_path:
            return
            
        print("Finding folder with most files...")
        
        # First, gather all folder file counts
        folder_file_counts = {}
        
        # Add all folders we've counted
        for folder_path, count in self.file_counts.items():
            if folder_path.startswith(self.root_path):
                folder_file_counts[folder_path] = count
                print(f"Folder {os.path.basename(folder_path)}: {count} files")
        
        # Find the folder with the most files
        if not folder_file_counts:
            best_folder = self.root_path  # Default to root path if no file counts available
            print(f"No file counts available, using root path {self.root_path}")
        else:
            best_folder = max(folder_file_counts.items(), key=lambda x: x[1])[0]
            print(f"Best folder: {best_folder} with {folder_file_counts[best_folder]} files")
            
            # If the best folder has 0 files, use the root folder
            if folder_file_counts[best_folder] == 0:
                best_folder = self.root_path
                print(f"Best folder has 0 files, using root path {self.root_path}")
        
        # Select this folder directly and emit signal
        print(f"Selecting folder: {best_folder}")
        self._select_folder_in_tree(best_folder, emit_signal=True)
    
    def _select_folder_in_tree(self, folder_path, emit_signal=False):
        """
        Select a folder in the tree
        
        Args:
            folder_path: Path to the folder to select
            emit_signal: Whether to emit the folder_selected signal (default: False)
                         Used to trigger folder selection handling when auto-selecting best folder
        """
        if folder_path not in self.folder_items:
            return
            
        # Get the item and select it
        item = self.folder_items[folder_path]
        self.tree_widget.setCurrentItem(item)
        
        # Ensure it's visible
        self.tree_widget.scrollToItem(item)
        
        # Make sure parents are expanded
        parent = item.parent()
        while parent:
            self.tree_widget.expandItem(parent)
            parent = parent.parent()
            
        # Update the selected folder
        self.selected_folder = folder_path
        
        # Only emit signal if explicitly requested or if the item is selected by user interaction
        # This prevents duplicate signals when the tree selection change already emits the signal
        if emit_signal:
            self.folder_selected.emit(folder_path)
    
    def get_selected_folder(self):
        """
        Get the currently selected folder
        """
        return self.selected_folder