
import os
import re
import json
import xml.etree.ElementTree as ET

from datetime import date, datetime
from urllib.parse import urlencode, urlparse


# ==========================================
# WEBSITE CONFIGURATION
# ==========================================

SITE_URL = "https://drsamangyi.com"

MOVIES_JSON = "movies.json"
SITEMAP_FILE = "sitemap.xml"

STATIC_LASTMOD = "2026-11-08"

R2_HOST = "pub-18678a28a2634123aa1c63d0b4feca75.r2.dev"


# ==========================================
# XML NAMESPACES
# ==========================================

NS = "http://www.sitemaps.org/schemas/sitemap/0.9"

IMAGE_NS = "http://www.google.com/schemas/sitemap-image/1.1"

VIDEO_NS = "http://www.google.com/schemas/sitemap-video/1.1"

ET.register_namespace("", NS)
ET.register_namespace("image", IMAGE_NS)
ET.register_namespace("video", VIDEO_NS)


def xml_tag(name, namespace=NS):
    return f"{{{namespace}}}{name}"


# ==========================================
# GENERAL VALIDATION
# ==========================================

def is_valid_https_url(value, allowed_host=None):

    if not isinstance(value, str):
        return False

    try:
        parsed = urlparse(value)

        if parsed.scheme != "https":
            return False

        if not parsed.hostname:
            return False

        if parsed.username or parsed.password:
            return False

        if parsed.port not in (None, 443):
            return False

        if allowed_host and parsed.hostname.lower() != allowed_host.lower():
            return False

        return True

    except (ValueError, TypeError):
        return False


def format_date(value):

    if not value:
        return STATIC_LASTMOD

    try:
        if isinstance(value, datetime):
            return value.date().isoformat()

        value = str(value).replace("Z", "+00:00")

        return datetime.fromisoformat(value).date().isoformat()

    except (ValueError, TypeError):
        return STATIC_LASTMOD


# ==========================================
# MOVIE IDENTIFICATION
# ==========================================

def get_movie_id(movie):

    video_url = movie.get("video", "")

    if not isinstance(video_url, str):
        return None

    try:
        path = urlparse(video_url).path
    except ValueError:
        return None

    match = re.search(
        r"/(movie\d{5})\.mp4$",
        path,
        re.IGNORECASE
    )

    return match.group(1).lower() if match else None


def generate_watch_url(movie_id):

    query = urlencode({
        "id": movie_id
    })

    return f"{SITE_URL}/watch?{query}"


# ==========================================
# MOVIE DATA VALIDATION
# ==========================================

def validate_movie(movie):

    if not isinstance(movie, dict):
        return False

    # Explicit approval required
    if movie.get("seoEligible") is not True:
        return False

    title = movie.get("title")
    image_url = movie.get("img")
    video_url = movie.get("video")

    if not isinstance(title, str) or not title.strip():
        return False

    if not is_valid_https_url(image_url, R2_HOST):
        return False

    if not is_valid_https_url(video_url, R2_HOST):
        return False

    if not get_movie_id(movie):
        return False

    # Do not automatically publish ambiguous or
    # potentially exploitative material in the sitemap.
    blocked_terms = [
        "ချောင်းရိုက်",
        "မသိတတ်သေးတဲအရွယ်",
        "မသိတတ်သေးတဲ့အရွယ်",
        "အရွယ်နုနုလေး",
        "စဖုတ်အကင်းလေး"
    ]

    normalized_title = title.casefold()

    if any(term.casefold() in normalized_title
           for term in blocked_terms):
        return False

    return True


# ==========================================
# STATIC WEBSITE PAGES
# ==========================================

def add_static_page(
    urlset,
    path,
    lastmod,
    changefreq,
    priority
):

    url = ET.SubElement(urlset, xml_tag("url"))

    ET.SubElement(
        url,
        xml_tag("loc")
    ).text = f"{SITE_URL}{path}"

    ET.SubElement(
        url,
        xml_tag("lastmod")
    ).text = lastmod

    ET.SubElement(
        url,
        xml_tag("changefreq")
    ).text = changefreq

    ET.SubElement(
        url,
        xml_tag("priority")
    ).text = priority


# ==========================================
# IMAGE SITEMAP
# ==========================================

def add_movie_image(url, image_url, title):

    image = ET.SubElement(
        url,
        xml_tag("image", IMAGE_NS)
    )

    ET.SubElement(
        image,
        xml_tag("loc", IMAGE_NS)
    ).text = image_url

    ET.SubElement(
        image,
        xml_tag("title", IMAGE_NS)
    ).text = title


# ==========================================
# VIDEO SITEMAP
# ==========================================

