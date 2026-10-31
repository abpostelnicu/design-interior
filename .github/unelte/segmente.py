"""Segmentele de dreaptă din fotografie, pentru calibrarea camerei.

    python segmente.py original.jpg out/                    # toate segmentele + imaginea numerotată
    python segmente.py original.jpg out/ --zona 600 0 1024 400 --min 30
    python segmente.py original.jpg out/ --marire 2         # o fotografie mică, de ~300 px
    python segmente.py --alege out/segmente_toate.json grupuri.json segments.json
    python segmente.py --muchie original.jpg --banda 55 110 [--de-la 4] [--pana-la 240] [--verticala]
                       [--pas 12] [--semn 1|-1] [--prag 1] [--segment u0 v0 u1 v1] [--imagine out/muchie.png]

1. Prima comandă detectează segmentele (LSD) și scrie `out/segmente_toate.json` și `out/segmente_numerotate.png`:
   fotografia mărită de 2 ori, cu fiecare segment colorat și cu indicele lui. Cu `--zona x0 y0 x1 y1` (pixeli
   din fotografie) desenezi doar o zonă, ca indicii să se citească ușor. Cu `--marire 2`, LSD rulează pe
   fotografia mărită de 2 ori și prinde și muchiile fine din pozele mici; coordonatele rămân în pixelii ei.
2. Te uiți pe imagine (unealta `view`) și alegi indicii pentru fiecare muchie cu poziție cunoscută: tavanul,
   colțurile, pardoseala, plinta, marginile unui obiect cu dimensiuni din fișa producătorului. Le scrii într-un
   `grupuri.json`: {"ceil": [12, 40], "corner_left": [3]}. Un grup = o singură dreaptă 3D.
3. A treia comandă scrie `segments.json`, pe grupuri, pentru `camera.calibreaza`.

O muchie slabă, pe care LSD n-o prinde (tavanul alb pe peretele alb), o cauți cu `--muchie`: în banda de rânduri
dată de `--banda` (de coloane, cu `--verticala`), locul unde luminozitatea se schimbă cel mai tare, coloană cu
coloană, cu precizie sub pixel. Comanda dă dreapta prin cele mai multe puncte și segmentul gata de pus în
segments.json; cu `--segment` verifici că un segment LSD de pe aceeași muchie e în prelungirea ei.
Coordonatele sunt ca la LSD: centrul pixelului (i, j) e în (i, j).
"""
import json
import math
import os
import sys

import cv2
import numpy as np


def detecteaza(img, lungime_min=20.0, marire=1.0):
    """Segmentele (N × 4: u0, v0, u1, v1, în px), de la cel mai lung la cel mai scurt.

    marire > 1: LSD rulează pe fotografia mărită de atâtea ori (de exemplu 2), ca să prindă și muchiile fine din
    pozele mici. Coordonatele se aduc înapoi în pixelii fotografiei, în aceeași convenție ca fără mărire
    (centrul pixelului la coordonate întregi), iar lungime_min rămâne în pixelii fotografiei.
    """
    g = img if img.ndim == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if g.dtype != np.uint8:
        g = np.clip(g * 255 + 0.5, 0, 255).astype(np.uint8)
    if marire != 1:
        h, w = g.shape
        g = cv2.resize(g, None, fx=marire, fy=marire, interpolation=cv2.INTER_CUBIC)
        kx, ky = g.shape[1] / w, g.shape[0] / h          # scara reală, după rotunjirea mărimii
    lines = cv2.createLineSegmentDetector(cv2.LSD_REFINE_ADV).detect(g)[0]
    if lines is None:
        return np.zeros((0, 4), np.float32)
    s = lines.reshape(-1, 4)
    if marire != 1:
        # cv2.resize pune centrul pixelului i al fotografiei în (i + 0,5)·k − 0,5 pe imaginea mărită
        s = s.copy()
        s[:, 0::2] = (s[:, 0::2] + 0.5) / kx - 0.5
        s[:, 1::2] = (s[:, 1::2] + 0.5) / ky - 0.5
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


# ------------------------------------------------------------------ muchia slabă, din gradient

def _gri(img):
    """Imaginea în tonuri de gri, float64, cu valorile 0…255 (ca diferențele de gradient să fie în niveluri)."""
    if img.ndim == 3:
        g = cv2.cvtColor(img if img.dtype == np.uint8 else img.astype(np.float32), cv2.COLOR_BGR2GRAY)
    else:
        g = img
    return g.astype(np.float64) * (1.0 if img.dtype == np.uint8 else 255.0)


