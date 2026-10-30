"""Randează polițele pentru viniluri din microciment și stejar în fotografia din living, în dreapta televizorului.

Aceleași 2 polițe flotante ca în „Polite viniluri”, prinse direct în perete pe tije ascunse, dar orizontalele
sunt din microciment (beton decorativ) pe miez de placaj de mesteacăn, iar între ele stă verticala din stejar
masiv din design.verticals(). Discurile stau în picioare, pe rândurile din design.row_extents(): la capetele libere au
opritoare L îmbrăcate în stejar, iar capătul sprijinit într-o verticală nu are opritor. Muchiile microcimentului
sunt rotunjite cu raza D["edge_r"]; verticala stă pe polița de jos și se oprește sub cea de sus, la rostul de
umbră D["vert_gap"] (capătul ei de sus vine din design.verticals()).
A: microciment gri. B: microciment antracit, ca fronturile comodei. Stejarul și discurile sunt aceleași în A și B.
"""
import os
import sys

import cv2
import numpy as np

from beton import concrete_edge, concrete_end, concrete_panel
from core import Canvas, H, HERE, PHOTO, SS, W, cam, wall_light_map
from design import CABINET, D, LP, SITE, TOWER, row_extents, shelves, verticals
from materials import R_OAK, SPINE_COLORS, SPINE_P, end_grain, glued_panel, sample

VARIANTS = {
    "A": dict(ton="gri", file="propunere_A_beton_gri.jpg"),
    "B": dict(ton="antracit", file="varianta_B_beton_antracit.jpg"),
}
# La scara randării, estomparea din finish() stinge urmele fine și norii slabi ai microcimentului, iar cantul
# arăta vopsit. Pe fețele care se văd se întărește doar variația de luminanță; media tonului rămâne aceeași, și pe
# porțiunea care se vede (fit_mean). B urmează fronturile comodei, A rămâne discretă. Cantul și capetele sunt fâșii
# tăiate dintr-un panou lat, ca urmele de gletieră să le traverseze curbe.
CONCRETE_GAIN = {
    "antracit": dict(cloud=1.5, trowel=1.5, vein=3.0, vein_w=1.4, vein_p=2.2, pass_area=0.35),
    "gri": dict(cloud=1.4, trowel=1.4, vein=3.0, vein_w=1.6, vein_p=2.2, pass_area=0.6),
}
# dedesubtul se vede razant și în umbră, unde aceeași variație relativă abia s-ar mai vedea; privite razant,
# norii și urmele de gletieră ies chiar mai mult în evidență, așa că acolo sunt puțin mai tari
UNDER_GAIN = dict(cloud=1.5, trowel=1.5, vein=1.3)
CONCRETE_CUT = 24.0     # cm, lățimea panoului din care se taie cantul și capetele
# lumina vine din față (ferestrele din spatele aparatului): factorul de umbrire pe direcția normalei
SHADE = {(0, 0, 1): 1.0, (1, 0, 0): 0.74, (-1, 0, 0): 0.70, (0, -1, 0): 0.56, (0, 1, 0): 1.04}
REC_BACK = 0.7                                         # discurile stau la 7 mm de perete
# copertele de la capetele rândurilor, BGR: alb, gri, antracit, albastru-gri, bleumarin, verde închis.
# Fără maro, galben sau roșu închis, ca să nu se confunde cu stejarul opritoarelor și al verticalei
COVER_COLORS = np.array([(226, 226, 222), (205, 207, 208), (52, 50, 54), (150, 122, 104), (96, 58, 36),
                         (120, 130, 92)], np.float32) / 255.0
REC_FRONT = REC_BACK + LP["size"]
GUARD_Y = TOWER["h"] + 1.5                             # sub capacul boxelor nu se pun umbre pe perete


def tone(x):
    """Compresie blândă a luminilor, ca stejarul luminat să nu se ardă."""
    k = 0.82
    return np.where(x < k, x, k + (1 - k) * (1 - np.exp(-(x - k) / (1 - k))))


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def gap(Xc, a, b):
    """Distanța (cm) de la coordonata Xc până la intervalul [a, b]; 0 în interior."""
    return np.maximum(np.maximum(a - Xc, Xc - b), 0)


