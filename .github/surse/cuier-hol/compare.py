"""Side-by-side sheet: the current photo next to the two rendered variants."""
import os

import matplotlib
from PIL import Image, ImageDraw, ImageFont

from design import D

HERE = os.path.dirname(os.path.abspath(__file__))


def fmt(v):
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


def main():
    fonts = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
    font = ImageFont.truetype(os.path.join(fonts, "DejaVuSans-Bold.ttf"), 30)
    small = ImageFont.truetype(os.path.join(fonts, "DejaVuSans.ttf"), 20)
    W, H = 768, 1024
    panels = [
        (Image.open(os.path.join(HERE, "original.jpg")).convert("RGB"), "Acum", ""),
        (Image.open(os.path.join(HERE, "out", "propunere_stejar.jpg")), "Propunere A – stejar",
         f"riflaj stejar {fmt(D['panel_w'])} × {fmt(D['panel_h'])} cm pe plintă, 5 cârlige negre"),
        (Image.open(os.path.join(HERE, "out", "propunere_antracit.jpg")), "Varianta B – negru/antracit",
         "aceleași piese, ca tâmplăria și ușa"),
    ]
    gap, bar = 16, 78
    out = Image.new("RGB", (3 * W + 4 * gap, H + bar + 2 * gap), "white")
    d = ImageDraw.Draw(out)
    for k, (im, title, sub) in enumerate(panels):
        x = gap + k * (W + gap)
        out.paste(im.resize((W, H), Image.LANCZOS), (x, bar + gap))
        d.text((x + 4, gap - 2), title, font=font, fill=(25, 25, 25))
        d.text((x + 4, gap + 38), sub, font=small, fill=(110, 110, 110))
    path = os.path.join(HERE, "out", "comparatie_acum_vs_propuneri.jpg")
    out.save(path, quality=90)
    print("saved", path, out.size)


if __name__ == "__main__":
    main()
