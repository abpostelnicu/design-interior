"""Randează polițele flotante pentru viniluri în fotografia din living, în dreapta televizorului.

Polițele sunt prinse direct în perete, pe tije ascunse în poliță. Discurile stau în picioare, între opritoare:
A: opritoare îmbrăcate în stejar, ca polițele. B: opritoare din oțel negru mat, ca picioarele comodei.
"""
import os
import sys

import cv2
import numpy as np

from core import Canvas, H, HERE, PHOTO, SS, W, cam, wall_light_map
from design import CABINET, D, LP, ROWS, SITE, TOWER, TV, shelves
from materials import R_OAK, SPINE_COLORS, SPINE_P, end_grain, glued_panel, sample

VARIANTS = {
    "A": dict(bookend="stejar", file="propunere_A_stejar.jpg"),
    "B": dict(bookend="otel", file="varianta_B_opritoare_negre.jpg"),
}
# lumina vine din față (ferestrele din spatele aparatului): factorul de umbrire pe direcția normalei
SHADE = {(0, 0, 1): 1.0, (1, 0, 0): 0.74, (-1, 0, 0): 0.70, (0, -1, 0): 0.56, (0, 1, 0): 1.04}
BLACK = np.array([0.072, 0.070, 0.068], np.float32)   # oțel vopsit negru mat (BGR)
REC_BACK = 0.7                                         # discurile stau la 7 mm de perete
COVER_COLORS = np.array([(226, 226, 222), (205, 207, 208), (52, 50, 54), (150, 122, 104), (62, 72, 150),
                         (120, 130, 92)], np.float32) / 255.0   # BGR: alb, gri, negru, albastru, roșu, verde închis
REC_FRONT = REC_BACK + LP["size"]
GUARD_Y = TOWER["h"] + 1.5                             # sub capacul boxelor nu se pun umbre pe perete


def tone(x):
    """Compresie blândă a luminilor, ca stejarul luminat să nu se ardă."""
    k = 0.82
    return np.where(x < k, x, k + (1 - k) * (1 - np.exp(-(x - k) / (1 - k))))


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


