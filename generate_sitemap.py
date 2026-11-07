import os
import json
import base64
import xml.etree.ElementTree as ET

from datetime import date, datetime
from urllib.parse import urlencode


# ==========================================
# WEBSITE CONFIGURATION
# ==========================================

SITE_URL = "https://drsamangyi.com"

MOVIES_JSON = "movies.json"
SITEMAP_FILE = "sitemap.xml"

# မူလ sitemap.xml ထဲက Static Pages များ၏ Last Modified Date
STATIC_LASTMOD = "2026-11-08"


# ==========================================
# XML NAMESPACES
# ==========================================

NS = "http://www.sitemaps.org/schemas/sitemap/0.9"

IMAGE_NS = "http://www.google.com/schemas/sitemap-image/1.1"

ET.register_namespace("", NS)
ET.register_namespace("image", IMAGE_NS)


def xml_tag(name, namespace=NS):
    return f"{{{namespace}}}{name}"


# ==========================================
# FORMAT LAST MODIFIED DATE
# ==========================================

def format_date(value):

    if not value:
        return date.today().isoformat()

    try:
        if isinstance(value, datetime):
            return value.date().isoformat()

        value = str(value).replace("Z", "+00:00")

        return datetime.fromisoformat(value).date().isoformat()

    except (ValueError, TypeError):
        return date.today().isoformat()


# ==========================================
# ADD STATIC WEBSITE PAGES
# ==========================================

def add_static_page(urlset, path, lastmod, changefreq, priority):

    url = ET.SubElement(urlset, xml_tag("url"))

    ET.SubElement(url, xml_tag("loc")).text = (
        f"{SITE_URL}{path}"
    )

    ET.SubElement(url, xml_tag("lastmod")).text = lastmod

    ET.SubElement(url, xml_tag("changefreq")).text = changefreq

    ET.SubElement(url, xml_tag("priority")).text = priority


# ==========================================
# GENERATE WATCH PAGE URL
# Compatible with current watch.html
# ==========================================

def generate_watch_url(movie):

    title = str(
        movie.get("title") or "drsamangyi Exclusive Movie"
    )

    video_url = movie.get("video")

    if not video_url:
        return None

    # UTF-8 Base64 encoding
    encoded_video = base64.b64encode(
        video_url.encode("utf-8")
    ).decode("ascii")

    # watch.html uses:
    # ?title=MOVIE_TITLE&v=BASE64_VIDEO_URL

    query_parameters = urlencode({
        "title": title,
        "v": encoded_video
    })

    return f"{SITE_URL}/watch.html?{query_parameters}"


# ==========================================
# ADD INDIVIDUAL MOVIE TO SITEMAP
# ==========================================

def add_movie_page(urlset, movie):

    title = str(
        movie.get("title") or "drsamangyi Exclusive Movie"
    )

    movie_url = generate_watch_url(movie)

    if not movie_url:
        return False

    # Google Sitemap URL limit
    if len(movie_url) > 2048:
        print(
            f"WARNING: Movie URL is too long. Skipped: {title}"
        )
        return False

    url = ET.SubElement(urlset, xml_tag("url"))

    # Movie Watch URL
    ET.SubElement(url, xml_tag("loc")).text = movie_url

    # Movie Last Modified Date
    ET.SubElement(url, xml_tag("lastmod")).text = (
        format_date(movie.get("createdAt"))
    )

    ET.SubElement(url, xml_tag("changefreq")).text = "weekly"

    ET.SubElement(url, xml_tag("priority")).text = "0.8"

    # ======================================
    # MOVIE THUMBNAIL IMAGE
    # ======================================

    image_url = movie.get("img")

    if image_url:

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

    return True


# ==========================================
# MAIN SITEMAP GENERATOR
# ==========================================

def generate_sitemap():

    # Check movies.json
    if not os.path.exists(MOVIES_JSON):

        raise FileNotFoundError(
            f"{MOVIES_JSON} was not found."
        )

    # Read movies.json
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

    # Create Sitemap Root
    urlset = ET.Element(xml_tag("urlset"))

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
    # 2. MOVIES LIST PAGE
    # ======================================

    add_static_page(
        urlset,
        "/movies.html",
        STATIC_LASTMOD,
        "daily",
        "0.9"
    )

    # ======================================
    # 3. INDIVIDUAL MOVIE PAGES
    # ======================================

    movie_count = 0

    for movie in movies:

        if not isinstance(movie, dict):
            continue

        if add_movie_page(urlset, movie):
            movie_count += 1

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
    # WRITE SITEMAP.XML
    # ======================================

    tree = ET.ElementTree(urlset)

    ET.indent(
        tree,
        space="  ",
        level=0
    )

    tree.write(
        SITEMAP_FILE,
        encoding="UTF-8",
        xml_declaration=True
    )

    # ======================================
    # RESULT
    # ======================================

    print("======================================")
    print(" SITEMAP GENERATED SUCCESSFULLY")
    print("======================================")

    print(f"Static Pages : 3")
    print(f"Movie Pages  : {movie_count}")
    print(f"Total URLs   : {movie_count + 3}")

    print(f"Output File  : {SITEMAP_FILE}")

    print("======================================")


# ==========================================
# RUN SCRIPT
# ==========================================

if __name__ == "__main__":

    generate_sitemap()
