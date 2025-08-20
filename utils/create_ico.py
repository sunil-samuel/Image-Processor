# -*- coding: utf-8 -*-
"""
@File    :   create_ico.py
@Time    :   2025/08/16
@Author  :   Sunil Samuel
@Version :   1.0
@Contact :   sgs@sunilsamuel.com
@Desc    :   Given an image, create a .ico file with different icon
             sizes consistent with standard .ico file.
"""


from PIL import Image
import os

# Define the path to your source 256x256 image (e.g., a PNG file)
source_image_path = os.path.join(
    "application", "Static", "Graphics", "Icons", "ipa_v4_square.png"
)

# Define the path for the output .ico file
icon_path = "my_icon.ico"

# A list of standard sizes to include in the .ico file
# Pillow will resize the source image to create each of these sizes
icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

try:
    # Open the source image
    img = Image.open(source_image_path)

    # Save the image as an ICO file, providing the list of sizes
    img.save(icon_path, format="ICO", sizes=icon_sizes)

    print(f"Successfully created icon: {icon_path}")

except FileNotFoundError:
    print(f"Error: The file '{source_image_path}' was not found.")
except Exception as e:
    print(f"An error occurred: {e}")
