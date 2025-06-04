from PyQt5.QtWidgets import QMainWindow, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

class MetadataWindow(QMainWindow):
    """
    Window for displaying DICOM metadata
    """
    def __init__(self, metadata=None):
        super().__init__()
        self.setWindowTitle("DICOM Metadata")
        self.setGeometry(150, 150, 800, 600)
        
        # Create a central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        layout = QVBoxLayout(central_widget)
        
        # Create tree widget to display metadata
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Tag", "Value"])
        self.tree.setColumnWidth(0, 300)
        layout.addWidget(self.tree)
        
        # Set metadata if provided
        if metadata:
            self.set_metadata(metadata)
    
    def set_metadata(self, metadata):
        """
        Set the metadata to display in the tree view
        
        Args:
            metadata: Dictionary of DICOM metadata (can be nested)
        """
        self.tree.clear()
        
        if not metadata:
            item = QTreeWidgetItem(["No metadata available", ""])
            self.tree.addTopLevelItem(item)
            return
        
        # Define the preferred order for top-level categories
        category_order = [
            "File Information",
            "Patient Information", 
            "Study Information", 
            "Series Information", 
            "Image Information", 
            "Other Attributes"
        ]
        
        # Add categories in the preferred order
        for category in category_order:
            if category in metadata:
                item = QTreeWidgetItem(self.tree)
                item.setText(0, category)
                item.setText(1, f"{len(metadata[category])} items")
                
                # Add sorted items within this category
                self._add_dict_to_tree(metadata[category], item)
                self.tree.addTopLevelItem(item)
        
        # Add any other categories not in the preferred order
        for category, values in metadata.items():
            if category not in category_order:
                item = QTreeWidgetItem(self.tree)
                item.setText(0, category)
                item.setText(1, f"{len(values)} items")
                
                # Add sorted items within this category
                self._add_dict_to_tree(values, item)
                self.tree.addTopLevelItem(item)
        
        # Expand all items
        self.tree.expandAll()
    
    def _add_dict_to_tree(self, data, parent_item):
        """
        Recursively add dictionary data to the tree widget
        
        Args:
            data: Dictionary to add
            parent_item: Parent tree item or None for top level
        """
        # Sort the keys alphabetically
        sorted_items = sorted(data.items(), key=lambda x: str(x[0]).lower())
        
        for key, value in sorted_items:
            if parent_item is None:
                item = QTreeWidgetItem(self.tree)
            else:
                item = QTreeWidgetItem(parent_item)
                
            # Set tag/key
            item.setText(0, str(key))
            
            # Handle different value types
            if isinstance(value, dict):
                # For dictionaries, create a branch and add children
                item.setText(1, f"{len(value)} items")
                self._add_dict_to_tree(value, item)
            elif isinstance(value, list):
                # For lists, create a branch and add each item
                item.setText(1, f"{len(value)} items")
                for i, list_item in enumerate(value):
                    child = QTreeWidgetItem(item)
                    child.setText(0, f"[{i}]")
                    
                    if isinstance(list_item, dict):
                        child.setText(1, f"{len(list_item)} items")
                        self._add_dict_to_tree(list_item, child)
                    else:
                        child.setText(1, str(list_item))
            else:
                # For simple values, just add the value
                item.setText(1, str(value))
                
            if parent_item is None:
                self.tree.addTopLevelItem(item)