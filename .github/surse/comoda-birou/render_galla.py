"""Randează alternativa întrebată de utilizator: dulapul Cioata Galla 120 (cod GL650), în locul comodei.

Dimensiuni din pagina Cioata: 120 × 51 × 150 cm (desenul cotat dă 119 cm), picioare de 16 cm, traverse de stejar
la 11,5 cm de pardoseală. Fața, din desenul producătorului: în stânga o ușă de 51 cm cu riflaj de stejar, pe
toată înălțimea; în dreapta, pe 68 cm, două sertare de 22 cm jos și, deasupra lor, o nișă de 34 cm cu polițe
de sticlă la 28 cm și o ușă canelată de 34 cm, în culoarea de contrast. Aici: Natural Oak (NO) cu contrast Nero
(NR), ca biroul și tâmplăria. Așezarea: centrat în peretele liber dintre colț și birou.
"""
import os

import cv2
import numpy as np

from core import Canvas, HERE, PHOTO, W, H, cam
from design import DESK
from materials import R_TEX, sample, veneer
from render import FACE_LIGHT, Scene as ElementScene, VARIANTS, finish, light_map, smooth, tone

G = {
    "w": 119.0, "d": 51.0, "h": 150.0, "leg_h": 16.0, "rail_y": 11.5,
    "left_w": 51.0, "right_w": 68.0, "niche_w": 34.0, "drawer_h": 22.0, "shelf_step": 28.0,
    "gap": 0.3, "side_t": 2.0, "back_t": 1.5, "rib": 2.4,
}
OAK_NO = np.array([0.514, 0.663, 0.745], np.float32)      # Cioata Natural Oak, din mostra producătorului (BGR)
NERO = np.array([0.071, 0.051, 0.055], np.float32)        # Cioata Nero, MDF vopsit
CERAMIC = np.array([0.11, 0.11, 0.12], np.float32)        # spatele nișei, ceramică închisă
STEEL = np.array([0.085, 0.085, 0.09], np.float32)


class Galla:
    def __init__(self):
        free = DESK["x0"]
        self.x0 = (free - G["w"]) / 2.0                     # centrat între colț și birou
        self.x1 = self.x0 + G["w"]
        self.z0 = 0.5
        self.z1 = self.z0 + G["d"]
        self.xm = self.x0 + G["left_w"]                     # unde începe partea din dreapta
        self.xn = self.xm + G["niche_w"]                    # unde se termină nișa și începe ușa din dreapta
        self.yd = G["leg_h"] + 2 * G["drawer_h"]            # deasupra sertarelor


