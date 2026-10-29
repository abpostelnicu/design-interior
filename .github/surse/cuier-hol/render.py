"""Render the coat-rack proposal into the hall photo using the calibrated camera."""
import os
import sys

import cv2
import numpy as np

from camera import load_camera
from design import CUTS, D, N_SLATS, SITE, ZF, ZS, Layout

HERE = os.path.dirname(os.path.abspath(__file__))
H_CEIL = SITE["ceiling"]
OUT = 2
SS = 2
RS = OUT * SS

VARIANTS = {
    "stejar": dict(slat="oak", felt=(0.105, 0.098, 0.100)),
    "antracit": dict(slat=(0.205, 0.180, 0.180), felt=(0.085, 0.080, 0.082)),
}

# ------------------------------------------------------------------ setup
cam1 = load_camera(H_CEIL)
cam = load_camera(H_CEIL, scale=RS)
# lay the panel out against the corner, window edge, window head and baseboard top as they appear in the photo
PHOTO_LEFT, PHOTO_WIN0, PHOTO_TOP = -cam1.q["W"], cam1.q["xwl"], cam1.q["ywt"]
PHOTO_BASE_TOP = cam1.q["hb"]
PHOTO_BASE_T = 1.5  # baseboard front plane used by the camera calibration (camera.py: base_top_back)
LY = Layout(PHOTO_LEFT, PHOTO_WIN0, PHOTO_TOP, PHOTO_BASE_TOP)
X0, X1, TOP, BOT = LY.x0, LY.x1, LY.top, LY.bottom
slat_x, hooks = LY.slat_x, LY.hooks
K = np.array([[cam.f, 0, cam.pp[0]], [0, cam.f, cam.pp[1]], [0, 0, 1.0]])
photo1 = cv2.imread(os.path.join(HERE, "original.jpg")).astype(np.float32) / 255.0
W, H = photo1.shape[1] * RS, photo1.shape[0] * RS
LIGHT = np.array([-90.0, 265.0, 110.0])
rng = np.random.RandomState(7)


def proj(P, c=cam):
    return c.project(np.atleast_2d(np.asarray(P, float)), distort=False)


def face_H(O, eu, ev, wu, hv, tw, th):
    A = np.diag([wu / tw, hv / th, 1.0])
    return K @ cam.R @ np.column_stack([eu, ev, np.asarray(O, float) - cam.C]) @ A


