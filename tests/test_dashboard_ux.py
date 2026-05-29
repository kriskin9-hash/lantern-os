import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_chat_is_first_class_above_controls() -> None:
    html = read("apps/lantern-garage/public/index.html")
    assert html.index('id="chatPanel"') < html.index('aria-label="Primary controls"')
    assert 'class="panel chat-panel chat-primary"' in html
    assert "cloud tunnel" in html.lower()


def test_markdown_links_use_formatted_reader() -> None:
    html = read("apps/lantern-garage/public/index.html")
    raw_doc_links = re.findall(r'href="/repo/[^"]+\.md"', html)
    assert raw_doc_links == []
    assert "/view?path=docs/ARC-REACTOR-MINING-LAB.md" in html
    assert "/view?path=skills/solo-mining/SKILL.md" in html


def test_file_preview_routes_api_to_local_app() -> None:
    js = read("apps/lantern-garage/public/app.js")
    assert 'window.location.protocol === "file:"' in js
    assert "http://127.0.0.1:4177" in js
    assert "normalizeInternalLinks();" in js


def test_primary_controls_have_handlers() -> None:
    js = read("apps/lantern-garage/public/app.js")
    for control_id in [
        "refresh",
        "runLoop",
        "localControls",
        "flatRagIngest",
        "autoUpdate",
        "conversationForm",
        "ragForm",
        "noteForm",
        "dispatchAll",
    ]:
        assert f'$("#{control_id}")' not in js
        assert f'("{control_id}")' in js
    assert "/api/actions/run-loop" in js
    assert "/api/actions/local-controls" in js
    assert "/api/actions/flat-rag-ingest" in js


def test_chat_understands_mining_safely() -> None:
    js = read("apps/lantern-garage/public/app.js")
    assert "Rock and stone" in js
    assert "CPU routes to Monero" in js
    assert "BTC only belongs on owned SHA-256 ASIC hardware" in js
    assert "No wallet cracking" in js


def test_server_has_formatted_reader_and_cors_for_preview() -> None:
    server = read("apps/lantern-garage/server.js")
    assert 'url.pathname === "/view"' in server
    assert "renderMarkdownDocument" in server
    assert "Access-Control-Allow-Origin" in server
    assert "OPTIONS" in server
