#!/usr/bin/env python3
"""Derive the web-sized images in assets/img/ from the originals in src/img/.

    python build_images.py

Drop a replacement photo (jpg, png or webp, at least 1600px wide) into src/img/
with the same base name and rerun. Outputs:
  assets/img/<name>.webp      banner, 1600x720 centre crop (hero: 1600x1000)
  assets/img/<name>-sm.webp   card thumbnail, 720x450 centre crop
"""
import pathlib
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src/img"
OUT = ROOT / "assets/img"
SIZES = {"banner": (1600, 720), "hero": (1600, 1000), "sm": (720, 450)}


def cover(im, size):
    w, h = im.size
    tw, th = size
    scale = max(tw / w, th / h)
    im = im.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    left = (im.width - tw) // 2
    top = (im.height - th) // 2
    return im.crop((left, top, left + tw, top + th))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for src in sorted(SRC.iterdir()):
        if src.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            continue
        name = src.stem
        im = Image.open(src).convert("RGB")
        main_size = SIZES["hero"] if name == "hero" else SIZES["banner"]
        cover(im, main_size).save(OUT / f"{name}.webp", "WEBP", quality=72, method=6)
        cover(im, SIZES["sm"]).save(OUT / f"{name}-sm.webp", "WEBP", quality=70, method=6)
        print(f"{name}: {main_size[0]}x{main_size[1]} + 720x450")


if __name__ == "__main__":
    main()