class Canvas:
    def __init__(self, bg):
        self.img = bg.copy()
        self.touch = np.zeros(bg.shape[:2], np.float32)

    def _bbox(self, Hm, tw, th, pad=3):
        pc = cv2.perspectiveTransform(np.array([[[0, 0], [tw, 0], [tw, th], [0, th]]], np.float64), Hm)[0]
        x0 = int(max(np.floor(pc[:, 0].min()) - pad, 0))
        x1 = int(min(np.ceil(pc[:, 0].max()) + pad, W))
        y0 = int(max(np.floor(pc[:, 1].min()) - pad, 0))
        y1 = int(min(np.ceil(pc[:, 1].max()) + pad, H))
        return x0, y0, x1, y1

    def face(self, tex, O, eu, ev, wu, hv, mask=None, shade=1.0, mult=None, solid=True):
        th, tw = tex.shape[:2]
        Hm = face_H(O, eu, ev, wu, hv, tw, th)
        x0, y0, x1, y1 = self._bbox(Hm, tw, th)
        if x1 <= x0 or y1 <= y0:
            return
        T = np.array([[1, 0, -x0], [0, 1, -y0], [0, 0, 1.0]]) @ Hm
        size = (x1 - x0, y1 - y0)
        rgb = cv2.warpPerspective(tex, T, size, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        m = np.ones((th, tw), np.float32) if mask is None else mask
        a = cv2.warpPerspective(m, T, size, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        if solid:
            a = np.clip(a * 2.0, 0, 1)
        rgb = rgb * shade
        if mult is not None:
            rgb = rgb * mult[y0:y1, x0:x1, None]
        self.blend(x0, y0, rgb, a)

    def multiply(self, fac, O, eu, ev, wu, hv):
        """Multiply the canvas by a factor map defined on a planar patch."""
        th, tw = fac.shape[:2]
        Hm = face_H(O, eu, ev, wu, hv, tw, th)
        x0, y0, x1, y1 = self._bbox(Hm, tw, th)
        if x1 <= x0 or y1 <= y0:
            return
        T = np.array([[1, 0, -x0], [0, 1, -y0], [0, 0, 1.0]]) @ Hm
        f = cv2.warpPerspective(fac.astype(np.float32), T, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR,
                                borderMode=cv2.BORDER_CONSTANT, borderValue=(1.0, 1.0, 1.0, 1.0))
        if f.ndim == 2:
            f = f[..., None]
        self.img[y0:y1, x0:x1] *= f
        changed = (np.abs(f - 1.0).max(axis=2) > 0.004).astype(np.float32)
        self.touch[y0:y1, x0:x1] = np.maximum(self.touch[y0:y1, x0:x1], changed)

    def poly(self, pts, color, aa=True):
        pts = np.asarray(pts, float)
        x0 = int(max(np.floor(pts[:, 0].min()) - 2, 0))
        x1 = int(min(np.ceil(pts[:, 0].max()) + 2, W))
        y0 = int(max(np.floor(pts[:, 1].min()) - 2, 0))
        y1 = int(min(np.ceil(pts[:, 1].max()) + 2, H))
        if x1 <= x0 or y1 <= y0:
            return
        m = np.zeros((y1 - y0, x1 - x0), np.uint8)
        p = np.round((pts - [x0, y0]) * 16).astype(np.int32)
        cv2.fillPoly(m, [p], 255, lineType=cv2.LINE_AA if aa else cv2.LINE_8, shift=4)
        a = np.clip(m.astype(np.float32) / 255.0 * 1.6, 0, 1)
        rgb = np.broadcast_to(np.asarray(color, np.float32), a.shape + (3,))
        self.blend(x0, y0, rgb, a)

    def blend(self, x0, y0, rgb, a):
        h, w = a.shape
        sl = (slice(y0, y0 + h), slice(x0, x0 + w))
        self.img[sl] = self.img[sl] * (1 - a[..., None]) + rgb * a[..., None]
        self.touch[sl] = np.maximum(self.touch[sl], a)


# ------------------------------------------------------------------ textures
def floor_texture(r=6.0, X=(-100.0, -10.0), Z=(33.0, 99.0)):
    O = np.array([X[0], 0.0, Z[0]])
    w, h = int((X[1] - X[0]) * r), int((Z[1] - Z[0]) * r)
    K1 = np.array([[cam1.f, 0, cam1.pp[0]], [0, cam1.f, cam1.pp[1]], [0, 0, 1.0]])
    Hm = K1 @ cam1.R @ np.column_stack([[1, 0, 0], [0, 0, 1], O - cam1.C]) @ np.diag([1 / r, 1 / r, 1])
    t = cv2.warpPerspective(photo1, Hm, (w, h), flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP)
    low = cv2.GaussianBlur(t, (0, 0), 30)
    t = t / np.maximum(low, 1e-3) * t.reshape(-1, 3).mean(0)
    return np.clip(t, 0, 1).astype(np.float32), r


OAK, OAK_R = floor_texture()
OAK_MEAN = OAK.reshape(-1, 3).mean(0)


def oak_strip(width_cm, length_cm, rng, along="v"):
    """Oak texture with grain along v (rows) or u (cols)."""
    r = OAK_R
    sw = max(int(round(width_cm * r)), 2)
    c = rng.randint(0, OAK.shape[1] - sw)
    s = OAK[:, c:c + sw]
    reps = int(np.ceil(length_cm * r / s.shape[0])) + 1
    tile = np.concatenate([s if k % 2 == 0 else s[::-1] for k in range(reps)], axis=0)
    off = rng.randint(0, s.shape[0])
    tile = tile[off:off + int(round(length_cm * r))]
    return np.ascontiguousarray(tile if along == "v" else tile.transpose(1, 0, 2))


def warm_oak(t, sat=1.18):
    """Slightly richer oak tone for vertical veneer (floor photo looks a bit washed out)."""
    m = t.mean(axis=2, keepdims=True)
    return np.clip(m + (t - m) * sat, 0, 1).astype(np.float32)


def wall_light_map():
    """Low-frequency wall luminance of the photo, used to light vertical surfaces like the wall."""
    L = cv2.cvtColor(photo1, cv2.COLOR_BGR2GRAY)
    m = np.zeros(L.shape, np.float32)
    xa, xb = PHOTO_LEFT + 1.0, PHOTO_WIN0 - 1.0
    poly = proj([[xa, 9, 0], [xb, 9, 0], [xb, 270, 0], [xa, 270, 0]], cam1)
    cv2.fillPoly(m, [np.round(poly).astype(np.int32)], 1.0)
    num = cv2.GaussianBlur(L * m, (0, 0), 14)
    den = cv2.GaussianBlur(m, (0, 0), 14)
    Lw = num / np.maximum(den, 1e-4)
    ref = np.median(Lw[m > 0.5])
    M = np.clip(Lw / ref, 0.6, 1.15)
    M[den < 0.02] = 1.0
    return cv2.resize(M, (W, H), interpolation=cv2.INTER_CUBIC)


def lambert(n, P, amb=0.62, k=0.38):
    Ld = LIGHT - np.asarray(P, float)
    Ld /= np.linalg.norm(Ld)
    front = amb + k * max(0.0, Ld @ np.array([0, 0, 1.0]))
    return (amb + k * max(0.0, Ld @ np.asarray(n, float))) / front


# ------------------------------------------------------------------ scene parts
def draw_panel(cv, var, M, rng):
    top, bot = TOP, BOT
    hgt = top - bot
    # the panel's front overhangs the baseboard by a few mm: soft shadow on the baseboard face right below it
    # (painted first, so the panel's own bottom edge stays on top of it)
    rr = 10.0
    fy = np.arange(0, 3.0, 1 / rr)
    fac = 1 - 0.30 * np.exp(-fy / 0.7)[:, None] * np.ones((1, int((X1 - X0 + 1) * rr)))
    cv.multiply(fac.astype(np.float32), [X0 - 0.5, bot, PHOTO_BASE_T + 0.02], [1, 0, 0], [0, -1, 0],
                X1 - X0 + 1, 3.0)
    felt = np.asarray(var["felt"], np.float32)
    r = 4.0
    fw, fh = int(D["panel_w"] * r), int(hgt * r)
    fmask = np.ones((fh, fw), np.float32)
    for c in CUTS:
        u0, u1 = int((c["x0"] - X0) * r), int((c["x1"] - X0) * r)
        v0, v1 = int((top - c["y1"]) * r), int((top - c["y0"]) * r)
        fmask[v0:v1, u0:u1] = 0
    ftex = np.ones((fh, fw, 3), np.float32) * felt
    ftex *= (1 + 0.04 * rng.randn(fh, fw, 1)).astype(np.float32)
    cv.face(ftex, [X0, top, ZF], [1, 0, 0], [0, -1, 0], D["panel_w"], hgt, mask=fmask, mult=M)
    # only the end faces turned towards the camera are visible
    right_visible = cam.C[0] > X1
    x_end = X1 if right_visible else X0
    cv.face(np.ones((8, 8, 3), np.float32) * felt * 0.8, [x_end, top, 0], [0, 0, 1], [0, -1, 0], ZF, hgt, mult=M)
    side_n = [1, 0, 0] if right_visible else [-1, 0, 0]

    for c in CUTS:
        hw, hh = c["x1"] - c["x0"], c["y1"] - c["y0"]
        rr = 20.0
        fac = np.ones((int(hh * rr), int(hw * rr)), np.float32)
        yy = np.arange(fac.shape[0])[:, None] / rr
        xx = np.arange(fac.shape[1])[None, :] / rr
        fac *= 1 - 0.45 * np.exp(-yy / 1.4)
        fac *= 1 - 0.25 * np.exp(-xx / 1.0)
        fac *= 1 - 0.12 * np.exp(-(hw - xx) / 0.8)
        cv.multiply(fac, [c["x0"], c["y1"], 0.05], [1, 0, 0], [0, -1, 0], hw, hh)

    # paint far-to-near so a slat's neighbour hides the part of its side face behind it
    # the panel stands on the uncut baseboard: its top edge shows, in shadow, at the foot of the gaps
    cv.face(np.ones((4, 8, 3), np.float32) * 0.42, [X0, bot, ZF], [1, 0, 0], [0, 0, 1], D["panel_w"],
            PHOTO_BASE_T - ZF)
    order = range(N_SLATS) if right_visible else reversed(range(N_SLATS))
    for i in order:
        xa, xb = slat_x(i)
        xs = xb if right_visible else xa
        pieces = [(bot, top)]
        for c in CUTS:
            if i not in c["slats"]:
                continue
            split = []
            for (a, b) in pieces:
                if a < c["y0"] < b:
                    split += [(a, c["y0"]), (c["y1"], b)]
                else:
                    split.append((a, b))
            pieces = split
        if var["slat"] == "oak":
            tex = warm_oak(oak_strip(D["slat_w"], hgt, rng)) * 0.97 * (1 + 0.05 * rng.randn())
        else:
            base = np.asarray(var["slat"], np.float32) * (1 + 0.02 * rng.randn())
            tex = np.ones((int(hgt * 2), 6, 3), np.float32) * base
            tex *= (1 + 0.015 * rng.randn(tex.shape[0], 1, 1)).astype(np.float32)
        for (ya, yb) in pieces:
            r0 = int(round((top - yb) / hgt * tex.shape[0]))
            r1 = max(int(round((top - ya) / hgt * tex.shape[0])), r0 + 2)
            t = np.ascontiguousarray(tex[r0:r1])
            cv.face(t, [xs, yb, ZF], [0, 0, 1], [0, -1, 0], D["slat_t"], yb - ya,
                    shade=lambert(side_n, [xs, 120, ZS]) * 0.93, mult=M)
            cv.face(t, [xa, yb, ZS], [1, 0, 0], [0, -1, 0], D["slat_w"], yb - ya, mult=M)
            if yb < cam.C[1] and yb < top - 1e-6:
                cv.face(t[:4], [xa, yb, ZF], [1, 0, 0], [0, 0, 1], D["slat_w"], D["slat_t"],
                        shade=lambert([0, 1, 0], [xa, yb, ZS]) * 1.02, mult=M)

    # soft shadows on the wall: cast shadow on the side away from the light, light occlusion on the other side
    rr = 10.0
    ramp = np.exp(-np.arange(int(3 * rr)) / rr / 0.9)
    rows = np.ones((int(hgt * rr / 4), 1))
    strong, weak = (0.32, 0.14) if LIGHT[0] > 0.5 * (X0 + X1) else (0.14, 0.32)
    fac_l = 1 - strong * ramp[::-1][None, :] * rows
    fac_r = 1 - weak * ramp[None, :] * rows
    cv.multiply(fac_l.astype(np.float32), [X0 - 3.0, top, 0.0], [1, 0, 0], [0, -1, 0], 3.0, hgt)
    cv.multiply(fac_r.astype(np.float32), [X1, top, 0.0], [1, 0, 0], [0, -1, 0], 3.0, hgt)


def cylinder(cv, p0, p1, radius, base, n=28, cap=True, spec=0.22, shin=18.0):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    ax = p1 - p0
    ax /= np.linalg.norm(ax)
    t1 = np.cross(ax, [0, 1.0, 0])
    if np.linalg.norm(t1) < 1e-6:
        t1 = np.cross(ax, [1.0, 0, 0])
    t1 /= np.linalg.norm(t1)
    t2 = np.cross(ax, t1)
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
    quads = []
    for k in range(n):
        a, b = ang[k], ang[(k + 1) % n]
        na = np.cos(a) * t1 + np.sin(a) * t2
        nb = np.cos(b) * t1 + np.sin(b) * t2
        nm = (na + nb) / np.linalg.norm(na + nb)
        Q = [p0 + radius * na, p0 + radius * nb, p1 + radius * nb, p1 + radius * na]
        ctr = np.mean(Q, axis=0)
        if nm @ (cam.C - ctr) <= 0:
            continue
        quads.append((np.linalg.norm(cam.C - ctr), Q, nm, ctr))
    quads.sort(key=lambda q: -q[0])
    for _, Q, nm, ctr in quads:
        cv.poly(proj(Q), shade_metal(nm, ctr, base, spec, shin))
    if cap:
        circ = [p1 + radius * (np.cos(a) * t1 + np.sin(a) * t2) for a in ang]
        if ax @ (cam.C - p1) > 0:
            cv.poly(proj(circ), shade_metal(ax, p1, base, spec, shin))


def shade_metal(n, P, base, spec, shin):
    Ld = LIGHT - P
    Ld /= np.linalg.norm(Ld)
    V = cam.C - P
    V /= np.linalg.norm(V)
    Hh = (Ld + V) / np.linalg.norm(Ld + V)
    d = 0.45 + 0.75 * max(0.0, n @ Ld)
    s = spec * max(0.0, n @ Hh) ** shin
    return np.clip(np.asarray(base) * d + s, 0, 1)


def draw_hooks(cv):
    base = np.array([0.075, 0.072, 0.078])
    tilt = np.radians(D["hook_tilt_deg"])
    hk = hooks()
    rr = 10.0
    sx = 4.6 if LIGHT[0] < 0.5 * (X0 + X1) else 3.4
    for (hx, hy) in hk:
        sh = np.zeros((int(14 * rr), int(8 * rr)), np.float32)
        cv2.ellipse(sh, (int(sx * rr), int(4.3 * rr)), (int(1.5 * rr), int(3.6 * rr)), 0, 0, 360, 1.0, -1)
        sh = cv2.GaussianBlur(sh, (0, 0), 1.1 * rr)
        cv.multiply(1 - 0.42 * sh, [hx - 4, hy + 2.0, ZS + 0.01], [1, 0, 0], [0, -1, 0], 8, 14)
    for (hx, hy) in sorted(hk, key=lambda h: -np.linalg.norm(cam.C - [h[0], h[1], ZS])):
        p0 = np.array([hx, hy, ZS])
        rosette_end = p0 + [0, 0, 0.5]
        cylinder(cv, p0, rosette_end, D["hook_r"] + 0.7, base, cap=True)
        tip = rosette_end + D["hook_len"] * np.array([0, np.sin(tilt), np.cos(tilt)])
        cylinder(cv, rosette_end, tip, D["hook_r"], base, cap=True)


def finish(cv):
    img, touch = cv.img, cv.touch
    blurred = cv2.GaussianBlur(img, (0, 0), 0.9 * SS)
    t = cv2.GaussianBlur(touch, (0, 0), 1.0)[..., None]
    img = img * (1 - t) + blurred * t
    noise = rng.randn(H // SS, W // SS, 1).astype(np.float32) * 0.010
    out = cv2.resize(img, (W // SS, H // SS), interpolation=cv2.INTER_AREA)
    tt = cv2.resize(t[..., 0], (W // SS, H // SS), interpolation=cv2.INTER_AREA)[..., None]
    out = out + noise * tt
    return np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8)


def render(name):
    var = VARIANTS[name]
    rng.seed(7)
    bg = cv2.resize(photo1, (W, H), interpolation=cv2.INTER_LANCZOS4)
    cv = Canvas(np.clip(bg, 0, 1))
    M = wall_light_map()
    draw_panel(cv, var, M, rng)
    draw_hooks(cv)
    return finish(cv)


if __name__ == "__main__":
    names = sys.argv[1:] or list(VARIANTS)
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    for nm in names:
        im = render(nm)
        cv2.imwrite(os.path.join(HERE, "out", f"propunere_{nm}.jpg"), im, [cv2.IMWRITE_JPEG_QUALITY, 92])
        print("saved", nm, im.shape)
