#!/usr/bin/env python3
"""Lantern OS Image Generator - procedural image creation tool."""

import argparse
import math
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:
    raise SystemExit("Pillow required: pip install Pillow")

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "images"


def save(img: Image.Image, name: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / name
    img.save(path)
    print(f"saved: {path}")
    return path


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def hash2d(x: int, y: int, seed: int = 0) -> float:
    n = x * 374761393 + y * 668265263 + seed * 1013904223
    n = (n ^ (n >> 13)) * 1274126177
    n = n ^ (n >> 16)
    return (n & 0x7FFFFFFF) / 0x7FFFFFFF


def noise2d(x: float, y: float, seed: int = 0) -> float:
    xi, yi = math.floor(x), math.floor(y)
    xf, yf = x - xi, y - yi
    u = smoothstep(0, 1, xf)
    v = smoothstep(0, 1, yf)
    n00 = hash2d(xi, yi, seed)
    n10 = hash2d(xi + 1, yi, seed)
    n01 = hash2d(xi, yi + 1, seed)
    n11 = hash2d(xi + 1, yi + 1, seed)
    return lerp(lerp(n00, n10, u), lerp(n01, n11, u), v)


def fbm(x: float, y: float, octaves: int = 6, lacunarity: float = 2.0, gain: float = 0.5, seed: int = 0) -> float:
    total, amplitude, frequency = 0.0, 1.0, 1.0
    for _ in range(octaves):
        total += amplitude * noise2d(x * frequency, y * frequency, seed)
        amplitude *= gain
        frequency *= lacunarity
    return total


# ── v1: random noise ────────────────────────────────────────────────
def v1_random_noise(width: int = 512, height: int = 512) -> Image.Image:
    img = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(img)
    for _ in range(2000):
        x, y = random.randint(0, width - 1), random.randint(0, height - 1)
        r = random.randint(50, 255)
        draw.point((x, y), fill=(r, 0, 255 - r))
    return img


# ── v2: gradient circles ────────────────────────────────────────────
def v2_gradient_circles(width: int = 512, height: int = 512) -> Image.Image:
    img = Image.new("RGB", (width, height), (10, 10, 30))
    draw = ImageDraw.Draw(img)
    for _ in range(40):
        cx, cy = random.randint(0, width), random.randint(0, height)
        radius = random.randint(20, 120)
        r, g, b = random.randint(50, 255), random.randint(50, 255), random.randint(100, 255)
        for dr in range(radius, 0, -2):
            alpha = int(255 * (1 - dr / radius))
            color = (r, g, b)
            draw.ellipse(
                (cx - dr, cy - dr, cx + dr, cy + dr),
                fill=color,
            )
    img = img.filter(ImageFilter.GaussianBlur(radius=2))
    return img


# ── v3: flowing perlin-like waves ─────────────────────────────────
def v3_flowing_waves(width: int = 512, height: int = 512) -> Image.Image:
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    scale = 0.01
    for y in range(height):
        for x in range(width):
            nx = x * scale
            ny = y * scale
            r = int(128 + 127 * math.sin(nx * 3 + math.sin(ny * 2)))
            g = int(128 + 127 * math.sin(ny * 4 + math.cos(nx * 3)))
            b = int(128 + 127 * math.sin((nx + ny) * 2))
            pixels[x, y] = (r, g, b)
    return img


# ── v4: fractal tree ──────────────────────────────────────────────
def v4_fractal_tree(width: int = 512, height: int = 512) -> Image.Image:
    img = Image.new("RGB", (width, height), (5, 5, 15))
    draw = ImageDraw.Draw(img)

    def branch(x1, y1, angle, length, depth):
        if depth == 0:
            return
        x2 = x1 + length * math.cos(math.radians(angle))
        y2 = y1 - length * math.sin(math.radians(angle))
        color = (255 - depth * 20, 180 + depth * 5, 50 + depth * 8)
        draw.line((x1, y1, x2, y2), fill=color, width=max(1, depth // 2))
        branch(x2, y2, angle - random.uniform(20, 35), length * 0.7, depth - 1)
        branch(x2, y2, angle + random.uniform(20, 35), length * 0.7, depth - 1)

    branch(width // 2, height - 50, 90, 100, 10)
    return img


# ── v5: particle burst (most interesting so far) ───────────────────
def v5_particle_burst(width: int = 512, height: int = 512) -> Image.Image:
    img = Image.new("RGB", (width, height), (5, 2, 10))
    pixels = img.load()
    cx, cy = width // 2, height // 2
    num_particles = 8000
    for _ in range(num_particles):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.gauss(0, width * 0.25)
        x = int(cx + dist * math.cos(angle))
        y = int(cy + dist * math.sin(angle))
        if 0 <= x < width and 0 <= y < height:
            hue = (angle + math.pi) / (2 * math.pi)
            r = int(255 * (0.5 + 0.5 * math.sin(hue * 2 * math.pi)))
            g = int(255 * (0.5 + 0.5 * math.sin(hue * 2 * math.pi + 2)))
            b = int(255 * (0.5 + 0.5 * math.sin(hue * 2 * math.pi + 4)))
            # additive blend
            pr, pg, pb = pixels[x, y]
            pixels[x, y] = (min(255, pr + r // 8), min(255, pg + g // 8), min(255, pb + b // 8))
    return img


# ── v6: mandala / geometric pattern ─────────────────────────────────
def v6_mandala(width: int = 512, height: int = 512) -> Image.Image:
    img = Image.new("RGB", (width, height), (10, 10, 10))
    draw = ImageDraw.Draw(img)
    cx, cy = width // 2, height // 2
    petals = 12
    for layer in range(8):
        radius = 30 + layer * 30
        for i in range(petals * (layer + 1)):
            angle = (2 * math.pi / (petals * (layer + 1))) * i + layer * 0.3
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            color = (
                int(100 + 155 * math.sin(layer * 0.8)),
                int(100 + 155 * math.sin(layer * 0.8 + 2)),
                int(100 + 155 * math.sin(layer * 0.8 + 4)),
            )
            draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=color)
    # add radial lines
    for i in range(petals):
        angle = (2 * math.pi / petals) * i
        x2 = cx + (width // 2 - 10) * math.cos(angle)
        y2 = cy + (height // 2 - 10) * math.sin(angle)
        draw.line((cx, cy, x2, y2), fill=(200, 200, 200), width=1)
    return img


# ── v7: landscape sunset (the "actual image" target) ──────────────
def v7_landscape(width: int = 1024, height: int = 768) -> Image.Image:
    img = Image.new("RGB", (width, height))
    pixels = img.load()

    # sky gradient
    for y in range(height):
        t = y / height
        r = int(255 * (1 - t * 0.7))
        g = int(100 + 80 * math.sin(t * math.pi))
        b = int(200 - 100 * t)
        for x in range(width):
            pixels[x, y] = (r, g, b)

    # sun
    sun_x, sun_y, sun_r = width // 2, height // 3, 60
    for y in range(height):
        for x in range(width):
            dx, dy = x - sun_x, y - sun_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < sun_r:
                brightness = int(255 * (1 - dist / sun_r))
                pr, pg, pb = pixels[x, y]
                pixels[x, y] = (
                    min(255, pr + brightness),
                    min(255, pg + brightness // 2),
                    pb,
                )

    # mountains
    draw = ImageDraw.Draw(img)
    points = [(0, height)]
    y_base = height * 0.6
    for x in range(0, width + 1, 40):
        y = int(y_base - 100 * math.sin(x * 0.01) - 50 * math.sin(x * 0.03) - random.randint(0, 20))
        points.append((x, y))
    points.append((width, height))
    draw.polygon(points, fill=(40, 30, 50))

    # water reflection
    for y in range(int(height * 0.65), height):
        for x in range(width):
            mirror_y = int(height * 0.65 - (y - height * 0.65))
            if 0 <= mirror_y < height:
                r, g, b = pixels[x, mirror_y]
                pixels[x, y] = (r // 2, g // 2 + 20, b // 2 + 40)

    return img


# ── v8: noise-based terrain with clouds, atmospheric perspective ──
def v8_noise_terrain(width: int = 1024, height: int = 768, seed: int = 42) -> Image.Image:
    img = Image.new("RGB", (width, height))
    px = img.load()
    random.seed(seed)

    # sky gradient
    for y in range(height):
        t = y / height
        if t < 0.35:
            r = int(20 + 200 * (1 - t / 0.35))
            g = int(10 + 100 * (1 - t / 0.35))
            b = int(60 + 120 * (1 - t / 0.35))
        elif t < 0.65:
            r = int(220 + 35 * math.sin((t - 0.35) / 0.3 * math.pi))
            g = int(80 + 100 * math.sin((t - 0.35) / 0.3 * math.pi))
            b = int(120 + 60 * math.sin((t - 0.35) / 0.3 * math.pi))
        else:
            r = int(30 + 15 * (1 - (t - 0.65) / 0.35))
            g = int(15 + 8 * (1 - (t - 0.65) / 0.35))
            b = int(50 + 20 * (1 - (t - 0.65) / 0.35))
        for x in range(width):
            px[x, y] = (r, g, b)

    # clouds using FBM
    for y in range(height // 2):
        for x in range(width):
            n = fbm(x * 0.003, y * 0.003 + 100, octaves=5, seed=seed + 1)
            if n > 0.45:
                intensity = int(255 * min(1.0, (n - 0.45) * 3))
                pr, pg, pb = px[x, y]
                px[x, y] = (
                    min(255, pr + intensity),
                    min(255, pg + intensity),
                    min(255, pb + intensity),
                )

    # sun with glow
    sun_x, sun_y = int(width * 0.7), int(height * 0.25)
    for y in range(height):
        for x in range(width):
            dx, dy = x - sun_x, y - sun_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 120:
                glow = int(200 * max(0, 1 - dist / 120))
                pr, pg, pb = px[x, y]
                px[x, y] = (min(255, pr + glow), min(255, pg + glow // 2), pb)

    # terrain with FBM ridges
    horizon = int(height * 0.58)
    terrain = []
    for x in range(width):
        h = fbm(x * 0.005, 0, octaves=6, lacunarity=2.2, gain=0.5, seed=seed + 2)
        h = abs(h)  # ridged
        h = h ** 1.5
        terrain.append(int(horizon - h * height * 0.35))

    # draw terrain layers (back to front for atmospheric perspective)
    layers = 5
    for layer in range(layers):
        t = layer / (layers - 1)
        color = (
            int(20 + 30 * t),
            int(15 + 25 * t),
            int(40 + 20 * t),
        )
        offset = int((1 - t) * 80)
        points = [(0, height)]
        for x in range(width):
            y = terrain[x] + offset + int(fbm(x * 0.01 + layer * 100, 0, octaves=3, seed=seed + 3) * 20)
            points.append((x, y))
        points.append((width, height))
        draw = ImageDraw.Draw(img)
        draw.polygon(points, fill=color)

    # water with reflection + noise ripples
    water_top = min(terrain) + 40
    for y in range(water_top, height):
        for x in range(width):
            mirror_y = water_top - (y - water_top)
            if 0 <= mirror_y < height:
                r, g, b = px[x, mirror_y]
                # ripple distortion
                ripple = fbm(x * 0.02, y * 0.02 + 50, octaves=4, seed=seed + 4)
                ripple_int = int(ripple * 30)
                px[x, y] = (
                    max(0, r // 3 + ripple_int),
                    max(0, g // 3 + 10 + ripple_int),
                    max(0, b // 2 + 30 + ripple_int),
                )

    return img


# ── v9: nebula / space scene ──────────────────────────────────────
def v9_nebula(width: int = 1024, height: int = 768, seed: int = 7) -> Image.Image:
    img = Image.new("RGB", (width, height), (2, 2, 8))
    px = img.load()
    random.seed(seed)

    # base nebula clouds
    for y in range(height):
        for x in range(width):
            n1 = fbm(x * 0.004, y * 0.004, octaves=6, seed=seed)
            n2 = fbm(x * 0.008 + 50, y * 0.008 + 50, octaves=4, seed=seed + 1)
            r = int(10 + 100 * n1 + 60 * n2)
            g = int(5 + 50 * n1 + 40 * n2)
            b = int(20 + 120 * n1 + 80 * n2)
            px[x, y] = (r, g, b)

    # bright gas pockets (optimized: fewer, smaller, precompute bounds)
    for _ in range(8):
        cx, cy = random.randint(50, width - 50), random.randint(50, height - 50)
        radius = random.randint(30, 90)
        hue = random.random()
        y0, y1 = max(0, cy - radius), min(height, cy + radius + 1)
        x0, x1 = max(0, cx - radius), min(width, cx + radius + 1)
        for y in range(y0, y1):
            dy = y - cy
            for x in range(x0, x1):
                dx = x - cx
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > radius:
                    continue
                falloff = 1 - dist / radius
                intensity = int(180 * falloff ** 2)
                r, g, b = px[x, y]
                hr = int(intensity * (0.5 + 0.5 * math.sin(hue * 2 * math.pi)))
                hg = int(intensity * (0.5 + 0.5 * math.sin(hue * 2 * math.pi + 2)))
                hb = int(intensity * (0.5 + 0.5 * math.sin(hue * 2 * math.pi + 4)))
                px[x, y] = (min(255, r + hr), min(255, g + hg), min(255, b + hb))

    # stars
    for _ in range(2000):
        x, y = random.randint(0, width - 1), random.randint(0, height - 1)
        brightness = random.randint(50, 255)
        if random.random() < 0.1:
            # bright star with bloom
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    d = math.sqrt(dx * dx + dy * dy)
                    if d > 2.5:
                        continue
                    sx, sy = x + dx, y + dy
                    if 0 <= sx < width and 0 <= sy < height:
                        pr, pg, pb = px[sx, sy]
                        bloom = int(brightness * (1 - d / 2.5) * 0.5)
                        px[sx, sy] = (min(255, pr + bloom), min(255, pg + bloom), min(255, pb + bloom))
        else:
            px[x, y] = (min(255, px[x, y][0] + brightness),
                        min(255, px[x, y][1] + brightness),
                        min(255, px[x, y][2] + brightness))

    return img


# ── v10: abstract fluid art ───────────────────────────────────────
def v10_fluid(width: int = 1024, height: int = 1024, seed: int = 99) -> Image.Image:
    img = Image.new("RGB", (width, height))
    px = img.load()
    random.seed(seed)

    # flow field particles
    num_particles = 50000
    for _ in range(num_particles):
        x, y = random.uniform(0, width), random.uniform(0, height)
        hue = random.random()
        sat = 0.6 + random.random() * 0.4
        val = 0.5 + random.random() * 0.5
        r, g, b = (
            int(255 * val * (0.5 + 0.5 * math.sin(hue * 2 * math.pi))),
            int(255 * val * (0.5 + 0.5 * math.sin(hue * 2 * math.pi + 2))),
            int(255 * val * (0.5 + 0.5 * math.sin(hue * 2 * math.pi + 4))),
        )
        # follow flow field
        for step in range(30):
            ix, iy = int(x), int(y)
            if not (0 <= ix < width and 0 <= iy < height):
                break
            angle = fbm(x * 0.003, y * 0.003, octaves=4, seed=seed) * 2 * math.pi
            x += math.cos(angle) * 2
            y += math.sin(angle) * 2
            # paint with soft falloff
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    d = math.sqrt(dx * dx + dy * dy)
                    if d > 2.5:
                        continue
                    sx, sy = ix + dx, iy + dy
                    if 0 <= sx < width and 0 <= sy < height:
                        falloff = 1 - d / 2.5
                        pr, pg, pb = px[sx, sy]
                        px[sx, sy] = (
                            min(255, pr + int(r * falloff * 0.08)),
                            min(255, pg + int(g * falloff * 0.08)),
                            min(255, pb + int(b * falloff * 0.08)),
                        )
    return img


VERSIONS = {
    "v1": v1_random_noise,
    "v2": v2_gradient_circles,
    "v3": v3_flowing_waves,
    "v4": v4_fractal_tree,
    "v5": v5_particle_burst,
    "v6": v6_mandala,
    "v7": v7_landscape,
    "v8": v8_noise_terrain,
    "v9": v9_nebula,
    "v10": v10_fluid,
}


def generate_with_api(prompt: str, model: str = "dall-e-3", size: str = "1024x1024") -> Optional[Image.Image]:
    """Call OpenAI DALL-E 3 to generate a real image from a text prompt."""
    try:
        from openai import OpenAI
    except ImportError:
        print("ERROR: openai package not installed. Run: pip install openai")
        return None

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        dotenv = Path(__file__).parent.parent / ".env"
        if dotenv.exists():
            for line in dotenv.read_text().splitlines():
                if line.startswith("OPENAI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in env or .env file")
        return None

    client = OpenAI(api_key=api_key)
    print(f"Calling {model} API with prompt: {prompt[:60]}...")
    try:
        response = client.images.generate(
            model=model,
            prompt=prompt,
            size=size,
            quality="standard",
            n=1,
        )
        import requests as req
        image_url = response.data[0].url
        img_data = req.get(image_url).content
        img = Image.open(__import__("io").BytesIO(img_data)).convert("RGB")
        return img
    except Exception as e:
        print(f"API error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Lantern OS Image Generator")
    parser.add_argument("version", nargs="?", default="v8",
                        choices=list(VERSIONS.keys()) + ["all"],
                        help="which procedural version to generate")
    parser.add_argument("--width", type=int, default=None)
    parser.add_argument("--height", type=int, default=None)
    parser.add_argument("--api", action="store_true", help="use DALL-E 3 API instead of procedural")
    parser.add_argument("--prompt", type=str, default="A surreal landscape painting with mountains, water, and dramatic sunset",
                        help="prompt for API generation")
    parser.add_argument("--seed", type=int, default=None, help="random seed for procedural generation")
    args = parser.parse_args()

    if args.api:
        img = generate_with_api(args.prompt)
        if img:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            save(img, f"api_{ts}.png")
        return

    if args.version == "all":
        for name, fn in VERSIONS.items():
            img = fn()
            save(img, f"{name}_sample.png")
    else:
        fn = VERSIONS[args.version]
        kwargs = {}
        if args.width:
            kwargs["width"] = args.width
        if args.height:
            kwargs["height"] = args.height
        if args.seed is not None:
            kwargs["seed"] = args.seed
        img = fn(**kwargs)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        save(img, f"{args.version}_{ts}.png")


if __name__ == "__main__":
    main()
