"""Imaginea de comparație: fotografia de acum și variantele randate, alăturate, fiecare cu titlu și subtitlu.

    from unelte import comparatie
    comparatie.compune([
        ("out/acum.jpg", "Acum", "televizorul apare stins în toate imaginile"),
        ("out/propunere_A_stejar.jpg", "Propunere A – stejar", "2 polițe flotante, prinse ascuns în perete"),
        ("out/varianta_B_opritoare_negre.jpg", "Varianta B – opritoare negre", "aceleași polițe, alt material"),
    ], "out/comparatie_acum_vs_propuneri.jpg")

    python comparatie.py <dest.jpg> <imagine> <titlu> <subtitlu> [<imagine> <titlu> <subtitlu> ...]

Panourile au 1024 × 768 px la fotografiile orizontale și 768 × 1024 la cele verticale (după primul panou), cu
16 px între ele și o bandă de 78 px pentru texte, ca în proiectele existente. Un titlu prea lung se micșorează
până încape; dacă nici așa nu încape, primești o eroare: îl scurtezi.
Preluat din `compare.py` din `.github/surse/polite-viniluri/` și `.github/surse/cuier-hol/`.
"""
import os
import sys

import matplotlib
from PIL import Image, ImageDraw, ImageFont

GAP, BAR = 16, 78


def _fonturi():
    d = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
    return os.path.join(d, "DejaVuSans-Bold.ttf"), os.path.join(d, "DejaVuSans.ttf")


def font_care_incape(draw, text, path, size, width, min_size):
    """Cel mai mare corp de literă, de la size în jos până la min_size, la care textul încape în width px."""
    for s in range(size, min_size - 1, -1):
        f = ImageFont.truetype(path, s)
        if draw.textlength(text, font=f) <= width:
            return f
    raise ValueError(f"textul nu încape pe panou nici la {min_size} px: {text!r}; scurtează-l")


def compune(panouri, dest, panou=None, gap=GAP, bar=BAR, calitate=88):
    """panouri: [(imagine: cale sau PIL.Image, titlu, subtitlu)], de la stânga la dreapta. Întoarce mărimea."""
    ims = [Image.open(p) if isinstance(p, (str, os.PathLike)) else p for p, _, _ in panouri]
    if panou is None:
        w0, h0 = ims[0].size
        panou = (1024, 768) if w0 >= h0 else (768, 1024)
    W, H = panou
    n = len(panouri)
    out = Image.new("RGB", (n * W + (n + 1) * gap, H + bar + 2 * gap), "white")
    d = ImageDraw.Draw(out)
    bold, regular = _fonturi()
    for k, (im, (_, titlu, sub)) in enumerate(zip(ims, panouri)):
        x = gap + k * (W + gap)
        out.paste(im.convert("RGB").resize((W, H), Image.LANCZOS), (x, bar + gap))
        d.text((x + 4, gap - 2), titlu, font=font_care_incape(d, titlu, bold, 30, W - 8, 20), fill=(25, 25, 25))
        if sub:
            d.text((x + 4, gap + 38), sub, font=font_care_incape(d, sub, regular, 20, W - 8, 13),
                   fill=(110, 110, 110))
    out.save(dest, quality=calitate)
    return out.size


def main(argv):
    if len(argv) < 4 or (len(argv) - 1) % 3:
        print(__doc__)
        return 2
    dest, rest = argv[0], argv[1:]
    panouri = [tuple(rest[i:i + 3]) for i in range(0, len(rest), 3)]
    size = compune(panouri, dest)
    print(f"salvat {dest} ({size[0]} × {size[1]})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