class Scene:
    def __init__(self, var, M, seed=11):
        self.var = var
        # polițele ies 33 cm din perete: urmează lumina peretelui doar în parte
        self.M = (1 + 0.45 * (M - 1)).astype(np.float32)
        self.rng = np.random.RandomState(seed)          # texturile de stejar (aceleași în A și B)
        self.rng_rec = np.random.RandomState(seed + 2)  # discurile (aceleași în A și B)

    def oak_color(self, tex, grain_u, n, off, ao=None, dims=None):
        M, R = self.M, R_OAK
        sh = SHADE[tuple(int(v) for v in n)]

        def color(s, t, X, yy, xx):
            if grain_u:
                rows, cols = (s + off[0]) * R, (t + off[1]) * R
            else:
                rows, cols = (t + off[0]) * R, (s + off[1]) * R
            c = sample(tex, cols, rows)
            f = M[yy, xx] * sh
            if ao is not None:
                f = f * ao(X)
            if dims is not None:
                # muchiile din față, ușor rotunjite, prind puțin mai multă lumină
                wu, hv = dims
                e = np.minimum(np.minimum(s, wu - s), np.minimum(t, hv - t))
                f = f * (1 + 0.10 * np.exp(-e / 0.15))
            return tone(c * f[..., None])
        return color

    def steel(self, n, ao=None, sheen=0.0):
        sh = SHADE[tuple(int(v) for v in n)]
        Mm = self.M

        def color(s, t, X, yy, xx):
            f = Mm[yy, xx] * sh * np.ones_like(s)
            if ao is not None:
                f = f * ao(X)
            c = BLACK[None, None, :] * f[..., None] + sheen
            return tone(c)
        return color

    # ---------------------------------------------------------------- polița
    def draw_shelf(self, cv, x0, yb, yt):
        L, P, T = D["L"], D["P"], D["T"]
        rng = self.rng
        face = glued_panel(L + 2, P + 2, rng, lam=(8.0, 12.0), tone=0.035)   # furnir pe fețe
        edge = glued_panel(L + 2, T + 2, rng, lam=(T + 1.0, T + 1.5), tone=0.03)  # cant din stejar masiv
        endg = end_grain(T, P, rng)

        def ao_under(X):
            return 1 - 0.38 * np.exp(-np.clip(X[..., 2], 0, None) / 3.5)

        cv.face([x0, yb, P], [1, 0, 0], [0, 1, 0], L, T,
                self.oak_color(edge, True, (0, 0, 1), (rng.uniform(0, 20), 0.5), None, dims=(L, T)))
        cv.face([x0, yb, 0], [1, 0, 0], [0, 0, 1], L, P,
                self.oak_color(face, True, (0, -1, 0), (rng.uniform(0, 20), 0.5), ao_under))
        cv.face([x0, yt, 0], [1, 0, 0], [0, 0, 1], L, P,
                self.oak_color(face, True, (0, 1, 0), (rng.uniform(0, 20), 0.5)))
        for xe, n in ((x0, (-1, 0, 0)), (x0 + L, (1, 0, 0))):
            cv.face([xe, yb, 0], [0, 1, 0], [0, 0, 1], T, P, self.oak_color(endg, False, n, (0.0, 0.0), ao_under))

    # ---------------------------------------------------------------- boxele din fotografie
    def occluders(self, cv):
        """Boxele de podea stau în fața peretelui: ce e în spatele lor rămâne ascuns, iar umbrele nu cad pe ele."""
        zb, zf = TOWER["z_back"], TOWER["z_back"] + TOWER["d"]
        for (xa, xb) in (TOWER["xl"], TOWER["xr"]):
            cv.face([xa, 0, zf], [1, 0, 0], [0, 1, 0], xb - xa, TOWER["h"], None)
            cv.face([xa, TOWER["h"], zb], [1, 0, 0], [0, 0, 1], xb - xa, zf - zb, None)
            for xe in (xa, xb):
                cv.face([xe, 0, zb], [0, 0, 1], [0, 1, 0], zf - zb, TOWER["h"], None)

    # ---------------------------------------------------------------- discurile și opritoarele
    def draw_row(self, cv, x0, yt, y_ceil, outer_left, fill):
        """Un rând de discuri lipit de capătul exterior al poliței, cu câte un opritor la fiecare capăt."""
        rng = self.rng_rec
        bt = D["bookend_a"]
        length = (D["L"] - 2 * bt) * fill
        thick = []
        while sum(thick) < length:
            thick.append(float(rng.choice([0.32, 0.36, 0.42, 0.5, 0.62, 0.8, 1.05],
                                          p=[0.2, 0.22, 0.2, 0.14, 0.12, 0.08, 0.04])))
        if outer_left:
            xs = x0 + bt
            end_a, end_b = x0, None
        else:
            xs = x0 + D["L"] - bt - sum(thick)
            end_a, end_b = None, x0 + D["L"] - bt
        x = xs
        recs = []
        for w in thick:
            h = LP["size"] + float(rng.choice([0.0, 0.0, 0.0, 0.2, -0.3]))
            zf = REC_FRONT + abs(rng.randn()) * 0.3 + (0.5 if rng.rand() < 0.06 else 0.0)
            col = np.clip(SPINE_COLORS[rng.choice(len(SPINE_COLORS), p=SPINE_P)] * (1 + 0.06 * rng.randn(3)), 0, 1)
            recs.append((x, w, h, zf, col))
            x += w
        x_end = x
        for (xr, w, h, zf, col) in recs:
            self.spine(cv, xr, w, h, zf, col, yt, y_ceil)
        # copertele de la capetele rândului, unde se văd
        for (xr, w, h, zf, col), side in ((recs[0], -1), (recs[-1], 1)):
            xe = xr if side < 0 else xr + w
            self.cover(cv, xe, side, h, zf, col, yt, y_ceil)
        # opritoarele, lipite de primul și de ultimul disc
        t = D["bookend_a"] if self.var["bookend"] == "stejar" else D["bookend_t"]
        side = 1 if cam.C[0] > x0 + D["L"] else -1   # fața laterală care se vede din aparat
        self.bookend(cv, xs - t, yt, side)
        self.bookend(cv, x_end, yt, side)
        return xs, x_end

    def spine(self, cv, xr, w, h, zf, col, yt, y_ceil):
        rng = self.rng_rec
        Mm = self.M
        band = rng.rand() < 0.35
        band_y = rng.uniform(0.04, 0.12)
        dark = col.mean() < 0.3

        def color(s, t, X, yy, xx):
            f = Mm[yy, xx] * 0.92
            if y_ceil is not None:
                f = f * (1 - 0.30 * np.exp(-(y_ceil - X[..., 1]) / 7.0))    # umbra poliței de deasupra
            f = f * (1 - 0.18 * np.exp(-(X[..., 1] - yt) / 2.5))           # ocluzie lângă poliță
            edge = np.minimum(s, w - s) / max(w, 1e-3)
            f = f * (0.80 + 0.20 * np.clip(edge * 6, 0, 1))
            c = np.broadcast_to(col, s.shape + (3,)).copy()
            if band:
                m = (np.abs(t / max(h, 1e-3) - band_y) < 0.012)[..., None]
                c = np.where(m, (0.85 - c * 0.5) if not dark else c + 0.35, c)
            return tone(c * f[..., None])

        cv.face([xr, yt, zf], [1, 0, 0], [0, 1, 0], w, h, color)
        # muchia de sus a copertei se vede doar dacă aparatul e mai sus; aici nu, dar o lăsăm pentru bufferul de adâncime
        cv.face([xr, yt + h, zf - LP["size"]], [1, 0, 0], [0, 0, 1], w, LP["size"],
                lambda s, t, X, yy, xx: tone(col * 0.8 * Mm[yy, xx][..., None]))

    def cover(self, cv, xe, side, h, zf, col, yt, y_ceil):
        """Coperta de la capătul rândului: culori estompate și un motiv simplu (cerc sau bandă)."""
        rng = self.rng_rec
        Mm = self.M

        def mute(c, k=0.55):
            g = float(np.mean(c))
            return np.clip(g + (c - g) * k, 0, 1).astype(np.float32)

        # copertele de la capete au culori care nu se confundă cu stejarul (fără maro și galben)
        c1 = mute(COVER_COLORS[rng.randint(len(COVER_COLORS))], 0.7)
        c2 = mute(SPINE_COLORS[rng.choice(len(SPINE_COLORS), p=SPINE_P)])
        kind = rng.choice(["cerc", "banda", "plin"], p=[0.45, 0.35, 0.2])
        cu, cv_, rad = rng.uniform(0.35, 0.65), rng.uniform(0.4, 0.7), rng.uniform(0.18, 0.3)
        n = (1, 0, 0) if side > 0 else (-1, 0, 0)
        sh = SHADE[n]
        S = LP["size"]

        def color(s, t, X, yy, xx):
            u, v = s / S, t / max(h, 1e-3)
            if kind == "cerc":
                m = np.clip((rad - np.hypot(u - cu, v - cv_)) / 0.02, 0, 1)
            elif kind == "banda":
                m = np.clip((0.08 - np.abs(v - cv_)) / 0.01, 0, 1)
            else:
                m = np.zeros_like(u)
            c = c1[None, None, :] * (1 - m[..., None]) + c2[None, None, :] * m[..., None]
            c = c * (0.94 + 0.06 * v[..., None])
            f = Mm[yy, xx] * sh * 0.82
            if y_ceil is not None:
                f = f * (1 - 0.30 * np.exp(-(y_ceil - X[..., 1]) / 7.0))
            return tone(c * f[..., None])

        cv.face([xe, yt, zf - LP["size"]], [0, 0, 1], [0, 1, 0], LP["size"], h, color)

    def bookend(self, cv, xa, yt, side):
        """Opritor L: placa verticală la x = xa … xa + grosime; talpa de oțel stă sub discuri și nu se vede."""
        bh = D["bookend_h"]
        z1 = REC_FRONT - 1.0
        n = (1, 0, 0) if side > 0 else (-1, 0, 0)
        if self.var["bookend"] == "otel":
            bt, bd = D["bookend_t"], D["bookend_d"]
            z0 = z1 - bd
            cv.face([xa, yt, z1], [1, 0, 0], [0, 1, 0], bt, bh, self.steel((0, 0, 1), sheen=0.02))
            cv.face([xa, yt + bh, z0], [1, 0, 0], [0, 0, 1], bt, bd, self.steel((0, 1, 0)))
            xe = xa + bt if side > 0 else xa
            cv.face([xe, yt, z0], [0, 0, 1], [0, 1, 0], bd, bh, self.steel(n, sheen=0.008))
            return
        # varianta A: placa de stejar de 2 cm acoperă opritorul de oțel
        bt, bd = D["bookend_a"], D["oak_d"]
        z0 = z1 - bd
        rng = self.rng   # generatorul texturilor de stejar, ca discurile să rămână aceleași în A și B
        tex = glued_panel(bh + 2, bd + 2, rng, lam=(bd + 1, bd + 1.5), tone=0.03)   # o singură lamelă, fibra în sus
        endg = end_grain(bt, bd, rng)
        cv.face([xa, yt, z1], [1, 0, 0], [0, 1, 0], bt, bh,
                self.oak_color(tex, False, (0, 0, 1), (0.5, rng.uniform(0, 1)), None, dims=(bt, bh)))
        cv.face([xa, yt + bh, z0], [0, 0, 1], [1, 0, 0], bd, bt, self.oak_color(endg, True, (0, 1, 0), (0.0, 0.0)))
        xe = xa + bt if side > 0 else xa
        cv.face([xe, yt, z0], [0, 0, 1], [0, 1, 0], bd, bh,
                self.oak_color(tex, False, n, (0.5, 0.5), lambda X: 1 - 0.15 * np.exp(-(X[..., 1] - yt) / 2.0)))

    # ---------------------------------------------------------------- umbrele pe perete
    def wall_shadows(self, cv, rows):
        L, P = D["L"], D["P"]
        for (side, level, x0, yb, yt) in shelves():
            x1 = x0 + L
            ra, rb = rows[(side, level)]

            def fac(Xw, Yw, x0=x0, x1=x1, yb=yb, yt=yt, ra=ra, rb=rb):
                dx = np.maximum(np.maximum(x0 - Xw, Xw - x1), 0)
                sx = np.exp(-dx / 5.0)
                d_below = np.maximum(yb - Yw, 0)
                d_above = np.maximum(Yw - yt, 0)
                # în dreptul grosimii poliței (yb … yt), dincolo de capete, se aplică ambele: umbra capătului
                below = (0.30 * np.exp(-d_below / 2.5) + 0.17 * np.exp(-d_below / 13.0)) * sx * (Yw <= yt)
                above = 0.20 * np.exp(-d_above / 1.6) * sx * (Yw >= yb)
                # discurile sunt lipite de perete: ocluzie deasupra lor și pe laturi
                rx = np.maximum(np.maximum(ra - Xw, Xw - rb), 0)
                top = yt + LP["size"]
                rec = 0.22 * np.exp(-np.hypot(rx, np.maximum(Yw - top, 0)) / 1.8) * (Yw >= yt)
                dark = np.clip(below + above + rec, 0, 0.6)
                dark = dark * smooth((Yw - GUARD_Y) / 5.0)
                return 1 - dark
            cv.multiply_wall(fac, max(x0 - 20, 0.0), min(x1 + 20, SITE["wall_w"] - 0.1), max(yb - 45, 0), yt + 40)


