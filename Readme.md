<p align='right'>
	<small>Sunil Samuel<br>
		web_github@sunilsamuel.com<br>
		http://www.sunilsamuel.com
	</small>
</p>

# Intelligent Image Archiving 🖼️

This application provides a simple solution for organizing and enriching digital image collections. It leverages EXIF metadata and artificial intelligence to automate file renaming, directory organization, and content-based indexing. By streamlining these sophisticated tasks, the system transforms unstructured image libraries into organized and searchable archives.  The application uses AI models to dynamically generate a description for each image.  These options are configurable by the user.

## Automatic Renaming 📅
The app checks each photo's metadata (EXIF) to find the exact date it was taken. It then automatically renames the file to include that date. This changes a generic name like IMG_4821.jpg into a clear, chronological one, instantly organizing your files by date.

## AI-Powered Descriptions 🤖
It uses artificial intelligence to analyze the contents of your pictures. The AI identifies objects, scenes, and actions and then generates a short text description. This description is saved directly into the image file's UserComment field, which makes your photos searchable using keywords.

## Tidy Folder Structure 📂

Finally, the tool sorts your photos into folders based on the year and month they were taken. This neatly organizes your entire collection into a clean directory structure, making it much easier to browse, manage, and back up your images.

## Installation ⚙️

The application is simple enough that following steps should get you running:

### Python Virtual Environment (venv) 💡

1. Create a virtual environment (This is not required, but it helps to separate out other environments and requirements)
    * > `cd /directory/to/my/venvs`
    * > `python -m venv exif_image_processing`
    * > `/directory/to/my/venvs/exif_image_processing/bin/activate` (or activate.csh, Activate.ps1, ...)
1. Install the following modules:
    * > `pip install PySide6 piexif transformers==4.49.0 Pillow win32_setctime huggingface_hub keyring timm einops "huggingface_hub[hf_xet]"`
    * > `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121`

1. Install keyring on some systems, such as Ubuntu.  If you are running this on Windows, then you should not need to install the keyring applicaiton
    * > `sudo apt-get update`
    * > `sudo apt-get install gnome-keyring`
1. Execute the `app.py`
    * > `/directory/to/my/venvs/exif_image_processing/bin/python /install_dir/app.py`

> 📝 NOTE: The `transformers==4.49.0` version is required for now since the model `microsoft/Florence-2-large` does not work with the latest.  Eventually, they will fix this and we should be able to use the latest `transformers`.

### Huggingface Token 🤗

In order to use the AI models to generate the dynamic descriptions for the images, you must first create a huggingface token.  Use the following URL to create this token:

`https://huggingface.co/settings/tokens`

Once the token is generated, use `File->Set Huggingface Token` and place this newly created token into the text box. This will persist the token into your personal folder so that the next time you run this application, the token is already set. 

The AI image-to-text pipeline will not work if this is not done.

The application uses the following models to analyze and generate image description:
* `microsoft/Florence-2-large`
* `ydshieh/vit-gpt2-coco-en`
* `Salesforce/blip-image-captioning-base`

> 📝 NOTE: The code stores the huggingface token using keyring so that token is encrypted.  If you are using an operating system that does not have keyring, then please install it.

## Application 💻

The application uses `PySide6` module that provides access to the `Qt` framework.  This framework provides the functionality to create GUI applications that works within different operating systems, such as Linux and Windows.

`https://pypi.org/project/PySide6/`

The application has the following interface.

<img style="text-align:center;" src="application/Static/Graphics/Icons/application-capture_20250814.png" alt="Application Interface">

### Images 🌄

The application uses images for several reasons, such as the main window icon and HTML help text.  These images must be converted to resources for them to work correctly.  Otherwise, the application will not be able to locate them.

The `resources.qrc` file lists all of the images that are used within this application.  The file is as follows:

```xml
<!DOCTYPE RCC>
<RCC version="1.0">
  <qresource prefix="/">
    <!-- These are the images for the application -->
    <file alias="app_icon.jpg">Static/Graphics/Icons/ipa_v4.jpeg</file>
    <file alias="window_icon.png">Static/Graphics/Icons/window_icon_256x256.png</file>
  </qresource>
</RCC>
```

Now, we must compile the resources to a .py file as follows:

```bash
pyside6-rcc -no-compress resources.qrc -o resources_rc.py --verbose
```

This will create a file named `resources_rc.py` that contains the compiled versions of all of the images.  Now, `import` this file into the main application.  See `app.py`.

At this point, we can use the images in the HTML and QIcons as follows:

```html
<html>
    ...
    <img width="200" src=":/app_icon.jpg">
    ...
</html>
```

or in the code:

```python
icon: QIcon = QIcon(":/window_icon.png")
```

### Native Application 💫

This application can be packaged to run as a native executible for your operating system. To compile this application as a native application, follow these steps:

1. Install PyInstaller, if not already available:
    > `pip install pyinstaller`
1. Install tkinter for splash screen, following for your OS:
  * **For Windows (and most Python installations)**
    > `tkinter` is usually included with Python. If it's missing, you may need to modify your Python installation. Go to "Add or remove programs," find your Python version, click "Modify," and ensure that "tcl/tk and IDLE" is checked.
  * **For Debian/Ubuntu/Mint Linux**
    > `sudo apt-get install python3-tk`
  * **For Fedora/CentOS/RHEL Linux**
    > `sudo dnf install python3-tkinter`
  * **For macOS**
    * tkinter is typically included with the standard Python installation from python.org. If you are using a different distribution like Homebrew, you may need to install it separately.
    > `brew install python-tk`
1. Change Directory to the `application` folder
    > `cd application`
1. Open the terminal (either PowerShell, CMD, WSL, ...) and run the following command:
    > `pyinstaller --onefile --windowed --icon=Static/Graphics/Icons/windows_icon.ico --name="ImageProcessor_v1" --splash=Static/Graphics/Icons/ipa_v4.jpeg app.py`

## Development Environment 🛠️

The best IDE for development is `Visual Studio Code`.  Update the IDE as follows.

1. Set the Python interpreter path in Visual Studio Code, follow these steps: 
  * Open the Command Palette:
    * Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (macOS).
    * Select Interpreter:
        * Type "**Python: Select Interpreter**" and select the corresponding command from the dropdown list, `Create Virtual Environment...` or `Enter interpreter path...` (if you already created the venv)
1. Install the following extensions (recommended, but optional):
  * Python (Microsoft)
  * Python Debugger (Microsoft)
  * Python Environments (Microsoft)
  * Qt Core (Qt Group)

Once the environment is set, run the `app.py` file as follows:

> Right click on `app.py` and choose `Run Python File in Terminal`

## Compiled Distribution

A precompiled version for Windows is in the `dist` directory.  If you are using Windows, try this application.

* Download a pre-compiled version <a href="dist/ImageProcessor_v1.exe" target="new">ImageProcessor_v1.exe</a>
