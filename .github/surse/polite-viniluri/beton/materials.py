"""Texturi și materiale luate din fotografie, ca piesele noi să aibă culorile și fibra din poză."""
import cv2
import numpy as np

from core import PHOTO, cam1

# tonurile măsurate pe comoda Veneto din fotografie (BGR, 0..1)
OAK_REF = np.array([121, 174, 222], np.float32) / 255.0              # rama și mânerul de stejar ale comodei


def _rectify_floor(X, Z, r):
    O = np.array([X[0], 0.0, Z[0]])
    w, h = int((X[1] - X[0]) * r), int((Z[1] - Z[0]) * r)
    K1 = np.array([[cam1.f, 0, cam1.pp[0]], [0, cam1.f, cam1.pp[1]], [0, 0, 1.0]])
    Hm = K1 @ cam1.R @ np.column_stack([[1, 0, 0], [0, 0, 1], O - cam1.C]) @ np.diag([1 / r, 1 / r, 1])
    return cv2.warpPerspective(PHOTO, Hm, (w, h), flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP)


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


R_OAK = 10.0  # pixeli de textură pe cm


def oak_source():
    """Fibra de stejar luată din parchetul din stânga covorului (fibra merge de-a lungul rândurilor)."""
    t = _rectify_floor((40.0, 86.0), (70.0, 116.0), R_OAK)
    t = cv2.GaussianBlur(t, (0, 0), 0.7)
    t = _highpass(t, 18)
    t = np.clip(t, 0.6, 1.5)
    return _match(t, OAK_REF, contrast=1.15)


OAK_SRC = oak_source()


def straight_grain(L, Wd, rng, density=1.6, amp=(0.03, 0.13), width=(0.9, 3.2)):
    """Linii de fibră mai închise, ușor ondulate, ca la stejarul tăiat radial."""
    n = max(int(Wd / R_OAK * density), 1)
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


def glued_panel(length_cm, width_cm, rng, lam=(4.5, 7.5), tone=0.05):
    """Panou de stejar masiv încleiat din lamele: fibra pe lungime (rânduri), lamelele pe lățime (coloane)."""
    r = R_OAK
    L = int(round(length_cm * r)) + 2
    Wd = int(round(width_cm * r)) + 2
    out = np.zeros((L, Wd, 3), np.float32)
    x = 0
    src_h, src_w = OAK_SRC.shape[:2]
    while x < Wd:
        lw = int(rng.uniform(*lam) * r)
        lw = min(lw, Wd - x)
        c = rng.randint(0, src_w - max(lw, 2))
        s = OAK_SRC[:, c:c + max(lw, 2)]
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


def end_grain(w_cm, h_cm, rng):
    r = R_OAK
    h, w = int(h_cm * r) + 2, int(w_cm * r) + 2
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cy, cx = rng.uniform(-40, -10) * r, rng.uniform(0, w_cm) * r
    rings = 0.5 + 0.5 * np.sin(np.hypot(yy - cy, xx - cx) / (0.18 * r) * 2 * np.pi)
    noise = cv2.GaussianBlur(rng.rand(h, w).astype(np.float32), (0, 0), 1.2)
    g = 0.86 + 0.07 * rings + 0.10 * (noise - 0.5)
    return np.clip(OAK_REF * 0.80 * g[..., None], 0, 1).astype(np.float32)


def sample(tex, u_px, v_px, mirror=True):
    """Eșantionare biliniară cu repetare în oglindă; u = coloana, v = rândul."""
    h, w = tex.shape[:2]
    if mirror:
        u = np.abs(np.mod(u_px, 2 * (w - 1)) - (w - 1))
        v = np.abs(np.mod(v_px, 2 * (h - 1)) - (h - 1))
    else:
        u = np.clip(u_px, 0, w - 1)
        v = np.clip(v_px, 0, h - 1)
    return cv2.remap(tex, u.astype(np.float32), v.astype(np.float32), cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_REFLECT)


# cotoarele discurilor: mai ales deschise și estompate, cu câteva culori puternice (BGR)
SPINE_COLORS = np.array([
    (232, 236, 238), (214, 222, 226), (196, 214, 226), (40, 38, 38), (30, 30, 32), (64, 62, 60),
    (58, 66, 170), (40, 120, 210), (70, 170, 228), (150, 110, 60), (120, 80, 40), (100, 130, 70),
    (60, 50, 120), (170, 160, 140), (90, 90, 160), (200, 190, 170), (120, 150, 190), (45, 80, 140),
    (180, 120, 120), (80, 100, 110), (215, 200, 150), (30, 60, 100),
], np.float32) / 255.0
SPINE_P = np.array([10, 8, 6, 10, 7, 6, 3, 3, 3, 3, 3, 2, 2, 4, 2, 4, 3, 2, 2, 3, 4, 2], np.float32)
SPINE_P /= SPINE_P.sum()
