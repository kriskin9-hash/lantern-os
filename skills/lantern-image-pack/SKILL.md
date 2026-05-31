---
name: lantern-image-pack
description: Generate, organize, and bundle image collections into shareable packs. Use when the user asks for N images in a pack, a gallery, a contact sheet, a zip of images, or any image batch task.
---

# Lantern Image Pack

Use this skill from `C:\tmp\lantern-os` when the user asks for:
- N images in a pack or folder
- A gallery, contact sheet, or zip of images
- Batch image organization or renaming
- Image pack validation (count, naming, checksums)

## Core Files

- Skill module: `skills/lantern-image-pack/pack.py`
- Templates: `skills/lantern-image-pack/templates/gallery.html`
- Output root: `data/image-packs/`

## Pack Shape

Every image pack is a folder with:

```
{pack-name}/
  images/
    01.png
    02.png
    ...
  index.html          # local gallery
  pack.json           # metadata
  {pack-name}.zip     # shareable zip
```

## Rules

1. Number images with zero-padded two-digit names (`01.png` … `20.png`).
2. Always generate `index.html` as a local-safe gallery.
3. Always generate `pack.json` with title, count, createdAt, and file list.
4. Validate count before marking complete.
5. Do not overwrite existing packs without operator approval.

## Next Safe Action

If the user asks for 20 images, create the pack folder, prepare the metadata, and report the path. If actual image generation is needed, mark it `held` and note the generator required (DALL-E, Midjourney, Stable Diffusion, etc.).
