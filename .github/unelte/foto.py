"""Fotografia de lucru: fără metadate, la mărimea standard, cu zoom-uri pe grilă, curățată de date personale.

    python foto.py pregateste <fotografia primită> original.jpg [1024]   # fără EXIF, 1024 px pe latura mare
    python foto.py exif <fișier> [<fișier>...]                          # ce metadate are; codul 1 la EXIF/GPS
    python foto.py grila original.jpg out/zoom.png x0 y0 x1 y1 [zoom]   # zoom cu grilă de coordonate (px)

Imaginile se țin în memorie ca la OpenCV: BGR, float32, valori 0…1 (`citeste`). Le salvezi cu `scrie`, prin PIL,
care nu adaugă metadate. Nu folosești `sips`: păstrează coordonatele GPS.

Curățarea (preluată din `.github/surse/polite-viniluri/curata_foto.py`):
- `stinge_ecran`: un ecran aprins devine sticlă neagră (pe televizor se vedeau numele rețelelor Wi-Fi din jur);
- `umple_de_sus`: acoperă un dreptunghi cu peretele sau tocul de deasupra (o persoană din golul ușii);
- `sterge` și `estompeaza`: text, numere de înmatriculare, documente, obiecte mici.
După curățare te uiți pe zoom-uri (`grila` + unealta `view`) la ecrane, ferestre, documente și persoane.
"""
import io
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageOps

GPS_IFD = 0x8825


def citeste(path):
    """Imaginea ca BGR float32, 0…1."""
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(path)
    return img.astype(np.float32) / 255.0


def to_u8(img):
    return img if img.dtype == np.uint8 else np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8)


def scrie(path, img, calitate=95):
    """Salvează o imagine BGR (float 0…1 sau uint8) prin PIL, fără metadate."""
    rgb = Image.fromarray(to_u8(img)[:, :, ::-1])
    if path.lower().endswith((".jpg", ".jpeg")):
        rgb.save(path, quality=calitate)
    else:
        rgb.save(path)
    return path


def metadate(path):
    """{"exif": câmpuri EXIF, "gps": are coordonate GPS, "altele": blocuri de metadate (xmp, iptc, comentarii)}."""
    with Image.open(path) as im:
        ex = im.getexif()
        gps = bool(ex) and (GPS_IFD in ex or bool(ex.get_ifd(GPS_IFD)))
        altele = sorted(k for k in im.info if k.lower() in ("exif", "xmp", "xml:com.adobe.xmp", "comment", "iptc",
                                                             "photoshop"))
        return {"exif": len(ex), "gps": gps, "altele": altele}


def _in_srgb(im):
    """Culorile în sRGB: fotografiile de pe telefon vin des în Display P3; fără conversie, ies mai șterse."""
    icc = im.info.get("icc_profile")
    if not icc:
        return im.convert("RGB")
    try:
        from PIL import ImageCms
        src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        return ImageCms.profileToProfile(im.convert("RGB"), src, ImageCms.createProfile("sRGB"), outputMode="RGB")
    except Exception:           # profil stricat sau Pillow fără LittleCMS: rămân culorile așa cum sunt
        return im.convert("RGB")


def pregateste(sursa, dest, latura=1024, calitate=95):
    """Fotografia primită -> fotografia de lucru: rotită după EXIF, în sRGB, latura mare de `latura` px, fără
    metadate (EXIF, GPS, XMP, comentarii, profil de culoare).

    O fotografie 4:3 iese 1024 × 768 (orizontală) sau 768 × 1024 (verticală), ca în proiectele existente.
    Fotografiile HEIC (iPhone) se deschid doar cu pachetul pillow-heif instalat.
    """
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
    except ImportError:
        pass
    with Image.open(sursa) as src:
        im = _in_srgb(ImageOps.exif_transpose(src))
    k = latura / max(im.size)
    size = (round(im.size[0] * k), round(im.size[1] * k))
    if size != im.size:
        im = im.resize(size, Image.LANCZOS)
    im.info = {}                # altfel Pillow copiază comentariul JPEG în fișierul nou
    im.save(dest, quality=calitate)
    m = metadate(dest)
    if m["exif"] or m["gps"] or m["altele"]:
        raise RuntimeError(f"{dest} a rămas cu metadate: {m}")
    return size


def _pas(span, zoom):
    for p in (5, 10, 20, 25, 50, 100, 200, 250, 500):
        if span / p <= 16 and p * zoom >= 40:
            return p
    return 500


