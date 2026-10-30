"""Beton decorativ (microciment) pentru polițe: textură procedurală care înlocuiește stejarul din materials.py.

Texturile au formatul celor din materials.py: np.ndarray float32 (rânduri, coloane, 3), canale BGR, valori
0…1, R_OAK = 10 pixeli pe cm; rândurile merg de-a lungul lungimii, coloanele pe lățime. Aspectul: nori fini de
ton, urme largi și discrete de mistrie (arce suprapuse, unele cu o linie fină la muchie), pori mici și rari,
granulație fină, fără nimic care să se repete. Finisajul mat-satinat apare doar ca diferențe mici de ton
între trecerile mistriei, fără luciu.

Aleatorul vine numai din parametrul rng (np.random.RandomState sau np.random.Generator).

Tonurile sunt culori aparente din fotografie, ca OAK_REF din materials.py, iar randarea le înmulțește cu
lumina peretelui:
- „antracit”: mediana fronturilor din microciment ale comodei, măsurată pe planul fronturilor (`measure_fronts`);
- „gri”: gri natural de beton, deschis spre mediu, ușor cald; e mai deschis și mai neutru decât peretele
  bej-gri din spatele polițelor (`measure_wall`).

Folosire în render.py (Scene.draw_shelf), în locul stejarului:
    face = concrete_panel(L + 22, P + 2, rng, ton)    # ton = "gri" sau "antracit"
    edge = concrete_edge(L + 22, T + 2, rng, ton)
    endg = concrete_end(T, P, rng, ton)
Lungimea are 20 cm în plus pentru că oak_color deplasează eșantionarea cu până la 20 cm; altfel `sample` ar
repeta textura în oglindă, iar la beton simetria s-ar vedea.

`python beton.py` măsoară tonurile, face mostrele out/beton_gri.png, out/beton_antracit.png și
out/beton_comparatie.png și afișează diferențele ΔE.
"""
import os

import cv2
import numpy as np

from core import HERE, PHOTO, cam1
from design import CABINET, D, TV
from materials import R_OAK

# BGR, 0…1: mediana fronturilor comodei (RGB 73, 74, 73) și griul de beton ales (RGB 170, 166, 158)
TONES = {
    "antracit": np.array([73, 74, 73], np.float32) / 255.0,
    "gri": np.array([158, 166, 170], np.float32) / 255.0,
}

# cât de vizibile sunt componentele, raportat la ton: pe antracit, urmele de mistrie se văd mai tare
STYLE = {
    "antracit": dict(cloud=0.030, trowel=0.045, vein=0.11, grain=0.012, pores=0.04, pore_depth=(0.12, 0.35),
                     pore_light=0.35, chroma=0.006, vein_w=(0.07, 0.12), vein_p=0.45, pass_area=110.0),
    "gri": dict(cloud=0.018, trowel=0.026, vein=0.04, grain=0.008, pores=0.035, pore_depth=(0.06, 0.20),
                pore_light=0.0, chroma=0.004, vein_w=(0.07, 0.12), vein_p=0.45, pass_area=110.0),
}
# vein_w = lățimea liniilor fine de la muchia mistriei (cm), vein_p = cât de des apar (din trecerile mistriei),
# pass_area = suprafața care revine unei treceri de mistrie (cm²); mai mică înseamnă mai multe urme


# ------------------------------------------------------------------ textura

def _smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _noise(rng, h, w, sigma):
    """Zgomot alb netezit gaussian (sigma în pixeli), cu deviația standard ~1 indiferent de mărimea panoului.

    Se generează pe o suprafață mai mare decât panoul, ca marginile să nu iasă în oglindă; câmpurile largi se
    calculează la rezoluție mică și se măresc.
    """
    k = max(1.0, sigma / 3.0)
    s = sigma / k
    p = int(np.ceil(3 * s)) + 1
    hh, ww = int(np.ceil(h / k)) + 2, int(np.ceil(w / k)) + 2
    n = rng.standard_normal((hh + 2 * p, ww + 2 * p)).astype(np.float32)
    n = cv2.GaussianBlur(n, (0, 0), s)[p:p + hh, p:p + ww]
    n *= 2 * np.sqrt(np.pi) * s           # deviația standard teoretică a zgomotului netezit e 1 / (2 √π s)
    if k > 1:
        n = cv2.resize(n, (int(round(ww * k)), int(round(hh * k))), interpolation=cv2.INTER_CUBIC)
    return n[:h, :w]


