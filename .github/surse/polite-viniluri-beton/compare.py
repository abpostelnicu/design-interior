"""Imaginea cu trei panouri: fotografia de acum și cele două variante randate."""
import os

import matplotlib
from PIL import Image, ImageDraw, ImageFont

from design import D, verticals

HERE = os.path.dirname(os.path.abspath(__file__))


def fmt(v):
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


def main():
    fonts = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
    font = ImageFont.truetype(os.path.join(fonts, "DejaVuSans-Bold.ttf"), 30)
    small = ImageFont.truetype(os.path.join(fonts, "DejaVuSans.ttf"), 20)
    W, H = 1024, 768
    size = f"{fmt(D['L'])} × {fmt(D['P'])} × {fmt(D['T'])} cm"
    nv = len(verticals())
    vert = "o verticală" if nv == 1 else f"{nv} verticale"
    panels = [
        (Image.open(os.path.join(HERE, "out", "acum.jpg")), "Acum", "televizorul apare stins în toate imaginile"),
        (Image.open(os.path.join(HERE, "out", "propunere_A_beton_gri.jpg")), "Propunerea A: beton gri și stejar",
         f"2 polițe de {size} din microciment gri; {vert} și opritoare din stejar"),
        (Image.open(os.path.join(HERE, "out", "varianta_B_beton_antracit.jpg")), "Varianta B: beton antracit și stejar",
         "aceleași polițe, din microciment antracit, ca fronturile comodei"),
    ]
    gap, bar = 16, 78
    out = Image.new("RGB", (3 * W + 4 * gap, H + bar + 2 * gap), "white")
    d = ImageDraw.Draw(out)
    for k, (im, title, sub) in enumerate(panels):
        x = gap + k * (W + gap)
        out.paste(im.convert("RGB").resize((W, H), Image.LANCZOS), (x, bar + gap))
        d.text((x + 4, gap - 2), title, font=font, fill=(25, 25, 25))
        d.text((x + 4, gap + 38), sub, font=small, fill=(110, 110, 110))
    path = os.path.join(HERE, "out", "comparatie_acum_vs_propuneri.jpg")
    out.save(path, quality=88)
    print("salvat", path, out.size)


if __name__ == "__main__":
    main()