class GallaScene(ElementScene):
    def __init__(self, light, seed=9):
        super().__init__(VARIANTS["A"], light, seed)
        self.g = Galla()
        rng = np.random.RandomState(seed)
        self.tex_door = veneer(G["left_w"] + 2, G["h"] + 2, rng, vertical=True)
        self.tex_drawer = veneer(G["right_w"] + 2, 2 * G["drawer_h"] + 2, rng, vertical=False)
        self.tex_side = veneer(G["d"] + 2, G["h"] + 2, rng, vertical=True)

    def lit(self, alb, n, extra=None):
        M, E0 = self.M, self.E0
        a = alb * self.wb

        def color(s, t, X, yy, xx):
            f = E0 * FACE_LIGHT[n] * M[yy, xx]
            if extra is not None:
                f = f * extra(s, t, X)
            return tone(a[None, None, :] * f[..., None])
        return color

    def oak(self, tex, n, extra=None, along_t=True):
        M, E0 = self.M, self.E0
        a = OAK_NO * self.wb

        def color(s, t, X, yy, xx):
            det = sample(tex, (s if along_t else t) * R_TEX, (t if along_t else s) * R_TEX)[..., None]
            f = E0 * FACE_LIGHT[n] * M[yy, xx]
            if extra is not None:
                f = f * extra(s, t, X)
            return tone(a[None, None, :] * det * f[..., None])
        return color

    def draw(self, cv):
        g, zf = self.g, self.g.z1
        gp = G["gap"]
        y0, y1 = G["leg_h"], G["h"]
        # în rosturile dintre fronturi se vede corpul, în umbră (nu peretele din spate); nișa rămâne deschisă
        dark = self.lit(OAK_NO * 0.22, (0, 0, 1))
        for (xa_, xb_, ya_, yb2) in ((g.x0, g.xm, y0, y1), (g.xm, g.x1, y0, g.yd), (g.xn, g.x1, g.yd, y1)):
            cv.face([xa_, ya_, zf - 0.4], [1, 0, 0], [0, 1, 0], xb_ - xa_, yb2 - ya_, dark)
        # ușa din stânga: riflaj de stejar (baghete de 2,4 cm), cu mânerul frezat lângă muchia din dreapta
        def rib(s, t, X):
            fr = np.mod(s / G["rib"], 1.0)
            x = 2 * fr - 1
            f = 0.78 + 0.22 * np.sqrt(np.clip(1 - 0.8 * x * x, 0, 1)) + 0.05 * x
            f = f * (1 - 0.35 * np.clip((np.abs(x) - 0.88) / 0.12, 0, 1))
            slot = (s > G["left_w"] - 3.4) & (s < G["left_w"] - 1.6) & (t > 72) & (t < 86)
            return np.where(slot, 0.25, f)
        cv.face([g.x0, y0, zf], [1, 0, 0], [0, 1, 0], G["left_w"] - gp, y1 - y0,
                self.oak(self.tex_door, (0, 0, 1), rib))
        # sertarele: jumătatea din stânga stejar, cea din dreapta Nero canelat, cu mâner negru peste îmbinare
        for k in range(2):
            yb = y0 + k * G["drawer_h"]
            hd = G["drawer_h"] - gp
            half = G["niche_w"]
            cv.face([g.xm, yb, zf], [1, 0, 0], [0, 1, 0], half - gp / 2, hd,
                    self.oak(self.tex_drawer, (0, 0, 1), lambda s, t, X: np.ones_like(s), along_t=False))
            cv.face([g.xn + gp / 2, yb, zf], [1, 0, 0], [0, 1, 0], G["right_w"] - half - gp / 2, hd,
                    self.lit(NERO, (0, 0, 1), self.flutes))
            hy = yb + hd / 2
            cv.box(g.xn - 11, g.xn + 11, hy - 0.5, hy + 0.5, zf, zf + 2.5, self.steel)
        # ușa din dreapta, deasupra sertarelor: Nero canelat
        cv.face([g.xn + gp / 2, g.yd, zf], [1, 0, 0], [0, 1, 0], G["right_w"] - G["niche_w"] - gp / 2, y1 - g.yd,
                self.lit(NERO, (0, 0, 1), self.flutes))
        # rama nișei (cantul corpului) și interiorul ei
        t = G["side_t"]
        xa, xb, ya, yb_ = g.xm + gp, g.xn - gp / 2, g.yd + gp, y1
        cv.face([xa, ya, zf - 0.01], [1, 0, 0], [0, 1, 0], xb - xa, t, self.oak(self.tex_side, (0, 0, 1)))
        cv.face([xa, yb_ - t, zf - 0.01], [1, 0, 0], [0, 1, 0], xb - xa, t, self.oak(self.tex_side, (0, 0, 1)))
        cv.face([xa, ya, zf - 0.01], [1, 0, 0], [0, 1, 0], t, yb_ - ya, self.oak(self.tex_side, (0, 0, 1)))
        cv.face([xb - t, ya, zf - 0.01], [1, 0, 0], [0, 1, 0], t, yb_ - ya, self.oak(self.tex_side, (0, 0, 1)))
        zi0, zi1 = g.z0 + G["back_t"], zf - 0.02
        xi0, xi1, yi0, yi1 = xa + t, xb - t, ya + t, yb_ - t
        dim = lambda s, t_, X: 0.55 * (0.6 + 0.4 * np.clip((X[..., 2] - zi0) / (zi1 - zi0), 0, 1))
        cv.face([xi0, yi0, zi0], [1, 0, 0], [0, 1, 0], xi1 - xi0, yi1 - yi0, self.lit(CERAMIC, (0, 0, 1), dim))
        cv.face([xi1, yi0, zi0], [0, 1, 0], [0, 0, 1], yi1 - yi0, zi1 - zi0, self.oak(self.tex_side, (-1, 0, 0), dim))
        cv.face([xi0, yi0, zi0], [1, 0, 0], [0, 0, 1], xi1 - xi0, zi1 - zi0, self.oak(self.tex_side, (0, 1, 0), dim))
        cv.face([xi0, yi1, zi0], [0, 0, 1], [1, 0, 0], zi1 - zi0, xi1 - xi0, self.oak(self.tex_side, (0, -1, 0), dim))
        # polițele de sticlă, cu ramă de stejar (se vede cantul din față și sticla, ca o bandă închisă)
        for k in (1, 2):
            ys = yi0 + k * G["shelf_step"] - 1.0
            if ys > yi1 - 2:
                continue
            cv.face([xi0, ys, zi1 - 2], [1, 0, 0], [0, 1, 0], xi1 - xi0, 1.8, self.oak(self.tex_side, (0, 0, 1)))
            cv.face([xi0, ys + 1.8, zi0], [1, 0, 0], [0, 0, 1], xi1 - xi0, zi1 - 2 - zi0,
                    self.lit(CERAMIC * 1.6, (0, 1, 0), dim))
        # picioarele negre și traversele de stejar de sub corp
        for x in (g.x0 + 3, g.x1 - 3):
            for z in (g.z0 + 3, g.z1 - 3):
                cv.box(x - 1, x + 1, 0, y0, z - 1, z + 1, self.steel)
            cv.box(x - 1.5, x + 1.5, G["rail_y"], y0, g.z0 + 2, g.z1 - 2, lambda n: self.oak(self.tex_side, n))

    @staticmethod
    def flutes(s, t, X):
        """Canelurile diagonale de pe panourile vopsite, la 45°, cu pasul de ~4 cm."""
        u = (s + t) / np.sqrt(2) / 4.0
        fr = np.mod(u, 1.0)
        return 1.0 - 0.45 * np.exp(-((fr - 0.5) / 0.06) ** 2) + 0.25 * np.exp(-((fr - 0.42) / 0.05) ** 2)

    def shadows(self, cv):
        g = self.g
        x0, x1, top, yb = g.x0, g.x1, G["h"], G["leg_h"]

        def wall(Xw, Yw):
            dx = np.maximum(np.maximum(x0 - Xw, Xw - x1), 0)
            inx = np.exp(-dx / 2.5)
            above = 0.10 * np.exp(-np.maximum(Yw - top, 0) / 3.0) * inx * (Yw >= top - 1)
            beside = 0.22 * np.exp(-np.maximum(Xw - x1, 0) / 4.0) * (Xw >= x1) * smooth((top + 4 - Yw) / 6.0)
            under = 0.42 * smooth((yb + 1 - Yw) / 4.0) * inx
            return 1 - np.clip(above + beside + under, 0, 0.6)

        cv.multiply_plane(wall, "Z", 0.0, max(x0 - 15, 0.1), min(x1 + 20, DESK["x0"] + 30), 0.0, top + 25)

        def floor(Xf, Zf):
            dx = np.maximum(np.maximum(x0 - Xf, Xf - x1), 0)
            dz = np.maximum(Zf - g.z1, 0)
            dist = np.hypot(dx, dz)
            body = np.where(dist > 0, 0.36 * np.exp(-dist / 5.0), 0.36 + 0.14 * np.exp(-(Zf - g.z0) / 15.0))
            contact = np.zeros_like(Xf)
            for lx in (x0 + 3, x1 - 3):
                for lz in (g.z0 + 3, g.z1 - 3):
                    rr = np.maximum(np.hypot(Xf - lx, Zf - lz) - 1, 0)
                    contact = np.maximum(contact, 0.35 * np.exp(-rr / 1.3))
            return 1 - np.clip(body + contact, 0, 0.62)

        cv.multiply_plane(floor, "Y", 0.0, max(x0 - 20, 0.1), x1 + 25, 0.0, g.z1 + 25)