def _clouds(rng, h, w, r):
    """Nori fini de ton, ușor curgători (câmp deformat de alt câmp de zgomot)."""
    c = (0.40 * _noise(rng, h, w, 9.0 * r) + 0.42 * _noise(rng, h, w, 3.0 * r) + 0.34 * _noise(rng, h, w, 1.0 * r)
         + 0.18 * _noise(rng, h, w, 0.4 * r))
    # pete cu margini mai clare, unde mistria a lustruit mai mult
    c += 0.45 * np.tanh(2.0 * _noise(rng, h, w, 2.4 * r))
    du = 1.6 * r * _noise(rng, h, w, 5.0 * r)
    dv = 1.6 * r * _noise(rng, h, w, 5.0 * r)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    c = cv2.remap(c, xx + du, yy + dv, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return c - c.mean()


def _trowel(rng, h, w, r, along=False, vein_w=(0.07, 0.12), vein_p=0.45, pass_area=110.0):
    """Urmele mistriei: arce late suprapuse, fiecare cu un ton puțin diferit (trecerile mai noi le acoperă pe
    cele vechi); muchia din față a mistriei e netă și uneori lasă o linie fină, mai deschisă.

    Întoarce (tonul trecerilor, liniile fine), amândouă cu media ~0. Cu along=True, trecerile merg de-a lungul
    rândurilor, ca pe un cant îngust.
    """
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    wob = 0.25 * r * _noise(rng, h, w, 1.5 * r)            # muchiile mistriei nu sunt perfect circulare
    gate = _noise(rng, h, w, 2.2 * r)                      # liniile fine apar pe bucăți
    T = np.zeros((h, w), np.float32)
    V = np.zeros((h, w), np.float32)
    n = max(3, int(round(h * w / r ** 2 / pass_area)))
    for _ in range(n):
        if along:
            R = rng.uniform(60, 160) * r
            bw = rng.uniform(5, 9) * r
            phi = (0.0 if rng.uniform() < 0.5 else np.pi) + rng.uniform(-0.15, 0.15)
        else:
            R = rng.uniform(16, 55) * r
            bw = rng.uniform(6, 12) * r
            phi = rng.uniform(0, 2 * np.pi)
        px, py = rng.uniform(-0.1 * w, 1.1 * w), rng.uniform(-0.1 * h, 1.1 * h)
        cx, cy = px + R * np.cos(phi), py + R * np.sin(phi)
        half = 0.5 * rng.uniform(18, 45) * r               # jumătate din lungimea trecerii, pe arc
        a0 = phi + np.pi
        sharp = 1.0 if rng.uniform() < 0.5 else -1.0       # partea muchiei nete
        delta = rng.standard_normal()
        alpha = rng.uniform(0.45, 0.9)
        has_vein = rng.uniform() < vein_p
        vein_sign = 1.0 if rng.uniform() < 0.9 else -0.6    # rar, câte o linie mai închisă
        soft = rng.uniform(1.5, 3.5) * r

        # doar în dreptunghiul care cuprinde arcul
        ang = a0 + np.linspace(-half / R, half / R, 24)
        ex, ey = cx + R * np.cos(ang), cy + R * np.sin(ang)
        m = bw + 2 * r
        x0, x1 = int(max(np.floor(ex.min() - m), 0)), int(min(np.ceil(ex.max() + m), w))
        y0, y1 = int(max(np.floor(ey.min() - m), 0)), int(min(np.ceil(ey.max() + m), h))
        if x1 <= x0 or y1 <= y0:
            continue
        sl = (slice(y0, y1), slice(x0, x1))
        X, Y = xx[sl] - cx, yy[sl] - cy
        d = (np.hypot(X, Y) - R + wob[sl]) * sharp         # d = +bw/2 la muchia netă
        along_arc = np.angle(np.exp(1j * (np.arctan2(Y, X) - a0))) * R
        ends = _smoothstep(half, half - rng.uniform(4, 9) * r, np.abs(along_arc))
        across = _smoothstep(0.5 * bw, 0.5 * bw - 0.25 * r, d) * _smoothstep(-0.5 * bw, -0.5 * bw + soft, d)
        mask = (across * ends).astype(np.float32)
        a = alpha * mask
        T[sl] = T[sl] * (1 - a) + delta * a
        if has_vein:
            lw = rng.uniform(*vein_w) * r
            line = np.exp(-((d - 0.5 * bw) / lw) ** 2) * ends * _smoothstep(-0.1, 0.7, gate[sl])
            V[sl] += vein_sign * line.astype(np.float32)
    return T - T.mean(), V


def _pores(rng, h, w, r, density, depth, light):
    """Pori mici și rari: pete de ~1–2 mm, mai închise (pe antracit, unii par mai deschiși)."""
    P = np.zeros((h + 8, w + 8), np.float32)
    n = rng.poisson(density * h * w / r ** 2)
    ky, kx = np.mgrid[-3:4, -3:4].astype(np.float32)
    for _ in range(n):
        y, x = rng.uniform(0, h), rng.uniform(0, w)
        s = rng.uniform(0.035, 0.09) * r
        dep = rng.uniform(*depth) * (-0.6 if rng.uniform() < light else 1.0)
        iy, ix = int(y), int(x)
        g = np.exp(-((ky - (y - iy)) ** 2 + (kx - (x - ix)) ** 2) / (2 * s * s))
        P[iy + 1:iy + 8, ix + 1:ix + 8] += dep * g
    return 1 - P[4:4 + h, 4:4 + w]


def _tone_ref(tone):
    if isinstance(tone, str):
        if tone not in TONES:
            raise ValueError(f"ton necunoscut: {tone!r}; tonurile sunt {sorted(TONES)}")
        return TONES[tone], STYLE[tone]
    ref = np.asarray(tone, np.float32).reshape(-1)
    if ref.size != 3:
        raise ValueError("tone e „gri”, „antracit” sau o culoare BGR 0…1 (3 valori)")
    style = STYLE["antracit"] if ref.mean() < 0.4 else STYLE["gri"]
    return ref, style


def _style(st, gain):
    """Stilul tonului cu câștigurile aplicate: gain = {componentă: multiplicator}, de exemplu dict(vein=2.0)."""
    st = dict(st)
    for k, g in (gain or {}).items():
        if k not in st:
            raise ValueError(f"componentă necunoscută: {k!r}; sunt {sorted(st)}")
        st[k] = tuple(v * g for v in st[k]) if isinstance(st[k], tuple) else st[k] * g
    st["vein_p"] = min(st["vein_p"], 1.0)
    return st


def _concrete(h, w, rng, tone, along=False, gain=None, cut=None):
    """Textura de h × w pixeli. Cu cut = lățimea în pixeli, e o fâșie din mijlocul unui panou de h × cut."""
    ref, st = _tone_ref(tone)
    st = _style(st, gain)
    if cut is not None and cut > w:
        full = _concrete(h, cut, rng, tone, along, gain)
        a = (cut - w) // 2
        out = full[:, a:a + w]
        out = out * (ref / out.reshape(-1, 3).mean(0))       # media exactă a tonului și pe fâșie
        return np.clip(out, 0, 1).astype(np.float32)
    r = R_OAK
    lum = 1 + st["cloud"] * _clouds(rng, h, w, r)
    T, V = _trowel(rng, h, w, r, along, st["vein_w"], st["vein_p"], st["pass_area"])
    lum += st["trowel"] * T + st["vein"] * V
    lum += st["grain"] * _noise(rng, h, w, 0.7)
    lum *= _pores(rng, h, w, r, st["pores"], st["pore_depth"], st["pore_light"])
    c = st["chroma"] * _noise(rng, h, w, 12.0 * r)          # nuanțe abia vizibile, spre cald sau spre rece
    out = ref[None, None, :] * lum[..., None]
    out[..., 0] *= 1 - c
    out[..., 2] *= 1 + c
    out *= ref / out.reshape(-1, 3).mean(0)                  # media exactă a tonului
    return np.clip(out, 0, 1).astype(np.float32)


def concrete_panel(length_cm, width_cm, rng, tone, gain=None):
    """Panou de microciment, ca materials.glued_panel: rândurile pe lungime, coloanele pe lățime.

    tone: „gri”, „antracit” sau o culoare BGR 0…1. Întoarce float32 (round(length_cm·10) + 2,
    round(width_cm·10) + 2, 3), BGR, 0…1.
    gain: multiplicatori pentru componentele din STYLE (cloud, trowel, vein, vein_w, vein_p, pass_area…), pentru
    randările mici, unde estomparea stinge urmele fine; media tonului rămâne aceeași.
    """
    r = R_OAK
    L = int(round(length_cm * r)) + 2
    Wd = int(round(width_cm * r)) + 2
    return _concrete(L, Wd, rng, tone, gain=gain)


def concrete_edge(length_cm, width_cm, rng, tone, gain=None, along=True, cut_cm=None):
    """Cantul din față (îngust); același format ca concrete_panel.

    Cu along=True, trecerile mistriei merg de-a lungul lui. Cu cut_cm, cantul e o fâșie din mijlocul unui
    panou lat de cut_cm, ca o bucată tăiată dintr-un front: urmele mistriei îl traversează curbe.
    """
    r = R_OAK
    L = int(round(length_cm * r)) + 2
    Wd = int(round(width_cm * r)) + 2
    cut = None if cut_cm is None else int(round(cut_cm * r)) + 2
    return _concrete(L, Wd, rng, tone, along=along, gain=gain, cut=cut)


def concrete_end(w_cm, h_cm, rng, tone, gain=None, cut_cm=None):
    """Capetele poliței, în locul materials.end_grain: (int(h_cm·10) + 2, int(w_cm·10) + 2, 3).

    cut_cm: ca la concrete_edge, capătul îngust e o fâșie dintr-un panou mai lat.
    """
    r = R_OAK
    h, w = int(h_cm * r) + 2, int(w_cm * r) + 2
    cut = None if cut_cm is None else int(round(cut_cm * r)) + 2
    return _concrete(h, w, rng, tone, gain=gain, cut=cut)


# ------------------------------------------------------------------ măsurători în fotografie

def rectify_z(X, Y, z, r):
    """Planul vertical Z = z din fotografie, privit din față: coloanele după X, rândul 0 la Y maxim."""
    O = np.array([X[0], Y[1], z])
    w, h = int(round((X[1] - X[0]) * r)), int(round((Y[1] - Y[0]) * r))
    K1 = np.array([[cam1.f, 0, cam1.pp[0]], [0, cam1.f, cam1.pp[1]], [0, 0, 1.0]])
    Hm = K1 @ cam1.R @ np.column_stack([[1, 0, 0], [0, -1, 0], O - cam1.C]) @ np.diag([1 / r, 1 / r, 1])
    return cv2.warpPerspective(PHOTO, Hm, (w, h), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)


# fronturile comodei, fără mânerul rotund, rosturi și margini: (dx0, dx1) față de marginea stângă, (y0, y1) în cm
FRONT_BOXES = {
    "ușa 1": ((4.5, 43.0), (25.0, 61.5)),
    "ușa 2": ((74.0, 111.5), (25.0, 61.5)),
    "ușa 3": ((115.5, 166.0), (25.0, 61.5)),
    "sertarul de sus": ((170.0, 237.0), (45.0, 61.5)),
    "sertarul de jos": ((170.0, 237.0), (25.0, 41.5)),
}
FRONT_Y = (22.0, 65.0)


def fronts_image(r=4):
    """Fronturile comodei rectificate, de la 2 la 240 cm de marginea stângă (fără ramă)."""
    xc = CABINET["x0"]
    return rectify_z((xc + 2.0, xc + 240.0), FRONT_Y, CABINET["z_front"], r)


def measure_fronts(r=4):
    """Mediana și media (BGR) fronturilor din microciment, plus media pe fiecare front."""
    xc = CABINET["x0"]
    pix, per = [], {}
    for name, ((a, b), (y0, y1)) in FRONT_BOXES.items():
        p = rectify_z((xc + a, xc + b), (y0, y1), CABINET["z_front"], r).reshape(-1, 3)
        per[name] = p.mean(0)
        pix.append(p)
    pix = np.concatenate(pix)
    return np.median(pix, 0), pix.mean(0), per


def wall_zone():
    """Peretele în dreptul polițelor: de la polița de jos până la marginea de sus a televizorului."""
    x0 = D["x_right"]
    return (x0, x0 + D["L"]), (D["bot_lo"], TV["y1"])


def measure_wall(r=4):
    X, Y = wall_zone()
    return rectify_z(X, Y, 0.0, r).reshape(-1, 3).mean(0)


def bgr_to_lab(bgr):
    """sRGB (BGR, 0…1) -> CIELAB, iluminant D65."""
    rgb = np.asarray(bgr, np.float64)[..., ::-1]
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    xyz = lin @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def delta_e76(lab1, lab2):
    return float(np.linalg.norm(np.asarray(lab1) - np.asarray(lab2)))


def delta_e2000(lab1, lab2):
    """CIEDE2000 (Sharma, Wu, Dalal 2005)."""
    L1, a1, b1 = (float(v) for v in lab1)
    L2, a2, b2 = (float(v) for v in lab2)
    C1, C2 = np.hypot(a1, b1), np.hypot(a2, b2)
    Cm = (C1 + C2) / 2
    G = 0.5 * (1 - np.sqrt(Cm ** 7 / (Cm ** 7 + 25.0 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360 if C1p else 0.0
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360 if C2p else 0.0
    dLp, dCp = L2 - L1, C2p - C1p
    dh = h2p - h1p
    if C1p * C2p == 0:
        dh = 0.0
    elif dh > 180:
        dh -= 360
    elif dh < -180:
        dh += 360
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dh / 2))
    Lpm, Cpm = (L1 + L2) / 2, (C1p + C2p) / 2
    if C1p * C2p == 0:
        hpm = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hpm = (h1p + h2p) / 2
    else:
        hpm = (h1p + h2p + 360) / 2 if h1p + h2p < 360 else (h1p + h2p - 360) / 2
    T = (1 - 0.17 * np.cos(np.radians(hpm - 30)) + 0.24 * np.cos(np.radians(2 * hpm))
         + 0.32 * np.cos(np.radians(3 * hpm + 6)) - 0.20 * np.cos(np.radians(4 * hpm - 63)))
    dtheta = 30 * np.exp(-(((hpm - 275) / 25) ** 2))
    Rc = 2 * np.sqrt(Cpm ** 7 / (Cpm ** 7 + 25.0 ** 7))
    Sl = 1 + 0.015 * (Lpm - 50) ** 2 / np.sqrt(20 + (Lpm - 50) ** 2)
    Sc, Sh = 1 + 0.045 * Cpm, 1 + 0.015 * Cpm * T
    Rt = -np.sin(np.radians(2 * dtheta)) * Rc
    return float(np.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh)))


