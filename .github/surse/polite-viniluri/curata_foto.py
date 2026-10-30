"""Pregătește `original.jpg` din fotografia primită, fără date personale.

    python curata_foto.py <fotografia primită>

- Salvează cu PIL, după `ImageOps.exif_transpose`, deci fără metadate EXIF (fără coordonate GPS).
- Stinge televizorul: pe ecran se vedeau numele rețelelor Wi-Fi din jur, iar unul conține o localitate.
- Scoate persoana care se vede prin ușa din dreapta și continuă tocul și peretele din spatele ei.

Fotografia primită nu intră în depozit; aici rămâne doar `original.jpg`, deja curățată.
"""
import sys

import cv2
import numpy as np
from PIL import Image, ImageOps

from camera import load_camera

cam1 = load_camera()


def proj(P):
    return cam1.project(np.atleast_2d(np.asarray(P, float)), distort=False)


def stinge_televizorul(img):
    """Ecranul devine sticlă neagră: gradient fin și o reflexie slabă, foarte estompată."""
    q = cam1.q
    x0, x1 = q["xtv"] + 0.45, q["xtv"] + 216.6 - 0.45
    y0, y1 = q["ytv"] + 1.6, q["ytv"] + 123.6 - 0.45
    poly = np.round(proj([[x0, y0, q["ztv"]], [x1, y0, q["ztv"]], [x1, y1, q["ztv"]], [x0, y1, q["ztv"]]]) * 8)
    m = np.zeros(img.shape[:2], np.uint8)
    cv2.fillPoly(m, [poly.astype(np.int32)], 255, lineType=cv2.LINE_AA, shift=3)
    a = (m.astype(np.float32) / 255.0)[..., None]
    hh, ww = img.shape[:2]
    yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
    base = np.array([0.085, 0.078, 0.072], np.float32)
    grad = 1.0 + 0.22 * (1 - (yy - 140) / 280.0) - 0.10 * ((xx - 520) / 480.0) ** 2
    sheen = 0.035 * np.exp(-(((xx - 600) - 0.55 * (yy - 280)) / 95.0) ** 2)
    # reflexia vine din fotografia estompată puternic (sigma 26 px): din ecranul vechi nu se mai poate citi nimic
    refl = cv2.GaussianBlur(img, (0, 0), 26).mean(axis=2, keepdims=True)
    screen = base * grad[..., None] + sheen[..., None] + 0.05 * (refl - refl[150:400, 300:760].mean())
    screen = np.clip(screen, 0.02, 0.3)
    return img * (1 - a) + screen * a


def scoate_persoana(img):
    """Persoana din golul ușii din dreapta (x ≥ 986, y 316–355 px): copiază în jos tocul și peretele de deasupra."""
    out = img.copy()
    ya, yb, xa = 316, 355, 986
    ww = img.shape[1]
    col = np.median(out[309:316, xa:ww], axis=0)
    fill = np.repeat(col[None], yb - ya, axis=0)
    fill = fill * (1 + 0.012 * np.random.RandomState(3).randn(*fill.shape[:2], 1)).astype(np.float32)
    patch = out[ya:yb, xa:ww]
    keep = np.zeros(patch.shape[:2], np.float32)
    keep[:, :4] = 1.0    # peretele din stânga tocului rămâne neatins
    keep[-3:, :] = 1.0   # capacul boxei din dreapta începe la y ≈ 352
    keep = cv2.GaussianBlur(keep, (0, 0), 0.8)[..., None]
    out[ya:yb, xa:ww] = patch * keep + fill * (1 - keep)
    return out


def main(sursa):
    im = ImageOps.exif_transpose(Image.open(sursa)).convert("RGB")
    assert im.size == (1024, 768), f"camera.json e calibrată pe 1024 × 768, nu pe {im.size}"
    bgr = np.asarray(im, np.float32)[:, :, ::-1] / 255.0
    bgr = scoate_persoana(stinge_televizorul(bgr))
    rgb = np.clip(bgr[:, :, ::-1] * 255 + 0.5, 0, 255).astype(np.uint8)
    Image.fromarray(rgb).save("original.jpg", quality=95)
    print("salvat original.jpg")


if __name__ == "__main__":
    main(sys.argv[1])
