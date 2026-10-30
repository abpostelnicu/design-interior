"""Randarea în fotografie: fețe plane texturate, desenate cu buffer de adâncime peste fotografia calibrată.

Fiecare față se calculează pixel cu pixel: raza din aparat se intersectează cu planul feței. Ce acoperă ce se
rezolvă cu bufferul de adâncime, nu cu ordinea de desenare. Obiectele din fotografie care stau în fața celor
noi (de exemplu boxele) le desenezi doar în buffer, cu color=None.

Tiparul, ca în `.github/surse/polite-viniluri/`:

    cam1 = camera.incarca("camera.json", size=(1024, 768))   # camera fotografiei
    photo = foto.citeste("original.jpg")                      # BGR, 0…1
    cv = Canvas.din_foto(photo, cam1, out=2, ss=2)            # se calculează la 4x și se micșorează la 2x
    M = wall_light_map(photo, cam1, perete, masti, size=(cv.W, cv.H))[0]
    cv.face(O, eu, ev, wu, hv, culoare)                       # un dreptunghi 3D, în cm
    box(cv, (x0, x1), (y0, y1), (z0, z1), lambda n: solid(STEJAR, M, SHADE[n]))
    save_jpg("out/propunere_A_stejar.jpg", finish(cv.img, cv.touch, cv.ss))

Preluat din `polite-viniluri/core.py` și `polite-viniluri/render.py`; aceleași formule, fără variabile globale.
"""
import cv2
import numpy as np

# lumina vine din față (ferestrele din spatele aparatului): factorul de umbrire pe direcția normalei
SHADE = {(0, 0, 1): 1.0, (1, 0, 0): 0.74, (-1, 0, 0): 0.70, (0, -1, 0): 0.56, (0, 1, 0): 1.04, (0, 0, -1): 0.5}
BLACK = np.array([0.072, 0.070, 0.068], np.float32)   # oțel vopsit negru mat (BGR)


def proj(cam, P):
    return cam.project(np.atleast_2d(np.asarray(P, float)), distort=False)