def _puncte_muchie(g, verticala, banda, de_la, pana_la, pas, latime, sigma, semn):
    """(poziția de-a lungul muchiei, poziția peste ea, gradientul) pentru fiecare coloană (rând, la verticală)."""
    if sigma > 0:
        g = cv2.GaussianBlur(g, (0, 0), sigma)
    if verticala:
        g = g.T                     # rândurile devin coloane, iar căutarea rămâne aceeași
    gd = np.diff(g, axis=0)         # gd[k] e granița dintre rândurile k și k + 1, adică la k + 0,5
    lo, hi = sorted(banda)
    a, b = max(0, math.ceil(lo - 0.5)), min(gd.shape[0], math.floor(hi - 0.5) + 1)
    if b - a < 3:
        raise ValueError("banda e prea îngustă sau iese din imagine")
    jum = max(0, int(latime) // 2)
    rez = []
    for i in range(max(0, math.ceil(de_la)), min(g.shape[1] - 1, math.floor(pana_la)) + 1, int(pas)):
        col = gd[a:b, max(0, i - jum):min(g.shape[1], i + jum + 1)].mean(axis=1)
        tinta = col * semn if semn else np.abs(col)
        k = int(np.argmax(tinta))
        dk = 0.0
        if 0 < k < len(tinta) - 1:                      # vârful parabolei prin cele trei valori din jur
            y0, y1, y2 = tinta[k - 1], tinta[k], tinta[k + 1]
            numitor = y0 - 2 * y1 + y2
            if numitor < 0:
                dk = 0.5 * (y0 - y2) / numitor
        rez.append((float(i), a + k + 0.5 + dk, float(col[k])))
    return rez


def _abateri(t, s, m, c):
    """Distanța perpendiculară, cu semn, a punctelor (t, s) până la dreapta s = m·t + c."""
    return (np.asarray(s, float) - (m * np.asarray(t, float) + c)) / math.hypot(1.0, m)


def _potrivire_robusta(t, s, prag, max_perechi=20000):
    """Dreapta cu cele mai multe puncte la cel mult `prag` px, rafinată apoi prin ele: (m, c, păstrate).

    Încearcă dreptele prin perechi de puncte, ca altă muchie din bandă, mai puternică pe o porțiune, să nu tragă
    dreapta după ea.
    """
    n = len(t)
    perechi = [(i, j) for i in range(n) for j in range(i + 1, n) if t[j] != t[i]]
    if len(perechi) > max_perechi:
        alese = np.random.default_rng(0).choice(len(perechi), max_perechi, replace=False)
        perechi = [perechi[k] for k in alese]
    cel_mai_bun, pastrate = None, np.ones(n, bool)
    for i, j in perechi:
        m = (s[j] - s[i]) / (t[j] - t[i])
        d = np.abs(_abateri(t, s, m, s[i] - m * t[i]))
        bune = d <= prag
        cheie = (int(bune.sum()), -float(np.sum(d[bune] ** 2)))
        if cel_mai_bun is None or cheie > cel_mai_bun:
            cel_mai_bun, pastrate = cheie, bune
    m, c = np.polyfit(t[pastrate], s[pastrate], 1)
    for _ in range(10):
        noi = np.abs(_abateri(t, s, m, c)) <= prag
        if noi.sum() < 2 or (noi == pastrate).all():
            break
        pastrate = noi
        m, c = np.polyfit(t[pastrate], s[pastrate], 1)
    return float(m), float(c), pastrate


def muchie_slaba(img, banda, de_la=None, pana_la=None, verticala=False, pas=12, latime=5, sigma=1.0, semn=0,
                 prag=1.0):
    """O muchie slabă, pe care LSD n-o prinde (tavanul alb pe peretele alb), găsită din gradientul fotografiei.

    Pentru o muchie aproape orizontală: în fiecare coloană u, din `pas` în `pas` px, de la `de_la` la `pana_la`,
    caută între rândurile banda = (v0, v1) locul unde luminozitatea se schimbă cel mai tare, cu precizie sub
    pixel. Gradientul e mediat pe `latime` coloane vecine, după o estompare gaussiană (`sigma`, px). semn = 1 ia
    doar muchiile care se luminează în jos (spre v mai mare), −1 doar pe cele care se întunecă, 0 pe oricare.
    Cu verticala=True, totul merge pe rânduri, iar banda e pe u. Apoi potrivește dreapta care trece prin cele mai
    multe puncte, la cel mult `prag` px.

    Întoarce un dict: puncte (N × 2, u și v), gradient, pastrate (punctele din potrivire), abateri (px, cu semn),
    dreapta (m, c: v = m·u + c sau, la verticală, u = m·v + c), rms (px), segment ([u0, v0, u1, v1], între primul
    și ultimul punct păstrat, gata de pus în segments.json), verticala și banda. Coordonatele sunt ca la
    `detecteaza`: centrul pixelului (i, j) e în (i, j).
    """
    g = _gri(img)
    lungime = g.shape[0] if verticala else g.shape[1]
    t0 = 0 if de_la is None else max(0, de_la)
    t1 = lungime - 1 if pana_la is None else min(lungime - 1, pana_la)
    pct = _puncte_muchie(g, verticala, banda, t0, t1, pas, latime, sigma, semn)
    if len(pct) < 2:
        raise ValueError("am găsit mai puțin de două puncte: mărește intervalul sau micșorează pasul")
    t = np.array([p[0] for p in pct])
    s = np.array([p[1] for p in pct])
    m, c, pastrate = _potrivire_robusta(t, s, prag)
    d = _abateri(t, s, m, c)
    ta, tb = float(t[pastrate].min()), float(t[pastrate].max())

    def uv(tt, ss):
        return (ss, tt) if verticala else (tt, ss)

    return {"puncte": np.array([uv(a, b) for a, b in zip(t, s)]), "gradient": np.array([p[2] for p in pct]),
            "pastrate": pastrate, "abateri": d, "dreapta": (m, c), "rms": float(np.sqrt(np.mean(d[pastrate] ** 2))),
            "segment": [round(float(v), 2) for v in (*uv(ta, m * ta + c), *uv(tb, m * tb + c))],
            "verticala": verticala, "banda": tuple(sorted(banda))}


def abateri_segment(muchie, segment):
    """Distanța capetelor unui segment [u0, v0, u1, v1] până la dreapta muchiei, în px, cu semn.

    Un segment LSD de pe aceeași muchie trebuie să fie în prelungirea ei: abateri sub ~1 px.
    """
    m, c = muchie["dreapta"]
    capete = ((segment[0], segment[1]), (segment[2], segment[3]))
    if muchie["verticala"]:
        return [float(_abateri([v], [u], m, c)[0]) for u, v in capete]
    return [float(_abateri([u], [v], m, c)[0]) for u, v in capete]


def deseneaza_muchie(img, muchie, dest, segmente=(), zoom=4, margine=20):
    """Imaginea de control, mărită: banda în albastru, punctele în verde (cele scoase din potrivire în portocaliu),
    dreapta în roșu, prelungită până la segmentele de verificare, desenate în mov. Întoarce mărimea ei."""
    u8 = img if img.dtype == np.uint8 else np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8)
    if u8.ndim == 2:
        u8 = cv2.cvtColor(u8, cv2.COLOR_GRAY2BGR)
    h, w = u8.shape[:2]
    pts, vert = muchie["puncte"], muchie["verticala"]
    us = list(pts[:, 0]) + [x for sg in segmente for x in sg[0::2]]
    vs = list(pts[:, 1]) + [x for sg in segmente for x in sg[1::2]]
    x0, x1 = max(0, int(min(us)) - margine), min(w, int(max(us)) + margine + 1)
    y0, y1 = max(0, int(min(vs)) - margine), min(h, int(max(vs)) + margine + 1)
    big = cv2.resize(u8[y0:y1, x0:x1], None, fx=zoom, fy=zoom, interpolation=cv2.INTER_CUBIC)

    def P(u, v):    # centrul pixelului i ajunge, pe imaginea mărită, în (i − x0 + 0,5)·zoom − 0,5
        return int(round((u - x0 + 0.5) * zoom - 0.5)), int(round((v - y0 + 0.5) * zoom - 0.5))

    for lim in muchie["banda"]:
        p, q = ((lim, y0), (lim, y1)) if vert else ((x0, lim), (x1, lim))
        cv2.line(big, P(*p), P(*q), (255, 120, 0), 1, cv2.LINE_AA)
    for sg in segmente:
        cv2.line(big, P(sg[0], sg[1]), P(sg[2], sg[3]), (200, 0, 200), 2, cv2.LINE_AA)
    m, c = muchie["dreapta"]
    ts = list(pts[:, 1] if vert else pts[:, 0]) + [x for sg in segmente for x in (sg[1::2] if vert else sg[0::2])]
    capete = [(m * t + c, t) if vert else (t, m * t + c) for t in (min(ts) - margine, max(ts) + margine)]
    cv2.line(big, P(*capete[0]), P(*capete[1]), (0, 0, 230), 1, cv2.LINE_AA)
    for (u, v), ok in zip(pts, muchie["pastrate"]):
        cv2.circle(big, P(u, v), 4, (0, 170, 0) if ok else (0, 140, 255), 2, cv2.LINE_AA)
    os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
    cv2.imwrite(dest, big)
    return big.shape[1], big.shape[0]


