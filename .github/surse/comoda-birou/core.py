"""Baza randării: camera calibrată și fețe plane texturate, desenate cu buffer de adâncime.

Fiecare față se calculează pixel cu pixel (raza din aparat intersectată cu planul feței), așa că ce acoperă ce
(comoda, biroul din fotografie) se rezolvă cu bufferul de adâncime. Pornește de la `polite-viniluri/core.py`;
în plus are umbre pe pardoseală (`multiply_plane` pe Y = 0).
"""
import os

import cv2
import numpy as np

from camera import load_camera

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = 3          # fotografia are doar 311 × 554 px: rezultatul are de 3 ori rezoluția ei
SS = 2           # supraeșantionare: se calculează la 6x și se micșorează
RS = OUT * SS

cam1 = load_camera()
cam = load_camera(scale=RS)
PHOTO = cv2.imread(os.path.join(HERE, "original.jpg")).astype(np.float32) / 255.0
W, H = PHOTO.shape[1] * RS, PHOTO.shape[0] * RS
KINV = np.linalg.inv(np.array([[cam.f, 0, cam.pp[0]], [0, cam.f, cam.pp[1]], [0, 0, 1.0]]))


def proj(P, c=cam):
    return c.project(np.atleast_2d(np.asarray(P, float)))


def _bbox(corners, pad=2):
    pc = proj(corners)
    x0 = int(max(np.floor(pc[:, 0].min()) - pad, 0))
    x1 = int(min(np.ceil(pc[:, 0].max()) + pad, W))
    y0 = int(max(np.floor(pc[:, 1].min()) - pad, 0))
    y1 = int(min(np.ceil(pc[:, 1].max()) + pad, H))
    return x0, x1, y0, y1


def _rays(x0, x1, y0, y1):
    us, vs = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
    pix = np.stack([us, vs, np.ones_like(us)], -1)
    return pix @ (cam.R.T @ KINV).T


