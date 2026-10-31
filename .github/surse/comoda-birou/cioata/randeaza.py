"""Randează variantele C și D în fotografia biroului: bufetele Cioata Raya 116 și Veneto 116, în stânga biroului.

C: Raya, stejar Natural Oak, cu uși din lamele verticale de stejar și banda neagră a mânerului la mijloc.
D: Veneto, același corp, cu uși din microciment C9 (antracit spre negru) și mânerul rotund din stejar, ca la
comoda TV din living. Amândouă stau pe picioare rotunde negre, cu traversa de stejar retrasă, lipite de perete.

Camera, lumina peretelui, ocluderul biroului și finisarea vin din scripturile proiectului (`../core.py`,
`../render.py`); microcimentul vine din trusa comună (`unelte.materiale.concrete_panel`).

    python randeaza.py          # out/propunere_C_cioata_raya.jpg, out/varianta_D_cioata_veneto.jpg, out/acum.jpg
"""
import os
import sys

import cv2
import numpy as np

from varianta import BUF, DESK, VARIANTE, X0, X1, Z0, Z1, lamele  # pune și `..` și `.github` în sys.path

from core import Canvas, H, PHOTO, W  # noqa: E402  (din proiect)
from materials import R_TEX, sample, veneer  # noqa: E402
from render import FACE_LIGHT, Scene as ElementScene, VARIANTS, current_photo, finish, light_map, smooth, tone  # noqa: E402
from unelte import materiale as mat  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

# Albedourile (BGR), măsurate pe fotografiile Cioata, raportate la fundalul lor alb.
OAK_NO = np.array([0.265, 0.42, 0.55], np.float32)        # Natural Oak, lamelele ușilor Raya
OAK_HANDLE = np.array([0.30, 0.47, 0.61], np.float32)      # mânerul rotund Veneto (stejar, mai luminat)
BLACK = np.array([0.085, 0.09, 0.10], np.float32)          # banda neagră Raya și rostul de sub blat
MICRO = np.array([0.183, 0.185, 0.19], np.float32)         # microcimentul C9 al ușilor Veneto
STEEL = np.array([0.085, 0.085, 0.09], np.float32)         # picioarele, Nero RAL 9005

Y_BOT = BUF["body_y0"]                                      # 20: dedesubtul corpului
Y_DOOR0 = Y_BOT + BUF["bottom_t"]                           # 22,2
Y_DOOR1 = Y_DOOR0 + BUF["door_h"]                           # 77,2
Y_TOP0 = BUF["h"] - BUF["top_t"]                            # 79,8
XM = (X0 + X1) / 2.0                                        # rostul dintre uși
XI0, XI1 = X0 + BUF["side_t"], X1 - BUF["side_t"]           # golul dintre laterale


