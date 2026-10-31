"""Imaginea cu trei panouri: fotografia de acum și cele două variante randate (după render.py)."""
import os

import matplotlib
from PIL import Image, ImageDraw, ImageFont

from design import EL, GAP_DESK

HERE = os.path.dirname(os.path.abspath(__file__))


def fmt(v):
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


def main():
    fonts = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
    font = ImageFont.truetype(os.path.join(fonts, "DejaVuSans-Bold.ttf"), 28)
    small = ImageFont.truetype(os.path.join(fonts, "DejaVuSans.ttf"), 18)
    W, H = 622, 1108                      # de 2 ori fotografia de 311 × 554
    size = f"{fmt(EL['w'])} × {fmt(EL['d'])} × {fmt(EL['h'])} cm"
    panels = [
        (Image.open(os.path.join(HERE, "out", "acum.jpg")), "Acum",
         ["peretele liber din stânga biroului: ~126 cm"]),
        (Image.open(os.path.join(HERE, "out", "propunere_A_stejar.jpg")), "Propunere A – stejar natur",
         [f"BoConcept Element, 3 sertare, {size}", f"la {fmt(GAP_DESK)} cm de birou; picioare negre"]),
        (Image.open(os.path.join(HERE, "out", "varianta_B_stejar_inchis.jpg")), "Varianta B – stejar închis",
         ["aceeași comodă, furnir de stejar închis,", "mai aproape de biroul negru"]),
    ]
    gap, bar = 16, 100
    out = Image.new("RGB", (3 * W + 4 * gap, H + bar + 2 * gap), "white")
    d = ImageDraw.Draw(out)
    for k, (im, title, sub) in enumerate(panels):
        x = gap + k * (W + gap)
        out.paste(im.convert("RGB").resize((W, H), Image.LANCZOS), (x, bar + gap))
        d.text((x + 4, gap - 2), title, font=font, fill=(25, 25, 25))
        for i, line in enumerate(sub):
            d.text((x + 4, gap + 38 + 24 * i), line, font=small, fill=(110, 110, 110))
    path = os.path.join(HERE, "out", "comparatie_acum_vs_propuneri.jpg")
    out.save(path, quality=88)
    print("salvat", path, out.size)


if __name__ == "__main__":
    main()
