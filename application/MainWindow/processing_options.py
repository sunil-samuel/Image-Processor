from enum import Enum


class ProcessingOptions(Enum):
    CREATED_DATE = {
        "objectName": "add_created_date",
        "title": "Add Created Date",
        "description": "Updated created date based on the 'taken date' of the picture",
        "checked": True,
        "enabled": True,
    }
    RECURSE_DIRECTORY = {
        "objectName": "open_sub_folders",
        "title": "Open Sub-Folders",
        "description": "Traverse all of the sub-folders in addition to the root directory",
        "checked": True,
        "enabled": True,
    }
    MOVE_FILES = {
        "objectName": "move_files",
        "title": "Move Files",
        "description": "Move the files into a directory based on year in the format YYYY",
        "checked": False,
        "enabled": True,
    }
    COPY_FILES = {
        "objectName": "copy_files",
        "title": "Copy Files",
        "description": "Instead of moving files, copy the files into a directory based on year in the format YYYY",
        "checked": False,
        "enabled": True,
    }
    CREATE_MONTH_FOLDER = {
        "objectName": "create_month_folder",
        "title": "Create Month Folder",
        "description": "If moving or copying files, then create sub-folders inside the year folder representing the month",
        "checked": False,
        "enabled": False,
    }
    CLASSIFY_IMAGE = {
        "objectName": "ai_description",
        "title": "AI Description",
        "description": "Use AI to dynamically analyze the image and create descriptions",
        "checked": True,
        "enabled": True,
    }
