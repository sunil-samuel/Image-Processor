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

import sys, logging, os
from logging import Logger
from PySide6.QtWidgets import QApplication
import Helper.file_to_string as helper
from MainWindow.new_window import MainWindow

from PySide6.QtWidgets import QApplication

# The 'resources_rc' import is required.
import resources_rc


#
# pyi_splash is only available if the application is created using
# PyInstaller.  The module will be available when we compile it.
# Otherwise, we'll ignore it.
#
try:
    import pyi_splash
except:
    pass


def splash_update_text(text: str) -> None:
    try:
        pyi_splash.update_text(text)
    except:
        pass


def splash_close() -> None:
    try:
        pyi_splash.close()
    except:
        pass


if __name__ == "__main__":
    splash_update_text("Starting application ...")

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

    splash_update_text("Starting QApplication ...")
    app: QApplication = QApplication(sys.argv)

    app.processEvents()

    app.setStyleSheet(
        helper.read_style_file_from_resource(":/app_stylesheet.qss", logger)
    )
    splash_update_text("Starting main window ...")
    main_app: MainWindow = MainWindow(root_dir)
    splash_close()

    main_app.show()

    sys.exit(app.exec())
