"""Imaginea de comparație pentru variantele C și D: fotografia de acum, Raya și Veneto (după randeaza.py).

    python compara.py           # out/comparatie_acum_vs_propuneri_cioata.jpg
"""
import os

from varianta import BUF, GAP_DESK, VARIANTE  # pune și `..` și `.github` în sys.path

from unelte import comparatie  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")


def fmt(v):
    return f"{v:.1f}".rstrip("0").rstrip(".").replace(".", ",")


def main():
    size = f"{fmt(BUF['w'])} × {fmt(BUF['d'])} × {fmt(BUF['h'])} cm"
    panouri = [
        (os.path.join(OUT, "acum.jpg"), "Acum", "peretele liber din stânga biroului: ~126 cm"),
        (os.path.join(OUT, VARIANTE["C"]["fisier"]), VARIANTE["C"]["titlu"],
         f"{size}, 2 uși, sertar interior; ~{fmt(GAP_DESK)} cm de birou"),
        (os.path.join(OUT, VARIANTE["D"]["fisier"]), VARIANTE["D"]["titlu"],
         "același corp, uși antracit, mâner rotund de stejar"),
    ]
    dest = os.path.join(OUT, "comparatie_acum_vs_propuneri_cioata.jpg")
    w, h = comparatie.compune(panouri, dest, panou=(622, 1108))   # ca la comparația variantelor A și B
    print("salvat", dest, (w, h))


if __name__ == "__main__":
    main()
