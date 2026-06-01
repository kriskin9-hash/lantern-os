import json, urllib.request, datetime
from collections import defaultdict

def fetch(url):
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())

now = datetime.datetime.now(datetime.timezone.utc)
markets_by_ticker = {}
for s in ['KXMLBGAME', 'KXMLBSPREAD', 'KXMLBTOTAL', 'KXMLBHRR']:
    data = fetch(f'https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker={s}&limit=100')
    for m in data.get('markets', []):
        t = m.get('ticker')
        if t and t not in markets_by_ticker:
            markets_by_ticker[t] = m

active = []
for t, m in markets_by_ticker.items():
    if m.get('status') != 'active':
        continue
    close = m.get('close_time', '')
    if not close:
        continue
    try:
        close_dt = datetime.datetime.fromisoformat(close.replace('Z', '+00:00'))
    except Exception:
        continue
    if close_dt < now:
        continue
    ya = float(m.get('yes_ask_dollars', 0) or 0)
    na = float(m.get('no_ask_dollars', 0) or 0)
    if ya == 0 and na == 0:
        continue
    active.append(m)

events = defaultdict(list)
for m in active:
    t = m['ticker']
    parts = t.rsplit('-', 1)
    event_key = parts[0] if len(parts) == 2 else t
    events[event_key].append(m)

def event_score(ms):
    return sum(float(m.get('volume_24h_fp', 0) or 0) for m in ms)

sorted_events = sorted(events.items(), key=lambda x: event_score(x[1]), reverse=True)

lines = []
lines.append("Kalshi MLB Odds — Top Active Games (by volume)")
lines.append(f"Checked at {now.isoformat()[:16]} UTC")
lines.append("")

for event_key, ms in sorted_events[:6]:
    total_vol = sum(float(m.get('volume_24h_fp', 0) or 0) for m in ms)
    close = ms[0].get('close_time', '')[:16]
    # Extract matchup from first GAME market
    game = None
    for m in ms:
        if 'GAME' in m['ticker'] and 'Winner' in m.get('title', ''):
            game = m
            break
    if game:
        title = game['title'].replace(' Winner?', '')
    else:
        title = event_key
    lines.append(f"{title}  |  Close: {close}  |  Vol24h: {total_vol:,.0f}")
    
    # Moneyline
    ml = []
    for m in ms:
        if 'GAME' in m['ticker'] and 'Winner' in m.get('title', ''):
            side = m['ticker'].split('-')[-1]
            yb = float(m.get('yes_bid_dollars', 0) or 0)
            ya = float(m.get('yes_ask_dollars', 0) or 0)
            ml.append((side, yb, ya))
    if ml:
        parts = []
        for side, yb, ya in ml:
            mid = (yb + ya) / 2
            parts.append(f"{side} {mid:.0%}")
        lines.append("  Moneyline: " + "  |  ".join(parts))
    
    # Spread (most liquid)
    spreads = []
    for m in ms:
        if 'SPREAD' in m['ticker']:
            side = m['ticker'].split('-')[-1]
            vol = float(m.get('volume_24h_fp', 0) or 0)
            yb = float(m.get('yes_bid_dollars', 0) or 0)
            ya = float(m.get('yes_ask_dollars', 0) or 0)
            if vol > 1000:
                spreads.append((m['title'].replace('?', '').strip(), vol, yb, ya))
    if spreads:
        spreads.sort(key=lambda x: x[1], reverse=True)
        s = spreads[0]
        lines.append(f"  Spread: {s[0]} — YES {s[2]:.0%}/{s[3]:.0%}")
    
    # Total (most liquid)
    totals = []
    for m in ms:
        if 'TOTAL' in m['ticker']:
            vol = float(m.get('volume_24h_fp', 0) or 0)
            yb = float(m.get('yes_bid_dollars', 0) or 0)
            ya = float(m.get('yes_ask_dollars', 0) or 0)
            if vol > 500:
                totals.append((m['title'].replace('?', '').strip(), vol, yb, ya))
    if totals:
        totals.sort(key=lambda x: x[1], reverse=True)
        s = totals[0]
        lines.append(f"  Total:   {s[0]} — YES {s[2]:.0%}/{s[3]:.0%}")
    lines.append("")

print("\n".join(lines))
