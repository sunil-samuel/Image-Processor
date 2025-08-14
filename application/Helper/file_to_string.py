from logging import Logger
from PySide6.QtCore import QFile, QTextStream
from PySide6.QtCore import QDir


def read_style_file(filepath: str, logger: Logger) -> str:
    """
    Read the style relative to the application and return
    the entire content of the style as a string.

    Returns:
        str: The entire content of style sheet.
    """

    logger.info(f"Using style file path : {filepath}")
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError as e:
        logger.warning(f"Could not open the file {filepath}.  {e}")
    except Exception as e:
        logger.warning(f"An error occurred: {e}")


def read_style_file_from_resource(filepath: str, logger: Logger) -> str | None:
    """
    Read a file from the resource file, .qrc

    Args:
        filepath (str): Path of the file
        logger (Logger): Logger

    Returns:
        str: Content from the file
    """

    logger.info(f"Loading file [{filepath}] from resources.")
    file: QFile = QFile(filepath)
    if file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
        stream: QTextStream = QTextStream(file)
        stylesheet: str = stream.readAll()
        file.close()
        logger.debug(f"Content for file [{filepath}] => [{stylesheet}]")
        return stylesheet
    else:
        logger.warning(f"Could not open file [{filepath}]")
    return None


def get_aliases_from_loaded_resources() -> list[str]:
    """
    Recursively scans the Qt Resource System and returns a list of all file aliases.
    Returns:
        list[str]: List of all of the resource aliases.
    """

    all_aliases = []

    # Use a stack for a non-recursive directory traversal
    # Start with the root of the resource system
    dir_stack = [":/"]

    while dir_stack:
        current_path = dir_stack.pop()
        resource_dir = QDir(current_path)

        # List all files in the current resource directory
        for file_name in resource_dir.entryList(QDir.Filter.Files):
            # Construct the full resource path (alias)
            full_alias = f"{current_path}{file_name}"
            all_aliases.append(full_alias)

        # List all subdirectories and add them to the stack to be processed
        for dir_name in resource_dir.entryList(
            QDir.Filter.Dirs | QDir.Filter.NoDotAndDotDot
        ):
            dir_stack.append(f"{current_path}{dir_name}/")

    return all_aliases
