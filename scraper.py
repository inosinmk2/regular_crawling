import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

URL = "https://physics.utexas.edu/news"
BASE_URL = "https://physics.utexas.edu"
LAST_FILE = Path("last_items.json")
FEED_FILE = "feed.xml"


def scrape_items():
    res = requests.get(URL, timeout=10)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, "html.parser")

    items = []
    for h3 in soup.select("h3"):
        a = h3.find("a")
        if not a:
            continue

        # 日付テキストを取得（h3の次の兄弟要素）
        date_text = ""
        for sibling in h3.next_siblings:
            text = (
                sibling.get_text(strip=True)
                if hasattr(sibling, "get_text")
                else str(sibling).strip()
            )
            if text:
                date_text = text.split("•")[0].strip()
                break

        link = a["href"]
        if not link.startswith("http"):
            link = BASE_URL + link

        items.append({
            "title": a.get_text(strip=True),
            "link": link,
            "date": date_text,
            "id": hashlib.md5(link.encode()).hexdigest(),
        })

    return items


def load_last_ids():
    if LAST_FILE.exists():
        data = json.loads(LAST_FILE.read_text(encoding="utf-8"))
        return {i["id"] for i in data}
    return set()


def build_feed(items):
    fg = FeedGenerator()
    fg.title("UT Austin Physics – News")
    fg.link(href=URL)
    fg.description("Auto-generated RSS feed for UT Austin Physics news")
    fg.language("en")

    for item in items[:20]:
        fe = fg.add_entry()
        fe.id(item["id"])
        fe.title(item["title"])
        fe.link(href=item["link"])
        fe.published(datetime.now(timezone.utc))

    fg.rss_file(FEED_FILE)
    print(f"feed.xml を生成しましたわ（{len(items[:20])}件）")


if __name__ == "__main__":
    items = scrape_items()
    last_ids = load_last_ids()

    new_items = [i for i in items if i["id"] not in last_ids]
    print(f"新着: {len(new_items)}件 / 全体: {len(items)}件")

    LAST_FILE.write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    build_feed(items)