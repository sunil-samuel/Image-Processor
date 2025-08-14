# -*- coding: utf-8 -*-
"""
@File    :   process_image.py
@Time    :   2025/07/18
@Author  :   Sunil Samuel
@Version :   1.0
@Contact :   sgs@sunilsamuel.com
"""

import logging, shutil, datetime, os, re, piexif
from logging import Logger
from typing import Any

from .AIProessor.image_to_text import ImageToText
from piexif import helper as pi_helper


class ProcessImage:
    """
    Given the full path to the image file, process the file and update
    the filename and created time.
    """

    __logger: Logger = logging.getLogger(__name__)
    __filepath: str = None
    __original_filepath: str = None
    __directory: str = None
    __filename: str = None
    __created_date: datetime.datetime = None
    __exif_dict: dict[str, Any] = None
    __platform: str = None
    __file_prefix_format: str = "%Y-%m-%d_%H.%M.%S"
    __file_prefix_pattern: str = r"\d{4}-\d{2}-\d{2}"
    __image_to_text = ImageToText()

    ############################################################################
    # __init__
    ############################################################################
    def __init__(self) -> None:
        None

    def get_filepath(self) -> str:
        return self.__filepath

    def get_original_filepath(self) -> str:
        return self.__original_filepath

    def init(self, filepath: str) -> None:
        self.__filepath = filepath
        self.__original_filepath = filepath
        self.__directory, self.__filename = os.path.split(self.__filepath)
        try:
            self.__exif_dict = piexif.load(self.__filepath)
        except:
            self.__exif_dict = {
                "0th": {},
                "Exif": {},
                "GPS": {},
                "1st": {},
                "thumbnail": None,
            }

        self.__created_date = (
            self._get_date_from_exif()
            or self._get_date_from_filename()
            or self._get_date_from_file_created_date()
        )

        self.__logger.info(
            f"Created date for file [{self.__filepath}] => [{self.__created_date}]"
        )


    # ===========================================================================
    # process_created_date :: public interface
    # ===========================================================================
    def process_created_date(self) -> tuple[bool, str]:
        """
        Update the create date of the file with the 'date taken' exif date.
        """

        try:
            # Do not format if the file already starts with this date.
            if not re.match(self.__file_prefix_pattern, self.__filename):
                self._rename_file_with_timestamp()
                self._update_create_date_of_file()
                return True, self.__filepath
            else:
                self.__logger.info(
                    f"The filename {self.__filepath} already starts with the date."
                )
                return False, self.__filepath
        except Exception as e:
            self.__logger.warning(
                f"Could not process created date for file [{self.__filepath}]"
            )
            return False, self.__filepath

    # ===========================================================================
    # classify_image_to_text :: public interface
    # ===========================================================================
    def process_classify_image_to_text(self) -> tuple[bool, str]:
        """
        Create a description for this image using AI.

        Returns:
            tuple[bool, str]: Status and updated file name e.g., [False, filename]
        """

        try:
            # Generate the AI description of the image
            description: list[str] = self.__image_to_text.process(self.__filepath)

            # Get any existing comments
            comment: str = self._get_user_comment_from_exif()
            # If there is existing comment(s), we want to make sure we are not adding
            # the same comment.
            if comment:
                filtered_comment = [item for item in description if item not in comment]
                self.__logger.info(f"Filtered list is [{filtered_comment}]")
                # filtered_comment.append(comment)
                description = filtered_comment

            description_str: str = ". ".join(description) + "."
            self.__logger.info(
                f"Comments for file {[self.__filepath]} is [{description}] string is [{description_str}]"
            )
            status: bool = self._write_exif_comment(description_str)
            return status, description_str
        except Exception as e:
            self.__logger.warning(
                f"Could not process classify image to text for file [{self.__filepath}]. [{e}]"
            )
            return False, f"Could not classify image [{self.__filepath}]"

    # ===========================================================================
    # process_move_image_to_folder :: public interface
    # ===========================================================================
    def process_move_image_to_folder(
        self, move: bool, copy: bool, dest_dir: str, create_month_folder: bool = False
    ) -> tuple[bool, str]:
        self.__logger.info(
            f"Move [{move}] | copy [{copy}] file [{self.__filepath}] to [{dest_dir}] - creating month folder [{create_month_folder}]"
        )

        try:
            year: int = self.__created_date.year
            self.__logger.info(f"Creating directory [{year}] within $[{dest_dir}]")
            dest_dir_with_date = os.path.join(dest_dir, str(year))
            if create_month_folder:
                dest_dir_with_date = os.path.join(
                    dest_dir_with_date, self.__created_date.strftime("%m-%B")
                )
            os.makedirs(dest_dir_with_date, exist_ok=True)
            self.__logger.info(
                f"Created directory with date time [{dest_dir_with_date}]"
            )
            try:
                # -- Copy or Move the file --
                if move:
                    shutil.move(self.__filepath, dest_dir_with_date)
                else:
                    shutil.copy2(self.__filepath, dest_dir_with_date)
                self.__filepath = os.path.join(dest_dir_with_date, self.__filename)
                self.__directory, self.__filename = os.path.split(self.__filepath)
                self.__logger.info(f"New filepath is [{self.__filepath}]")
            except FileNotFoundError:
                self.__logger.warning(f"File [{self.__filepath}] was not found")
            except Exception as e:
                self.__logger.warning(
                    f"Error moving or copying file [{self.__filepath}]. {e}"
                )
            return True, self.__filepath
        except Exception as e:
            self.__logger.warning(
                f"Could not process move image to folder for file [{self.__filepath}] [{e}]"
            )
            return False, self.__filepath

    ############################################################################
    # _get_date_from_exif
    ############################################################################
    def _get_date_from_exif(self) -> datetime.datetime | None:
        """
        Check if the exif for this image has the date.

        Returns:
            datetime.datetime | None: The date from exif
        """
        try:
            date: str = None
            date_raw: bytes = self.__exif_dict["Exif"].get(
                piexif.ExifIFD.DateTimeOriginal
            ) or self.__exif_dict["Exif"].get(piexif.ExifIFD.DateTimeDigitized)
            if not date_raw:
                return None
            date = date_raw.decode("utf-8")
            converted: datetime.datetime = self._convert_time(date)
            self.__logger.info(
                f"EXIF date from file [{self.__filepath}] => [{date}] converted is [{converted}]"
            )
            return converted
        except Exception as e:
            self.__logger.info(
                f"Could not find date from EXIF for file [{self.__filepath}] => [{e}]"
            )
            return None

    ############################################################################
    # _get_date_from_filename
    ############################################################################
    def _get_date_from_filename(self) -> datetime.datetime | None:
        """
        Check if the name of the file contains the date and time.

        Returns:
            datetime.datetime | None: File datetime
        """
        # ^      - asserts position at start of the string
        # \d{4}  - matches exactly four digits (the year)
        # \d{2}  - matches exactly two digits (the month)
        # \d{2}  - matches exactly two digits (the day)
        patterns: list[str] = (
            r"^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})",  # YYYYMMDD_HHMMSS
            r"^(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})",  # YYYY-MM-DD_HH-MM-SS
            r"^(\d{4})(\d{2})(\d{2})",  # YYYYMMDD
            r"^(\d{4})-(\d{2})-(\d{2})",  # YYYY-MM-DD
        )

        for pattern in patterns:
            match = re.match(pattern, self.__filename)
            self.__logger.info(
                f"Checking filename date matches [{pattern}] => [{self.__filepath}]"
            )
            if match:
                if match.lastindex == 6:
                    year, month, day, hour, min, sec = match.groups()
                    file_date: datetime.datetime = datetime.datetime(
                        int(year), int(month), int(day), int(hour), int(min), int(sec)
                    )
                    self.__logger.info(
                        f"Filename Pattern datetime for file [{self.__filepath}] => [{file_date}]"
                    )
                    return file_date
                elif match.lastindex == 3:
                    year, month, day = match.groups()
                    file_date: datetime.datetime = datetime.datetime(
                        int(year), int(month), int(day)
                    )
                    self.__logger.info(
                        f"Filename Pattern datetime for file [{self.__filepath}] => [{file_date}]"
                    )
                    return file_date
        return None

    ############################################################################
    # _get_date_from_file_created_date
    ############################################################################
    def _get_date_from_file_created_date(self) -> datetime.datetime:
        """
        Find out the creation date of the file irrespective of the platform.

        Returns:
            datetime.datetime: Creation date
        """

        if self.__platform == "Windows":
            # On Windows, getctime() returns the creation time
            creation_timestamp = os.path.getctime(self.__filepath)
        else:
            # On Unix-based systems (macOS, Linux), we need to use st_birthtime
            stat_info: os.stat_result = os.stat(self.__filepath)
            creation_timestamp = stat_info.st_ctime
        self.__logger.info(
            f"Creation timestamp for file [{self.__filepath}] is [{creation_timestamp}]"
        )
        creation_time:datetime.datetime = datetime.datetime.fromtimestamp(creation_timestamp)
        self.__logger.info(f"Creation datetime for file [{self.__filepath} => [{creation_time}]")
        return creation_time

    ############################################################################
    # _convert_time
    ############################################################################
    def _convert_time(self, timestamp: str) -> datetime.datetime | None:
        """
        Given a text form a datetime, convert that to a valid datetime object
        that can be used to process time objects.
        Args:
            timestamp (str): String representation of date time to be converted
        Returns:
            datetime.datetime | None: Return the converted datetime
        """

        if isinstance(timestamp, datetime.datetime):
            return timestamp

        for format in [
            "%Y:%m:%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
        ]:
            try:
                self.__logger.info(
                    f"Attempting to format timestamp [{timestamp}] with format [{format}]"
                )
                return datetime.datetime.strptime(timestamp, format)
            except Exception as e:
                self.__logger.info(
                    f"Could not convert timestamp [{timestamp}] with format [{format}].  Exception [{e}]"
                )
        # If we are here, then we could not convert the given date format.
        self.__logger.warning(
            f"The timestamp provided [{timestamp}] was not successfully converted."
        )
        raise Exception(
            f"Timestamp [{timestamp}] could not be converted given the formats."
        )

    ############################################################################
    # _create_new_filename
    ############################################################################
    def _create_new_filename(self, formatted_date: str) -> str:
        """
        Given the date associated with the file, create a new file with the
        date as prefix to the filename.
        Args:
            date (datetime.datetime): The file date
        Returns:
            str: The new updated filename
        """

        new_filename = os.path.join(
            self.__directory, formatted_date + "_" + self.__filename
        )
        self.__logger.info(f"Filename [{self.__filepath}] => [{new_filename}]")
        return new_filename

    ############################################################################
    # _get_user_comment_from_exif
    ############################################################################
    def _get_user_comment_from_exif(self) -> str | None:
        """
        Get the user comment EXIF tag from the file.

        Returns:
            str | None: Return the user comment if it exists
        """

        try:
            user_comment_raw = self.__exif_dict["Exif"].get(piexif.ExifIFD.UserComment)

            if user_comment_raw:
                # Use the piexif helper to correctly decode the comment

                decoded_comment = pi_helper.UserComment.load(user_comment_raw)
                self.__logger.debug(f"UserComment is [{decoded_comment}]")
                return decoded_comment
            else:
                return None
        except Exception as e:
            self.__logger.warning(f"Could not read comment: {e}")
            return None

    ############################################################################
    # _write_exif_comment
    ############################################################################
    def _write_exif_comment(self, new_comment: str) -> bool:
        """
        Loads an image, writes a comment to its EXIF data, and saves it to a new file
        using only the piexif library.

        Args:
            image_path (str): The path to the source image.
            new_comment (str): The comment string to write.
            output_path (str): The path to save the modified image.
        """

        try:
            encoded_comment = str(new_comment)
            self.__exif_dict["Exif"][piexif.ExifIFD.UserComment] = (
                pi_helper.UserComment.dump(
                    encoded_comment,
                    encoding="unicode",  # Use 'unicode' for broader character support
                )
            )

            # Convert the EXIF dictionary back into bytes
            exif_bytes = piexif.dump(self.__exif_dict)

            # Insert the new EXIF data into the new file, overwriting it.
            piexif.insert(exif_bytes, self.__filepath)
            self.__logger.info(f"Successfully wrote comment to '{self.__filepath}'")
            return True

        except FileNotFoundError:
            self.__logger.warning(f"Error: The file '{self.__filepath}' was not found.")
            return False
        except Exception as e:
            self.__logger.warning(f"An error occurred: {e}")
            return False

    ############################################################################
    # _rename_file_with_timestamp
    ############################################################################
    def _rename_file_with_timestamp(self) -> None:
        """
        Get the date from exif tag and prefix the filename with this date.

        Returns:
            datetime.datetime: Date and time from the exif metadata
        """

        formatted_date: str = self.__created_date.strftime(self.__file_prefix_format)
        new_filename: str = self._create_new_filename(formatted_date)
        self.__logger.info(f"Renaming file [{self.__filepath}] -> [{new_filename}]")
        os.rename(self.__filepath, new_filename)
        self.__filepath = new_filename

    ############################################################################
    # _update_create_date_of_file
    ############################################################################
    def _update_create_date_of_file(self) -> None:
        """
        Update the access and modified times with the provided time.
        """

        self.__logger.info(
            f"Updating file {[self.__filepath]} with date [{self.__created_date}]"
        )

        # Convert the datetime object to a Unix timestamp (seconds since epoch)
        timestamp: float = self.__created_date.timestamp()

        # os.utime takes a tuple of (atime, mtime)
        # atime = access time, mtime = modification time
        os.utime(self.__filepath, (timestamp, timestamp))