def shelf_above(xa, xb, y):
    """Cota feței de jos a celei mai apropiate polițe de deasupra lui y, care acoperă intervalul [xa, xb]."""
    return min(yb for (_, _, x0, yb, _) in shelves() if yb >= y - 1e-6 and x0 <= xa and xb <= x0 + D["L"])


def fit_mean(tex, off, size):
    """Textura cu media porțiunii eșantionate (off, size, în cm) egală cu media întregii texturi, adică tonul.

    Cu norii mai puternici, porțiunea care se vede ar ieși altfel puțin mai deschisă sau mai închisă decât tonul.
    """
    r0, c0 = (int(round(v * R_OAK)) for v in off)
    h, w = (int(round(v * R_OAK)) for v in size)
    win = tex[r0:r0 + h, c0:c0 + w].reshape(-1, 3).mean(0)
    return np.clip(tex * (tex.reshape(-1, 3).mean(0) / win), 0, 1).astype(np.float32)


class Scene:
    def __init__(self, var, M, seed=11):
        self.var = var
        # polițele ies 33 cm din perete: urmează lumina peretelui doar în parte
        self.M = (1 + 0.45 * (M - 1)).astype(np.float32)
        self.rng = np.random.RandomState(seed)          # texturile de microciment
        self.rng_oak = np.random.RandomState(seed + 1)  # stejarul verticalelor și al opritoarelor (același în A și B)
        self.rng_rec = np.random.RandomState(seed + 2)  # discurile (aceleași în A și B)
        self.verts = verticals()

    def tex_color(self, tex, grain_u, n, off, ao=None, dims=None, edge=0.10):
        """Culoarea unei fețe: textura × lumina peretelui × orientarea față de lumină × ocluzia ao(X)."""
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
                f = f * (1 + edge * np.exp(-e / 0.15))
            return tone(c * f[..., None])
        return color

    # ---------------------------------------------------------------- polița din microciment
    def draw_shelf(self, cv, x0, yb, yt):
        L, P, T = D["L"], D["P"], D["T"]
        rng, ton = self.rng, self.var["ton"]
        # 20 cm în plus la lungime: eșantionarea se deplasează cu până la 20 cm, iar microcimentul nu trebuie
        # să se repete în oglindă
        gain = CONCRETE_GAIN[ton]
        # panoul e pentru dedesubt și pentru fața de sus, care nu se vede din aparat
        face = concrete_panel(L + 22, P + 2, rng, ton, {k: v * UNDER_GAIN.get(k, 1.0) for k, v in gain.items()})
        edge = concrete_edge(L + 22, T + 2, rng, ton, gain, along=False, cut_cm=CONCRETE_CUT)
        endg = concrete_end(T, P, rng, ton, gain, cut_cm=CONCRETE_CUT)
        # deplasările eșantionării: cantul, dedesubtul și fața de sus; pe porțiunile văzute media rămâne tonul
        oe, ou, ot = (rng.uniform(0, 20) for _ in range(3))
        edge = fit_mean(edge, (oe, 0.5), (L, T))
        face_u, face_t = fit_mean(face, (ou, 0.5), (L, P)), fit_mean(face, (ot, 0.5), (L, P))
        # verticalele care stau pe fața de sus (la polița de jos) și cele care se opresc sub fața de jos
        # (la polița de sus), cu rostul de umbră dintre ele și poliță
        under = [v for v in self.verts if abs(shelf_above(v[0], v[1], v[3]) - yb) < 0.05]
        over = [v for v in self.verts if abs(v[2] - yt) < 0.05]
        r = D["edge_r"]
        x1 = x0 + L

        def ao_wall(X):
            return 1 - 0.38 * np.exp(-np.clip(X[..., 2], 0, None) / 3.5)

        def ao_verts(vs, soft, slot):
            """Colțul cu peretele și cu fiecare verticală; soft = umbra largă de lângă ea, slot = rostul de sus."""
            def f(X):
                a = ao_wall(X)
                for (xa, xb, _, y1, dep) in vs:
                    dx = gap(X[..., 0], xa, xb)
                    a = a * (1 - (0.38 * np.exp(-dx / 1.8) + soft * np.exp(-dx / 7.0)) * (X[..., 2] <= dep + 0.3))
                    if slot and yb - y1 > 0:
                        # deasupra verticalei, în rostul de umbră de câțiva milimetri, lumina abia intră
                        a = a * (1 - 0.55 * ((dx <= 0) & (X[..., 2] <= dep)))
                return a
            return f

        def rounded(n, borders, ao=None, notch=()):
            """Muchiile rotunjite cu raza r: în banda de lățime r, lumina trece moale spre cea a feței vecine.

            borders = [(axa, cota muchiei, normala feței vecine)]; latura lipită de perete rămâne dreaptă.
            notch = [(xa, xb, axa, cota)]: sub verticală sau deasupra ei, rotunjirea muchiei rămâne în umbră.
            """
            sh = SHADE[n]

            def f(X):
                a = np.ones(X.shape[:-1], np.float32) if ao is None else ao(X)
                for ax, c, nb in borders:
                    w = np.clip(1 - np.abs(X[..., ax] - c) / r, 0, 1) ** 2
                    a = a * (1 + (SHADE[nb] / sh - 1) * 0.5 * w)
                for (xa, xb, ax, c) in notch:
                    w = np.clip(1 - np.abs(X[..., ax] - c) / r, 0, 1) ** 2
                    a = a * (1 - 0.45 * w * (gap(X[..., 0], xa, xb) <= 0))
                return a
            return f

        ends = [(0, x0, (-1, 0, 0)), (0, x1, (1, 0, 0))]
        notch = [(v[0], v[1], 1, yt) for v in over] + [(v[0], v[1], 1, yb) for v in under]
        cv.face([x0, yb, P], [1, 0, 0], [0, 1, 0], L, T,
                self.tex_color(edge, True, (0, 0, 1), (oe, 0.5),
                               rounded((0, 0, 1), [(1, yb, (0, -1, 0)), (1, yt, (0, 1, 0))] + ends, notch=notch)))
        cv.face([x0, yb, 0], [1, 0, 0], [0, 0, 1], L, P,
                self.tex_color(face_u, True, (0, -1, 0), (ou, 0.5),
                               rounded((0, -1, 0), [(2, P, (0, 0, 1))] + ends, ao_verts(under, 0.0, True))))
        # fața de sus nu se vede din aparat (e mai jos decât polițele), dar umbra verticalei e pusă și aici
        cv.face([x0, yt, 0], [1, 0, 0], [0, 0, 1], L, P,
                self.tex_color(face_t, True, (0, 1, 0), (ot, 0.5),
                               rounded((0, 1, 0), [(2, P, (0, 0, 1))] + ends, ao_verts(over, 0.12, False))))
        for xe, n in ((x0, (-1, 0, 0)), (x1, (1, 0, 0))):
            cv.face([xe, yb, 0], [0, 1, 0], [0, 0, 1], T, P,
                    self.tex_color(endg, False, n, (0.0, 0.0),
                                   rounded(n, [(2, P, (0, 0, 1)), (1, yb, (0, -1, 0)), (1, yt, (0, 1, 0))], ao_wall)))

    # ---------------------------------------------------------------- verticala din stejar
    def draw_vertical(self, cv, xa, xb, y0, y1, dep):
        """Verticala din stejar masiv dintre polițe, pe toată adâncimea, cu fibra în sus.

        Se desenează fața din față și fața laterală care se vede din aparat. Jos, piesa intră în polița de jos;
        sus, între ea și polița de sus rămâne rostul de umbră D["vert_gap"].
        """
        rng = self.rng_oak
        ys = shelf_above(xa, xb, y1)        # fața de jos a poliței de sus; între ea și verticală e rostul de umbră
        t, h = xb - xa, y1 - y0
        edge = glued_panel(h + 2, t + 2, rng, lam=(t + 1.0, t + 1.5), tone=0.03)   # cantul: o singură lamelă
        face = glued_panel(h + 2, dep + 2, rng, lam=(6.0, 10.0), tone=0.035)     # lamele de 6–10 cm, încleiate
        side = 1 if cam.C[0] > xb else -1
        xs = xb if side > 0 else xa

        def seam(y):
            # jos, îmbinarea cu polița de jos, cu muchia ei rotunjită; sus, umbra din rostul de sub polița de sus
            dn, up = np.maximum(y - y0, 0), np.maximum(y1 - y, 0)
            return (1 - 0.50 * np.exp(-dn / 0.14)) * (1 - 0.30 * np.exp(-up / 0.10))

        def ao_front(X):
            e = np.maximum(np.minimum(X[..., 0] - xa, xb - X[..., 0]), 0)
            return seam(X[..., 1]) * (1 + 0.10 * np.exp(-e / 0.15))       # muchiile verticale, rotunjite

        def ao_side(X):
            y, z = X[..., 1], X[..., 2]
            up, dn = np.maximum(ys - y, 0), np.maximum(y - y0, 0)
            f = 1 - 0.38 * np.exp(-np.clip(z, 0, None) / 3.5)                       # colțul cu peretele
            f = f * (1 - 0.30 * np.exp(-up / 7.0))                                    # umbra poliței de sus
            f = f * (1 - 0.36 * np.exp(-up / 2.0)) * (1 - 0.36 * np.exp(-dn / 2.0))   # colțurile cu polițele
            return f * seam(y) * (1 + 0.10 * np.exp(-np.maximum(dep - z, 0) / 0.15))  # muchia din față

        cv.face([xa, y0, dep], [1, 0, 0], [0, 1, 0], t, h,
                self.tex_color(edge, False, (0, 0, 1), (rng.uniform(0, 1), 0.5), ao_front))
        cv.face([xs, y0, 0], [0, 0, 1], [0, 1, 0], dep, h,
                self.tex_color(face, False, (side, 0, 0), (rng.uniform(0, 1), 0.5), ao_side))

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
    def draw_row(self, cv, xa, xb, stops, yt, y_ceil):
        """Un rând de discuri de la xa la xb; stops = (opritor în stânga, opritor în dreapta).

        Capătul fără opritor e sprijinit într-o verticală, așa că discurile umplu exact rândul.
        """
        rng = self.rng_rec
        length = xb - xa
        thick = []
        while sum(thick) < length:
            thick.append(float(rng.choice([0.32, 0.36, 0.42, 0.5, 0.62, 0.8, 1.05],
                                          p=[0.2, 0.22, 0.2, 0.14, 0.12, 0.08, 0.04])))
        if len(thick) > 1 and sum(thick) - length > thick[-1] / 2:
            thick.pop()
        # grosimile se potrivesc cu câteva procente, ca rândul să nu intre în verticală sau în opritor
        k = length / sum(thick)
        thick = [w * k for w in thick]
        x = xa
        recs = []
        for w in thick:
            h = LP["size"] + float(rng.choice([0.0, 0.0, 0.0, 0.2, -0.3]))
            zf = REC_FRONT + abs(rng.randn()) * 0.3 + (0.5 if rng.rand() < 0.06 else 0.0)
            col = np.clip(SPINE_COLORS[rng.choice(len(SPINE_COLORS), p=SPINE_P)] * (1 + 0.06 * rng.randn(3)), 0, 1)
            recs.append((x, w, h, zf, col))
            x += w
        # fața verticalei de care se sprijină rândul face un colț cu cotoarele
        walls = [xe for xe, stop in ((xa, stops[0]), (xb, stops[1])) if not stop]
        for (xr, w, h, zf, col) in recs:
            self.spine(cv, xr, w, h, zf, col, yt, y_ceil, walls)
        # coperta de la capăt se vede doar lângă un opritor (deasupra și în spatele lui) și doar spre aparat
        for (xr, w, h, zf, col), side, stop in ((recs[0], -1, stops[0]), (recs[-1], 1, stops[1])):
            xe = xr if side < 0 else xr + w
            if stop and (cam.C[0] - xe) * side > 0:
                self.cover(cv, xe, side, h, zf, col, yt, y_ceil)
        bt = D["bookend_a"]
        if stops[0]:
            self.bookend(cv, xa - bt, yt)
        if stops[1]:
            self.bookend(cv, xb, yt)
        return xa, xb

    def spine(self, cv, xr, w, h, zf, col, yt, y_ceil, walls=()):
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
            for xw in walls:
                f = f * (1 - 0.22 * np.exp(-np.abs(X[..., 0] - xw) / 0.8))  # colțul cu verticala
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

        # fondul și motivul au culori care nu se confundă cu stejarul (fără maro și galben)
        i1 = rng.randint(len(COVER_COLORS))
        i2 = (i1 + 1 + rng.randint(len(COVER_COLORS) - 1)) % len(COVER_COLORS)
        c1, c2 = mute(COVER_COLORS[i1], 0.7), mute(COVER_COLORS[i2], 0.8)
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

    def bookend(self, cv, xa, yt):
        """Opritor L îmbrăcat în stejar: placa de 2 cm acoperă oțelul, x = xa … xa + grosime.

        Talpa de oțel stă sub discuri și nu se vede.
        """
        bh, bt, bd = D["bookend_h"], D["bookend_a"], D["oak_d"]
        z1 = REC_FRONT - 1.0
        z0 = z1 - bd
        side = 1 if cam.C[0] > xa + bt else -1   # fața laterală care se vede din aparat
        n = (side, 0, 0)
        rng = self.rng_oak
        tex = glued_panel(bh + 2, bd + 2, rng, lam=(bd + 1, bd + 1.5), tone=0.03)   # o singură lamelă, fibra în sus
        endg = end_grain(bt, bd, rng)
        cv.face([xa, yt, z1], [1, 0, 0], [0, 1, 0], bt, bh,
                self.tex_color(tex, False, (0, 0, 1), (0.5, rng.uniform(0, 1)), None, dims=(bt, bh)))
        cv.face([xa, yt + bh, z0], [0, 0, 1], [1, 0, 0], bd, bt, self.tex_color(endg, True, (0, 1, 0), (0.0, 0.0)))
        xe = xa + bt if side > 0 else xa
        cv.face([xe, yt, z0], [0, 0, 1], [0, 1, 0], bd, bh,
                self.tex_color(tex, False, n, (0.5, 0.5), lambda X: 1 - 0.15 * np.exp(-(X[..., 1] - yt) / 2.0)))

    # ---------------------------------------------------------------- umbrele pe perete
    def wall_shadows(self, cv, rows):
        L = D["L"]
        for (side, level, x0, yb, yt) in shelves():
            x1 = x0 + L

            def fac(Xw, Yw, x0=x0, x1=x1, yb=yb, yt=yt, rr=rows[level]):
                sx = np.exp(-gap(Xw, x0, x1) / 5.0)
                d_below = np.maximum(yb - Yw, 0)
                d_above = np.maximum(Yw - yt, 0)
                # în dreptul grosimii poliței (yb … yt), dincolo de capete, se aplică ambele: umbra capătului
                below = (0.30 * np.exp(-d_below / 2.5) + 0.17 * np.exp(-d_below / 13.0)) * sx * (Yw <= yt)
                above = 0.20 * np.exp(-d_above / 1.6) * sx * (Yw >= yb)
                # discurile sunt lipite de perete: ocluzie deasupra lor și pe laturi
                top = yt + LP["size"]
                rec = np.zeros_like(Xw)
                for (ra, rb) in rr:
                    rec = np.maximum(rec, 0.22 * np.exp(-np.hypot(gap(Xw, ra, rb), np.maximum(Yw - top, 0)) / 1.8))
                dark = np.clip(below + above + rec * (Yw >= yt), 0, 0.6)
                dark = dark * smooth((Yw - GUARD_Y) / 5.0)
                return 1 - dark
            cv.multiply_wall(fac, max(x0 - 20, 0.0), min(x1 + 20, SITE["wall_w"] - 0.1), max(yb - 45, 0), yt + 40)
        # verticalele sunt lipite de perete pe toată înălțimea: colțul cu peretele și o umbră largă, slabă,
        # de o parte și de alta (lumina vine din față, ca la polițe)
        for (xa, xb, y0, y1, dep) in self.verts:
            def fac(Xw, Yw, xa=xa, xb=xb, y0=y0, y1=y1):
                dx = gap(Xw, xa, xb)
                between = smooth((Yw - y0) / 0.6) * smooth((y1 - Yw) / 0.6)
                dark = (0.24 * np.exp(-dx / 1.8) + 0.10 * np.exp(-dx / 7.0)) * between
                return 1 - dark * smooth((Yw - GUARD_Y) / 5.0)
            cv.multiply_wall(fac, max(xa - 25, 0.0), min(xb + 25, SITE["wall_w"] - 0.1), y0, y1)


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
    sc.occluders(cv)
    for (side, level, x0, yb, yt) in shelves():
        sc.draw_shelf(cv, x0, yb, yt)
    for v in sc.verts:
        sc.draw_vertical(cv, *v)
    rows = {}
    for (side, level, x0, yb, yt) in shelves():
        y_ceil = D["bot_up"] if level == "jos" else None
        rows[level] = [sc.draw_row(cv, xa, xb, (sl, sr), yt, y_ceil) for (xa, xb, sl, sr) in row_extents(level, x0)]
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