def door_check():
    """Cât loc au ușile la 90°: ușa din stânga spre peretele din colț, cea din dreapta spre blatul biroului."""
    g = Galla()
    door_t = 2.5                                          # grosimea ușilor, cu riflajul  # est.
    print(f"Galla 120: X {g.x0:.1f} … {g.x1:.1f} cm; până în colț {g.x0:.1f} cm, până la birou {DESK['x0'] - g.x1:.1f} cm")
    print(f"  ușa din stânga (51 cm) la 90°: iese ~{door_t} cm în lateral; rămân ~{g.x0 - door_t:.1f} cm până la perete")
    print(f"  ușa din dreapta (34 cm) la 90°: rămân ~{DESK['x0'] - g.x1 - door_t:.1f} cm până la blat; "
          f"la 110° marginea ei ar intra ~{20.2 * np.sin(np.radians(20)) + door_t - (DESK['x0'] - g.x1):.1f} cm în blat")


if __name__ == "__main__":
    door_check()
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    light = light_map()
    bg = np.clip(cv2.resize(PHOTO, (W, H), interpolation=cv2.INTER_LANCZOS4), 0, 1)
    cv = Canvas(bg)
    sc = GallaScene(light)
    sc.occluders(cv)
    sc.draw(cv)
    sc.shadows(cv)
    im = finish(cv.img, cv.touch)
    path = os.path.join(HERE, "out", "alternativa_cioata_galla_120.jpg")
    cv2.imwrite(path, im, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print("salvat", path, im.shape)
