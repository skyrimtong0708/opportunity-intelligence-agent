from __future__ import annotations

import json
import hashlib
import hmac
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import Evidence, MediaSignal, ProductCandidate


def _stable_id(prefix: str, *values: str) -> str:
    digest = hashlib.sha256("|".join(values).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def _json_request(url: str, *, headers: dict[str, str] | None = None, body: dict | None = None) -> dict:
    encoded = json.dumps(body).encode("utf-8") if body is not None else None
    request = Request(url, data=encoded, headers=headers or {}, method="POST" if body is not None else "GET")
    with urlopen(request, timeout=30) as response:  # noqa: S310 - endpoints are fixed by adapters
        return json.loads(response.read().decode("utf-8"))


class SourceAdapter(ABC):
    """Contract for lawful sources. Adapters must honor robots.txt, ToS and rate limits."""

    @abstractmethod
    def collect(self, niche_id: str) -> list[Evidence]:
        raise NotImplementedError


class JsonlSampleAdapter(SourceAdapter):
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def collect(self, niche_id: str) -> list[Evidence]:
        items: list[Evidence] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record["niche_id"] == niche_id:
                items.append(Evidence(**record))
        return items


class RssAdapter(SourceAdapter):
    """Public RSS/Atom stub. Add an allowlisted feed and conditional GET before enabling."""

    def __init__(self, feed_urls: list[str]):
        self.feed_urls = feed_urls

    def collect(self, niche_id: str) -> list[Evidence]:
        return []


class PublicApiAdapter(SourceAdapter):
    """Public/official API stub; deliberately performs no network request in the MVP."""

    def __init__(self, endpoints: list[str]):
        self.endpoints = endpoints

    def collect(self, niche_id: str) -> list[Evidence]:
        return []


class ProductSourceAdapter(ABC):
    @abstractmethod
    def collect_products(self, niche_id: str) -> list[ProductCandidate]:
        raise NotImplementedError


class MediaSourceAdapter(ABC):
    @abstractmethod
    def collect_media(self, niche_id: str) -> list[MediaSignal]:
        raise NotImplementedError


class JsonlProductAdapter(ProductSourceAdapter):
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def collect_products(self, niche_id: str) -> list[ProductCandidate]:
        return [
            ProductCandidate(**record)
            for record in (json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip())
            if record["niche_id"] == niche_id
        ]


class JsonlMediaAdapter(MediaSourceAdapter):
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def collect_media(self, niche_id: str) -> list[MediaSignal]:
        return [
            MediaSignal(**record)
            for record in (json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip())
            if record["niche_id"] == niche_id
        ]


class YouTubeDataApiAdapter(MediaSourceAdapter):
    """Official YouTube Data API v3 adapter. Requires YOUTUBE_API_KEY."""

    SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
    VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

    def __init__(self, queries: list[str], api_key: str | None = None, max_results: int = 10):
        self.queries = queries
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        self.max_results = min(max(max_results, 1), 50)

    def collect_media(self, niche_id: str) -> list[MediaSignal]:
        if not self.api_key:
            return []
        results: dict[str, MediaSignal] = {}
        for query in self.queries:
            params = urlencode({"part": "snippet", "q": query, "type": "video", "maxResults": self.max_results,
                                "regionCode": "VN", "relevanceLanguage": "vi", "key": self.api_key})
            payload = _json_request(f"{self.SEARCH_URL}?{params}")
            video_ids = [item.get("id", {}).get("videoId") for item in payload.get("items", [])]
            video_ids = [item for item in video_ids if item]
            stats: dict[str, dict] = {}
            if video_ids:
                stats_params = urlencode({"part": "statistics", "id": ",".join(video_ids), "key": self.api_key})
                stats = {item["id"]: item.get("statistics", {}) for item in _json_request(f"{self.VIDEOS_URL}?{stats_params}").get("items", [])}
            for item in payload.get("items", []):
                video_id = item.get("id", {}).get("videoId")
                if not video_id:
                    continue
                snippet = item.get("snippet", {})
                metrics = stats.get(video_id, {})
                results[video_id] = MediaSignal(
                    id=_stable_id("media", "youtube", video_id), niche_id=niche_id, platform="YouTube",
                    source_type="official_api", source_url=f"https://www.youtube.com/watch?v={video_id}",
                    title=snippet.get("title", ""), description=snippet.get("description", ""),
                    creator=snippet.get("channelTitle", ""), published_at=snippet.get("publishedAt", ""), query=query,
                    view_count=int(metrics.get("viewCount", 0)), like_count=int(metrics.get("likeCount", 0)),
                    comment_count=int(metrics.get("commentCount", 0)), metadata={"api": "youtube_data_v3"},
                )
        return list(results.values())


class TikTokDisplayApiAdapter(MediaSourceAdapter):
    """Official Display API adapter for videos authorized by their creator; not public search."""

    URL = "https://open.tiktokapis.com/v2/video/list/?fields=id,title,video_description,duration,cover_image_url,share_url,create_time,like_count,comment_count,share_count,view_count"

    def __init__(self, queries: list[str], access_token: str | None = None):
        self.queries = [query.lower() for query in queries]
        self.access_token = access_token or os.getenv("TIKTOK_DISPLAY_ACCESS_TOKEN")

    def collect_media(self, niche_id: str) -> list[MediaSignal]:
        if not self.access_token:
            return []
        payload = _json_request(self.URL, headers={"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}, body={"max_count": 20})
        results = []
        for item in payload.get("data", {}).get("videos", []):
            text = f"{item.get('title', '')} {item.get('video_description', '')}".lower()
            query = next((query for query in self.queries if query in text), "creator-authorized feed")
            if self.queries and query == "creator-authorized feed":
                continue
            video_id = str(item.get("id", ""))
            results.append(MediaSignal(
                id=_stable_id("media", "tiktok", video_id), niche_id=niche_id, platform="TikTok",
                source_type="creator_authorized_api", source_url=item.get("share_url", ""),
                title=item.get("title") or item.get("video_description", "Untitled TikTok"),
                description=item.get("video_description", ""), creator="authorized creator",
                published_at=datetime.fromtimestamp(int(item.get("create_time", 0)), tz=timezone.utc).isoformat(), query=query,
                view_count=int(item.get("view_count", 0)), like_count=int(item.get("like_count", 0)),
                comment_count=int(item.get("comment_count", 0)), metadata={"api": "tiktok_display_v2"},
            ))
        return results


class ShopeeOpenPlatformAdapter(ProductSourceAdapter):
    """Official Shopee seller-authorized catalog adapter; it does not crawl public search pages."""

    BASE_URL = "https://partner.shopeemobile.com"

    def __init__(self, problem_tags: list[str]):
        self.problem_tags = problem_tags
        self.partner_id = os.getenv("SHOPEE_PARTNER_ID")
        self.partner_key = os.getenv("SHOPEE_PARTNER_KEY")
        self.shop_id = os.getenv("SHOPEE_SHOP_ID")
        self.access_token = os.getenv("SHOPEE_ACCESS_TOKEN")

    def _get(self, path: str, request_params: dict[str, str | int]) -> dict:
        if not all([self.partner_id, self.partner_key, self.shop_id, self.access_token]):
            return {}
        timestamp = int(time.time())
        base = f"{self.partner_id}{path}{timestamp}{self.access_token}{self.shop_id}"
        signature = hmac.new(self.partner_key.encode(), base.encode(), hashlib.sha256).hexdigest()
        common = {"partner_id": self.partner_id, "timestamp": timestamp, "shop_id": self.shop_id,
                  "access_token": self.access_token, "sign": signature}
        return _json_request(f"{self.BASE_URL}{path}?{urlencode(common | request_params)}")

    def collect_products(self, niche_id: str) -> list[ProductCandidate]:
        if not all([self.partner_id, self.partner_key, self.shop_id, self.access_token]):
            return []
        listing = self._get("/api/v2/product/get_item_list", {"offset": 0, "page_size": 100, "item_status": "NORMAL"})
        ids = [str(item["item_id"]) for item in listing.get("response", {}).get("item", [])]
        results = []
        for start in range(0, len(ids), 50):
            details = self._get("/api/v2/product/get_item_base_info", {"item_id_list": ",".join(ids[start:start + 50])})
            for item in details.get("response", {}).get("item_list", []):
                prices = item.get("price_info", [])
                price = float(prices[0].get("current_price", 0)) if prices else 0.0
                item_id = str(item.get("item_id"))
                results.append(ProductCandidate(
                    id=_stable_id("product", "shopee", self.shop_id or "", item_id), niche_id=niche_id,
                    source_type="seller_authorized_api", source_name="Shopee Open Platform",
                    source_url=f"https://shopee.vn/product/{self.shop_id}/{item_id}", title=item.get("item_name", ""),
                    supplier_name=f"Authorized shop {self.shop_id}", marketplace="Shopee", price=price, currency=item.get("currency", "VND"),
                    min_order_quantity=1, shipping_origin="authorized shop", rating=None, review_count=0, sold_count=0,
                    problem_tags=self.problem_tags, dimensions={"pain_fit": 5, "demand_signal": 3, "repeat_purchase": 5,
                    "gross_margin_potential": 4, "supplier_reliability": 6, "differentiation": 4, "ease_of_test": 8},
                    metadata={"api": "shopee_open_platform_v2", "shop_authorized": True},
                ))
        return results
