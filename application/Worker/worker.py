# -*- coding: utf-8 -*-
"""
@File    :   worker.py
@Time    :   2025/07/18
@Author  :   Sunil Samuel
@Version :   1.0
@Contact :   sgs@sunilsamuel.com
"""

import logging
from logging import Logger
from PySide6.QtCore import QThread, Signal
from Processor.process_directory import ProcessDirectory
from Processor.process_image import ProcessImage
from MainWindow.processing_options import ProcessingOptions


class Worker(QThread):
    """
    A worker thread to simulate a long-running task and send progress updates.
    Uses PySide6's Signal.
    """

    progress: Signal = Signal(int)
    log_message: Signal = Signal(str, str)
    finished: Signal = Signal()

    # Lazy loading to show splash page
    __process_image: ProcessImage = ProcessImage()

    # This flag is used to stop the worker while it's running.
    __is_running = True

    __dir: str = None
    __move_dir: str = None
    __options: dict[str, bool] = None
    __logger: Logger = logging.getLogger(__file__)

    def __init__(
        self,
        process_image: ProcessImage,
        dir: str,
        move_dir: str,
        options: dict[str, bool],
    ) -> None:
        super().__init__()
        self.__dir = dir
        self.__move_dir = move_dir
        self.__options = options
        self.__process_image = process_image

    def setStop(self) -> None:
        self.__is_running = False

    def run(self):
        """
        Simulates a task by emitting progress and log messages.
        """

        self.log_message.emit("Starting background task...", "default")

        if not self.__process_image:
            self.__process_image = ProcessImage()

        file_list: list[str] = list(
            ProcessDirectory().pre_process_directory(
                self.__dir, self.__options[ProcessingOptions.RECURSE_DIRECTORY.name]
            )
        )
        total_files: int = len(file_list)
        self.log_message.emit(f"Total files = [{total_files}]", "default")

        for index, filename in enumerate(file_list):
            if not self.__is_running:
                self.log_message.emit("User interrupted ...", "error")
                return

            self.log_message.emit("hr", "hr")

            self.log_message.emit(f"Processing File [{filename}]", "header")
            self.__process_image.init(filename)
            self.__process_move_files(filename)
            self.__process_classify_image(filename)
            self.__process_created_date(filename)

            self.log_message.emit(f"Processing file {filename}", "default")
            self.__logger.info(f"Processing file [{filename}]")
            self.progress.emit(index / total_files * 100)

        self.log_message.emit("Background task finished.", "default")

    def __process_created_date(self, filename: str) -> None:
        create_date: bool = self.__options[ProcessingOptions.CREATED_DATE.name]
        self.log_message.emit(
            f"Process Created Date for image [{filename}] - [{create_date}]", "default"
        )
        if create_date:
            flag, new_filename = self.__process_image.process_created_date()
            self.__emit_process_status(
                flag,
                f"Successfully renamed file [{filename}] to [{new_filename}]",
                f"File [{new_filename}] already has date.  Therefore, not processing file.",
                "Created Date",
            )

    def __process_classify_image(self, filename: str) -> None:
        classify_image: bool = self.__options[ProcessingOptions.CLASSIFY_IMAGE.name]
        self.log_message.emit(f"Process Classify Image -[{classify_image}]", "default")
        if classify_image:
            flag, description = self.__process_image.process_classify_image_to_text(
                self.__options["ai_level"]
            )
            self.__emit_process_status(
                flag,
                f"Successfully classified image {[filename]} with [{description}]",
                f"Could not classify image [{filename}] with error [{description}]",
                "Classify Image",
            )

    def __process_move_files(self, filename: str) -> None:
        process_file: bool = (
            self.__options[ProcessingOptions.MOVE_FILES.name]
            or self.__options[ProcessingOptions.COPY_FILES.name]
        )
        self.log_message.emit(f"Process Move Files = [{process_file}]", "default")
        if process_file:
            flag, new_filename = self.__process_image.process_move_image_to_folder(
                self.__options[ProcessingOptions.MOVE_FILES.name],
                self.__options[ProcessingOptions.COPY_FILES.name],
                self.__move_dir,
                self.__options[ProcessingOptions.CREATE_MONTH_FOLDER.name],
            )
            self.__emit_process_status(
                flag,
                f"Successfully moved/copied file [{filename}] to [{new_filename}]",
                f"Could not move/copy file [{filename}] with error [{new_filename}]",
                "Move/Copy File",
            )

    def __emit_process_status(
        self, process_status: bool, msg_success: str, msg_fail: str, process_name: str
    ) -> None:
        if process_status:
            self.log_message.emit(f"{process_name} -> {msg_success}", "default")
        else:
            self.log_message.emit(f"{process_name} -> {msg_fail}", "error")
