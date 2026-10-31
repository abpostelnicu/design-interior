"""Modelul aparatului foto: cameră pinhole cu distorsiune radială k1, calibrată din segmente de dreaptă.

Coordonatele lumii sunt în cm: X de-a lungul peretelui din fața aparatului, spre dreapta; Y în sus, cu Y = 0 pe
pardoseală; Z iese din perete spre aparat, cu Z = 0 pe fața peretelui. Pixelii au originea în colțul din stânga
sus al fotografiei; unghiurile din camera.json sunt în radiani.

Calibrarea: pentru fiecare grup de segmente din `segments.json` (de exemplu „ceil”, „tv_top”) scrii o funcție
care întoarce dreapta 3D a grupului din parametrii scenei. `calibreaza` caută parametrii aparatului (f, yaw,
pitch, roll, cx, cy, cz și, la nevoie, k1) și pe cei ai scenei, astfel încât dreptele proiectate să cadă peste
segmente. Scara vine din ce e cunoscut: tavanul măsurat sau obiecte cu dimensiuni din fișa producătorului.
O eroare medie (rms) sub 1 px e bună, dar nu garantează că fiecare parametru e determinat: `profil` fixează un
parametru pe rând la mai multe valori și compară eroarea, iar `rezumat_profil` spune dacă fotografia îl determină.

Preluat din `.github/surse/polite-viniluri/camera.py` (calibrarea pe obiecte cunoscute) și din
`.github/surse/cuier-hol/camera.py` (calibrarea pe tavan): `Camera` dă exact aceleași proiecții.
"""
import json

import numpy as np

RN = 640.0                                  # raza de normalizare a distorsiunii (px), ca în proiectele existente
CAM = ("f", "yaw", "pitch", "roll", "cx", "cy", "cz")
UNGHIURI = ("yaw", "pitch", "roll")


def rot(yaw, pitch, roll):
    cy, sy = np.cos(yaw), np.sin(yaw)
    cp, sp = np.cos(pitch), np.sin(pitch)
    cr, sr = np.cos(roll), np.sin(roll)
    R0 = np.diag([1.0, -1.0, -1.0])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    Rz = np.array([[cr, -sr, 0], [sr, cr, 0], [0, 0, 1]])
    return Rz @ Rx @ Ry @ R0


class Camera:
    def __init__(self, q, scale=1.0, size=None):
        """q: parametrii, ca în camera.json; size = (lățime, înălțime) a fotografiei, în px.

        Punctul principal e q["pp"], dacă există, altfel centrul fotografiei de mărimea size (camera.json din
        proiectele vechi nu are pp). Cu scale > 1 ai aceeași cameră pentru imaginea mărită de scale ori.
        """
        self.q = dict(q)
        if "pp" in q:
            pp = np.asarray(q["pp"], float)
        elif size is not None:
            pp = np.array([size[0] / 2.0, size[1] / 2.0])
        else:
            raise ValueError("lipsește punctul principal: dă size=(lățime, înălțime) sau pune „pp” în camera.json")
        self.pp0 = pp
        self.rn = float(q.get("rn", RN))
        self.f = q["f"] * scale
        self.pp = pp * scale
        self.k1 = float(q.get("k1", 0.0))
        self.scale = scale
        self.R = rot(q["yaw"], q["pitch"], q["roll"])
        self.C = np.array([q["cx"], q["cy"], q["cz"]], float)

    def scaled(self, k):
        """Aceeași cameră pentru imaginea mărită de k ori față de fotografie."""
        q = dict(self.q)
        q["pp"] = self.pp0.tolist()
        return Camera(q, k)

    def fara_distorsiune(self):
        """Aceeași cameră, la aceeași scară, cu k1 = 0: modelul pinhole pe care îl cere randarea.

        Merge când distorsiunea e mică acolo unde desenezi piese noi. La „Cuier hol” (k1 = −0,004), pixelii se
        mută cu cel mult 2,5 px în toată fotografia și sub 0,5 px în zona cuierului; scriptul proiectului a randat
        tot așa (`distort=False`). Dacă piesele ajung spre marginile unei fotografii cu unghi larg, calibrezi
        direct cu k1 = 0 și verifici rms-ul.
        """
        q = dict(self.q, k1=0.0, pp=self.pp0.tolist())
        return Camera(q, self.scale)

    @property
    def K(self):
        return np.array([[self.f, 0, self.pp[0]], [0, self.f, self.pp[1]], [0, 0, 1.0]])

    def to_cam(self, P):
        return (self.R @ (np.atleast_2d(P) - self.C).T).T

    def project(self, P, distort=True):
        """Pixelii (N × 2) ai punctelor 3D P (N × 3, cm)."""
        Pc = self.to_cam(np.asarray(P, float))
        uv = self.f * Pc[:, :2] / Pc[:, 2:3] + self.pp
        if distort and abs(self.k1) > 1e-9:
            uv = self._distort(uv)
        return uv

    def _distort(self, uv):
        d_u = uv - self.pp
        d = d_u.copy()
        rn = self.rn * self.scale
        for _ in range(10):
            r2 = (d ** 2).sum(1, keepdims=True) / rn ** 2
            d = d_u / (1 + self.k1 * r2)
        return self.pp + d

    def undistort(self, uv):
        d = np.atleast_2d(np.asarray(uv, float)) - self.pp
        r2 = (d ** 2).sum(1, keepdims=True) / (self.rn * self.scale) ** 2
        return self.pp + d * (1 + self.k1 * r2)

    def ray(self, uv):
        u = self.undistort(np.array(uv, float))[0]
        d = self.R.T @ np.array([(u[0] - self.pp[0]) / self.f, (u[1] - self.pp[1]) / self.f, 1.0])
        return d / np.linalg.norm(d)

    def backproject(self, uv, axis, value):
        """Punctul 3D al pixelului uv pe planul axis = value; de exemplu ("Z", 0) e fața peretelui."""
        d = self.ray(uv)
        i = "XYZ".index(axis)
        t = (value - self.C[i]) / d[i]
        return self.C + t * d


