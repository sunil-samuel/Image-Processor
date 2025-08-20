# -*- coding: utf-8 -*-
"""
@File    :   new_window.py
@Time    :   2025/07/18
@Author  :   Sunil Samuel
@Version :   1.0
@Contact :   sgs@sunilsamuel.com
"""

import logging, keyring
from logging import Logger
from huggingface_hub import login

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QHBoxLayout,
    QCheckBox,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QLabel,
    QProgressBar,
    QFileDialog,
    QFrame,
    QMenuBar,
    QMessageBox,
    QDialog,
    QTextBrowser,
    QDialogButtonBox,
    QComboBox,
)

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor, QAction, QKeySequence, QIcon
from Worker.worker import Worker
from .processing_options import ProcessingOptions
from Helper.snippet import Snippet
import Helper.file_to_string as helper

from Processor.process_image import ProcessImage



class MainWindow:
    """
    Controller class for the main application window.
    It creates and manages a QMainWindow instance.
    """

    __window: QMainWindow = None
    __central_widget: QWidget = None
    __main_layout: QVBoxLayout = None
    __options_group_box: QGroupBox = None
    __options_layout: QHBoxLayout = None
    __src_dir_group_box: QGroupBox = None
    __src_dir_layout: QHBoxLayout = None
    __src_dir_path_line_edit: QLineEdit = None
    __src_dir_browse_button: QPushButton = None
    __move_file_dir_layout: QHBoxLayout = None
    __move_file_dir_path_line_edit: QLineEdit = None
    __move_file_dir_browse_button: QPushButton = None
    __progress_group_box: QGroupBox = None
    __progress_layout: QVBoxLayout = None
    __log_text_edit: QTextEdit = None
    __progress_bar: QProgressBar = None
    __start_button: QPushButton = None
    __quit_app_button: QPushButton = None
    __worker: Worker = None
    __about_message: str = None
    __application_message: str = None
    __snippet: Snippet = None
    __huggingface_token: str = None

    #
    # keyring service names and token keys are used to
    # store the huggingface token as encrypted key.
    #
    __SERVICE_NAME = "ImageProcessorApplication"
    __TOKEN_KEY = "HuggingFaceAPIToken"

    __logger: Logger = logging.getLogger(__name__)
    __root_dir: str = None

    __options_checkbox: dict[str, QCheckBox] = None

    def __init__(self, root_dir: str) -> None:
        self.__root_dir = root_dir
        self.__snippet = Snippet(root_dir)

        self.__load_huggingface_token_from_user()

        self.__create_main_window()
        self.__create_menu_bar()
        self.__create_main_layout()
        self.__create_options_section()
        self.__create_AI_options()
        self.__create_src_dir_group_box()
        self.__create_move_file_dir_group_box()
        self.__create_progress_group_box()
        self.__create_log_text_edit()
        self.__create_progress_bar()
        self.__create_start_button()
        self.__update_widget_dependencies()

    ############################################################################
    # show
    ############################################################################
    def show(self):
        """Shows the main window."""
        self.__window.show()
        
    def post_process(self):
        
        self.__logger.info("Processing post_process")
        self.__process_image:ProcessImage = ProcessImage()
        self.__process_image.post_process()

    ############################################################################
    # open_directory_dialog
    ############################################################################
    def open_directory_dialog(self, title: str, line_edit: QLineEdit) -> None:
        """
        Opens a dialog to select a directory and updates the line edit.
        The parent is now self.__window.
        """

        if line_edit.isEnabled():
            directory: str = QFileDialog.getExistingDirectory(self.__window, title)
            if directory:
                line_edit.setText(directory)
        else:
            self.__create_message_box(
                "Invalid Selection",
                "Please make sure to select the correct options before opening directory.",
                "Please see the section 'Processing Options' within the Help menu.",
                QMessageBox.Icon.Warning,
            )

    def get_window(self) -> QMainWindow:
        return self.__window

    def __set_huggingface_token(self) -> None:
        dialog: QDialog = QDialog(self.__window)
        dialog.setWindowTitle("Enter Huggingface Token")

        label: QLabel = QLabel("Enter Huggingface API Token:")
        token_input: QLineEdit = QLineEdit()
        token_input.setEchoMode(QLineEdit.EchoMode.Password)
        token_input.setPlaceholderText("e.g., hf_xxxxxxxxxxxxxxxx")
        button_box: QDialogButtonBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        layout: QVBoxLayout = QVBoxLayout(dialog)
        layout.addWidget(label)
        layout.addWidget(token_input)
        layout.addWidget(button_box)

        def validate_and_accept():
            token = token_input.text().strip()
            # A simple validation for a Hugging Face token
            if token and token.startswith("hf_"):
                # This closes the dialog with an "Accepted" result
                dialog.accept()
            else:
                self.__create_message_box(
                    "Invalid Huggingface Token",
                    "Please make sure to enter a valid huggingface token.",
                    "Token must start with 'hf_'",
                    QMessageBox.Icon.Critical,
                )

        button_box.accepted.connect(validate_and_accept)
        button_box.rejected.connect(dialog.reject)
        if dialog.exec():
            huggingface_token: str = token_input.text()
            self.__set_huggingface_token_from_user(huggingface_token)
        else:
            return None

    ############################################################################
    # quit_application
    ############################################################################
    def _quit_application(self) -> None:
        self.stop_task(message_box=False)
        if self.__worker is not None and self.__worker.isRunning():
            self.__logger.info("Worker is still running, waiting ...")
            self.update_log_area(
                "Requested to stop processing.  Please wait ...", "error"
            )

            self.__worker.wait()

        self.__window.close()

    ############################################################################
    # _toggle_full_screen
    ############################################################################
    def _toggle_full_screen(self, checked):
        if checked:
            self.__window.showFullScreen()
        else:
            self.__window.showNormal()

    ############################################################################
    # _about
    ############################################################################
    def _about(self) -> None:
        if not self.__about_message:
            self.__about_message = helper.read_style_file_from_resource(
                ":/about.html", self.__logger
            )
            self.__about_message = self.__snippet.snippet_replace(self.__about_message)
        QMessageBox.about(self.__window, "About Image Processor", self.__about_message)

    ############################################################################
    # _application_help
    ############################################################################
    def _application_help(self) -> None:
        if not self.__application_message:
            self.__application_message = helper.read_style_file_from_resource(
                ":/usage.html", self.__logger
            )
            self.__application_message = self.__snippet.snippet_replace(
                self.__application_message
            )
        dialog: QDialog = QDialog(self.__window)
        dialog.setWindowTitle("Image Processor Help")
        dialog.setMinimumSize(800, 600)

        text_browser: QTextBrowser = QTextBrowser()
        text_browser.setHtml(self.__application_message)
        text_browser.setOpenExternalLinks(True)

        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)

        layout: QVBoxLayout = QVBoxLayout(dialog)
        layout.addWidget(text_browser)
        layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight)

        dialog.exec()

    ############################################################################
    # _copy_or_move_file_select
    ############################################################################
    def _copy_or_move_file_select(self, checkbox: QCheckBox) -> None:
        # Only one of copy or move can be checked, but not both

        self.__logger.debug(f"Checkbox [{checkbox.text()}] is [{checkbox.isChecked()}]")
        if checkbox.isChecked():
            opposite: str = (
                ProcessingOptions.MOVE_FILES.name
                if checkbox.objectName() == "copy_files"
                else ProcessingOptions.COPY_FILES.name
            )
            self.__logger.debug(f"Opposite is [{opposite}]")
            self.__options_checkbox[opposite].setChecked(False)

        checked: bool = (
            self.__options_checkbox[ProcessingOptions.COPY_FILES.name].isChecked()
            or self.__options_checkbox[ProcessingOptions.MOVE_FILES.name].isChecked()
        )

        self.__move_file_dir_group_box.setEnabled(checked)
        self.__move_file_dir_browse_button.setEnabled(checked)
        self.__options_checkbox[ProcessingOptions.CREATE_MONTH_FOLDER.name].setEnabled(
            checked
        )
        if not checked:
            self.__options_checkbox[
                ProcessingOptions.CREATE_MONTH_FOLDER.name
            ].setChecked(False)

    ############################################################################
    # start_task
    ############################################################################
    def start_task(self):
        """
        Starts the background worker thread to simulate a task.
        """

        if not self.__huggingface_token:
            self.__create_message_box(
                "Missing Huggingface Token",
                "Please set the huggingface token using 'File Menu'",
                "See the 'Help Application' section for more information",
                QMessageBox.Icon.Critical,
            )
            return

        if not self.__src_dir_path_line_edit.text():
            self.__create_message_box(
                "Missing Selection",
                "Please select a source directory before processing.",
                "See 'Source Directory Selection'",
                QMessageBox.Icon.Warning,
            )
            return

        if (
            self.__options_checkbox[ProcessingOptions.MOVE_FILES.name].isChecked()
            or self.__options_checkbox[ProcessingOptions.COPY_FILES.name].isChecked()
        ) and not self.__move_file_dir_path_line_edit.text():
            self.__create_message_box(
                "Missing Selection",
                "You selected to move or copy the files to a destination directory, but haven't provided the destination directory.",
                "See 'Destination Directory Selection'",
                QMessageBox.Icon.Warning,
            )
            return

        if self.__worker is None or not self.__worker.isRunning():
            # Log selected options
            self.update_log_area("Starting Task:", "header")
            self.update_log_area(f"Directory: [{self.__src_dir_path_line_edit.text()}]")

            options: dict[str, bool | int] = {}
            for key, value in self.__options_checkbox.items():
                self.__logger.info(f"[{key}] => [{value.isChecked()}]")
                self.update_log_area(f"[{key}] => [{value.isChecked()}]")
                options[key] = value.isChecked()

            # Add the AI level of description so that worker will send
            # correct prompt to model.
            options["ai_level"] = self.__ai_option.currentIndex()

            self.__worker = Worker(
                process_image= self.__process_image,
                dir=self.__src_dir_path_line_edit.text(),
                move_dir=self.__move_file_dir_path_line_edit.text(),
                options=options,
            )
            self.__worker.progress.connect(self.__progress_bar.setValue)
            self.__worker.log_message.connect(self.update_log_area)
            self.__worker.finished.connect(self.task_finished)
            self.__worker.start()

    def stop_task(self, message_box: bool = True):
        if self.__worker is None or not self.__worker.isRunning():
            self.__logger.info(f"Stop Task message box [{message_box}]")
            if message_box:
                self.__create_message_box(
                    "Not Processing",
                    "The application is currently not processing files.",
                    "Please click 'Start Processing'.  See 'Help' menu.",
                )
        else:
            self.__worker.setStop()
            self.__worker.requestInterruption()

    def update_log_area(self, message: str, type: str = "default") -> None:
        """
        Single point of logging into the logging widget on the main window.
        Not all tags work well with the widget.  Not all tags support .

        Args:
            message (str): Message to display
            type (str, optional): css class. Defaults to "default".
        """

        if message == "hr":
            self.__log_text_edit.insertHtml("<hr>")
            return

        css_base: str = "font-size:10pt;"
        css: dict[str, str] = {
            "title": "font-weight:bold;font-size:18pt;text-align:center;width:100%;border:1px solid red;display:block;color:white;",
            "default": "font-weight:normal;text-align:left;margin:10px;padding:10px;display:block;",
            "header": "font-weight:bold;font-size:14pt;text-align:left;display:block;",
            "error": "font-weight:bold;color:red;display:block;",
            "bold": "font-weight:bold;",
            "highlight": "color:white;",
        }

        tag: str = "p" if type in ["title", "header"] else "span"

        html_message: str = (
            f"<{tag} style='{css_base}{css.get(type, "default")}'>{message}</{tag}><br>"
        )
        # This moveCursor will ensure that the vertical scrollbar will always show
        # the last item written.
        self.__log_text_edit.moveCursor(QTextCursor.MoveOperation.End)
        self.__log_text_edit.insertHtml(html_message)

    ############################################################################
    # task_finished
    ############################################################################
    def task_finished(self):
        """
        Called when the worker thread is finished.
        """
        self.update_log_area("Task Complete", "header")
        self.__progress_bar.setValue(100)  # Ensure it ends at 100%

    ############################################################################
    # __create_main_window
    ############################################################################
    def __create_main_window(self) -> None:
        self.__window = QMainWindow()
        self.__window.setWindowTitle("Image Processor")
        self.__window.setGeometry(100, 100, 1200, 900)
        # Set a minimum size to prevent layout from breaking
        self.__window.setMinimumSize(550, 450)

        self.__central_widget = QWidget()
        self.__window.setCentralWidget(self.__central_widget)

        # Create an icon for the window
        icon: QIcon = QIcon(":/window_icon.png")
        self.__window.setWindowIcon(icon)
        self.__window.setWindowIconText("Image Processor (sunil samuel)")

    def __create_AI_options(self) -> None:
        # Define the three allowed values for our slider
        self.__allowed_values = ["Brief", "Standard", "Full"]

        # --- Create the Slider ---
        self.__ai_option = QComboBox()

        self.__ai_option.addItems(self.__allowed_values)
        self.__ai_option.setCurrentIndex(2)
        self.__ai_option.setPlaceholderText(
            "Level of description detail AI creates for the image"
        )

    def slider_value_changed(self, value):
        """
        This function is the "slot" that receives the slider's valueChanged signal.
        The 'value' is now an index (0, 1, or 2) which we use to get the
        display text from our list of allowed values.
        """
        self.__logger.info(f"Slider value is [{value}]")
        # self.value_label.setText(f"Current Value: {display_text}")

    def __create_menu_bar(self) -> None:
        menu_bar: QMenuBar = self.__window.menuBar()
        # -- 1. Create the Top Menu Items
        file_menu = menu_bar.addMenu("&File")
        view_menu = menu_bar.addMenu("&View")
        help_menu = menu_bar.addMenu("&Help")

        # -- 2. Create all of the actions that will be in all of the menu

        set_huggingface_token_action = QAction("Set H&uggingface Token", self.__window)
        set_huggingface_token_action.setShortcut("Ctrl+U")
        set_huggingface_token_action.triggered.connect(self.__set_huggingface_token)

        open_src_dir_action = QAction("Select &Source Directory", self.__window)
        open_src_dir_action.setShortcut("Ctrl+S")
        open_src_dir_action.triggered.connect(
            lambda: self.open_directory_dialog(
                "Select Source Directory", self.__src_dir_path_line_edit
            )
        )

        open_dest_dir_action = QAction("Select &Destination Directory", self.__window)
        open_dest_dir_action.setShortcut("Ctrl+D")
        open_dest_dir_action.triggered.connect(
            lambda: self.open_directory_dialog(
                "Select Destination Directory", self.__move_file_dir_path_line_edit
            )
        )

        quit_action = QAction("E&xit Application", self.__window)
        quit_action.setShortcut(QKeySequence.StandardKey.Close)
        quit_action.triggered.connect(self.__window.close)

        full_screen_action = QAction("Fu&ll Screen", self.__window)
        full_screen_action.setShortcut("F11")
        full_screen_action.setCheckable(True)
        full_screen_action.triggered.connect(self._toggle_full_screen)

        about_action = QAction("&About ...", self.__window)
        about_action.setShortcut("Ctrl+H")
        about_action.triggered.connect(self._about)

        application_help_action = QAction("A&pplication Help ...", self.__window)
        application_help_action.setShortcut("Ctrl+P")
        application_help_action.triggered.connect(self._application_help)

        # -- 3. Add all of the actions to corresponding menu
        file_menu.addAction(set_huggingface_token_action)
        file_menu.addAction(open_src_dir_action)
        file_menu.addAction(open_dest_dir_action)
        file_menu.addAction(quit_action)
        view_menu.addAction(full_screen_action)
        help_menu.addAction(about_action)
        help_menu.addAction(application_help_action)

    ############################################################################
    # __create_main_layout
    ############################################################################
    def __create_main_layout(self) -> None:
        self.__main_layout = QVBoxLayout(self.__central_widget)
        self.__main_layout.setContentsMargins(20, 20, 20, 20)
        self.__main_layout.setSpacing(15)

    ############################################################################
    # __create_options_section
    ############################################################################
    def __create_options_section(self) -> None:
        self.__options_group_box = QGroupBox("Processing Options")

        self.__options_layout = QHBoxLayout()
        self.__options_layout.setSpacing(20)

        self.__options_checkbox = {}

        for option in ProcessingOptions:
            self.__options_checkbox[option.name] = self.__create_checkbox(option.value)

        self.__options_checkbox[ProcessingOptions.MOVE_FILES.name].clicked.connect(
            lambda: self._copy_or_move_file_select(
                self.__options_checkbox[ProcessingOptions.MOVE_FILES.name]
            )
        )
        self.__options_checkbox[ProcessingOptions.COPY_FILES.name].clicked.connect(
            lambda: self._copy_or_move_file_select(
                self.__options_checkbox[ProcessingOptions.COPY_FILES.name]
            )
        )

    ############################################################################
    # __create_src_dir_group_box
    ############################################################################
    def __create_src_dir_group_box(self) -> None:

        self.__src_dir_group_box = QGroupBox("Source Directory Selection")
        self.__src_dir_layout = QHBoxLayout()
        self.__src_dir_layout.setSpacing(10)

        self.__src_dir_path_line_edit = QLineEdit()
        self.__src_dir_path_line_edit.setObjectName("source_dir")
        self.__src_dir_path_line_edit.setPlaceholderText(
            "Select the source directory..."
        )
        self.__src_dir_path_line_edit.setReadOnly(True)

        self.__src_dir_browse_button = QPushButton("Browse ...")
        self.__src_dir_browse_button.clicked.connect(
            lambda: self.open_directory_dialog(
                "Open Source Directory", self.__src_dir_path_line_edit
            )
        )
        self.__src_dir_browse_button.setObjectName("browseButton")

        self.__src_dir_group_box.setLayout(self.__src_dir_layout)

        self.__src_dir_layout.addWidget(self.__src_dir_path_line_edit)
        self.__src_dir_layout.addWidget(self.__src_dir_browse_button)

    ############################################################################
    # __create_move_file_dir_group_box
    ############################################################################
    def __create_move_file_dir_group_box(self) -> None:

        self.__move_file_dir_group_box = QGroupBox("Destination Directory Selection")
        self.__move_file_dir_group_box.setObjectName("dest_dir")
        self.__move_file_dir_group_box
        # default it to disabled
        # self.__move_file_dir_group_box.setDisabled(True)
        self.__move_file_dir_group_box.setEnabled(False)
        self.__move_file_dir_layout = QHBoxLayout()
        self.__move_file_dir_layout.setSpacing(10)

        self.__move_file_dir_path_line_edit = QLineEdit()
        self.__move_file_dir_path_line_edit.setObjectName("move_file_dir")
        self.__move_file_dir_path_line_edit.setPlaceholderText(
            "Select the destination directory ..."
        )
        self.__move_file_dir_path_line_edit.setReadOnly(True)

        self.__move_file_dir_browse_button = QPushButton("Browse ...")
        self.__move_file_dir_browse_button.setEnabled(False)
        self.__move_file_dir_browse_button.clicked.connect(
            lambda: self.open_directory_dialog(
                "Open Destination Directory", self.__move_file_dir_path_line_edit
            )
        )
        self.__move_file_dir_browse_button.setObjectName("moveFileBrowse")

        self.__move_file_dir_group_box.setLayout(self.__move_file_dir_layout)

        self.__move_file_dir_layout.addWidget(self.__move_file_dir_path_line_edit)
        self.__move_file_dir_layout.addWidget(self.__move_file_dir_browse_button)

    ############################################################################
    # __create_progress_group_box
    ############################################################################
    def __create_progress_group_box(self) -> None:
        """
        Progress Section
        """
        self.__progress_group_box = QGroupBox("Application Progress")
        self.__progress_layout = QVBoxLayout()
        self.__progress_layout.setSpacing(10)

    ############################################################################
    # __create_log_text_edit
    ############################################################################
    def __create_log_text_edit(self) -> None:
        self.__log_text_edit = QTextEdit()
        self.__log_text_edit.setReadOnly(True)
        self.__log_text_edit.setAcceptRichText(True)
        self.__log_text_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)

        self.update_log_area("Notification Area", "title")

    ############################################################################
    # __create_progress_bar
    ############################################################################
    def __create_progress_bar(self) -> None:
        self.__progress_bar = QProgressBar()
        self.__progress_bar.setValue(0)
        self.__progress_bar.setTextVisible(True)
        self.__progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)

    ############################################################################
    # __create_start_button
    ############################################################################
    def __create_start_button(self) -> None:

        self.__quit_app_button = QPushButton("Quit")
        self.__quit_app_button.clicked.connect(self._quit_application)
        self.__quit_app_button.setObjectName("QuitApplication")

        self.__start_button = QPushButton("Start Processing")
        self.__start_button.clicked.connect(self.start_task)
        self.__start_button.setObjectName("startButton")

        self.__stop_button = QPushButton("Stop Processing")
        self.__stop_button.clicked.connect(lambda: self.stop_task(message_box=True))
        self.__stop_button.setObjectName("stopButton")

        self.__button_layout: QHBoxLayout = QHBoxLayout()
        self.__button_layout.addWidget(
            self.__start_button, 0, Qt.AlignmentFlag.AlignLeft
        )
        self.__button_layout.addWidget(
            self.__stop_button, 0, Qt.AlignmentFlag.AlignRight
        )

    ############################################################################
    # __update_widget_dependencies
    ############################################################################
    def __update_widget_dependencies(self) -> None:
        self.__main_layout.setParent(self.__central_widget)
        for value in self.__options_checkbox.values():
            self.__options_layout.addWidget(self.__create_separator())
            self.__options_layout.addWidget(value)

        self.__options_layout.addWidget(self.__ai_option)
        self.__options_layout.addWidget(self.__create_separator())

        # Push checkboxes to the center
        self.__options_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.__options_group_box.setLayout(self.__options_layout)
        self.__main_layout.addWidget(self.__options_group_box)

        # Add the src dir browse and all of the widgets for it
        self.__main_layout.addWidget(self.__src_dir_group_box)
        self.__main_layout.addWidget(self.__move_file_dir_group_box)

        self.__progress_layout.addWidget(QLabel("Log:"))
        self.__progress_layout.addWidget(self.__log_text_edit)

        self.__progress_layout.addWidget(QLabel("Progress:"))
        self.__progress_layout.addWidget(self.__progress_bar)

        # self.__progress_layout.addWidget(
        #     self.__start_button, 0, Qt.AlignmentFlag.AlignRight
        # )

        # self.__progress_layout.addWidget(
        #     self.__stop_button, 0, Qt.AlignmentFlag.AlignRight
        # )

        self.__progress_layout.addLayout(self.__button_layout)

        # Make the log text edit expand vertically
        self.__progress_layout.setStretchFactor(self.__log_text_edit, 1)

        self.__progress_group_box.setLayout(self.__progress_layout)
        self.__main_layout.addWidget(self.__progress_group_box)

        self.__main_layout.addWidget(self.__quit_app_button)

        # Set stretch factors for the main layout
        self.__main_layout.setStretchFactor(self.__options_group_box, 0)
        self.__main_layout.setStretchFactor(self.__src_dir_group_box, 0)
        self.__main_layout.setStretchFactor(self.__progress_group_box, 1)

    ############################################################################
    # __create_checkbox
    ############################################################################
    def __create_checkbox(self, option: dict[str, any]) -> QCheckBox:

        self.__logger.info(f"Create Checkbox with option [{option}]")
        checkbox: QCheckBox = QCheckBox(option["title"])
        checkbox.setToolTip(option["description"])
        checkbox.setChecked(option["checked"])
        checkbox.setObjectName(option["objectName"])
        if not option["enabled"]:
            checkbox.setEnabled(False)
        return checkbox

    ############################################################################
    # __create_message_box
    ############################################################################
    def __create_message_box(
        self,
        title: str,
        text: str,
        informativeText: str,
        icon: QMessageBox.Icon = QMessageBox.Icon.Information,
    ) -> None:
        msg_box: QMessageBox = QMessageBox(self.__window)
        msg_box.setWindowTitle(title)
        msg_box.setIcon(icon)
        msg_box.setText(text)
        msg_box.setInformativeText(informativeText)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()

    def __create_separator(self) -> QFrame:
        separator: QFrame = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)  # Vertical line
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        return separator

    def __load_huggingface_token_from_user(self) -> None:
        self.__huggingface_token = keyring.get_password(
            self.__SERVICE_NAME, self.__TOKEN_KEY
        )
        self.__login_huggingface()

    def __set_huggingface_token_from_user(self, token: str) -> None:
        self.__logger.info("Setting huggingface token to system")
        keyring.set_password(self.__SERVICE_NAME, self.__TOKEN_KEY, token)
        self.__huggingface_token = token
        self.__login_huggingface()

    def __login_huggingface(self) -> None:
        if self.__huggingface_token:
            login(token=self.__huggingface_token)
