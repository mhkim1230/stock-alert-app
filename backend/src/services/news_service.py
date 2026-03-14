import logging
from typing import Dict, List, Optional

import feedparser


class NewsService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.feeds = {
            "Bloomberg": "https://feeds.bloomberg.com/economics/news.rss",
            "MarketWatch": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
            "Reuters": "https://feeds.reuters.com/reuters/businessNews",
        }

    async def get_latest_news(self, query: Optional[str] = None, limit: int = 10) -> List[Dict[str, str]]:
        query_lower = query.lower() if query else None
        results: List[Dict[str, str]] = []
        for source_name, feed_url in self.feeds.items():
            try:
                feed = feedparser.parse(feed_url)
            except Exception as exc:
                self.logger.warning("Feed parse failed for %s: %s", source_name, exc)
                continue

            for entry in feed.entries:
                title = str(entry.get("title", ""))
                summary = str(entry.get("summary", ""))
                combined = f"{title} {summary}".lower()
                if query_lower and query_lower not in combined:
                    continue
                results.append(
                    {
                        "title": title,
                        "summary": summary[:240],
                        "url": str(entry.get("link", "")),
                        "published": str(entry.get("published", "")),
                        "source": source_name,
                    }
                )
                if len(results) >= limit:
                    return results
        return results[:limit]
