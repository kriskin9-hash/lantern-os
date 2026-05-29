import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_cloud_mirror_manifest_has_multiple_cloud_urls() -> None:
    manifest = json.loads((ROOT / "manifests" / "cloud-mirrors.json").read_text(encoding="utf-8"))
    mirrors = manifest["cloudMirrors"]
    urls = [item["url"] for item in mirrors]
    assert manifest["deployProvider"] == "Render"
    assert manifest["deployBranch"] == "master"
    assert len(urls) >= 2
    assert len(urls) == len(set(urls))
    assert all(url.startswith("https://") for url in urls)
    assert all("onrender.com" in url for url in urls)


def test_render_blueprint_uses_master_and_health_check() -> None:
    text = (ROOT / "render.yaml").read_text(encoding="utf-8")
    assert "branch: master" in text
    assert "rootDir: apps/lantern-garage" in text
    assert "healthCheckPath: /api/health" in text
    assert "LANTERN_CLOUD_MIRROR_URLS" in text


def test_server_supports_cloud_port_and_mirror_api() -> None:
    text = (ROOT / "apps" / "lantern-garage" / "server.js").read_text(encoding="utf-8")
    assert "process.env.PORT" in text
    assert "0.0.0.0" in text
    assert '"/api/cloud-mirrors"' in text
    assert "LANTERN_CLOUD_MIRROR_URLS" in text
