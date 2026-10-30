"""Baza randării: camera calibrată și fețe plane texturate, desenate cu buffer de adâncime.

Fiecare față se calculează pixel cu pixel (raza din aparat intersectată cu planul feței), așa că ce acoperă
ce (lemnul, discurile, spatele) se rezolvă cu bufferul de adâncime, nu cu o ordine de desenare făcută de mână.
Fotografia `original.jpg` e deja curățată de `curata_foto.py` (televizor stins, fără persoana din ușă).
"""
import os

import cv2
import numpy as np

from camera import load_camera

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = 2          # rezultatul are de 2 ori rezoluția fotografiei de 1024 × 768
SS = 2           # supraeșantionare: se calculează la 4x și se micșorează
RS = OUT * SS

cam1 = load_camera()
cam = load_camera(scale=RS)
PHOTO = cv2.imread(os.path.join(HERE, "original.jpg")).astype(np.float32) / 255.0
W, H = PHOTO.shape[1] * RS, PHOTO.shape[0] * RS
KINV = np.linalg.inv(np.array([[cam.f, 0, cam.pp[0]], [0, cam.f, cam.pp[1]], [0, 0, 1.0]]))


def proj(P, c=cam):
    return c.project(np.atleast_2d(np.asarray(P, float)), distort=False)


class Canvas:
    def __init__(self, bg):
        self.img = bg.copy()
        self.z = np.full(bg.shape[:2], np.inf, np.float32)
        self.touch = np.zeros(bg.shape[:2], np.float32)

    def face(self, O, eu, ev, wu, hv, color, pad=2):
        """Dreptunghiul plan O + s*eu + t*ev (0 <= s <= wu, 0 <= t <= hv).

        color(s, t, X, yy, xx) întoarce culorile (h, w, 3) pentru pixelii feței; s, t în cm, yy/xx indicii
        pixelilor. Scrie doar unde fața e cea mai apropiată suprafață de până acum. Cu color=None, fața doar
        ascunde ce e în spatele ei (de exemplu boxele din fotografie), fără să schimbe pixelii.
        """
        O, eu, ev = (np.asarray(v, float) for v in (O, eu, ev))
        n = np.cross(eu, ev)
        ctr = O + 0.5 * wu * eu + 0.5 * hv * ev
        if n @ (cam.C - ctr) < 0:
            n = -n
        if n @ (cam.C - ctr) <= 1e-9:
            return
        corners = np.array([O, O + wu * eu, O + wu * eu + hv * ev, O + hv * ev])
        pc = proj(corners)
        x0 = int(max(np.floor(pc[:, 0].min()) - pad, 0))
        x1 = int(min(np.ceil(pc[:, 0].max()) + pad, W))
        y0 = int(max(np.floor(pc[:, 1].min()) - pad, 0))
        y1 = int(min(np.ceil(pc[:, 1].max()) + pad, H))
        if x1 <= x0 or y1 <= y0:
            return
        us, vs = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        pix = np.stack([us, vs, np.ones_like(us)], -1)
        d = pix @ (cam.R.T @ KINV).T
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

    def multiply_wall(self, fac_fn, X0, X1, Y0, Y1, z=0.0):
        """Înmulțește fundalul (umbre pe perete) doar unde peretele se vede și nu e acoperit de fețele noi."""
        O = np.array([X0, Y0, z])
        corners = np.array([O, [X1, Y0, z], [X1, Y1, z], [X0, Y1, z]])
        pc = proj(corners)
        x0 = int(max(np.floor(pc[:, 0].min()) - 2, 0))
        x1 = int(min(np.ceil(pc[:, 0].max()) + 2, W))
        y0 = int(max(np.floor(pc[:, 1].min()) - 2, 0))
        y1 = int(min(np.ceil(pc[:, 1].max()) + 2, H))
        if x1 <= x0 or y1 <= y0:
            return
        us, vs = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        pix = np.stack([us, vs, np.ones_like(us)], -1)
        d = pix @ (cam.R.T @ KINV).T
        tt = (z - cam.C[2]) / d[..., 2]
        X = cam.C + d * tt[..., None]
        f = fac_fn(X[..., 0], X[..., 1])
        sl = (slice(y0, y1), slice(x0, x1))
        free = ~np.isfinite(self.z[sl])
        f = np.where(free, f, 1.0).astype(np.float32)
        self.img[sl] *= f[..., None]
        self.touch[sl] = np.maximum(self.touch[sl], (np.abs(f - 1) > 0.004).astype(np.float32))


def wall_light_map(mask_polys, sigma=10):
    """Lumina peretelui din fotografie, netezită și raportată la mediana ei, la rezoluția de lucru."""
    L = cv2.cvtColor(PHOTO, cv2.COLOR_BGR2GRAY)
    m = np.zeros(L.shape, np.float32)
    Hc = cam1.q["H"]
    cv2.fillPoly(m, [np.round(proj([[0.5, 9, 0], [418.5, 9, 0], [418.5, Hc - 0.5, 0], [0.5, Hc - 0.5, 0]],
                                   cam1)).astype(np.int32)], 1.0)
    for poly in mask_polys:
        cv2.fillPoly(m, [np.round(proj(poly, cam1)).astype(np.int32)], 0.0)
    m[:, 985:] = 0
    num = cv2.GaussianBlur(L * m, (0, 0), sigma)
    den = cv2.GaussianBlur(m, (0, 0), sigma)
    Lw = num / np.maximum(den, 1e-4)
    ref = np.median(Lw[m > 0.5])
    M = np.clip(Lw / ref, 0.55, 1.6)
    M[den < 0.02] = 1.0
    return cv2.resize(M, (W, H), interpolation=cv2.INTER_CUBIC), ref
