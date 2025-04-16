"""
Instructions for downloading member profile images:

1. Visit the Google Drive link: https://drive.google.com/drive/folders/1dllv8TMgC0yYzYzThcxGYz3r_U5cEehl
2. Download all 12 images to your local computer
3. Place the downloaded images in the 'static/images/members' directory
4. Rename the images as follows:
   - First 6 images: m1.jpg, m2.jpg, m3.jpg, m4.jpg, m5.jpg, m6.jpg
   - Next 6 images: f1.jpg, f2.jpg, f3.jpg, f4.jpg, f5.jpg, f6.jpg

This script will help you verify that the images are correctly placed.
"""

import os
import sys

def check_images():
    # Define the directory where images should be placed
    image_dir = os.path.join('static', 'images', 'members')
    
    # Create the directory if it doesn't exist
    os.makedirs(image_dir, exist_ok=True)
    
    # Define the expected image filenames
    expected_images = [f'm{i}.jpg' for i in range(1, 7)] + [f'f{i}.jpg' for i in range(1, 7)]
    
    # Check if all expected images exist
    missing_images = []
    for img in expected_images:
        img_path = os.path.join(image_dir, img)
        if not os.path.exists(img_path):
            missing_images.append(img)
    
    if missing_images:
        print(f"The following images are missing: {', '.join(missing_images)}")
        print(f"Please place them in the {image_dir} directory.")
    else:
        print("All member profile images are correctly placed!")
        print(f"Images directory: {os.path.abspath(image_dir)}")

if __name__ == "__main__":
    check_images()
