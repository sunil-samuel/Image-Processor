# -*- coding: utf-8 -*-
"""
@File    :   process_directory.py
@Time    :   2025/07/18
@Author  :   Sunil Samuel
@Version :   1.0
@Contact :   sgs@sunilsamuel.com
"""

import logging, os
from logging import Logger
from typing import Generator


class ProcessDirectory:
    """
    This class will process the given root directory and traverse
    the directory recursively or not based on the parameters provided.
    The class will then process the individual image files
    """

    __logger: Logger = logging.getLogger(__name__)

    ############################################################################
    # pre_process_directory
    ############################################################################
    def pre_process_directory(
        self, root_dir: str, recurse: bool = True
    ) -> Generator[str, None, None]:
        """
        Given the root directory, process the files, either recursively or not.
        """

        self.__logger.debug(f"Root dir [{root_dir}] recurse [{recurse}]")

        if not os.path.isdir(root_dir):
            self.__logger.error(
                f"The directory provided [{root_dir}] is not a valid directory"
            )
            raise NotADirectoryError(
                f"The directory provided [{root_dir}] is not a valid directory"
            )

        for root, _, files in os.walk(root_dir):
            for filename in files:
                if self._is_valid_image(filename):
                    file_path: str = os.path.join(root, filename)
                    self.__logger.debug(f"Processing file {file_path}")
                    yield file_path
            if not recurse:
                self.__logger.debug(
                    f"Only processing first level directory since recursive is {recurse}"
                )
                return

    ############################################################################
    # _is_valid_image
    ############################################################################
    def _is_valid_image(self, filename: str) -> bool:
        """
        Given the name of the file, validate the name as an image or not.
        Args:
            filename (str): File to inspect to see if it's an image.
        Returns:
            bool: True - if image, flase - not an image
        """
        is_valid_image: bool = filename.lower().endswith(
            (".jpg", ".jpeg", ".tiff", ".png", ".gif", ".webp", ".heic")
        )
        self.__logger.debug(
            f"Checking file is valid image [{filename}] -> [{is_valid_image}]"
        )
        return is_valid_image
