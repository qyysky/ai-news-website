#!/usr/bin/env python3
"""Fetch public AI news feeds and write data/news.json for GitHub Pages."""
import html
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "news.json"
FEEDS = [
    ("Google News", "https://news.google.com/rss/search?q=artificial+intelligence+when:1d&hl=en-US&gl=US&ceid=US:en"),
    ("Hugging Face", "https://huggingface.co/blog/feed.xml"),
]
MAX_ITEMS = 24

def text(element, tag):
    node = element.find(tag)
    return (node.text or "").strip() if node is not None else ""

def clean_title(value):
    return re.sub(r"\s+", " ", html.unescape(value)).strip()

def parse_date(value):
    if not value:
        return datetime.now(timezone.utc)
    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc)
    except (TypeError, ValueError):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            return datetime.now(timezone.utc)

def fetch(source, url):
    request = urllib.request.Request(url, headers={"User-Agent": "AI-Daily-GitHub-Action/1.0"})
    with urllib.request.urlopen(request, timeout=25) as response:
        root = ET.fromstring(response.read())
    entries = root.findall(".//item") or root.findall("{http://www.w3.org/2005/Atom}entry")
    result = []
    atom = "{http://www.w3.org/2005/Atom}"
    for entry in entries:
        title = text(entry, "title") or text(entry, atom + "title")
        link = text(entry, "link")
        if not link:
            link_el = entry.find(atom + "link")
            link = link_el.get("href", "") if link_el is not None else ""
        published = text(entry, "pubDate") or text(entry, atom + "published") or text(entry, atom + "updated")
        if title and link:
            result.append({"title": clean_title(title), "url": link, "source": source, "published": parse_date(published).isoformat()})
    return result

def main():
    items = []
    for source, url in FEEDS:
        try:
            items.extend(fetch(source, url))
        except Exception as error:
            print(f"Unable to fetch {source}: {error}")
    # Keep latest unique links. The site remains functional if one source fails.
    seen, unique = set(), []
    for item in sorted(items, key=lambda x: x["published"], reverse=True):
        if item["url"] not in seen:
            seen.add(item["url"]); unique.append(item)
    # Do not replace a healthy published edition with an empty file during a
    # temporary network or feed outage.
    if not unique and OUTPUT.exists():
        print("No feeds succeeded; keeping the previously published data")
        return
    payload = {"generated_at": datetime.now(timezone.utc).isoformat(), "items": unique[:MAX_ITEMS]}
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(payload['items'])} articles")

if __name__ == "__main__":
    main()
