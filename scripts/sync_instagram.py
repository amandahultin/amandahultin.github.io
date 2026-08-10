"""Fetch the latest Instagram posts for the connected Business account via
Meta's Instagram Graph API and save them as square thumbnails in
assets/instagram/. Run by .github/workflows/instagram-sync.yml on a schedule.

Requires env vars IG_ACCESS_TOKEN (long-lived token) and IG_USER_ID
(Instagram Business Account ID).
"""
import io
import os

import requests
from PIL import Image

TOKEN = os.environ["IG_ACCESS_TOKEN"]
USER_ID = os.environ["IG_USER_ID"]
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "instagram")
GRAPH_VERSION = "v21.0"


def main():
    resp = requests.get(
        f"https://graph.facebook.com/{GRAPH_VERSION}/{USER_ID}/media",
        params={
            "fields": "id,media_type,media_url,thumbnail_url,permalink,timestamp",
            "access_token": TOKEN,
            "limit": 6,
        },
        timeout=30,
    )
    resp.raise_for_status()
    items = [
        item for item in resp.json().get("data", [])
        if item.get("media_type") != "VIDEO" or item.get("thumbnail_url")
    ][:3]

    if not items:
        print("No media returned, leaving existing thumbnails untouched.")
        return

    os.makedirs(OUT_DIR, exist_ok=True)
    for i, item in enumerate(items, start=1):
        url = item.get("thumbnail_url") or item.get("media_url")
        if not url:
            continue
        img_resp = requests.get(url, timeout=30)
        img_resp.raise_for_status()
        im = Image.open(io.BytesIO(img_resp.content)).convert("RGB")

        w, h = im.size
        side = min(w, h)
        left, top = (w - side) // 2, (h - side) // 2
        im = im.crop((left, top, left + side, top + side))
        im.thumbnail((640, 640), Image.LANCZOS)
        im.save(os.path.join(OUT_DIR, f"{i}.jpg"), quality=82, optimize=True)
        print(f"Saved {i}.jpg from {item.get('permalink')}")


if __name__ == "__main__":
    main()
