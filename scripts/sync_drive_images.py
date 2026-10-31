#!/usr/bin/env python3
"""Sync numbered product images from one Google Drive folder into product-images/."""
import hashlib
import io
import json
import os
import re
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "product-images"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}
# Remove only the final separator + sequence number. Everything before it is the folder name.
NUMBERED_NAME = re.compile(r"^(?P<product>.+?)[ _.-]+(?P<number>\\d+)$")

def md5_file(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def main() -> None:
    folder_id = os.environ["DRIVE_FOLDER_ID"].strip()
    service_account_info = json.loads(os.environ["DRIVE_SERVICE_ACCOUNT_JSON"])
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    drive = build("drive", "v3", credentials=credentials, cache_discovery=False)
    query = f"'{folder_id}' in parents and trashed = false"
    page_token = None
    changed = 0

    while True:
        response = drive.files().list(
            q=query,
            pageSize=1000,
            pageToken=page_token,
            fields="nextPageToken, files(id,name,mimeType,md5Checksum)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()

        for item in response.get("files", []):
            filename = item["name"]
            source_name = Path(filename)
            if source_name.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            match = NUMBERED_NAME.fullmatch(source_name.stem)
            if not match:
                print(f"Skipping (expected a trailing image number): {filename}")
                continue

            product_folder = match.group("product").strip()
            # Keep the prefix exactly as written, while preventing unsafe path components.
            if not product_folder or product_folder in {".", ".."} or "/" in product_folder or "\\" in product_folder:
                print(f"Skipping unsafe product prefix: {filename}")
                continue

            target = DESTINATION / product_folder / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            expected_md5 = item.get("md5Checksum")
            if target.exists() and expected_md5 and md5_file(target) == expected_md5:
                print(f"Unchanged: {product_folder}/{filename}")
                continue

            request = drive.files().get_media(fileId=item["id"], supportsAllDrives=True)
            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request, chunksize=1024 * 1024)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            target.write_bytes(buffer.getvalue())
            changed += 1
            print(f"Synced: {product_folder}/{filename}")

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    print(f"Sync complete. {changed} image(s) added or updated.")

if __name__ == "__main__":
    main()