def puncte(cam, uvs, axis, value):
    """backproject pentru mai mulți pixeli: un tablou N × 3, în cm."""
    return np.array([cam.backproject(uv, axis, value) for uv in uvs])


def incarca(path, scale=1.0, size=None):
    with open(path, encoding="utf-8") as f:
        return Camera(json.load(f), scale, size)


def salveaza(q, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(q, f, indent=1)


def citeste_segmente(path):
    with open(path, encoding="utf-8") as f:
        return {k: np.array(v, float).reshape(-1, 4) for k, v in json.load(f).items()}


def _reziduuri_grup(cam, a, b, arr):
    n = np.array([-(b - a)[1], (b - a)[0]])
    n /= np.linalg.norm(n)
    out = []
    for sg in arr:
        u = cam.undistort(np.linspace(sg[:2], sg[2:], 4))
        out.extend(((u - a) @ n).tolist())
    return out


def calibreaza(segmente, dreapta, p0, size, fixe=None, k1_liber=False, regularizare=None, max_nfev=40000):
    """Calibrează aparatul și parametrii scenei din segmentele de dreaptă.

    segmente: {grup: [[u0, v0, u1, v1], ...]}, în pixelii fotografiei (ca în segments.json).
    dreapta(grup, q): întoarce două puncte 3D (cm) de pe dreapta pe care stau segmentele grupului, calculate din
        parametrii q (de exemplu tavanul: ([0, q["H"], 0], [419, q["H"], 0])).
    p0: valorile de pornire. Pentru aparat: f (px), yaw, pitch, roll (radiani), cx, cy, cz (cm; poziția
        aparatului, cam la 120–170 cm înălțime și 250–400 cm de perete). Plus necunoscutele scenei folosite în
        `dreapta`. O pornire bună: f ≈ 0,75 × lățimea fotografiei, unghiurile 0.
    size: (lățime, înălțime) a fotografiei; punctul principal e în centru.
    fixe: parametrii ținuți constanți, de exemplu {"H": 270.0} pentru tavanul măsurat.
    k1_liber: calibrează și distorsiunea k1 (fotografiile cu unghi larg). Randarea cere însă k1 = 0.
    regularizare: {parametru: pondere}; trage parametrul spre 0, de exemplu {"roll": 20} ține aparatul
        orizontal când sunt puține muchii verticale (așa e calibrat „Cuier hol”). k1 are mereu ponderea 5.
    Întoarce q: toți parametrii, plus pp, rn, rms și max (px) și rms_grupuri (px, pe fiecare grup). Un grup cu
    eroare mult peste celelalte are segmente alese greșit sau o dreaptă 3D greșită.
    """
    from scipy.optimize import least_squares

    fixe = dict(fixe or {})
    regularizare = dict(regularizare or {})
    if not k1_liber:
        fixe["k1"] = 0.0
    lipsa = [k for k in CAM if k not in p0 and k not in fixe]
    if lipsa:
        raise ValueError(f"lipsesc valorile de pornire pentru {lipsa}")
    nume = [k for k in p0 if k not in fixe]
    if k1_liber and "k1" not in nume:
        nume.append("k1")
    start = np.array([float(p0.get(k, 0.0)) for k in nume])
    segs = {k: np.asarray(v, float).reshape(-1, 4) for k, v in segmente.items()}
    baza = {"pp": [size[0] / 2.0, size[1] / 2.0], "rn": RN}

    def unpack(p):
        q = dict(baza)
        q.update(zip(nume, (float(v) for v in p)))
        q.update(fixe)
        return q

    def residuals(p):
        q = unpack(p)
        cam = Camera(q)
        res = []
        for g, arr in segs.items():
            a, b = cam.project(np.asarray(dreapta(g, q), float), distort=False)
            res.extend(_reziduuri_grup(cam, a, b, arr))
        res.append(q["k1"] * 5)
        res.extend(q[k] * w for k, w in regularizare.items())
        return np.array(res)

    sol = least_squares(residuals, start, method="lm", max_nfev=max_nfev)
    q = unpack(sol.x)
    cam = Camera(q)
    r_all, per = [], {}
    for g, arr in segs.items():
        a, b = cam.project(np.asarray(dreapta(g, q), float), distort=False)
        r = np.array(_reziduuri_grup(cam, a, b, arr))
        per[g] = round(float(np.sqrt((r ** 2).mean())), 3)
        r_all.append(r)
    r_all = np.concatenate(r_all)
    q["rms"] = float(np.sqrt((r_all ** 2).mean()))
    q["max"] = float(np.abs(r_all).max())
    q["rms_grupuri"] = per
    return q


def rezumat(q):
    """Parametrii calibrării, câte unul pe rând, cu unghiurile în grade."""
    rows = []
    for k, v in q.items():
        if k in UNGHIURI:
            rows.append(f"{k:8s} {np.degrees(v):9.3f}°")
        elif isinstance(v, (int, float)):
            rows.append(f"{k:8s} {v:9.3f}")
        else:
            rows.append(f"{k:8s} {v}")
    return "\n".join(rows)


def profil(segmente, dreapta, p0, size, parametru, valori, **kw):
    """Profilul erorii: calibrează din nou cu `parametru` fixat, pe rând, la fiecare valoare din `valori`.

    Înainte să crezi un parametru liber (tavanul, poziția unui obiect), îl fixezi la mai multe valori și compari
    eroarea. Dacă rms-ul rămâne același, fotografia nu-l determină: alți parametri îl compensează (de exemplu
    obiectul cunoscut se mută față de perete), iar limitele puse parametrilor nu rezolvă asta, doar ascund
    problema. Atunci valoarea vine de la tine, măsurată. kw merg mai departe la `calibreaza` (fixe, k1_liber,
    regularizare, max_nfev). Întoarce lista calibrărilor, câte un q pentru fiecare valoare, în ordine.
    """
    fixe = dict(kw.pop("fixe", None) or {})
    return [calibreaza(segmente, dreapta, p0, size, fixe=dict(fixe, **{parametru: float(v)}), **kw) for v in valori]


def rezumat_profil(qs, parametru, arata=(), prag=0.01):
    """Tabelul profilului (valoarea, rms-ul și parametrii din `arata`) și concluzia: dacă rms-ul variază cu mai
    puțin de `prag` px, parametrul nu e determinat de fotografie."""
    def f(v, z=2):
        return f"{v:.{z}f}".replace(".", ",")

    rows = [f"{parametru:>9s} {'rms (px)':>9s}" + "".join(f" {k:>9s}" for k in arata)]
    for q in qs:
        rows.append(f"{f(q[parametru]):>9s} {f(q['rms'], 4):>9s}" + "".join(f" {f(q[k]):>9s}" for k in arata))
    rms = [q["rms"] for q in qs]
    if max(rms) - min(rms) < prag:
        rows.append(f"rms-ul variază cu doar {f(max(rms) - min(rms), 4)} px: {parametru} nu e determinat de "
                    "fotografie; îl dai tu, măsurat")
    else:
        best = qs[int(np.argmin(rms))]
        rows.append(f"rms-ul variază cu {f(max(rms) - min(rms), 3)} px; e cel mai mic la {parametru} = "
                    f"{f(best[parametru])}")
    return "\n".join(rows)