def finish(img, touch, seed=7):
    rng = np.random.RandomState(seed)
    t = cv2.GaussianBlur(touch, (0, 0), 1.5)[..., None]
    soft = cv2.GaussianBlur(img, (0, 0), 0.8 * SS)
    img = img * (1 - t) + soft * t
    out = cv2.resize(img, (W // SS, H // SS), interpolation=cv2.INTER_AREA)
    tt = cv2.resize(t[..., 0], (W // SS, H // SS), interpolation=cv2.INTER_AREA)[..., None]
    soft2 = cv2.GaussianBlur(out, (0, 0), 0.7)
    out = out * (1 - tt) + soft2 * tt
    out = out + rng.randn(*out.shape[:2], 1).astype(np.float32) * 0.009 * tt
    return np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8)


def light_map():
    q = cam.q
    masks = [
        [[q["xtv"] - 3, q["ytv"] - 3, 6], [q["xtv"] + 219.6, q["ytv"] - 3, 6], [q["xtv"] + 219.6, q["ytv"] + 126.6, 6],
         [q["xtv"] - 3, q["ytv"] + 126.6, 6]],
        [[CABINET["x0"] - 2, 0, 57], [CABINET["x1"] + 2, 0, 57], [CABINET["x1"] + 2, 92, 57], [CABINET["x0"] - 2, 92, 57]],
        [[0, 0, 60], [50, 0, 60], [50, 115, 60], [0, 115, 60]],
        [[380, 0, 50], [425, 0, 50], [425, 115, 50], [380, 115, 50]],
        [[345, 219, 3], [377, 219, 3], [377, 252, 3], [345, 252, 3]],
    ]
    return wall_light_map(masks)[0]


def render(name, M, bg):
    var = VARIANTS[name]
    cv = Canvas(bg)
    sc = Scene(var, M)
    rows = {}
    sc.occluders(cv)
    for (side, level, x0, yb, yt) in shelves():
        sc.draw_shelf(cv, x0, yb, yt)
    for (side, level, x0, yb, yt) in shelves():
        outer_left, fill = ROWS[(side, level)]
        y_ceil = D["bot_up"] if level == "jos" else None
        rows[(side, level)] = sc.draw_row(cv, x0, yt, y_ceil, outer_left, fill)
    sc.wall_shadows(cv, rows)
    return finish(cv.img, cv.touch)


def current_photo():
    """Fotografia de acum, la dimensiunea randărilor."""
    big = cv2.resize(PHOTO, (W // SS, H // SS), interpolation=cv2.INTER_LANCZOS4)
    return np.clip(big * 255 + 0.5, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    names = sys.argv[1:] or list(VARIANTS)
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    M = light_map()
    bg = np.clip(cv2.resize(PHOTO, (W, H), interpolation=cv2.INTER_LANCZOS4), 0, 1)
    cv2.imwrite(os.path.join(HERE, "out", "acum.jpg"), current_photo(), [cv2.IMWRITE_JPEG_QUALITY, 92])
    for nm in names:
        im = render(nm, M, bg)
        path = os.path.join(HERE, "out", VARIANTS[nm]["file"])
        cv2.imwrite(path, im, [cv2.IMWRITE_JPEG_QUALITY, 92])
        print("salvat", path, im.shape)
