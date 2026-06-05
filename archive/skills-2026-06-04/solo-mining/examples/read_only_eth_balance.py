from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request


def rpc_call(rpc_url: str, method: str, params: list[object]) -> dict:
    payload = json.dumps({
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
    }).encode("utf-8")
    request = urllib.request.Request(
        rpc_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: python read_only_eth_balance.py <rpc_url> <0x_address>")
        return 2

    rpc_url, address = sys.argv[1], sys.argv[2]
    if not address.startswith("0x") or len(address) != 42:
        raise ValueError("expected a 20-byte 0x Ethereum address")

    data = rpc_call(rpc_url, "eth_getBalance", [address, "latest"])
    if "result" not in data:
        raise RuntimeError(data)
    wei = int(data["result"], 16)
    print(json.dumps({
        "address": address,
        "eth": wei / 10**18,
        "method": "eth_getBalance",
        "mode": "read_only",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.URLError as exc:
        raise SystemExit(f"rpc_error: {exc}") from exc
