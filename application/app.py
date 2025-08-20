# -*- coding: utf-8 -*-
"""
@File    :   app.py
@Time    :   2025/07/18
@Author  :   Sunil Samuel
@Version :   1.0
@Contact :   sgs@sunilsamuel.com
@Desc    :   This application traverses the given directory looking for images
             and the EXIF information, specifically the 'taken date'.  If the
             file has this meta data, then the file's 'created date' will be
             changed to this 'taken date' and the name of the file will be
             modified to contain this date. This is used to sort the files
             according to the age of the image.
"""

import sys, logging, os, time
from logging import Logger
import Helper.file_to_string as helper
from MainWindow.new_window import MainWindow

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap

# The 'resources_rc' import is required.
import resources_rc

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
        filename="image_processor.log",
        # Remove the file, if it exists.
        filemode="w",
    )

    logger: Logger = logging.getLogger(__name__)
    root_dir: str = os.path.dirname(__file__)
    logger.info("Starting the application")

    app: QApplication = QApplication(sys.argv)

    logger.info("Starting splash page")

    # 1. Load your splash image from resources.
    pixmap: QPixmap = QPixmap(":/splash_screen.png")
    scaled_pixmap = pixmap.scaledToHeight(
        800, Qt.TransformationMode.SmoothTransformation
    )

    splash: QSplashScreen = QSplashScreen(scaled_pixmap)

    screen_geometry = app.primaryScreen().geometry()
    center_point = screen_geometry.center() - splash.geometry().center()
    splash.move(center_point)

    splash.show()

    logger.info("Splash is showing now")
    splash.showMessage(
        "Loading application components...",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
        Qt.GlobalColor.black,
    )
    app.processEvents()
    time.sleep(2)

    app.setStyleSheet(
        helper.read_style_file_from_resource(":/app_stylesheet.qss", logger)
    )
    main_app: MainWindow = MainWindow(root_dir)
    main_app.show()
    main_app.post_process()
    splash.finish(main_app.get_window())

    sys.exit(app.exec())
