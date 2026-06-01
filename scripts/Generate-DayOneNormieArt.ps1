param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$OutputDir = "reports/assets/day-one-normie"
)

$ErrorActionPreference = "Stop"

$outDir = Join-Path $Root $OutputDir
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$python = @"
from pathlib import Path
from math import sin, cos, pi
from PIL import Image, ImageDraw, ImageFilter
import random

root = Path(r"$Root")
out_dir = root / r"$OutputDir"
out_dir.mkdir(parents=True, exist_ok=True)

assets = [
    ("cover.png", "LOCAL FIRST GARAGE", ((252, 188, 92), (56, 96, 108), (244, 241, 226))),
    ("memory-rag.png", "SORT THE PILE", ((70, 135, 128), (236, 194, 96), (250, 246, 234))),
    ("learning-packet.png", "MAKE IT READABLE", ((86, 121, 185), (245, 202, 117), (247, 246, 236))),
    ("pro-cleanup.png", "SAVE THE HANDOFF", ((110, 88, 145), (230, 168, 97), (248, 244, 232))),
    ("token-time.png", "SPEND TOKENS LAST", ((48, 102, 120), (141, 194, 154), (246, 246, 235))),
    ("practical-wins.png", "SMALL REAL WIN", ((59, 126, 103), (240, 176, 84), (250, 245, 235))),
]

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def make_asset(name, label, palette, seed):
    random.seed(seed)
    w, h = 1600, 900
    img = Image.new("RGB", (w, h), palette[2])
    px = img.load()
    for y in range(h):
        for x in range(w):
            t = (x / w * 0.55) + (y / h * 0.45)
            wave = (sin((x + seed * 17) / 95) + cos((y + seed * 23) / 80)) * 0.035
            base = lerp(palette[2], palette[0], max(0, min(1, t + wave)))
            px[x, y] = base

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    # Large lantern/window geometry.
    center = (int(w * 0.36), int(h * 0.50))
    for i in range(10):
        r = 520 - i * 42
        alpha = 25 + i * 7
        color = (*palette[1], min(130, alpha))
        box = [center[0] - r, center[1] - int(r * 0.56), center[0] + r, center[1] + int(r * 0.56)]
        d.rounded_rectangle(box, radius=42, outline=color, width=8)

    # Worktable / packet tiles.
    for i in range(9):
        x = int(w * (0.58 + random.random() * 0.30))
        y = int(h * (0.18 + random.random() * 0.58))
        rw = random.randint(135, 240)
        rh = random.randint(70, 150)
        fill = (*lerp(palette[2], palette[1], 0.35 + random.random() * 0.25), 120)
        d.rounded_rectangle([x, y, x + rw, y + rh], radius=18, fill=fill, outline=(*palette[0], 135), width=3)
        d.line([x + 20, y + 28, x + rw - 20, y + 28], fill=(*palette[0], 120), width=3)

    # Convergence paths.
    for i in range(18):
        y = int(h * (0.18 + i * 0.038))
        d.arc([int(w*0.08), y, int(w*0.94), y + 360], 190, 345, fill=(*palette[0], 70), width=3)

    # Light source.
    d.ellipse([int(w*0.18), int(h*0.22), int(w*0.52), int(h*0.77)], fill=(*palette[1], 40))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).filter(ImageFilter.UnsharpMask(radius=1.2, percent=120))

    d = ImageDraw.Draw(img)
    d.rounded_rectangle([70, 60, 710, 165], radius=28, fill=(255, 255, 255, 188), outline=(*palette[0], 190), width=3)
    d.text((105, 92), label, fill=(32, 45, 50))
    d.text((105, 126), "Lantern Day One packet art", fill=(65, 78, 82))

    img.convert("RGB").save(out_dir / name, quality=94)

for idx, item in enumerate(assets):
    make_asset(*item, seed=20260526 + idx)

print(out_dir)
"@

$temp = Join-Path $env:TEMP ("generate-day-one-normie-art-{0}-{1}.py" -f $PID, ([guid]::NewGuid().ToString("N")))
$python | Set-Content -LiteralPath $temp -Encoding UTF8
try {
    python $temp
}
finally {
    Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue
}
