# -*- coding: utf-8 -*-
"""
@File    :   snippet.py
@Time    :   2025/08/08
@Author  :   Sunil Samuel
@Version :   1.0
@Contact :   sgs@sunilsamuel.com
"""

import os, logging
from logging import Logger
import Helper.file_to_string as helper


class Snippet:
    """
    A module that will read all of the snippet HTML content from a given
    directory and create a key value pair where the user can access the
    content of the file, given the name of the file.  This is used to
    enrich and reuse content that will be used within several HTML
    pages, such as version, description, changes, ...

    Returns:
        _type_: _description_
    """

    __logger: Logger = logging.getLogger(__file__)
    __content: dict[str, str] = {}

    def __init__(self, root_dir: str) -> None:
        snippet_dir: str = os.path.join(root_dir, "Static", "Content", "Snippet")

        self.__logger.info(f"Starting directory for snippet is [{snippet_dir}]")

        aliases: list[str] = helper.get_aliases_from_loaded_resources()

        for alias in aliases:
            if alias.startswith(":/snippet_"):
                name: str = os.path.splitext(alias[10:])[0]
                content: str = helper.read_style_file_from_resource(
                    alias, self.__logger
                )
                self.__logger.debug(
                    f"Found snippet names [{alias}] => [{name}] => content [{content}]"
                )
                self.__content[name] = content

        self.__logger.debug(f"Content [{self.__content}]")

    def get_keys(self) -> list[str]:
        return list(self.__content)

    def get_value(self, key: str) -> str | None:
        return self.__content[key]

    def snippet_replace(self, content: str) -> str:
        rval: str = content
        for key in self.__content.keys():
            replace_value: str = "${" + key + "}"
            self.__logger.debug(f"Replace value is [{replace_value}]")
            rval = rval.replace(replace_value, self.__content[key])
        return rval
