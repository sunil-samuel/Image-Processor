import sys
import time
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QMainWindow
from PySide6.QtGui import QPixmap, QMouseEvent
from PySide6.QtCore import Qt, QPoint

# --- 1. Import your compiled resource file ---
# This makes all the resource paths available.
import resources_rc


class MovableSplash(QWidget):
    """
    A movable splash screen that displays an image centered
    within a larger, fixed-size window.
    """

    def __init__(self, image_resource_path):
        super().__init__()
        # self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)

        # 1. Set a fixed size for the window, larger than the image.
        self.setFixedHeight(800)
        # 2. Apply a background color to the window itself.
        self.setStyleSheet("background-color: #2c3e50;")  # A dark blue

        # Load the original image from resources
        original_pixmap = QPixmap(image_resource_path)

        # Scale the image to a desired size (e.g., 200px height)
        self.pixmap = original_pixmap.scaledToHeight(
            800, Qt.TransformationMode.SmoothTransformation
        )

        # Create the label to hold the image
        self.label = QLabel(self)
        self.label.setPixmap(self.pixmap)

        # 3. Center the label's content (the pixmap) within the window.
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Set up the layout to make the label fill the entire window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)

        # Variable to handle window dragging
        self.drag_position = QPoint()

    def mousePressEvent(self, event: QMouseEvent):
        """Captures the mouse click position to prepare for dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        """Moves the window when the left mouse button is held down."""
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