def add_movie_video(url, movie, movie_url):

    title = movie["title"].strip()

    description = str(
        movie.get("description") or title
    ).strip()

    video_url = movie["video"]
    image_url = movie["img"]

    video = ET.SubElement(
        url,
        xml_tag("video", VIDEO_NS)
    )

    ET.SubElement(
        video,
        xml_tag("thumbnail_loc", VIDEO_NS)
    ).text = image_url

    ET.SubElement(
        video,
        xml_tag("title", VIDEO_NS)
    ).text = title[:100]

    ET.SubElement(
        video,
        xml_tag("description", VIDEO_NS)
    ).text = description[:2048]

    ET.SubElement(
        video,
        xml_tag("content_loc", VIDEO_NS)
    ).text = video_url

    ET.SubElement(
        video,
        xml_tag("player_loc", VIDEO_NS)
    ).text = movie_url

    # Adult content must not be represented as family-friendly.
    ET.SubElement(
        video,
        xml_tag("family_friendly", VIDEO_NS)
    ).text = "no"

    # Optional publication date
    created_at = movie.get("createdAt")

    if created_at:

        try:
            parsed_date = datetime.fromisoformat(
                str(created_at).replace("Z", "+00:00")
            )

            ET.SubElement(
                video,
                xml_tag("publication_date", VIDEO_NS)
            ).text = parsed_date.isoformat()

        except (ValueError, TypeError):
            pass

    # Optional duration in seconds
    duration = movie.get("duration")

    if isinstance(duration, int) and 0 < duration <= 28800:

        ET.SubElement(
            video,
            xml_tag("duration", VIDEO_NS)
        ).text = str(duration)


# ==========================================
# ADD INDIVIDUAL MOVIE
# ==========================================

def add_movie_page(urlset, movie):

    if not validate_movie(movie):
        return False

    movie_id = get_movie_id(movie)

    title = movie["title"].strip()

    movie_url = generate_watch_url(movie_id)

    if len(movie_url) > 2048:
        print(f"WARNING: URL too long: {movie_id}")
        return False

    url = ET.SubElement(
        urlset,
        xml_tag("url")
    )

    ET.SubElement(
        url,
        xml_tag("loc")
    ).text = movie_url

    ET.SubElement(
        url,
        xml_tag("lastmod")
    ).text = format_date(
        movie.get("createdAt")
    )

    ET.SubElement(
        url,
        xml_tag("changefreq")
    ).text = "weekly"

    ET.SubElement(
        url,
        xml_tag("priority")
    ).text = "0.8"

    add_movie_image(
        url,
        movie["img"],
        title
    )

    add_movie_video(
        url,
        movie,
        movie_url
    )

    return True


# ==========================================
# MAIN SITEMAP GENERATOR
# ==========================================

def generate_sitemap():

    if not os.path.exists(MOVIES_JSON):

        raise FileNotFoundError(
            f"{MOVIES_JSON} was not found."
        )

    with open(
        MOVIES_JSON,
        "r",
        encoding="utf-8"
    ) as file:

        movies = json.load(file)

    if not isinstance(movies, list):

        raise ValueError(
            "movies.json must contain a JSON array."
        )

    urlset = ET.Element(
        xml_tag("urlset")
    )

    # ======================================
    # 1. HOME PAGE
    # ======================================

    add_static_page(
        urlset,
        "/",
        STATIC_LASTMOD,
        "daily",
        "1.0"
    )

    # ======================================
    # 2. MOVIES PAGE
    # ======================================

    add_static_page(
        urlset,
        "/movies.html",
        STATIC_LASTMOD,
        "daily",
        "0.9"
    )

    # ======================================
    # 3. MOVIE PAGES
    # ======================================

    movie_count = 0

    seen_ids = set()
    seen_urls = set()

    skipped_count = 0

    for movie in movies:

        if not isinstance(movie, dict):
            skipped_count += 1
            continue

        movie_id = get_movie_id(movie)

        if not movie_id:
            skipped_count += 1
            continue

        movie_url = generate_watch_url(movie_id)

        if movie_id in seen_ids or movie_url in seen_urls:
            print(f"WARNING: Duplicate movie skipped: {movie_id}")
            skipped_count += 1
            continue

        if add_movie_page(urlset, movie):

            movie_count += 1

            seen_ids.add(movie_id)
            seen_urls.add(movie_url)

        else:
            skipped_count += 1

    # ======================================
    # 4. CONTACT PAGE
    # ======================================

    add_static_page(
        urlset,
        "/contact.html",
        STATIC_LASTMOD,
        "monthly",
        "0.3"
    )

    # ======================================
    # 5. XML VALIDATION
    # ======================================

    tree = ET.ElementTree(urlset)

    ET.indent(
        tree,
        space="  ",
        level=0
    )

    # ======================================
    # 6. WRITE SITEMAP
    # ======================================

    tree.write(
        SITEMAP_FILE,
        encoding="UTF-8",
        xml_declaration=True
    )

    # Verify generated XML
    ET.parse(SITEMAP_FILE)

    # ======================================
    # 7. RESULT
    # ======================================

    print()
    print("======================================")
    print(" SITEMAP GENERATED SUCCESSFULLY")
    print("======================================")

    print(f"Static Pages    : 3")
    print(f"Approved Movies : {movie_count}")
    print(f"Skipped Movies  : {skipped_count}")
    print(f"Total URLs      : {movie_count + 3}")

    print(f"Output File     : {SITEMAP_FILE}")

    print("======================================")
    print()


# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":

    generate_sitemap()
