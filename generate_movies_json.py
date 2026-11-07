import os
import json
import boto3

from urllib.parse import quote
from botocore.exceptions import ClientError

# ==========================================
# Cloudflare R2 Configuration
# ==========================================

R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.environ.get("R2_BUCKET_NAME")
R2_ENDPOINT_URL = os.environ.get("R2_ENDPOINT_URL")

PUBLIC_R2_DOMAIN = (
    "https://pub-18678a28a2634123aa1c63d0b4feca75.r2.dev"
)

# ==========================================
# Validate Credentials
# ==========================================

required_variables = {
    "R2_ACCESS_KEY_ID": R2_ACCESS_KEY_ID,
    "R2_SECRET_ACCESS_KEY": R2_SECRET_ACCESS_KEY,
    "R2_BUCKET_NAME": R2_BUCKET_NAME,
    "R2_ENDPOINT_URL": R2_ENDPOINT_URL
}

missing = [
    name for name, value in required_variables.items()
    if not value
]

if missing:
    raise ValueError(
        f"Missing R2 credentials: {', '.join(missing)}"
    )

# ==========================================
# Connect to Cloudflare R2
# ==========================================

s3 = boto3.client(
    "s3",
    region_name="auto",
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    endpoint_url=R2_ENDPOINT_URL
)

# ==========================================
# Generate movies.json
# ==========================================

def generate_json():

    movies = []
    total_files = 0

    print(f"Connecting to R2 bucket: {R2_BUCKET_NAME}")

    try:
        # Pagination: Retrieve all objects, including > 1,000
        paginator = s3.get_paginator("list_objects_v2")

        pages = paginator.paginate(
            Bucket=R2_BUCKET_NAME
        )

        for page in pages:

            contents = page.get("Contents", [])

            for video in contents:

                filename = video["Key"]

                # Only MP4 videos
                if not filename.lower().endswith(".mp4"):
                    continue

                total_files += 1

                # Extract filename
                base_filename = os.path.basename(filename)
                name_without_ext = os.path.splitext(
                    base_filename
                )[0]

                title = name_without_ext.replace(
                    "_", " "
                ).title()

                # URL encode filename while preserving folders
                encoded_filename = quote(
                    filename, safe="/"
                )

                encoded_thumbname = quote(
                    name_without_ext + ".jpg",
                    safe=""
                )

                # Full Video URL
                video_url = (
                    f"{PUBLIC_R2_DOMAIN}/{encoded_filename}"
                )

                # Thumbnail URL
                # Preserve original .thumb/ directory structure
                thumb_url = (
                    f"{PUBLIC_R2_DOMAIN}/.thumb/"
                    f"{encoded_thumbname}"
                )

                created_at = video["LastModified"].isoformat()

                movies.append({
                    "title": title,
                    "genre": "mm-collections",
                    "img": thumb_url,
                    "video": video_url,
                    "createdAt": created_at
                })

        # Latest videos first
        movies.sort(
            key=lambda x: x["createdAt"],
            reverse=True
        )

        # Write movies.json
        with open(
            "movies.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                movies,
                f,
                ensure_ascii=False,
                indent=4
            )

        print("--------------------------------")
        print("R2 SYNC COMPLETED SUCCESSFULLY")
        print("--------------------------------")
        print(f"Total MP4 files: {total_files}")
        print(f"Generated movies: {len(movies)}")
        print("Output: movies.json")
        print("--------------------------------")

    except ClientError as e:
        print("Cloudflare R2 API Error:")
        print(e)
        raise

    except Exception as e:
        print("Sync Error:")
        print(e)
        raise


if __name__ == "__main__":
    generate_json()
