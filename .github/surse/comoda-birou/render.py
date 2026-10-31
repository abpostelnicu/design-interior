"""Randează comoda BoConcept Element (3 sertare, 115 × 46,5 × 91 cm) în fotografia biroului, în stânga lui.

A: furnir de stejar natur. B: furnir de stejar închis. Picioarele duble sunt negre în ambele variante, ca ale biroului.
Comoda stă la 8 cm de birou, cu spatele lipit de perete, deasupra plintei; partea ei din stânga iese din cadru.
"""
import os
import sys

import cv2
import numpy as np

from core import Canvas, H, HERE, PHOTO, SS, W, cam, cam1, proj, wall_light_map
from design import DESK, EL, SITE, Layout
from materials import ALBEDO, R_TEX, STEEL, reeding, sample, veneer

VARIANTS = {
    "A": dict(oak="stejar", file="propunere_A_stejar.jpg"),
    "B": dict(oak="stejar_inchis", file="varianta_B_stejar_inchis.jpg"),
}
WALL_ALBEDO = 0.88
# lumina pe fețe, față de peretele din spate (care privește spre cameră, ca fața comodei)
FACE_LIGHT = {(0, 0, 1): 1.0, (0, 1, 0): 1.22, (1, 0, 0): 0.92, (-1, 0, 0): 0.78, (0, -1, 0): 0.4, (0, 0, -1): 0.5}


def tone(x):
    """Compresie blândă a luminilor."""
    k = 0.84
    return np.where(x < k, x, k + (1 - k) * (1 - np.exp(-np.maximum(x - k, 0) / (1 - k))))


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def light_map():
    """Lumina peretelui din fotografie, fără birou, fereastră și pata de soare."""
    d = DESK
    corners = np.array([[x, y, z] for x in (d["x0"] - 2, d["x0"] + d["w"] + 2) for y in (0, d["h"] + 25)
                        for z in (-1, d["z0"] + d["d"] + 2)], float)
    pc = proj(corners, cam1).astype(np.float32)
    desk_hull = cv2.convexHull(pc).reshape(-1, 2)
    window = proj([[SITE["win_x"] - 3, 30, 0], [SITE["wall_len"], 30, 0], [SITE["wall_len"], 249, 0],
                   [SITE["win_x"] - 3, 249, 0]], cam1)
    sun = [(138, 76), (218, 76), (258, 248), (226, 266)]                   # dâra de soare de pe perete
    plugs = [(205, 219), (222, 219), (222, 230), (205, 230)]                # întrerupătorul de deasupra biroului
    return wall_light_map([desk_hull, window, sun, plugs], SITE["win_x"] + 5)