# ------------------------------------------------------------------ mostrele

def _u8(img):
    return np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8)


def _rgb(bgr):
    return tuple(int(round(v)) for v in np.asarray(bgr)[::-1] * 255)


def comparison(samples, out_path, r=5):
    """Fronturile comodei din fotografie, deasupra celor două mostre și a peretelui, toate la aceeași scară."""
    from PIL import Image, ImageDraw, ImageFont
    import matplotlib
    fdir = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
    font = ImageFont.truetype(os.path.join(fdir, "DejaVuSans.ttf"), 17)
    bold = ImageFont.truetype(os.path.join(fdir, "DejaVuSans-Bold.ttf"), 19)

    fr = fronts_image(r)
    X, Y = wall_zone()
    ym = 0.5 * (Y[0] + Y[1])
    wall = rectify_z(X, (ym - 16.5, ym + 16.5), 0.0, r)
    # texturile au lungimea pe rânduri: se întorc, ca polița să stea culcată
    panels = [cv2.resize(samples[k].transpose(1, 0, 2), (int(80 * r), int(33 * r)), interpolation=cv2.INTER_AREA)
              for k in ("antracit", "gri")] + [wall]
    labels = samples["_labels"]

    pad, gap, th = 24, 28, 58
    Wc = max(fr.shape[1], sum(p.shape[1] for p in panels) + 2 * gap) + 2 * pad
    Hc = pad + th + fr.shape[0] + pad + th + max(p.shape[0] for p in panels) + pad + 30
    canvas = Image.new("RGB", (Wc, Hc), (250, 250, 248))
    dr = ImageDraw.Draw(canvas)
    y = pad
    dr.text((pad, y), "Fronturile comodei din fotografie (microciment antracit), privite din față", (20, 20, 20), bold)
    dr.text((pad, y + 26), labels["fronturi"], (90, 90, 90), font)
    y += th
    canvas.paste(Image.fromarray(_u8(fr)[..., ::-1]), (pad, y))
    y += fr.shape[0] + pad
    x = pad
    titles = [("Mostră „antracit”, 80 × 33 cm", labels["antracit"]), ("Mostră „gri”, 80 × 33 cm", labels["gri"]),
              ("Peretele, în dreptul polițelor", labels["perete"])]
    for p, (t1, t2) in zip(panels, titles):
        dr.text((x, y), t1, (20, 20, 20), bold)
        dr.text((x, y + 26), t2, (90, 90, 90), font)
        canvas.paste(Image.fromarray(_u8(p)[..., ::-1]), (x, y + th))
        x += p.shape[1] + gap
    dr.text((pad, Hc - pad - 8), "Aceeași scară peste tot (5 px/cm). Fotografia are ~2,5 px/cm, deci detaliile fine se văd "
            "doar pe mostre.", (90, 90, 90), font)
    canvas.save(out_path)


