from __future__ import annotations

DANGEROUS = {
    "0x095ea7b3": "ERC-20 approve(address,uint256)",
    "0xa22cb465": "ERC-721 setApprovalForAll(address,bool)",
    "0x23b872dd": "transferFrom(address,address,uint256) -- review carefully",
}


def inspect_calldata(calldata_hex: str) -> dict[str, object]:
    calldata_hex = calldata_hex.strip().lower()
    if not calldata_hex.startswith("0x") or len(calldata_hex) < 10:
        return {"ok": False, "reason": "invalid calldata"}
    selector = calldata_hex[:10]
    if selector in DANGEROUS:
        return {"ok": False, "selector": selector, "reason": DANGEROUS[selector]}
    return {"ok": True, "selector": selector, "reason": "selector not on local denylist"}


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) != 2:
        print("usage: python claim_guard.py <calldata_hex>")
        raise SystemExit(2)
    print(json.dumps(inspect_calldata(sys.argv[1]), sort_keys=True))