class Scene:
    def __init__(self, var, light, seed=5):
        self.var = var
        self.M, ref, wall_bgr = light
        self.E0 = ref / WALL_ALBEDO                                 # lumina pe un perete alb, în unitățile pozei
        self.wb = (wall_bgr / wall_bgr.mean()).astype(np.float32)   # balansul de alb al fotografiei
        self.alb = ALBEDO[var["oak"]] * self.wb
        self.L = Layout()
        rng = np.random.RandomState(seed)                           # aceleași texturi în A și B
        L = self.L
        self.tex_front = veneer(EL["w"] + 2, EL["h"] + 2, rng, vertical=True)
        self.tex_top = veneer(EL["w"] + 2, EL["d"] + 2, rng, vertical=False)
        self.contrast = 1.0 if var["oak"] == "stejar" else 0.7

    def _detail(self, tex, s, t):
        d = sample(tex, s * R_TEX, t * R_TEX)
        return (1 + (d - 1) * self.contrast)[..., None]

    # ---------------------------------------------------------------- comoda
    def front_color(self):
        L, fr, g = self.L, EL["frame"], EL["gap"]
        wu, hv = EL["w"], EL["h"] - EL["leg_h"]
        drawers = [(a - EL["leg_h"], b - EL["leg_h"]) for a, b in L.drawers]
        reveal = EL["gap"]                                         # rostul dintre ramă și fronturi, ca între sertare
        M, E0, alb = self.M, self.E0, self.alb

        def color(s, t, X, yy, xx):
            det = self._detail(self.tex_front, s, t)
            inner = (s > fr) & (s < wu - fr) & (t > fr) & (t < hv - fr)
            on_front = np.zeros_like(s, bool)
            for a, b in drawers:
                on_front |= (t >= a) & (t <= b)
            on_front &= inner & (s >= fr + reveal) & (s <= wu - fr - reveal)
            f = np.ones_like(s)
            f = np.where(on_front, reeding(s - fr, EL["reed"]), f)
            gap = inner & ~on_front
            f = np.where(gap, 0.24, f)
            # muchia de sus prinde puțin mai multă lumină; jos, spre pardoseală, ocluzie ușoară
            f = f * (1 + 0.06 * np.exp(-(hv - t) / 0.25)) * (0.92 + 0.08 * smooth(t / 25.0))
            c = alb[None, None, :] * det * (E0 * FACE_LIGHT[(0, 0, 1)] * M[yy, xx] * f)[..., None]
            return tone(c)
        return color

    def top_color(self):
        M, E0, alb = self.M, self.E0, self.alb
        z0 = self.L.z0
        dd = EL["d"]

        def color(s, t, X, yy, xx):
            det = self._detail(self.tex_top, s, t)
            ao = 1 - 0.10 * np.exp(-(X[..., 2] - z0) / 3.0)
            edge = 1 + 0.07 * np.exp(-(dd - t) / 0.3)
            f = E0 * FACE_LIGHT[(0, 1, 0)] * M[yy, xx] * ao * edge
            return tone(alb[None, None, :] * det * f[..., None])
        return color

    def steel(self, n):
        M, E0 = self.M, self.E0
        col = STEEL * self.wb
        sh = FACE_LIGHT.get(tuple(n), 0.8)

        def color(s, t, X, yy, xx):
            f = E0 * sh * M[yy, xx] * (0.85 + 0.15 * smooth(X[..., 1] / EL["leg_h"]))
            return tone(col[None, None, :] * f[..., None] + 0.012)
        return color

    def draw_chest(self, cv):
        L = self.L
        y0, y1 = EL["leg_h"], EL["h"]
        cv.face([L.x0, y0, L.z1], [1, 0, 0], [0, 1, 0], EL["w"], y1 - y0, self.front_color())
        cv.face([L.x0, y1, L.z0], [1, 0, 0], [0, 0, 1], EL["w"], EL["d"], self.top_color())
        # laturile și dedesubtul se desenează doar dacă se văd (fețele întoarse sunt sărite)
        side = lambda n: (lambda s, t, X, yy, xx: tone(self.alb[None, None, :] * (
            self.E0 * FACE_LIGHT[n] * self.M[yy, xx])[..., None]))
        cv.face([L.x1, y0, L.z0], [0, 1, 0], [0, 0, 1], y1 - y0, EL["d"], side((1, 0, 0)))
        cv.face([L.x0, y0, L.z0], [0, 0, 1], [0, 1, 0], EL["d"], y1 - y0, side((-1, 0, 0)))
        r = EL["leg_rod"] / 2
        for (x, z) in L.legs:
            cv.box(x - r, x + r, 0, y0, z - r, z + r, self.steel)

    # ---------------------------------------------------------------- biroul din fotografie
    def occluders(self, cv):
        """Biroul stă în spatele comodei; îl desenăm doar în bufferul de adâncime, ca să rămână neatins."""
        d = DESK
        x0, x1 = d["x0"], d["x0"] + d["w"]
        none = lambda n: None
        cv.box(x0, x1, d["h"] - d["top_t"], d["h"], d["z0"], d["z0"] + d["d"], none)
        for xc in (cam1.q["lx1"], cam1.q["lx2"]):
            cv.box(xc - 3, xc + 3, 0, d["h"] - d["top_t"], d["z0"] + 30, d["z0"] + 40, none)

    # ---------------------------------------------------------------- umbrele
    def shadows(self, cv):
        L = self.L
        x0, x1, top, yb = L.x0, L.x1, EL["h"], EL["leg_h"]

        def wall(Xw, Yw):
            dx = np.maximum(np.maximum(x0 - Xw, Xw - x1), 0)
            inx = np.exp(-dx / 2.5)
            dy_top = np.maximum(Yw - top, 0)
            above = 0.15 * np.exp(-dy_top / 3.0) * inx * (Yw >= top - 1)
            beside = 0.20 * np.exp(-np.maximum(Xw - x1, 0) / 4.0) * (Xw >= x1) * smooth((top + 4 - Yw) / 6.0)
            under = 0.42 * smooth((yb + 1 - Yw) / 4.0) * inx
            return 1 - np.clip(above + beside + under, 0, 0.6)

        cv.multiply_plane(wall, "Z", 0.0, max(x0 - 15, 0.1), min(x1 + 20, DESK["x0"] + 30), 0.0, top + 25)

        legs = L.legs
        r = EL["leg_rod"] / 2

        def floor(Xf, Zf):
            dx = np.maximum(np.maximum(x0 - Xf, Xf - x1), 0)
            dz = np.maximum(Zf - L.z1, 0)
            dist = np.hypot(dx, dz)
            body = np.where(dist > 0, 0.36 * np.exp(-dist / 5.0), 0.36 + 0.14 * np.exp(-(Zf - L.z0) / 15.0))
            contact = np.zeros_like(Xf)
            for (lx, lz) in legs:
                rr = np.maximum(np.hypot(Xf - lx, Zf - lz) - r, 0)
                contact = np.maximum(contact, 0.35 * np.exp(-rr / 1.3))
            return 1 - np.clip(body + contact, 0, 0.62)

        cv.multiply_plane(floor, "Y", 0.0, max(x0 - 20, 0.1), x1 + 25, 0.0, L.z1 + 25)


