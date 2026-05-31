"""
Lantern Image Pack — generate, organize, and bundle image collections.
"""
from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = REPO_ROOT / "data" / "image-packs"


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_pack_dir(name: str) -> Path:
    safe = "".join(c for c in name if c.isalnum() or c in "_-").strip("-_")
    if not safe:
        safe = "untitled-pack"
    path = OUTPUT_ROOT / safe
    path.mkdir(parents=True, exist_ok=True)
    (path / "images").mkdir(exist_ok=True)
    return path


def write_pack_json(pack_dir: Path, title: str, count: int, files: list[str]):
    meta = {
        "title": title,
        "count": count,
        "createdAt": now_utc(),
        "files": files,
    }
    (pack_dir / "pack.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def write_gallery_html(pack_dir: Path, title: str, files: list[str]):
    figures = "\n".join(
        f'      <figure><img src="images/{f}" alt="{title} image {i+1}"><figcaption>Image {i+1:02d}</figcaption></figure>'
        for i, f in enumerate(files)
    )
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    body {{ margin: 0; font-family: "Segoe UI", Arial, sans-serif; background: #f7f8f5; color: #172026; }}
    main {{ width: min(1180px, calc(100% - 32px)); margin: 0 auto; padding: 32px 0; }}
    h1 {{ margin: 0 0 8px; font-size: clamp(2rem, 5vw, 4rem); }}
    p {{ color: #52616b; line-height: 1.5; max-width: 760px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 14px; margin-top: 24px; }}
    figure {{ margin: 0; padding: 10px; border: 1px solid #c9d2d8; border-radius: 8px; background: #fff; }}
    img {{ display: block; width: 100%; height: auto; border-radius: 4px; }}
    figcaption {{ margin-top: 8px; font-size: 0.9rem; color: #35505a; font-weight: 700; }}
  </style>
</head>
<body>
  <main>
    <h1>{title}</h1>
    <p>{len(files)} images in this pack. Open locally in any browser.</p>
    <section class="grid" aria-label="Image pack">
{figures}
    </section>
  </main>
</body>
</html>"""
    (pack_dir / "index.html").write_text(html, encoding="utf-8")


def create_zip(pack_dir: Path, name: str):
    zip_path = pack_dir.parent / f"{name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in pack_dir.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(pack_dir.parent))
    return zip_path


def make_pack(title: str, count: int, image_files: list[str] | None = None) -> Path:
    """
    Create an image pack folder with metadata, gallery, and zip.
    If image_files is None, placeholder entries are written.
    Returns the pack directory path.
    """
    pack_dir = ensure_pack_dir(title)
    files = image_files or [f"{i:02d}.png" for i in range(1, count + 1)]
    write_pack_json(pack_dir, title, len(files), files)
    write_gallery_html(pack_dir, title, files)
    zip_path = create_zip(pack_dir, pack_dir.name)
    return pack_dir


if __name__ == "__main__":
    print(f"[INFO] Lantern Image Pack skill loaded. Output root: {OUTPUT_ROOT}")
