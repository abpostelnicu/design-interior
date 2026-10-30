"""Materialele pieselor noi: stejar luat din fotografie, microciment procedural și măsurători de culoare (Lab, ΔE).

Texturile sunt np.ndarray float32 (rânduri, coloane, 3), canale BGR, valori 0…1, la R = 10 px pe cm; rândurile
merg de-a lungul lungimii piesei, coloanele pe lățime. Le citești în funcția de culoare a unei fețe cu `sample`.

- Stejar: `oak_source(photo, cam, X, Z)` ia fibra din parchetul din fotografie (o zonă de pardoseală fără covor
  sau mobilă), iar `glued_panel` face din ea un panou de stejar masiv încleiat din lamele; `end_grain` dă
  capetele. Fără parchet în poză: `oak_procedural`.
- Microciment (beton decorativ): `concrete_panel`, `concrete_edge`, `concrete_end`, în tonurile din TONES sau
  într-o culoare măsurată în fotografie.
- Culoarea: `rectify_z` și `rectify_floor` îndreaptă un plan din fotografie, `masoara` dă mediana și media unei
  zone, iar `bgr_to_lab` și `delta_e2000` spun cât de departe e o mostră de ce e deja în cameră
  (ΔE00 sub ~2 abia se vede; peste ~5 se vede clar).

Rectificările folosesc modelul fără distorsiune (k1 = 0), ca randarea.
Preluat din `.github/surse/polite-viniluri/materials.py` și din `.github/surse/polite-viniluri/beton/beton.py`;
aleatorul vine doar din parametrul rng (np.random.RandomState sau Generator).
"""
import cv2
import numpy as np

R = 10.0                 # pixeli de textură pe cm
R_OAK = R                # numele din proiectele existente

# tonul stejarului natural, măsurat pe rama comodei Veneto din fotografia proiectului „Polițe viniluri” (BGR)
OAK_REF = np.array([121, 174, 222], np.float32) / 255.0


# ------------------------------------------------------------------ planuri din fotografie

def rectify_floor(photo, cam, X, Z, r=R):
    """Pardoseala (Y = 0) din fotografie, văzută de sus: coloanele după X, rândurile după Z, r px/cm."""
    O = np.array([X[0], 0.0, Z[0]])
    w, h = int((X[1] - X[0]) * r), int((Z[1] - Z[0]) * r)
    Hm = cam.K @ cam.R @ np.column_stack([[1, 0, 0], [0, 0, 1], O - cam.C]) @ np.diag([1 / r, 1 / r, 1])
    return cv2.warpPerspective(photo, Hm, (w, h), flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP)


def rectify_z(photo, cam, X, Y, z, r=R):
    """Planul vertical Z = z din fotografie, privit din față: coloanele după X, rândul 0 la Y maxim."""
    O = np.array([X[0], Y[1], z])
    w, h = int(round((X[1] - X[0]) * r)), int(round((Y[1] - Y[0]) * r))
    Hm = cam.K @ cam.R @ np.column_stack([[1, 0, 0], [0, -1, 0], O - cam.C]) @ np.diag([1 / r, 1 / r, 1])
    return cv2.warpPerspective(photo, Hm, (w, h), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)


def masoara(photo, cam, X, Y, z=0.0, r=4):
    """Culoarea unei zone dreptunghiulare de pe planul Z = z (cm): (mediana, media), BGR 0…1.

    Alegi zona fără prize, rame, umbre puternice sau reflexii; mediana e mai sigură decât media.
    """
    p = rectify_z(photo, cam, X, Y, z, r).reshape(-1, 3).astype(np.float64)   # în float32, media pierde ~0,1/255
    return np.median(p, 0), p.mean(0)


# ------------------------------------------------------------------ stejar

def _highpass(t, sigma):
    low = cv2.GaussianBlur(t, (0, 0), sigma)
    return t / np.maximum(low, 1e-3)