class Canvas:
    def __init__(self, bg, cam, ss=1):
        """bg: fundalul (BGR, 0…1) la rezoluția de lucru; cam: camera la aceeași rezoluție (cam1.scaled(k))."""
        if abs(cam.k1) > 1e-6:
            raise ValueError("randarea nu ține cont de distorsiunea k1: calibrează camera cu k1 = 0 sau, dacă "
                             "distorsiunea e mică în zona pieselor, folosește cam.fara_distorsiune()")
        self.img = bg.astype(np.float32).copy()
        self.z = np.full(bg.shape[:2], np.inf, np.float32)
        self.touch = np.zeros(bg.shape[:2], np.float32)
        self.cam = cam
        self.H, self.W = bg.shape[:2]
        self.ss = ss
        self._m = cam.R.T @ np.linalg.inv(cam.K)

    @classmethod
    def din_foto(cls, photo, cam1, out=2, ss=2):
        """Pânza la out × ss ori fotografia (implicit 4x); finish o micșorează cu ss, deci rezultatul e la out x."""
        rs = out * ss
        bg = np.clip(cv2.resize(photo, (photo.shape[1] * rs, photo.shape[0] * rs),
                                interpolation=cv2.INTER_LANCZOS4), 0, 1)
        return cls(bg, cam1.scaled(rs), ss)

    def _rays(self, x0, x1, y0, y1):
        us, vs = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        pix = np.stack([us, vs, np.ones_like(us)], -1)
        return pix @ self._m.T

    def _bbox(self, corners, pad):
        pc = proj(self.cam, corners)
        x0 = int(max(np.floor(pc[:, 0].min()) - pad, 0))
        x1 = int(min(np.ceil(pc[:, 0].max()) + pad, self.W))
        y0 = int(max(np.floor(pc[:, 1].min()) - pad, 0))
        y1 = int(min(np.ceil(pc[:, 1].max()) + pad, self.H))
        return x0, x1, y0, y1

    def face(self, O, eu, ev, wu, hv, color, pad=2):
        """Dreptunghiul plan O + s*eu + t*ev (0 <= s <= wu, 0 <= t <= hv), în cm.

        color(s, t, X, yy, xx) întoarce culorile (h, w, 3) pentru pixelii feței; s, t în cm, X punctele 3D,
        yy/xx indicii pixelilor. Scrie doar unde fața e cea mai apropiată suprafață de până acum. Cu color=None,
        fața doar ascunde ce e în spatele ei, fără să schimbe pixelii.
        """
        cam = self.cam
        O, eu, ev = (np.asarray(v, float) for v in (O, eu, ev))
        n = np.cross(eu, ev)
        ctr = O + 0.5 * wu * eu + 0.5 * hv * ev
        if n @ (cam.C - ctr) < 0:
            n = -n
        if n @ (cam.C - ctr) <= 1e-9:
            return
        corners = np.array([O, O + wu * eu, O + wu * eu + hv * ev, O + hv * ev])
        x0, x1, y0, y1 = self._bbox(corners, pad)
        if x1 <= x0 or y1 <= y0:
            return
        d = self._rays(x0, x1, y0, y1)
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

    def _multiply(self, fac, sl):
        free = ~np.isfinite(self.z[sl])
        fac = np.where(free, fac, 1.0).astype(np.float32)
        self.img[sl] *= fac[..., None]
        self.touch[sl] = np.maximum(self.touch[sl], (np.abs(fac - 1) > 0.004).astype(np.float32))

    def multiply_wall(self, fac_fn, X0, X1, Y0, Y1, z=0.0):
        """Umbre pe perete: înmulțește fundalul cu fac_fn(X, Y), doar unde nu l-au acoperit fețele noi."""
        corners = np.array([[X0, Y0, z], [X1, Y0, z], [X1, Y1, z], [X0, Y1, z]], float)
        x0, x1, y0, y1 = self._bbox(corners, 2)
        if x1 <= x0 or y1 <= y0:
            return
        d = self._rays(x0, x1, y0, y1)
        tt = (z - self.cam.C[2]) / d[..., 2]
        X = self.cam.C + d * tt[..., None]
        self._multiply(fac_fn(X[..., 0], X[..., 1]), (slice(y0, y1), slice(x0, x1)))

    def multiply_floor(self, fac_fn, X0, X1, Z0, Z1, y=0.0):
        """Umbre pe pardoseală: înmulțește fundalul cu fac_fn(X, Z) pe planul Y = y."""
        corners = np.array([[X0, y, Z0], [X1, y, Z0], [X1, y, Z1], [X0, y, Z1]], float)
        x0, x1, y0, y1 = self._bbox(corners, 2)
        if x1 <= x0 or y1 <= y0:
            return
        d = self._rays(x0, x1, y0, y1)
        with np.errstate(divide="ignore", invalid="ignore"):
            tt = (y - self.cam.C[1]) / d[..., 1]
        X = self.cam.C + d * tt[..., None]
        fac = np.where(tt > 0, fac_fn(X[..., 0], X[..., 2]), 1.0)
        self._multiply(fac, (slice(y0, y1), slice(x0, x1)))


def solid(bgr, M=None, shade=1.0):
    """Culoare uniformă (BGR, 0…1) pentru Canvas.face, înmulțită cu lumina M[yy, xx] (dacă e dată) și cu shade."""
    c = np.asarray(bgr, np.float32) * shade

    def color(s, t, X, yy, xx):
        f = M[yy, xx][..., None] if M is not None else 1.0
        return np.broadcast_to(c * f, s.shape + (3,)).astype(np.float32)
    return color


def box(cv, xs, ys, zs, colors):
    """Cutie cu muchiile pe axe: xs = (x0, x1), ys = (y0, y1), zs = (z0, z1), în cm.

    colors(n) dă funcția de culoare pentru fața cu normala exterioară n, de exemplu (0, 0, 1) pentru fața din
    față; None o desenează doar în bufferul de adâncime. Se desenează doar fețele întoarse spre aparat.
    """
    (x0, x1), (y0, y1), (z0, z1) = xs, ys, zs
    ex, ey, ez = np.eye(3)
    faces = [((0, 0, 1), (x0, y0, z1), ex, ey, x1 - x0, y1 - y0),
             ((0, 0, -1), (x0, y0, z0), ex, ey, x1 - x0, y1 - y0),
             ((1, 0, 0), (x1, y0, z0), ez, ey, z1 - z0, y1 - y0),
             ((-1, 0, 0), (x0, y0, z0), ez, ey, z1 - z0, y1 - y0),
             ((0, 1, 0), (x0, y1, z0), ex, ez, x1 - x0, z1 - z0),
             ((0, -1, 0), (x0, y0, z0), ex, ez, x1 - x0, z1 - z0)]
    for n, O, eu, ev, wu, hv in faces:
        ctr = np.asarray(O, float) + 0.5 * wu * eu + 0.5 * hv * ev
        if np.dot(n, cv.cam.C - ctr) > 1e-9:
            cv.face(O, eu, ev, wu, hv, colors(n))


