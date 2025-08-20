# -*- coding: utf-8 -*-
"""
@File    :   process_image.py
@Time    :   2025/07/18
@Author  :   Sunil Samuel
@Version :   1.0
@Contact :   sgs@sunilsamuel.com
"""


import logging, shutil, datetime, os, re, piexif, sys
from logging import Logger
from typing import Any

from .AIProessor.image_to_text import ImageToText
from piexif import helper as pi_helper

# Check if the operating system is Windows
if sys.platform == "win32":
    try:
        # Attempt to import the Windows-specific module
        import win32file
        import win32con
        import pywintypes

        print("Successfully imported Windows-specific modules.")
    except ImportError:
        print("Could not import pywin32. Please install it with 'pip install pywin32'")
        sys.exit(1)


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
    __image_to_text = None

    ############################################################################
    # __init__
    ############################################################################
    def __init__(self) -> None:
        None

    def get_filepath(self) -> str:
        return self.__filepath

    def get_original_filepath(self) -> str:
        return self.__original_filepath

    def post_process(self) -> None:
        self.__image_to_text = ImageToText()

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
        self._get_gps_information()

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
            self._rename_file_with_timestamp()
            self._update_create_date_of_file()
            self._update_create_date_of_file_windows()
            return True, self.__filepath
        except Exception as e:
            self.__logger.warning(
                f"Could not process created date for file [{self.__filepath}].  {e}"
            )
            return False, self.__filepath

    # ===========================================================================
    # classify_image_to_text :: public interface
    # ===========================================================================
    def process_classify_image_to_text(self, level: str) -> tuple[bool, str]:
        """
        Create a description for this image using AI.

        Returns:
            tuple[bool, str]: Status and updated file name e.g., [False, filename]
        """

        try:
            # Generate the AI description of the image
            description: list[str] = self.__image_to_text.process(
                self.__filepath, level
            )

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
        creation_time: datetime.datetime = datetime.datetime.fromtimestamp(
            creation_timestamp
        )
        self.__logger.info(
            f"Creation datetime for file [{self.__filepath} => [{creation_time}]"
        )
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

    def _get_gps_information(self) -> None:

        # DMS - Degrees, Minutes, and Seconds
        # REF - Direction such as 'S', 'W'
        self.__lat_dms = None
        self.__lat_ref = None
        self.__lon_dms = None
        self.__lon_ref = None
        self.__lat_decimal = None
        self.__lon_decimal = None

        # Check if the 'GPS' tag exists in the EXIF data
        if piexif.GPSIFD.GPSLatitude not in self.__exif_dict["GPS"]:
            self.__logger.info(
                f"GPS information was not found for file [{self.__filename}]"
            )
            return None
        # Get the raw GPS data
        gps_data = self.__exif_dict["GPS"]

        self.__lat_dms = gps_data[piexif.GPSIFD.GPSLatitude]
        self.__lat_ref = gps_data[piexif.GPSIFD.GPSLatitudeRef].decode("utf-8")
        self.__lon_dms = gps_data[piexif.GPSIFD.GPSLongitude]
        self.__lon_ref = gps_data[piexif.GPSIFD.GPSLongitudeRef].decode("utf-8")
        self.__lat_decimal = self._dms_to_decimal(self.__lat_dms, self.__lat_ref)
        self.__lon_decimal = self._dms_to_decimal(self.__lon_dms, self.__lon_ref)

        self.__logger.info(f"Latitude and longitude for file [{self.__filepath}]")
        self.__logger.info(f"\t\t__lat_dms: [{self.__lat_dms}]")
        self.__logger.info(f"\t\t__lat_ref: [{self.__lat_ref}]")
        self.__logger.info(f"\t\t__lon_dms: [{self.__lon_dms}]")
        self.__logger.info(f"\t\t__lon_ref: [{self.__lon_ref}]")
        self.__logger.info(f"\t\t__lat_decimal: [{self.__lat_decimal}]")
        self.__logger.info(f"\t\t__lon_decimal: [{self.__lon_decimal}]")

    def _dms_to_decimal(self, dms, ref):
        degrees = dms[0][0] / dms[0][1]
        minutes = dms[1][0] / dms[1][1] / 60.0
        seconds = dms[2][0] / dms[2][1] / 3600.0

        decimal_val = degrees + minutes + seconds

        if ref in ["S", "W"]:
            decimal_val = -decimal_val

        return decimal_val

    ############################################################################
    # _rename_file_with_timestamp
    ############################################################################
    def _rename_file_with_timestamp(self) -> None:
        """
        Get the date from exif tag and prefix the filename with this date.

        Returns:
            datetime.datetime: Date and time from the exif metadata
        """

        self._remove_datetime_prefix_from_filename()
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
        self.__logger.info(
            f"Updating timestamp for file [{self.__filepath}] ({timestamp})"
        )
        os.utime(self.__filepath, (timestamp, timestamp))

    def _update_create_date_of_file_windows(self) -> None:
        self.__logger.info("Windows updating creation date")
        if sys.platform == "win32":
            # Convert the Python datetime into a pywintypes TIME object
            pywin_create_date = pywintypes.Time(self.__created_date)

            # Get a "handle" to the file to perform operations on it
            file_handle = win32file.CreateFile(
                self.__filepath,
                win32con.GENERIC_WRITE,
                win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
                None,
                win32con.OPEN_EXISTING,
                win32con.FILE_ATTRIBUTE_NORMAL,
                None,
            )

            # Set the file's time (creation, access, modification)
            # We pass the new time for the first argument (creation time)
            # and None for the others to leave them unchanged.
            win32file.SetFileTime(file_handle, pywin_create_date, None, None)

            # Close the handle to release the file
            file_handle.close()
            self.__logger.info(
                f"Windows creation time has been update for [{self.__filepath}]"
            )

    def _remove_datetime_prefix_from_filename(self) -> None:
        """
        Removes a date and/or time prefix from a filename string.

        Args:
            filename (str): The original filename.

        Returns:
            str: The filename with the datetime prefix removed.
        """
        # A list of regex patterns to match various date/time formats at the start of a string.
        # You can add more patterns to this list to suit your needs.
        datetime_patterns = [
            # Matches YYYY-MM-DD HH-MM-SS, YYYY_MM_DD-HH.MM, etc.
            r"\d{4}[-_\. ]?\d{1,2}[-_\. ]?\d{1,2}[-_\. ]?\d{1,2}[-_\.: ]?\d{1,2}[-_\.: ]?\d{1,2}",
            # Matches YYYY-MM-DD, YYYY_MM_DD, YYYY.MM.DD
            r"\d{4}[-_\.]\d{1,2}[-_\.]\d{1,2}",
            # Matches YYYYMMDDHHMMSS
            r"\d{14}",
            # Matches YYYYMMDD
            r"\d{8}",
        ]

        # Combine all patterns into a single regex, joined by '|' (OR).
        # ^                  - Anchors the search to the beginning of the string.
        # (...)              - A capturing group for all our patterns.
        # \s*[-_]?\s* - Matches any space, hyphen, or underscore after the date/time.
        combined_pattern = re.compile(
            r"^(" + "|".join(datetime_patterns) + r")\s*[-_]?\s*"
        )

        # Use re.sub() to replace the matched pattern with an empty string.
        cleaned_filename = combined_pattern.sub("", self.__filename)
        self.__logger.info(f"Cleaning file [{self.__filename}] to [{cleaned_filename}]")
        self.__filename = cleaned_filename