class Canvas:
    def __init__(self, bg):
        self.img = bg.copy()
        self.z = np.full(bg.shape[:2], np.inf, np.float32)
        self.touch = np.zeros(bg.shape[:2], np.float32)

    def face(self, O, eu, ev, wu, hv, color, pad=2):
        """Dreptunghiul plan O + s*eu + t*ev (0 <= s <= wu, 0 <= t <= hv).

        color(s, t, X, yy, xx) întoarce culorile (h, w, 3); s, t în cm, yy/xx indicii pixelilor. Scrie doar unde
        fața e cea mai apropiată suprafață de până acum. Cu color=None, fața doar ascunde ce e în spatele ei
        (biroul din fotografie), fără să schimbe pixelii. Fețele întoarse cu spatele la aparat nu se desenează.
        """
        O, eu, ev = (np.asarray(v, float) for v in (O, eu, ev))
        n = np.cross(eu, ev)
        ctr = O + 0.5 * wu * eu + 0.5 * hv * ev
        if abs(n @ (cam.C - ctr)) <= 1e-9:
            return
        corners = np.array([O, O + wu * eu, O + wu * eu + hv * ev, O + hv * ev])
        x0, x1, y0, y1 = _bbox(corners, pad)
        if x1 <= x0 or y1 <= y0:
            return
        d = _rays(x0, x1, y0, y1)
        denom = d @ n
        ok = np.abs(denom) > 1e-12
        tt = np.where(ok, ((O - cam.C) @ n) / np.where(ok, denom, 1.0), np.inf)
        X = cam.C + d * tt[..., None]
        rel = X - O
        s = rel @ eu
        t = rel @ ev
        inside = ok & (tt > 0) & (s >= 0) & (s <= wu) & (t >= 0) & (t <= hv)
        if not inside.any():
            return
        depth = (X - cam.C) @ cam.R[2]
        zb = self.z[y0:y1, x0:x1]
        win = inside & (depth < zb - 1e-3)
        if not win.any():
            return
        zb[win] = depth[win]
        if color is None:
            return
        yy, xx = np.mgrid[y0:y1, x0:x1]
        rgb = color(np.clip(s, 0, wu), np.clip(t, 0, hv), X, yy, xx)
        sl = (slice(y0, y1), slice(x0, x1))
        self.img[sl][win] = rgb[win]
        self.touch[sl][win] = 1.0

    def box(self, x0, x1, y0, y1, z0, z1, color_fn):
        """Paralelipiped aliniat cu axele; color_fn(normala) dă funcția de culoare a fiecărei fețe (sau None)."""
        faces = [
            ([x0, y0, z1], [1, 0, 0], [0, 1, 0], x1 - x0, y1 - y0, (0, 0, 1)),
            ([x0, y0, z0], [0, 1, 0], [1, 0, 0], y1 - y0, x1 - x0, (0, 0, -1)),
            ([x0, y1, z0], [0, 0, 1], [1, 0, 0], z1 - z0, x1 - x0, (0, 1, 0)),
            ([x0, y0, z0], [1, 0, 0], [0, 0, 1], x1 - x0, z1 - z0, (0, -1, 0)),
            ([x1, y0, z0], [0, 1, 0], [0, 0, 1], y1 - y0, z1 - z0, (1, 0, 0)),
            ([x0, y0, z0], [0, 0, 1], [0, 1, 0], z1 - z0, y1 - y0, (-1, 0, 0)),
        ]
        for O, eu, ev, wu, hv, nrm in faces:
            nn = np.array(nrm, float)
            ctr = np.array(O, float) + 0.5 * wu * np.array(eu, float) + 0.5 * hv * np.array(ev, float)
            if nn @ (cam.C - ctr) <= 0:
                continue
            self.face(O, eu, ev, wu, hv, color_fn(nrm))

    def multiply_plane(self, fac_fn, axis, value, a0, a1, b0, b1):
        """Înmulțește fundalul (umbre) pe planul axis = value, doar unde nu e acoperit de fețele noi.

        axis "Z": peretele (a = X, b = Y); axis "Y": pardoseala (a = X, b = Z). fac_fn(a, b) dă factorul.
        """
        if axis == "Z":
            corners = np.array([[a0, b0, value], [a1, b0, value], [a1, b1, value], [a0, b1, value]])
        else:
            corners = np.array([[a0, value, b0], [a1, value, b0], [a1, value, b1], [a0, value, b1]])
        x0, x1, y0, y1 = _bbox(corners)
        if x1 <= x0 or y1 <= y0:
            return
        d = _rays(x0, x1, y0, y1)
        i = "XYZ".index(axis)
        tt = (value - cam.C[i]) / d[..., i]
        X = cam.C + d * tt[..., None]
        if axis == "Z":
            a, b = X[..., 0], X[..., 1]
        else:
            a, b = X[..., 0], X[..., 2]
        inside = (tt > 0) & (a >= a0) & (a <= a1) & (b >= b0) & (b <= b1)
        f = np.where(inside, fac_fn(a, b), 1.0)
        sl = (slice(y0, y1), slice(x0, x1))
        free = ~np.isfinite(self.z[sl])
        f = np.where(free, f, 1.0).astype(np.float32)
        self.img[sl] *= f[..., None]
        self.touch[sl] = np.maximum(self.touch[sl], (np.abs(f - 1) > 0.004).astype(np.float32))


def wall_light_map(mask_px, x_max, sigma=8):
    """Lumina peretelui din fotografie, netezită și raportată la mediana ei, la rezoluția de lucru.

    mask_px: poligoane în pixelii fotografiei originale, scoase din calcul (biroul, fereastra, pata de soare).
    Întoarce harta (la rezoluția de lucru), mediana luminii peretelui (gri, 0..1) și culoarea lui (BGR).
    """
    L = cv2.cvtColor(PHOTO, cv2.COLOR_BGR2GRAY)
    m = np.zeros(L.shape, np.float32)
    Hc = 250.0
    cv2.fillPoly(m, [np.round(proj([[0.5, 10, 0], [x_max, 10, 0], [x_max, Hc - 1, 0], [0.5, Hc - 1, 0]],
                                   cam1)).astype(np.int32)], 1.0)
    for poly in mask_px:
        cv2.fillPoly(m, [np.round(np.asarray(poly, float)).astype(np.int32)], 0.0)
    num = cv2.GaussianBlur(L * m, (0, 0), sigma)
    den = cv2.GaussianBlur(m, (0, 0), sigma)
    Lw = num / np.maximum(den, 1e-4)
    ref = float(np.median(Lw[m > 0.5]))
    M = np.clip(Lw / ref, 0.6, 1.5)
    M[den < 0.02] = 1.0
    wall_bgr = np.array([np.median(PHOTO[..., k][m > 0.5]) for k in range(3)], np.float32)
    return cv2.resize(M, (W, H), interpolation=cv2.INTER_CUBIC), ref, wall_bgr
