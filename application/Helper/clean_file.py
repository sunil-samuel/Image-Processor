import re

def remove_datetime_prefix(filename):
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
    combined_pattern = re.compile(r"^(" + "|".join(datetime_patterns) + r")\s*[-_]?\s*")

    # Use re.sub() to replace the matched pattern with an empty string.
    cleaned_filename = combined_pattern.sub("", filename)

    return cleaned_filename
