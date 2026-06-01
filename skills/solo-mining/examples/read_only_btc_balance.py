from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request


def get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: python read_only_btc_balance.py <esplora_base_url> <btc_address>")
        return 2

    base, address = sys.argv[1].rstrip("/"), sys.argv[2]
    payload = get_json(f"{base}/address/{address}")
    chain = payload["chain_stats"]
    mempool = payload["mempool_stats"]

    confirmed_sat = chain["funded_txo_sum"] - chain["spent_txo_sum"]
    unconfirmed_sat = mempool["funded_txo_sum"] - mempool["spent_txo_sum"]
    print(json.dumps({
        "address": address,
        "confirmed_btc": confirmed_sat / 100_000_000,
        "unconfirmed_btc": unconfirmed_sat / 100_000_000,
        "mode": "watch_only",
        "privacy_note": "Third-party explorers can learn the address queried; self-host Esplora for better privacy.",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.URLError as exc:
        raise SystemExit(f"esplora_error: {exc}") from exc
