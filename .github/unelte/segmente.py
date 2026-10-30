"""Segmentele de dreaptă din fotografie, pentru calibrarea camerei.

    python segmente.py original.jpg out/                    # toate segmentele + imaginea numerotată
    python segmente.py original.jpg out/ --zona 600 0 1024 400 --min 30
    python segmente.py --alege out/segmente_toate.json grupuri.json segments.json

1. Prima comandă detectează segmentele (LSD) și scrie `out/segmente_toate.json` și `out/segmente_numerotate.png`:
   fotografia mărită de 2 ori, cu fiecare segment colorat și cu indicele lui. Cu `--zona x0 y0 x1 y1` (pixeli
   din fotografie) desenezi doar o zonă, ca indicii să se citească ușor.
2. Te uiți pe imagine (unealta `view`) și alegi indicii pentru fiecare muchie cu poziție cunoscută: tavanul,
   colțurile, pardoseala, plinta, marginile unui obiect cu dimensiuni din fișa producătorului. Le scrii într-un
   `grupuri.json`: {"ceil": [12, 40], "corner_left": [3]}. Un grup = o singură dreaptă 3D.
3. A treia comandă scrie `segments.json`, pe grupuri, pentru `camera.calibreaza`.
"""
import json
import os
import sys

import cv2
import numpy as np


def detecteaza(img, lungime_min=20.0):
    """Segmentele (N × 4: u0, v0, u1, v1, în px), de la cel mai lung la cel mai scurt."""
    g = img if img.ndim == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if g.dtype != np.uint8:
        g = np.clip(g * 255 + 0.5, 0, 255).astype(np.uint8)
    lines = cv2.createLineSegmentDetector(cv2.LSD_REFINE_ADV).detect(g)[0]
    if lines is None:
        return np.zeros((0, 4), np.float32)
    s = lines.reshape(-1, 4)
    L = np.hypot(s[:, 2] - s[:, 0], s[:, 3] - s[:, 1])
    keep = L >= lungime_min
    return s[keep][np.argsort(-L[keep])]


def _culoare(i):
    h = (i * 47) % 180
    c = cv2.cvtColor(np.uint8([[[h, 230, 255]]]), cv2.COLOR_HSV2BGR)[0, 0]
    return tuple(int(v) for v in c)


def deseneaza(img, segs, dest, zona=None, zoom=2):
    """Fotografia mărită, cu segmentele colorate și numerotate; zona = (x0, y0, x1, y1) în px."""
    if img.dtype != np.uint8:
        img = np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8)
    x0, y0, x1, y1 = zona or (0, 0, img.shape[1], img.shape[0])
    crop = img[y0:y1, x0:x1]
    big = cv2.resize(crop, None, fx=zoom, fy=zoom, interpolation=cv2.INTER_CUBIC)
    big = (big * 0.75).astype(np.uint8)
    for i, (a, b, c, d) in enumerate(segs):
        mid = ((a + c) / 2, (b + d) / 2)
        if not (x0 <= mid[0] < x1 and y0 <= mid[1] < y1):
            continue
        p = (int((a - x0) * zoom), int((b - y0) * zoom))
        q = (int((c - x0) * zoom), int((d - y0) * zoom))
        col = _culoare(i)
        cv2.line(big, p, q, col, 2, cv2.LINE_AA)
        m = (int((mid[0] - x0) * zoom) + 3, int((mid[1] - y0) * zoom) - 3)
        cv2.putText(big, str(i), m, cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 3, cv2.LINE_AA)
        cv2.putText(big, str(i), m, cv2.FONT_HERSHEY_SIMPLEX, 0.45, col, 1, cv2.LINE_AA)
    cv2.imwrite(dest, big)
    return big.shape[1], big.shape[0]


def alege(segs, grupuri):
    """{grup: [indici]} -> {grup: [[u0, v0, u1, v1], ...]}, gata de scris în segments.json."""
    segs = np.asarray(segs, float)
    out = {}
    for g, idx in grupuri.items():
        bad = [i for i in idx if not 0 <= i < len(segs)]
        if bad:
            raise IndexError(f"grupul {g!r}: indicii {bad} nu există (sunt {len(segs)} segmente)")
        out[g] = [[round(float(v), 2) for v in segs[i]] for i in idx]
    return out


def main(argv):
    if argv and argv[0] == "--alege":
        toate, grupuri, dest = argv[1:4]
        with open(toate, encoding="utf-8") as f:
            segs = json.load(f)
        with open(grupuri, encoding="utf-8") as f:
            gr = json.load(f)
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(alege(segs, gr), f, indent=1)
        print("salvat", dest, "·", ", ".join(f"{g}: {len(v)}" for g, v in gr.items()))
        return 0
    if len(argv) < 2:
        print(__doc__)
        return 2
    src, outdir = argv[0], argv[1]
    zona, lmin = None, 20.0
    if "--zona" in argv:
        i = argv.index("--zona")
        zona = tuple(int(v) for v in argv[i + 1:i + 5])
    if "--min" in argv:
        lmin = float(argv[argv.index("--min") + 1])
    img = cv2.imread(src)
    if img is None:
        print("nu pot citi", src)
        return 1
    segs = detecteaza(img, lmin)
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "segmente_toate.json"), "w", encoding="utf-8") as f:
        json.dump([[round(float(v), 2) for v in s] for s in segs], f)
    size = deseneaza(img, segs, os.path.join(outdir, "segmente_numerotate.png"), zona)
    print(f"{len(segs)} segmente; salvat segmente_toate.json și segmente_numerotate.png ({size[0]} × {size[1]})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