def _main_muchie(argv):
    """`segmente.py --muchie original.jpg --banda A B [opțiuni]`."""
    spec = {"--banda": 2, "--de-la": 1, "--pana-la": 1, "--verticala": 0, "--pas": 1, "--latime": 1, "--sigma": 1,
            "--semn": 1, "--prag": 1, "--segment": 4, "--imagine": 1}
    poz, o, i = [], {"--segment": []}, 0
    try:
        while i < len(argv):
            a, n = argv[i], spec.get(argv[i])
            if n is None:
                if a.startswith("--"):
                    raise ValueError(f"opțiune necunoscută: {a}")
                poz.append(a)
                i += 1
                continue
            vals = argv[i + 1:i + 1 + n]
            if len(vals) < n:
                raise ValueError(f"{a} cere {n} {'valoare' if n == 1 else 'valori'}")
            nums = [float(v.replace(",", ".")) for v in vals] if a != "--imagine" else vals
            if a == "--segment":
                o[a].append(nums)
            else:
                o[a] = True if n == 0 else (nums[0] if n == 1 else nums)
            i += 1 + n
        if len(poz) != 1 or "--banda" not in o:
            raise ValueError("dai fotografia și --banda A B")
    except ValueError as e:
        msg = str(e) if "could not convert" not in str(e) else "o valoare nu e un număr"
        print(f"eroare: {msg}. Vezi: python segmente.py --help", file=sys.stderr)
        return 2
    img = cv2.imread(poz[0])
    if img is None:
        print("nu pot citi", poz[0])
        return 1
    vert = "--verticala" in o
    try:
        rez = muchie_slaba(img, o["--banda"], o.get("--de-la"), o.get("--pana-la"), vert, int(o.get("--pas", 12)),
                           int(o.get("--latime", 5)), o.get("--sigma", 1.0), int(o.get("--semn", 0)),
                           o.get("--prag", 1.0))
    except ValueError as e:
        print(f"eroare: {e}", file=sys.stderr)
        return 2

    def f(v, z=2):
        return f"{v:.{z}f}".replace(".", ",")

    at, asx = ("v", "u") if vert else ("u", "v")
    m, c = rez["dreapta"]
    a, b = rez["banda"]
    print(f"Muchie {'verticală' if vert else 'orizontală'} în banda {asx} {f(a, 1)} … {f(b, 1)}, din "
          f"{int(o.get('--pas', 12))} în {int(o.get('--pas', 12))} px")
    print(f"{at:>7} {asx:>8} {'gradient':>9} {'abatere':>8}")
    for (u, v), g, d, ok in zip(rez["puncte"], rez["gradient"], rez["abateri"], rez["pastrate"]):
        tt, ss = (v, u) if vert else (u, v)
        print(f"{f(tt, 1):>7} {f(ss):>8} {f(g):>9} {f(d):>8}" + ("" if ok else "  * scos"))
    n_ok = int(rez["pastrate"].sum())
    print(f"Dreapta: {asx} = {f(m, 5)}·{at} + {f(c)} (unghi {f(math.degrees(math.atan(m)))}°), prin {n_ok} din "
          f"{len(rez['puncte'])} puncte; abaterea medie pătratică {f(rez['rms'])} px")
    print(f"Segmentul pentru segments.json: {json.dumps(rez['segment'])}")
    cod = 0
    for sg in o["--segment"]:
        d0, d1 = abateri_segment(rez, sg)
        ok = max(abs(d0), abs(d1)) <= o.get("--prag", 1.0)
        cod |= not ok
        print(f"Segmentul {json.dumps(sg)}: capetele la {f(d0)} și {f(d1)} px de dreaptă → "
              + ("e în prelungirea ei." if ok else "NU e pe aceeași dreaptă."))
    if "--imagine" in o:
        size = deseneaza_muchie(img, rez, o["--imagine"], o["--segment"])
        print(f"salvat {os.path.basename(o['--imagine'])} ({size[0]} × {size[1]})")
    return cod


def main(argv):
    if argv and argv[0] == "--muchie":
        return _main_muchie(argv[1:])
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
    marire = float(argv[argv.index("--marire") + 1]) if "--marire" in argv else 1.0
    img = cv2.imread(src)
    if img is None:
        print("nu pot citi", src)
        return 1
    segs = detecteaza(img, lmin, marire)
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "segmente_toate.json"), "w", encoding="utf-8") as f:
        json.dump([[round(float(v), 2) for v in s] for s in segs], f)
    size = deseneaza(img, segs, os.path.join(outdir, "segmente_numerotate.png"), zona)
    print(f"{len(segs)} segmente; salvat segmente_toate.json și segmente_numerotate.png ({size[0]} × {size[1]})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
