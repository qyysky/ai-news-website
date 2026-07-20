#!/usr/bin/env python3
"""Collect publicly available recruitment information for Xiangyang.

The script deliberately only reads pages that are viewable without an account.
It does not collect résumés, contact details, or content from login-protected
recruitment platforms.
"""
import html
import json
import re
import ssl
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "news.json"
MAX_ITEMS = 36
USER_AGENT = "Xiangyang-Jobs-Daily/1.0 (+public-information-aggregator)"
GOOGLE_NEWS_RSS = (
    "https://news.google.com/rss/search?q=%E8%A5%84%E9%98%B3+%E6%8B%9B%E8%81%98+when%3A14d"
    "&hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans"
)
TALENT_PLATFORM = "https://www.xyrczhfw.cn/recruit/index.html"
RECRUITMENT_WORDS = ("招聘", "招录", "引进", "招募", "聘用", "岗位")
LOCATION_WORDS = ("襄阳", "襄城", "樊城", "襄州", "枣阳", "宜城", "老河口", "南漳", "谷城", "保康")


class LinkCollector(HTMLParser):
    """Capture links and the immediately following date marker from the portal."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self._href = ""
        self._title = ""
        self._text = []
        self._last = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "a":
            self._href = attributes.get("href", "")
            self._title = attributes.get("title", "")
            self._text = []
        elif tag == "span" and self._last is not None:
            self._text = []

    def handle_data(self, data):
        self._text.append(data)

    def handle_endtag(self, tag):
        value = " ".join(self._text).strip()
        if tag == "a" and self._href:
            title = self._title or value
            if title:
                self.links.append({"title": title, "href": self._href, "date": "", "has_title": bool(self._title)})
                self._last = len(self.links) - 1
            self._href = ""
            self._title = ""
            self._text = []
        elif tag == "span" and self._last is not None and re.fullmatch(r"\d{2}\.\d{2}", value):
            self.links[self._last]["date"] = value


def fetch_bytes(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30, context=ssl.create_default_context()) as response:
        return response.read()


def clean(value):
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()


def parse_date(value, fallback=None):
    fallback = fallback or datetime.now(timezone.utc)
    if not value:
        return fallback
    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc)
    except (TypeError, ValueError):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            pass
    match = re.fullmatch(r"(\d{2})\.(\d{2})", value)
    if match:
        now = datetime.now(timezone.utc)
        month, day = map(int, match.groups())
        try:
            candidate = now.replace(month=month, day=day, hour=0, minute=0, second=0, microsecond=0)
            if candidate > now:
                candidate = candidate.replace(year=candidate.year - 1)
            return candidate
        except ValueError:
            return fallback
    return fallback


def item(title, url, source, published, kind):
    return {
        "title": clean(title), "url": url, "source": source,
        "published": published.astimezone(timezone.utc).isoformat(), "kind": kind,
    }


def fetch_talent_platform():
    parser = LinkCollector()
    parser.feed(fetch_bytes(TALENT_PLATFORM).decode("utf-8", errors="replace"))
    items = []
    for link in parser.links:
        url = urljoin(TALENT_PLATFORM, link["href"])
        path = urlparse(url).path
        title = clean(link["title"])
        if "/recruit/show/id/" in path and link["has_title"] and any(word in title for word in RECRUITMENT_WORDS):
            items.append(item(title, url, "襄阳人才综合服务平台", parse_date(link["date"]), "招聘公告"))
        elif "/recruit/shdetail/id/" in path:
            items.append(item(title, url, "襄阳人才综合服务平台", parse_date(link["date"]), "企业岗位"))
    return items


def xml_text(entry, tag):
    node = entry.find(tag)
    return (node.text or "").strip() if node is not None else ""


def fetch_google_news():
    root = ET.fromstring(fetch_bytes(GOOGLE_NEWS_RSS))
    results = []
    for entry in root.findall(".//item"):
        title = clean(xml_text(entry, "title"))
        url = xml_text(entry, "link")
        published = parse_date(xml_text(entry, "pubDate"))
        if title and url and any(word in title for word in RECRUITMENT_WORDS) and any(place in title for place in LOCATION_WORDS):
            results.append(item(title, url, "公开资讯检索", published, "招聘资讯"))
    return results


def main():
    collected = []
    for name, fetcher in (("襄阳人才综合服务平台", fetch_talent_platform), ("公开资讯检索", fetch_google_news)):
        try:
            fetched = fetcher()
            print(f"{name}: {len(fetched)} items")
            collected.extend(fetched)
        except Exception as error:
            print(f"Unable to fetch {name}: {error}")

    # A portal may link to an item more than once (for example in a carousel).
    seen, unique = set(), []
    for record in sorted(collected, key=lambda value: value["published"], reverse=True):
        key = record["url"] or re.sub(r"\W+", "", record["title"]).lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(record)
    if not unique and OUTPUT.exists():
        print("No source succeeded; keeping the previously published data")
        return
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "location": "湖北省襄阳市",
        "sources": ["襄阳人才综合服务平台", "公开资讯检索"],
        "items": unique[:MAX_ITEMS],
    }
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(payload['items'])} recruitment items")


if __name__ == "__main__":
    main()