class BufetScene(ElementScene):
    def __init__(self, var, light, seed=21):
        super().__init__(VARIANTS["A"], light, seed)
        self.var = var
        rng = np.random.RandomState(seed)                    # texturile, aceleași în C și D
        # stejarul Cioata e masiv, cu fibra vizibilă: contrast mai mare decât furnirul BoConcept
        self.tex_lam = veneer(30, 60, rng, vertical=True, contrast=2.0)    # fibra lamelelor (verticală)
        self.tex_top = veneer(BUF["w"] + 4, BUF["d"] + 4, rng, vertical=False, contrast=1.7)
        self.tex_edge = veneer(BUF["w"] + 4, 8, rng, vertical=False, contrast=1.7)
        self.tex_rail = veneer(BUF["w"] + 4, 8, rng, vertical=False, contrast=1.7)
        self.tex_handle = veneer(BUF["handle_d"] + 2, BUF["handle_d"] + 2, rng, vertical=True, contrast=2.0)
        r2 = np.random.RandomState(seed + 5)
        # la ~3 px/cm, urmele fine ale mistriei se estompează: le întărim, media tonului rămâne aceeași
        self.tex_micro = [mat.concrete_panel(BUF["door_h"] + 22, BUF["door_w"] + 22, r2, MICRO,
                                             gain=dict(cloud=1.8, trowel=2.2, vein=1.8)) for _ in range(2)]
        # lamelele: lățimi de 5–12 cm, cu tonuri și decalaje proprii, aceleași ca în plan (varianta.lamele)
        self.lams = lamele(seed + 9)

    # ---------------------------------------------------------------- culorile
    def lit(self, alb, n, extra=None):
        M, E0, a = self.M, self.E0, alb * self.wb

        def color(s, t, X, yy, xx):
            f = E0 * FACE_LIGHT[n] * M[yy, xx]
            if extra is not None:
                f = f * extra(s, t, X)
            return tone(a[None, None, :] * f[..., None])
        return color

    def oak(self, tex, n, alb=OAK_NO, extra=None, along_t=False, off=(0.0, 0.0)):
        M, E0, a = self.M, self.E0, alb * self.wb

        def color(s, t, X, yy, xx):
            u, v = ((s, t) if not along_t else (t, s))
            det = sample(tex, (u + off[0]) * R_TEX, (v + off[1]) * R_TEX)[..., None]
            f = E0 * FACE_LIGHT[n] * M[yy, xx]
            if extra is not None:
                f = f * extra(s, t, X)
            return tone(a[None, None, :] * det * f[..., None])
        return color

    def door_raya(self, k):
        """Ușa k (0 = stânga, 1 = dreapta) din lamele de stejar; ușa din stânga are banda neagră pe muchia dreaptă."""
        edges, tones, offs, relief = self.lams[k]
        M, E0 = self.M, self.E0
        oak, blk = OAK_NO * self.wb, BLACK * self.wb
        w = BUF["door_w"]
        strip = BUF["strip_w"] if k == 0 else 0.0

        def color(s, t, X, yy, xx):
            idx = np.clip(np.searchsorted(edges, s, side="right") - 1, 0, len(edges) - 2)
            u = s - edges[idx]
            det = sample(self.tex_lam, (u + offs[idx, 0]) * R_TEX, (t + offs[idx, 1]) * R_TEX)
            c = oak[None, None, :] * (det * tones[idx])[..., None]
            # rosturile dintre lamele, umbra lamelelor care ies și lumina pe muchia lor din dreapta
            dl = np.minimum(u, edges[idx + 1] - edges[idx] - u)
            groove = np.clip(1 - dl / 0.12, 0, 1)
            sh = 1 - 0.45 * groove - 0.10 * relief[idx] * np.exp(-u / 0.5)
            sh = sh + 0.05 * relief[idx] * np.exp(-(edges[idx + 1] - edges[idx] - u) / 0.4)
            c = c * sh[..., None]
            if strip:
                m = (s > w - strip)[..., None]
                edge = np.exp(-np.abs(s - (w - strip)) / 0.15)[..., None]   # muchia benzii, spre stejar
                c = np.where(m, blk[None, None, :] * (1 + 0.15 * edge), c * (1 - 0.25 * edge))
            f = E0 * FACE_LIGHT[(0, 0, 1)] * M[yy, xx] * (0.94 + 0.06 * smooth((t - 1) / 10))
            return tone(c * f[..., None])
        return color

    def door_veneto(self, k):
        """Ușa k din microciment C9, cu jumătatea ei din mânerul rotund de stejar, lângă rostul dintre uși."""
        M, E0 = self.M, self.E0
        mc, ho = self.tex_micro[k], OAK_HANDLE * self.wb
        w, h, R = BUF["door_w"], BUF["door_h"], BUF["handle_d"] / 2
        cx = w if k == 0 else 0.0                               # centrul mânerului, pe rostul dintre uși
        cy = h / 2

        def color(s, t, X, yy, xx):
            c = mat.sample(mc, (s + 11) * mat.R, (t + 11) * mat.R) * self.wb[None, None, :]
            d = np.hypot(s - cx, t - cy)
            inside = d <= R
            det = sample(self.tex_handle, (s - cx + R + 1) * R_TEX, (t - cy + R + 1) * R_TEX)
            oakc = ho[None, None, :] * det[..., None]
            # muchia rotunjită a mânerului: mai luminată sus-dreapta (fereastra), mai întunecată jos-stânga
            rim = np.exp(-np.abs(d - R) / 0.35) * inside
            facing = ((s - cx) * 0.6 + (t - cy) * 0.8) / np.maximum(d, 1e-3)
            oakc = oakc * (1 + 0.22 * rim * facing)[..., None]
            # umbra mânerului (iese 1,5 cm) pe microciment, spre stânga și în jos
            ds = np.hypot(s - cx + 0.9, t - cy + 0.6)
            shadow = 1 - 0.35 * np.clip((R + 0.8 - ds) / 1.2, 0, 1) * (~inside)
            c = np.where(inside[..., None], oakc, c * shadow[..., None])
            f = E0 * FACE_LIGHT[(0, 0, 1)] * M[yy, xx] * (0.94 + 0.06 * smooth((t - 1) / 10))
            return tone(c * f[..., None])
        return color

    # ---------------------------------------------------------------- bufetul
    def draw(self, cv):
        zf = Z1
        g = BUF["gap"]
        # interiorul văzut prin rosturi: corpul, în umbră (cât tot corpul, ca privirea piezișă prin rost să-l atingă)
        cv.face([X0, Y_BOT, zf - 1.2], [1, 0, 0], [0, 1, 0], X1 - X0, Y_TOP0 - Y_BOT, self.lit(BLACK, (0, 0, 1)))
        # blatul (stejar masiv): fața de sus și cantul din față
        cv.face([X0, BUF["h"], Z0], [1, 0, 0], [0, 0, 1], BUF["w"], BUF["d"],
                self.oak(self.tex_top, (0, 1, 0), extra=lambda s, t, X: 1 - 0.10 * np.exp(-(X[..., 2] - Z0) / 3.0)))
        cv.face([X0, Y_TOP0, zf], [1, 0, 0], [0, 1, 0], BUF["w"], BUF["top_t"],
                self.oak(self.tex_edge, (0, 0, 1), extra=lambda s, t, X: 1 + 0.06 * np.exp(-(BUF["top_t"] - t) / 0.3)))
        # lateralele și fundul, cu cantul din față
        for xa in (X0, X1 - BUF["side_t"]):
            cv.face([xa, Y_BOT, zf], [1, 0, 0], [0, 1, 0], BUF["side_t"], Y_TOP0 - Y_BOT,
                    self.oak(self.tex_edge, (0, 0, 1), along_t=True, off=(xa, 0)))
        cv.face([XI0, Y_BOT, zf], [1, 0, 0], [0, 1, 0], XI1 - XI0, BUF["bottom_t"],
                self.oak(self.tex_edge, (0, 0, 1), off=(0, 3)))
        # banda neagră de sub blat, puțin retrasă
        cv.face([XI0, Y_DOOR1, zf - 0.6], [1, 0, 0], [0, 1, 0], XI1 - XI0, Y_TOP0 - Y_DOOR1, self.lit(BLACK, (0, 0, 1)))
        # ușile
        for k, (xa, xb) in enumerate(((XI0 + g, XM - g / 2), (XM + g / 2, XI1 - g))):
            fn = self.door_raya(k) if self.var["usa"] == "lamele" else self.door_veneto(k)
            wide = xb - xa
            s0 = BUF["door_w"] - wide if k == 0 else 0.0        # ușa se taie din exterior, rostul rămâne la mijloc

            def shifted(s, t, X, yy, xx, fn=fn, s0=s0):
                return fn(s + s0, t, X, yy, xx)
            cv.face([xa, Y_DOOR0 + 0.2, zf], [1, 0, 0], [0, 1, 0], wide, BUF["door_h"] - 0.2, shifted)
        # traversa de stejar, între picioarele din față (le ating axul), sub corp, și picioarele negre
        xr0, xr1 = X0 + BUF["leg_in_x"], X1 - BUF["leg_in_x"]
        zr = zf - BUF["rail_in"]
        cv.face([xr0, BUF["leg_h"], zr], [1, 0, 0], [0, 1, 0], xr1 - xr0, BUF["rail_h"],
                self.oak(self.tex_rail, (0, 0, 1),
                         extra=lambda s, t, X: 0.68 + 0.32 * smooth((BUF["rail_h"] - t) / BUF["rail_h"] + 0.3)))
        r = BUF["leg_d"] / 2
        for x in (X0 + BUF["leg_in_x"], X1 - BUF["leg_in_x"]):
            for z in (Z0 + BUF["leg_in_z"], Z1 - BUF["leg_in_z"]):
                cv.box(x - r, x + r, 0, BUF["leg_h"], z - r, z + r, self.steel_leg)

    def steel_leg(self, n):
        M, E0, col = self.M, self.E0, STEEL * self.wb
        sh = FACE_LIGHT.get(tuple(n), 0.8)

        def color(s, t, X, yy, xx):
            f = E0 * sh * M[yy, xx] * (0.85 + 0.15 * smooth(X[..., 1] / BUF["leg_h"]))
            return tone(col[None, None, :] * f[..., None] + 0.012)
        return color

    # ---------------------------------------------------------------- umbrele
    def shadows(self, cv):
        x0, x1, top, yb = X0, X1, BUF["h"], BUF["body_y0"]

        def wall(Xw, Yw):
            dx = np.maximum(np.maximum(x0 - Xw, Xw - x1), 0)
            inx = np.exp(-dx / 3.0)
            above = 0.10 * np.exp(-np.maximum(Yw - top, 0) / 3.0) * inx * (Yw >= top - 1)
            beside = 0.20 * np.exp(-np.maximum(Xw - x1, 0) / 4.0) * (Xw >= x1) * smooth((top + 4 - Yw) / 6.0)
            under = 0.62 * smooth((yb + 2 - Yw) / 6.0) * inx         # sub corpul adânc de 48 cm
            return 1 - np.clip(above + beside + under, 0, 0.68)

        cv.multiply_plane(wall, "Z", 0.0, max(x0 - 15, 0.1), min(x1 + 20, DESK["x0"] + 30), 0.0, top + 25)
        r = BUF["leg_d"] / 2
        legs = [(x, z) for x in (x0 + BUF["leg_in_x"], x1 - BUF["leg_in_x"]) for z in (Z0 + BUF["leg_in_z"], Z1 - BUF["leg_in_z"])]

        def floor(Xf, Zf):
            dx = np.maximum(np.maximum(x0 + 2 - Xf, Xf - x1 + 2), 0)
            dz = np.maximum(Zf - Z1 + 2, 0)
            dist = np.hypot(dx, dz)
            body = np.where(dist > 0, 0.34 * np.exp(-dist / 8.0), 0.36 + 0.20 * np.exp(-(Zf - Z0) / 15.0))
            contact = np.zeros_like(Xf)
            for (lx, lz) in legs:
                rr = np.maximum(np.hypot(Xf - lx, Zf - lz) - r, 0)
                contact = np.maximum(contact, 0.40 * np.exp(-rr / 1.4))
            return 1 - np.clip(body + contact, 0, 0.68)

        cv.multiply_plane(floor, "Y", 0.0, max(x0 - 20, 0.1), x1 + 25, 0.0, Z1 + 30)


def render(name, light, bg):
    cv = Canvas(bg)
    sc = BufetScene(VARIANTE[name], light)
    sc.occluders(cv)
    sc.draw(cv)
    sc.shadows(cv)
    return finish(cv.img, cv.touch)


if __name__ == "__main__":
    names = sys.argv[1:] or list(VARIANTE)
    os.makedirs(OUT, exist_ok=True)
    light = light_map()
    bg = np.clip(cv2.resize(PHOTO, (W, H), interpolation=cv2.INTER_LANCZOS4), 0, 1)
    cv2.imwrite(os.path.join(OUT, "acum.jpg"), current_photo(), [cv2.IMWRITE_JPEG_QUALITY, 92])
    for nm in names:
        im = render(nm, light, bg)
        path = os.path.join(OUT, VARIANTE[nm]["fisier"])
        cv2.imwrite(path, im, [cv2.IMWRITE_JPEG_QUALITY, 92])
        print("salvat", path, im.shape)