def grila(img, dest, zona=None, zoom=3, pas=None):
    """Zona (x0, y0, x1, y1) din fotografie, mărită de zoom ori, cu grilă și cu coordonatele în pixelii fotografiei.

    O folosești ca să citești pozițiile exacte (prize, rame, plinte, colțuri), apoi le treci în
    `Camera.backproject` sau în segments.json.
    """
    u8 = to_u8(img)
    x0, y0, x1, y1 = zona or (0, 0, u8.shape[1], u8.shape[0])
    crop = cv2.resize(u8[y0:y1, x0:x1], None, fx=zoom, fy=zoom, interpolation=cv2.INTER_CUBIC)
    p = pas or _pas(max(x1 - x0, y1 - y0), zoom)
    m = 44
    out = np.full((crop.shape[0] + m, crop.shape[1] + m, 3), 255, np.uint8)
    out[m:, m:] = crop
    over = out.copy()
    for x in range((x0 // p + 1) * p if x0 % p else x0, x1, p):
        X = m + int((x - x0) * zoom)
        cv2.line(over, (X, m), (X, out.shape[0] - 1), (0, 0, 255), 1)
        cv2.putText(out, str(x), (X - 14, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 160), 1, cv2.LINE_AA)
    for y in range((y0 // p + 1) * p if y0 % p else y0, y1, p):
        Y = m + int((y - y0) * zoom)
        cv2.line(over, (m, Y), (out.shape[1] - 1, Y), (0, 0, 255), 1)
        cv2.putText(out, str(y), (2, Y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 160), 1, cv2.LINE_AA)
    out[m:, m:] = cv2.addWeighted(out[m:, m:], 0.55, over[m:, m:], 0.45, 0)
    cv2.imwrite(dest, out)
    return out.shape[1], out.shape[0]


def _masca(shape, poligon):
    m = np.zeros(shape[:2], np.uint8)
    cv2.fillPoly(m, [np.round(np.asarray(poligon, float) * 8).astype(np.int32)], 255, lineType=cv2.LINE_AA, shift=3)
    return (m.astype(np.float32) / 255.0)[..., None]


def stinge_ecran(img, poligon, sigma=26.0):
    """Ecranul aprins devine sticlă neagră: gradient fin, un luciu diagonal și reflexia foarte estompată a camerei.

    poligon: colțurile ecranului, în px (de exemplu proiectate cu camera calibrată din colțurile 3D ale ecranului).
    Reflexia vine din fotografia estompată cu sigma = 26 px: din ecranul vechi nu se mai poate citi nimic.
    """
    img = img.astype(np.float32)
    a = _masca(img.shape, poligon)
    poly = np.asarray(poligon, float)
    (x0, y0), (x1, y1) = poly.min(0), poly.max(0)
    w, h = max(x1 - x0, 1.0), max(y1 - y0, 1.0)
    xc, yc = (x0 + x1) / 2, (y0 + y1) / 2
    hh, ww = img.shape[:2]
    yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
    base = np.array([0.085, 0.078, 0.072], np.float32)
    grad = 1.0 + 0.22 * (1 - (yy - y0) / h) - 0.10 * ((xx - xc) / w) ** 2
    sheen = 0.035 * np.exp(-(((xx - xc - 0.17 * w) - 0.55 * (yy - yc)) / (0.2 * w)) ** 2)
    refl = cv2.GaussianBlur(img, (0, 0), sigma).mean(axis=2, keepdims=True)
    inside = refl[int(y0):int(np.ceil(y1)) + 1, int(x0):int(np.ceil(x1)) + 1]
    screen = base * grad[..., None] + sheen[..., None] + 0.05 * (refl - inside.mean())
    screen = np.clip(screen, 0.02, 0.3)
    return img * (1 - a) + screen * a


def umple_de_sus(img, x0, y0, x1, y1, randuri=7, pastreaza_stanga=0, pastreaza_jos=0, seed=3):
    """Acoperă dreptunghiul cu ce e deasupra lui: mediana celor `randuri` rânduri de sus, coborâtă în jos.

    Merge când deasupra e un toc sau un perete uniform. pastreaza_stanga / pastreaza_jos: câți pixeli de la
    marginea din stânga / de jos rămân neatinși (de exemplu peretele de lângă toc sau capacul unei boxe).
    """
    out = img.astype(np.float32).copy()
    col = np.median(out[y0 - randuri:y0, x0:x1], axis=0)
    fill = np.repeat(col[None], y1 - y0, axis=0)
    fill = fill * (1 + 0.012 * np.random.RandomState(seed).randn(*fill.shape[:2], 1)).astype(np.float32)
    patch = out[y0:y1, x0:x1]
    keep = np.zeros(patch.shape[:2], np.float32)
    if pastreaza_stanga:
        keep[:, :pastreaza_stanga] = 1.0
    if pastreaza_jos:
        keep[-pastreaza_jos:, :] = 1.0
    keep = cv2.GaussianBlur(keep, (0, 0), 0.8)[..., None]
    out[y0:y1, x0:x1] = patch * keep + fill * (1 - keep)
    return out


def sterge(img, poligon, raza=6):
    """Șterge zona din poligon (px) și o reface din jur, cu cv2.inpaint: text, plăcuțe, obiecte mici."""
    u8 = to_u8(img)
    m = np.zeros(u8.shape[:2], np.uint8)
    cv2.fillPoly(m, [np.round(np.asarray(poligon, float)).astype(np.int32)], 255)
    m = cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=2)
    res = cv2.inpaint(u8, m, raza, cv2.INPAINT_TELEA)
    return res if img.dtype == np.uint8 else res.astype(np.float32) / 255.0


def estompeaza(img, poligon, sigma=10.0):
    """Estompează puternic zona din poligon (px), ca textul să nu se mai poată citi."""
    f = img.astype(np.float32)
    a = _masca(f.shape, poligon)
    out = f * (1 - a) + cv2.GaussianBlur(f, (0, 0), sigma) * a
    return out.astype(img.dtype) if img.dtype == np.uint8 else out


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    cmd, args = argv[0], argv[1:]
    if cmd == "pregateste":
        size = pregateste(args[0], args[1], int(args[2]) if len(args) > 2 else 1024)
        print(f"salvat {os.path.basename(args[1])}: {size[0]} × {size[1]}, fără metadate")
        return 0
    if cmd == "exif":
        bad = 0
        for p in args:
            m = metadate(p)
            ok = not (m["exif"] or m["gps"] or m["altele"])
            bad += not ok
            print(("ok  " if ok else "ARE ") + f"{p}: EXIF {m['exif']} câmpuri, GPS {'da' if m['gps'] else 'nu'}"
                  + (f", {', '.join(m['altele'])}" if m["altele"] else ""))
        return 1 if bad else 0
    if cmd == "grila":
        zona = tuple(int(v) for v in args[2:6])
        zoom = float(args[6]) if len(args) > 6 else 3
        size = grila(citeste(args[0]), args[1], zona, zoom)
        print(f"salvat {args[1]} ({size[0]} × {size[1]})")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
