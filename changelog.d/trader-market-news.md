### Market News panel on the stock trader (surfaces the existing RSS feed)

- The stock trader footer now has a **Market News** panel that surfaces the already-ingested market-news feed (`lib/news-collector.js` → Yahoo Finance RSS → `/api/trading/news/recent`). Each item shows `[source · timestamp · symbols]`, flags high-impact headlines, and links out to the original article in a new tab. (#1582)
- Reuses the existing local-first ingestion module and endpoint — **no new subsystem** and no paywalled API. Headlines are HTML-escaped; the panel degrades gracefully to "News feed offline" when the endpoint errors and "No market news yet" when it returns empty. Refreshes every 2 minutes.
