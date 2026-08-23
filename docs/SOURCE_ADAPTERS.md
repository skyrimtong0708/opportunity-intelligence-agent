# Source adapter policy and setup

This project separates three things that are often mixed together:

1. **Problem evidence**: observations that may support a pain-point hypothesis.
2. **Media signals**: content worth human review; views are not treated as willingness to pay.
3. **Product candidates**: possible supply-side offers; listing popularity is not treated as product-market fit.

Network adapters remain inert until their official credentials are supplied. Credentials are read from environment variables and are never written to snapshots.

## YouTube

`YouTubeDataApiAdapter` uses the official YouTube Data API v3 `search.list` and `videos.list` endpoints. It searches configured niche queries for Vietnamese-region videos and attaches public statistics. Set `YOUTUBE_API_KEY`.

Operational controls required before scheduled use:

- restrict the key to YouTube Data API and the production caller;
- enforce a daily request budget and cache IDs already collected;
- store metadata and source URLs, not downloaded video files;
- send candidates to human review before promoting them to problem evidence.

## TikTok

`TikTokDisplayApiAdapter` uses TikTok Display API for a creator who explicitly authorizes the app. It does **not** search TikTok globally. Set `TIKTOK_DISPLAY_ACCESS_TOKEN`; the adapter filters that authorized feed against niche queries.

TikTok Research Tools are intentionally not enabled for commercial opportunity discovery. TikTok states that access is for approved independent/academic, non-profit research. If a future use case qualifies, implement it as a separately approved adapter and record the approval basis.

For broader commercial discovery, use creator-consented exports, licensed analytics data, or manually curated URLs under the applicable terms.

## Shopee

`ShopeeOpenPlatformAdapter` uses signed Shopee Open Platform v2 seller-authorized calls. It reads only the catalog of a shop that granted access; it does not scrape public search pages. Set:

- `SHOPEE_PARTNER_ID`
- `SHOPEE_PARTNER_KEY`
- `SHOPEE_SHOP_ID`
- `SHOPEE_ACCESS_TOKEN`

Shopee Affiliate access is a separate program. Add a dedicated adapter only after receiving its credentials and current API contract. For supplier discovery without an approved API, import a seller/affiliate export into the product contract instead of crawling Shopee pages.

## Sample data

`data/sample/products.jsonl` and `data/sample/media_signals.jsonl` are synthetic fixtures. `sample://` URLs are deliberately non-navigable. Ratings, sales, prices, views and engagement are invented solely to exercise ranking and UI behavior.

## Promotion gate

A media or product record can influence an opportunity score only after:

- source authorization is recorded;
- the observation is manually reviewed;
- duplicate/affiliate amplification is removed;
- price, stock and supplier identity are rechecked;
- a reviewer explicitly promotes it into the Evidence contract.

