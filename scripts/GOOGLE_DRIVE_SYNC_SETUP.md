# Google Drive product-image sync

This repository can periodically copy numbered product images from one Google Drive folder into `product-images/`.

## Filename rule

Use a product prefix followed by a separator and a sequence number before the extension:

- `vector point_1.png` -> `product-images/vector point/vector point_1.png`
- `vector point_2.png` -> `product-images/vector point/vector point_2.png`
- `brit_accent_1.webp` -> `product-images/brit_accent/brit_accent_1.webp`

The prefix is the complete filename stem before the final separator and number. The original image filename and extension are retained. Supported extensions: JPG, JPEG, PNG, WEBP, GIF and AVIF.

## One-time Google Drive setup

1. In Google Cloud Console, create or select a project and enable the Google Drive API.
2. Create a service account and generate a JSON key. Keep this key private.
3. Create a folder in Google Drive for incoming product images.
4. Share that folder with the service account's email address as a Viewer. If it is in a Shared Drive, ensure the service account has access there too.
5. Copy the folder ID from its URL: `https://drive.google.com/drive/folders/FOLDER_ID`.

## One-time GitHub setup

In this repository, open Settings -> Secrets and variables -> Actions -> New repository secret. Add:

- `DRIVE_FOLDER_ID`: the Google Drive folder ID.
- `DRIVE_SERVICE_ACCOUNT_JSON`: the entire contents of the service-account JSON key file.

Then open Actions -> Sync product images from Google Drive -> Run workflow for the first sync. After that, the workflow checks the Drive folder every 15 minutes.

## Notes

- The workflow only reads images directly inside the selected Drive folder; it does not recurse into Drive subfolders.
- Files without a trailing sequence number are skipped.
- If a Drive image changes but keeps the same filename, the repository copy is updated.
- GitHub Actions commits changed images to `product-images/<product prefix>/<original filename>`.
- Do not commit the service-account JSON key or add it to the repository. Store it only as the GitHub Actions secret.