def _match(t, ref_mean, contrast=1.0):
    """Hartă de detaliu cu media 1 -> culoare cu media de referință; contrast scalează detaliul."""
    g = t.mean(axis=2, keepdims=True)
    g = 1 + (g / g.mean() - 1) * contrast
    chroma = t / np.maximum(t.mean(axis=2, keepdims=True), 1e-3)
    chroma = 1 + (chroma - 1) * 0.35
    return np.clip(ref_mean * g * chroma, 0, 1).astype(np.float32)


def oak_source(photo, cam, X, Z, ref=OAK_REF, r=R):
    """Fibra de stejar din parchetul fotografiei, pe zona X × Z (cm) a pardoselii, în tonul ref.

    Fibra merge de-a lungul rândurilor parchetului. În „Polițe viniluri”: X = (40, 86), Z = (70, 116), stânga
    covorului. Zona trebuie să fie doar parchet: fără covor, mobilă, umbre de picioare sau lumină directă.
    """
    t = rectify_floor(photo, cam, X, Z, r)
    t = cv2.GaussianBlur(t, (0, 0), 0.7)
    t = _highpass(t, 18)
    t = np.clip(t, 0.6, 1.5)
    return _match(t, np.asarray(ref, np.float32), contrast=1.15)


def oak_procedural(rng, length_cm=46.0, width_cm=46.0, ref=OAK_REF):
    """Sursă de fibră fără fotografie: zgomot alungit pe rânduri, în tonul ref (când în poză nu e parchet)."""
    h, w = int(length_cm * R), int(width_cm * R)
    fine = cv2.resize(_noise(rng, h // 10 + 2, w, 1.0), (w, h), interpolation=cv2.INTER_CUBIC)
    mid = cv2.resize(_noise(rng, h // 20 + 2, w, 4.0), (w, h), interpolation=cv2.INTER_CUBIC)
    g = np.clip(1 + 0.07 * fine + 0.05 * mid + 0.012 * _noise(rng, h, w, 0.7), 0.6, 1.5)
    return _match(np.repeat(g[..., None], 3, 2), np.asarray(ref, np.float32))


def straight_grain(L, Wd, rng, density=1.6, amp=(0.03, 0.13), width=(0.9, 3.2)):
    """Linii de fibră mai închise, ușor ondulate, ca la stejarul tăiat radial."""
    n = max(int(Wd / R * density), 1)
    cols = np.arange(Wd, dtype=np.float32)
    prof = np.ones(Wd, np.float32)
    for _ in range(n):
        c = rng.uniform(0, Wd)
        w = rng.uniform(*width)
        a = rng.uniform(*amp)
        prof -= a * np.exp(-((cols - c) / w) ** 2)
    prof = np.clip(prof, 0.75, 1.0)
    prof = prof / prof.mean()
    rows = np.arange(L, dtype=np.float32)[:, None]
    wave = 1.4 * np.sin(rows / rng.uniform(250, 700) * 2 * np.pi + rng.uniform(0, 6.3))
    u = np.clip(cols[None, :] + wave, 0, Wd - 1).astype(np.float32)
    g = cv2.remap(prof[None, :].repeat(L, 0), u, np.repeat(rows, Wd, 1).astype(np.float32), cv2.INTER_LINEAR)
    low = 1 + 0.035 * np.sin(rows / rng.uniform(400, 900) * 2 * np.pi + rng.uniform(0, 6.3))
    return (g * low)[..., None].astype(np.float32)


def glued_panel(src, length_cm, width_cm, rng, lam=(4.5, 7.5), tone=0.05):
    """Panou de stejar masiv încleiat din lamele late de lam cm: fibra pe lungime (rânduri), lamelele pe lățime.

    src: sursa de fibră (oak_source sau oak_procedural); tone: cât diferă tonul de la o lamelă la alta.
    """
    L = int(round(length_cm * R)) + 2
    Wd = int(round(width_cm * R)) + 2
    out = np.zeros((L, Wd, 3), np.float32)
    x = 0
    src_h, src_w = src.shape[:2]
    while x < Wd:
        lw = int(rng.uniform(*lam) * R)
        lw = min(lw, Wd - x)
        c = rng.randint(0, src_w - max(lw, 2))
        s = src[:, c:c + max(lw, 2)]
        if rng.rand() < 0.5:
            s = s[:, ::-1]
        reps = int(np.ceil(L / src_h)) + 1
        tile = np.concatenate([s if k % 2 == 0 else s[::-1] for k in range(reps)], axis=0)
        off = rng.randint(0, src_h)
        piece = tile[off:off + L, :lw] * straight_grain(L, lw, rng)
        piece = piece * (1 + tone * rng.randn())
        out[:, x:x + lw] = piece
        if x > 0:
            out[:, x:x + 1] *= 0.93
        x += lw
    return np.clip(out, 0, 1)


def end_grain(w_cm, h_cm, rng, ref=OAK_REF):
    """Capătul unei piese de stejar: inele de creștere, mai închis decât fața."""
    h, w = int(h_cm * R) + 2, int(w_cm * R) + 2
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cy, cx = rng.uniform(-40, -10) * R, rng.uniform(0, w_cm) * R
    rings = 0.5 + 0.5 * np.sin(np.hypot(yy - cy, xx - cx) / (0.18 * R) * 2 * np.pi)
    noise = cv2.GaussianBlur(rng.rand(h, w).astype(np.float32), (0, 0), 1.2)
    g = 0.86 + 0.07 * rings + 0.10 * (noise - 0.5)
    return np.clip(np.asarray(ref, np.float32) * 0.80 * g[..., None], 0, 1).astype(np.float32)


def sample(tex, u_px, v_px, mirror=True):
    """Eșantionare biliniară cu repetare în oglindă; u = coloana, v = rândul (px de textură).

    În interiorul texturii, sample(tex, u, v) = tex[v, u]; dincolo de margini, textura se repetă în oglindă.
    Varianta din `.github/surse/polite-viniluri/materials.py` întorcea textura în oglindă și în interior (u = 0 lua
    ultima coloană); la lemn și beton nu se vedea, dar un text sau o imagine pusă pe o față ar fi ieșit întoarsă.
    """
    h, w = tex.shape[:2]
    if mirror:
        u = (w - 1) - np.abs(np.mod(u_px, 2 * (w - 1)) - (w - 1))
        v = (h - 1) - np.abs(np.mod(v_px, 2 * (h - 1)) - (h - 1))
    else:
        u = np.clip(u_px, 0, w - 1)
        v = np.clip(v_px, 0, h - 1)
    return cv2.remap(tex, u.astype(np.float32), v.astype(np.float32), cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_REFLECT)


# ------------------------------------------------------------------ microciment (beton decorativ)

# BGR, 0…1: „antracit” = mediana fronturilor din microciment ale comodei (RGB 73, 74, 73); „gri” = gri natural de
# beton, deschis și ușor cald (RGB 170, 166, 158), ales mai deschis și mai neutru decât peretele bej-gri
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
            Rr = rng.uniform(60, 160) * r
            bw = rng.uniform(5, 9) * r
            phi = (0.0 if rng.uniform() < 0.5 else np.pi) + rng.uniform(-0.15, 0.15)
        else:
            Rr = rng.uniform(16, 55) * r
            bw = rng.uniform(6, 12) * r
            phi = rng.uniform(0, 2 * np.pi)
        px, py = rng.uniform(-0.1 * w, 1.1 * w), rng.uniform(-0.1 * h, 1.1 * h)
        cx, cy = px + Rr * np.cos(phi), py + Rr * np.sin(phi)
        half = 0.5 * rng.uniform(18, 45) * r               # jumătate din lungimea trecerii, pe arc
        a0 = phi + np.pi
        sharp = 1.0 if rng.uniform() < 0.5 else -1.0       # partea muchiei nete
        delta = rng.standard_normal()
        alpha = rng.uniform(0.45, 0.9)
        has_vein = rng.uniform() < vein_p
        vein_sign = 1.0 if rng.uniform() < 0.9 else -0.6    # rar, câte o linie mai închisă
        soft = rng.uniform(1.5, 3.5) * r

        # doar în dreptunghiul care cuprinde arcul
        ang = a0 + np.linspace(-half / Rr, half / Rr, 24)
        ex, ey = cx + Rr * np.cos(ang), cy + Rr * np.sin(ang)
        m = bw + 2 * r
        x0, x1 = int(max(np.floor(ex.min() - m), 0)), int(min(np.ceil(ex.max() + m), w))
        y0, y1 = int(max(np.floor(ey.min() - m), 0)), int(min(np.ceil(ey.max() + m), h))
        if x1 <= x0 or y1 <= y0:
            continue
        sl = (slice(y0, y1), slice(x0, x1))
        X, Y = xx[sl] - cx, yy[sl] - cy
        d = (np.hypot(X, Y) - Rr + wob[sl]) * sharp        # d = +bw/2 la muchia netă
        along_arc = np.angle(np.exp(1j * (np.arctan2(Y, X) - a0))) * Rr
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
    r = R
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
    """Panou de microciment, ca glued_panel: rândurile pe lungime, coloanele pe lățime.

    tone: „gri”, „antracit” sau o culoare BGR 0…1 (de exemplu mediana din `masoara`). Întoarce float32
    (round(length_cm·10) + 2, round(width_cm·10) + 2, 3), BGR, 0…1, cu media exact pe ton.
    gain: multiplicatori pentru componentele din STYLE (cloud, trowel, vein, vein_w, vein_p, pass_area…), pentru
    randările mici, unde estomparea stinge urmele fine; media tonului rămâne aceeași.
    Pentru randare, fă panoul cu ~20 cm mai lung decât piesa, dacă deplasezi eșantionarea: altfel `sample`
    repetă textura în oglindă, iar la beton simetria se vede.
    """
    L = int(round(length_cm * R)) + 2
    Wd = int(round(width_cm * R)) + 2
    return _concrete(L, Wd, rng, tone, gain=gain)


def concrete_edge(length_cm, width_cm, rng, tone, gain=None, along=True, cut_cm=None):
    """Cantul din față (îngust); același format ca concrete_panel.

    Cu along=True, trecerile mistriei merg de-a lungul lui. Cu cut_cm, cantul e o fâșie din mijlocul unui
    panou lat de cut_cm, ca o bucată tăiată dintr-un front: urmele mistriei îl traversează curbe.
    """
    L = int(round(length_cm * R)) + 2
    Wd = int(round(width_cm * R)) + 2
    cut = None if cut_cm is None else int(round(cut_cm * R)) + 2
    return _concrete(L, Wd, rng, tone, along=along, gain=gain, cut=cut)


def concrete_end(w_cm, h_cm, rng, tone, gain=None, cut_cm=None):
    """Capetele piesei, în locul lui end_grain: (int(h_cm·10) + 2, int(w_cm·10) + 2, 3).

    cut_cm: ca la concrete_edge, capătul îngust e o fâșie dintr-un panou mai lat.
    """
    h, w = int(h_cm * R) + 2, int(w_cm * R) + 2
    cut = None if cut_cm is None else int(round(cut_cm * R)) + 2
    return _concrete(h, w, rng, tone, gain=gain, cut=cut)


# ------------------------------------------------------------------ culoarea

def din_rgb(r, g, b):
    """Culoarea RGB 0…255 (ca în fișele producătorilor) ca BGR 0…1, formatul texturilor."""
    return np.array([b, g, r], np.float32) / 255.0


def rgb255(bgr):
    """BGR 0…1 -> (R, G, B) 0…255, pentru texte și README."""
    return tuple(int(round(v)) for v in np.asarray(bgr)[::-1] * 255)


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


def diferenta(bgr1, bgr2):
    """ΔE2000 între două culori BGR 0…1."""
    return delta_e2000(bgr_to_lab(bgr1), bgr_to_lab(bgr2))
