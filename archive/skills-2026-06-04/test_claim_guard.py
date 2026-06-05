from pathlib import Path
import importlib.util


ROOT = Path(__file__).resolve().parents[1]
CLAIM_GUARD = ROOT / "skills" / "solo-mining" / "examples" / "claim_guard.py"


def load_claim_guard():
    spec = importlib.util.spec_from_file_location("claim_guard", CLAIM_GUARD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_claim_guard_rejects_erc20_approve():
    guard = load_claim_guard()
    result = guard.inspect_calldata("0x095ea7b300000000")
    assert result["ok"] is False
    assert "approve" in result["reason"]


def test_claim_guard_rejects_erc721_set_approval_for_all():
    guard = load_claim_guard()
    result = guard.inspect_calldata("0xa22cb46500000000")
    assert result["ok"] is False
    assert "setApprovalForAll" in result["reason"]


def test_claim_guard_allows_unknown_selector_for_review_only():
    guard = load_claim_guard()
    result = guard.inspect_calldata("0x1234567800000000")
    assert result["ok"] is True
    assert result["selector"] == "0x12345678"


def test_read_only_scripts_do_not_send_transactions_or_request_secrets():
    scripts = [
        ROOT / "skills" / "solo-mining" / "examples" / "read_only_eth_balance.py",
        ROOT / "skills" / "solo-mining" / "examples" / "read_only_btc_balance.py",
    ]
    forbidden = [
        "eth_sendTransaction",
        "eth_sendRawTransaction",
        "private_key",
        "seed_phrase",
        "mnemonic",
    ]
    for script in scripts:
        text = script.read_text(encoding="utf-8")
        present = [item for item in forbidden if item in text]
        assert present == []