def finish(img, touch, seed=7):
    rng = np.random.RandomState(seed)
    t = cv2.GaussianBlur(touch, (0, 0), 2.0)[..., None]
    soft = cv2.GaussianBlur(img, (0, 0), 0.6 * SS)
    img = img * (1 - t) + soft * t
    out = cv2.resize(img, (W // SS, H // SS), interpolation=cv2.INTER_AREA)
    tt = cv2.resize(t[..., 0], (W // SS, H // SS), interpolation=cv2.INTER_AREA)[..., None]
    soft2 = cv2.GaussianBlur(out, (0, 0), 0.55)
    out = out * (1 - tt) + soft2 * tt
    out = out + rng.randn(*out.shape[:2], 1).astype(np.float32) * 0.010 * tt
    return np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8)


def render(name, light, bg):
    cv = Canvas(bg)
    sc = Scene(VARIANTS[name], light)
    sc.occluders(cv)
    sc.draw_chest(cv)
    sc.shadows(cv)
    return finish(cv.img, cv.touch)


def current_photo():
    """Fotografia de acum, la dimensiunea randărilor."""
    big = cv2.resize(PHOTO, (W // SS, H // SS), interpolation=cv2.INTER_LANCZOS4)
    return np.clip(big * 255 + 0.5, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    names = sys.argv[1:] or list(VARIANTS)
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    light = light_map()
    bg = np.clip(cv2.resize(PHOTO, (W, H), interpolation=cv2.INTER_LANCZOS4), 0, 1)
    cv2.imwrite(os.path.join(HERE, "out", "acum.jpg"), current_photo(), [cv2.IMWRITE_JPEG_QUALITY, 92])
    for nm in names:
        im = render(nm, light, bg)
        path = os.path.join(HERE, "out", VARIANTS[nm]["file"])
        cv2.imwrite(path, im, [cv2.IMWRITE_JPEG_QUALITY, 92])
        print("salvat", path, im.shape)