def wall_light_map(photo, cam1, wall, masks=(), sigma=10, exclude_px=(), size=None):
    """Lumina peretelui din fotografie, netezită și raportată la mediana ei.

    wall: poligonul 3D (cm) al peretelui liber; masks: poligoane 3D scoase din calcul (obiectele din fața
    peretelui: televizorul, mobila, boxele); exclude_px: dreptunghiuri (x0, y0, x1, y1) în pixelii fotografiei,
    scoase și ele (de exemplu golul unei uși); size: (W, H) la care întorci harta, de obicei (cv.W, cv.H).
    Întoarce (M, ref): M = 1 la luminozitatea mediană a peretelui; înmulțești culorile pieselor noi cu M.
    """
    L = cv2.cvtColor(photo.astype(np.float32), cv2.COLOR_BGR2GRAY)
    m = np.zeros(L.shape, np.float32)
    cv2.fillPoly(m, [np.round(proj(cam1, wall)).astype(np.int32)], 1.0)
    for poly in masks:
        cv2.fillPoly(m, [np.round(proj(cam1, poly)).astype(np.int32)], 0.0)
    for (x0, y0, x1, y1) in exclude_px:
        m[y0:y1, x0:x1] = 0
    num = cv2.GaussianBlur(L * m, (0, 0), sigma)
    den = cv2.GaussianBlur(m, (0, 0), sigma)
    Lw = num / np.maximum(den, 1e-4)
    ref = float(np.median(Lw[m > 0.5]))
    M = np.clip(Lw / ref, 0.55, 1.6)
    M[den < 0.02] = 1.0
    if size is not None:
        M = cv2.resize(M, tuple(size), interpolation=cv2.INTER_CUBIC)
    return M.astype(np.float32), ref


def tone(x, k=0.82):
    """Compresie blândă a luminilor, ca lemnul deschis luminat să nu se ardă."""
    return np.where(x < k, x, k + (1 - k) * (1 - np.exp(-(x - k) / (1 - k))))


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def finish(img, touch, ss=2, seed=7, noise=0.009):
    """Integrează piesele în fotografie: estompare fină pe ce s-a desenat, micșorare cu ss și zgomot fin."""
    rng = np.random.RandomState(seed)
    H, W = img.shape[:2]
    t = cv2.GaussianBlur(touch, (0, 0), 1.5)[..., None]
    soft = cv2.GaussianBlur(img, (0, 0), 0.8 * ss)
    img = img * (1 - t) + soft * t
    out = cv2.resize(img, (W // ss, H // ss), interpolation=cv2.INTER_AREA)
    tt = cv2.resize(t[..., 0], (W // ss, H // ss), interpolation=cv2.INTER_AREA)[..., None]
    soft2 = cv2.GaussianBlur(out, (0, 0), 0.7)
    out = out * (1 - tt) + soft2 * tt
    out = out + rng.randn(*out.shape[:2], 1).astype(np.float32) * noise * tt
    return np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8)


def current_photo(photo, out=2):
    """Fotografia de acum, la mărimea randărilor (out x), pentru panoul „Acum” din comparație."""
    big = cv2.resize(photo, (photo.shape[1] * out, photo.shape[0] * out), interpolation=cv2.INTER_LANCZOS4)
    return np.clip(big * 255 + 0.5, 0, 255).astype(np.uint8)


def save_jpg(path, img_u8, quality=92):
    """JPEG fără metadate (OpenCV nu scrie EXIF)."""
    if not cv2.imwrite(path, img_u8, [cv2.IMWRITE_JPEG_QUALITY, quality]):
        raise OSError(f"nu pot scrie {path}")
    return path
