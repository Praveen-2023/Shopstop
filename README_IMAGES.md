# Member Profile Images Setup

This document provides instructions for setting up the member profile images for the ShopStop application.

## Instructions

1. Download the member profile images from the Google Drive link:
   https://drive.google.com/drive/folders/1dllv8TMgC0yYzYzThcxGYz3r_U5cEehl

2. Create the following directory structure if it doesn't exist:
   ```
   DB_A3/DB_A3/static/images/members/
   ```

3. Place the downloaded images in the `DB_A3/DB_A3/static/images/members/` directory.

4. Rename the images as follows:
   - First 6 images: `m1.jpg`, `m2.jpg`, `m3.jpg`, `m4.jpg`, `m5.jpg`, `m6.jpg` (for male members)
   - Next 6 images: `f1.jpg`, `f2.jpg`, `f3.jpg`, `f4.jpg`, `f5.jpg`, `f6.jpg` (for female members)

5. Create a placeholder image named `placeholder.jpg` for members without a profile image.

## Verification

You can run the `download_member_images.py` script to verify that all the required images are in place:

```bash
python download_member_images.py
```

If any images are missing, the script will tell you which ones need to be added.

## Image Assignment

The application assigns profile images to members based on their member ID:
- Even member IDs get female images (f1.jpg to f6.jpg)
- Odd member IDs get male images (m1.jpg to m6.jpg)
- The specific image is determined by `(member_id % 6) + 1`

For example:
- Member ID 1 gets m1.jpg
- Member ID 2 gets f2.jpg
- Member ID 3 gets m3.jpg
- Member ID 7 gets m1.jpg (since 7 % 6 = 1)
- Member ID 8 gets f2.jpg (since 8 % 6 = 2)

## Troubleshooting

If images are not displaying correctly:

1. Make sure all images are in the correct directory
2. Check that the image filenames match exactly (case-sensitive)
3. Verify that the images are accessible by visiting `/static/images/members/m1.jpg` in your browser
4. Check the browser console for any 404 errors related to image loading