if __name__ == "__main__":
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    med, mean, per = measure_fronts()
    wall = measure_wall()
    print("fronturile comodei, RGB: mediana", _rgb(med), "· media", _rgb(mean))
    for k, v in per.items():
        print(f"   {k:16s} RGB {_rgb(v)}  L* {bgr_to_lab(v)[0]:.1f}")
    print("peretele în dreptul polițelor, RGB", _rgb(wall), "Lab", bgr_to_lab(wall).round(1))

    samples, stats = {}, {}
    for i, name in enumerate(("gri", "antracit")):
        rng = np.random.RandomState(5 + i)
        tex = concrete_panel(80, 33, rng, name)
        samples[name] = tex
        m = tex.reshape(-1, 3).mean(0)
        stats[name] = m
        # culcată și fără marginea de 1 px: exact 80 × 33 cm, la 10 px/cm
        cv2.imwrite(os.path.join(HERE, "out", f"beton_{name}.png"), _u8(tex[1:-1, 1:-1].transpose(1, 0, 2)))
        print(f"{name:9s} {tex.shape} {tex.dtype} min {tex.min():.3f} max {tex.max():.3f}  RGB {_rgb(m)}  "
              f"Lab {bgr_to_lab(m).round(1)}  abatere L {tex.mean(2).std() / tex.mean():.3f}")

    lab_f, lab_fm, lab_w = bgr_to_lab(med), bgr_to_lab(mean), bgr_to_lab(wall)
    lab_a, lab_g = bgr_to_lab(stats["antracit"]), bgr_to_lab(stats["gri"])
    de = {
        "antracit-fronturi (mediana)": (delta_e76(lab_a, lab_f), delta_e2000(lab_a, lab_f)),
        "antracit-fronturi (media)": (delta_e76(lab_a, lab_fm), delta_e2000(lab_a, lab_fm)),
        "gri-perete": (delta_e76(lab_g, lab_w), delta_e2000(lab_g, lab_w)),
    }
    for k, (e76, e00) in de.items():
        print(f"ΔE*ab {k}: {e76:.1f}  (ΔE2000 {e00:.1f})")

    samples["_labels"] = {
        "fronturi": f"mediana RGB {_rgb(med)}; lumina vine din stânga, de la ușa 1 (L* {bgr_to_lab(per['ușa 1'])[0]:.0f}) "
                    f"la sertare (L* {bgr_to_lab(per['sertarul de jos'])[0]:.0f})",
        "antracit": f"RGB {_rgb(stats['antracit'])} · ΔE*ab {de['antracit-fronturi (mediana)'][0]:.1f} față de fronturi",
        "gri": f"RGB {_rgb(stats['gri'])} · ΔE*ab {de['gri-perete'][0]:.1f} față de perete",
        "perete": f"RGB {_rgb(wall)} (media zonei polițelor)",
    }
    comparison(samples, os.path.join(HERE, "out", "beton_comparatie.png"))
    print("salvat out/beton_gri.png, out/beton_antracit.png, out/beton_comparatie.png")
