"""Modelul aparatului foto pentru fotografia biroului din Dormitor 2, calibrat din muchiile drepte ale camerei
și ale biroului.

Coordonate (cm): X de-a lungul peretelui cu biroul (peretele exterior dinspre est), cu X = 0 în colțul din stânga
(cu peretele dinspre Dormitor 1) și pozitiv spre dreapta, adică spre fereastra de colț; Y în sus (Y = 0 pardoseala
finită); Z din perete spre aparatul foto (Z = 0 fața peretelui).

Ce se știe sigur: tavanul are 250 cm (dat de utilizator); golul ferestrei Fe-06 începe la 278,9 cm de colț
(din planul etajului: 151,45 pt × 1,8412 cm/pt); blatul Secretlab MAGNUS Pro are 150 × 70 cm.
Necunoscute: distanța focală, orientarea și poziția aparatului, plinta, capul golului ferestrei, poziția și
înălțimea biroului și pozițiile picioarelor lui.

    python camera.py          # salvează camera.json
    python camera.py liber    # lasă liberă și marginea golului ferestrei, ca verificare
    python camera.py tavan    # scanează tavanul: eroarea nu se schimbă, se mută doar biroul față de perete

Fotografia singură nu dă tavanul: cu altă înălțime, biroul se mută față de perete și eroarea rămâne aceeași.
Scara vine din tavanul dat. Modul `tavan` arată la ce tavan biroul ar sta lipit de perete, cum pare în poză.
"""
import json
import os
import sys

import numpy as np
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
PP = np.array([155.5, 277.0])
RN = 320.0

H = 250.0          # tavanul, dat de utilizator
XW = 278.9         # marginea din stânga a golului ferestrei Fe-06, din plan
WALL_L = 366.2     # peretele cu biroul, din plan: de la colț până la fața peretelui dinspre fațadă
SILL = 47.0        # parapetul ferestrei, din plan (HP = 47)
BT = 1.5           # grosimea plintei (estimată)
DESK_W, DESK_D = 150.0, 70.0

NAMES = ["f", "yaw", "pitch", "roll", "cx", "cy", "cz", "hb", "ywt", "xd", "zb", "hd",
         "lx1", "lx2", "rx1", "rx2", "xw"]
LEG_Z = DESK_D / 2  # coloanele picioarelor stau la mijlocul adâncimii blatului


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
    def __init__(self, q, scale=1.0):
        # scale > 1 dă aceeași cameră pentru o imagine mărită (randarea se face la rezoluție mai mare)
        self.q = dict(q)
        self.f = q["f"] * scale
        self.pp = PP * scale
        self.k1 = q.get("k1", 0.0)
        self.scale = scale
        self.R = rot(q["yaw"], q["pitch"], q["roll"])
        self.C = np.array([q["cx"], q["cy"], q["cz"]])

    def to_cam(self, P):
        return (self.R @ (np.atleast_2d(P) - self.C).T).T

    def project(self, P, distort=False):
        Pc = self.to_cam(P)
        return self.f * Pc[:, :2] / Pc[:, 2:3] + self.pp

    def ray(self, uv):
        u = np.asarray(uv, float)
        d = self.R.T @ np.array([(u[0] - self.pp[0]) / self.f, (u[1] - self.pp[1]) / self.f, 1.0])
        return d / np.linalg.norm(d)

    def backproject(self, uv, axis, value):
        """Punctul 3D al pixelului uv pe planul axis = value, de ex. ("Z", 0) = fața peretelui."""
        d = self.ray(uv)
        i = "XYZ".index(axis)
        t = (value - self.C[i]) / d[i]
        return self.C + t * d


def desk_points(q):
    xd, zb, hd = q["xd"], q["zb"], q["hd"]
    return {
        "FL": np.array([xd, hd, zb + DESK_D]),
        "BL": np.array([xd, hd, zb]),
        "FR": np.array([xd + DESK_W, hd, zb + DESK_D]),
        "BR": np.array([xd + DESK_W, hd, zb]),
    }


def _line3d(name, q):
    p = desk_points(q)
    xw = q["xw"]
    H = q.get("H", globals()["H"])
    return np.array({
        "ceil": ([0, H, 0], [WALL_L, H, 0]),
        "win_top": ([xw, q["ywt"], 0], [WALL_L, q["ywt"], 0]),
        "win_left": ([xw, SILL, 0], [xw, q["ywt"], 0]),
        "floor": ([0, 0, BT], [WALL_L, 0, BT]),
        "base_top": ([0, q["hb"], BT], [WALL_L, q["hb"], BT]),
        "desk_front": (p["FL"], p["FR"]),
        "desk_left": (p["BL"], p["FL"]),
        "desk_back": (p["BL"], p["BR"]),
        "leg_l1": ([q["lx1"], 0, q["zb"] + LEG_Z], [q["lx1"], q["hd"], q["zb"] + LEG_Z]),
        "leg_l2": ([q["lx2"], 0, q["zb"] + LEG_Z], [q["lx2"], q["hd"], q["zb"] + LEG_Z]),
        "leg_r1": ([q["rx1"], 0, q["zb"] + LEG_Z], [q["rx1"], q["hd"], q["zb"] + LEG_Z]),
        "leg_r2": ([q["rx2"], 0, q["zb"] + LEG_Z], [q["rx2"], q["hd"], q["zb"] + LEG_Z]),
    }[name], float)


def load_segments():
    raw = json.load(open(os.path.join(HERE, "segments.json")))
    segs = {k: np.array(v, float) for k, v in raw.items() if not k.startswith("_") and not k.startswith("pt_")}
    pts = {k[3:]: np.array(v, float) for k, v in raw.items() if k.startswith("pt_")}
    return segs, pts


def calibrate(free_xw=False):
    segs, pts = load_segments()
    names = NAMES

    def unpack(p):
        q = dict(zip(names, p))
        if not free_xw:
            q["xw"] = XW
        return q

    def residuals(p):
        q = unpack(p)
        cam = Camera(q)
        res = []
        for name, arr in segs.items():
            a, b = cam.project(_line3d(name, q))
            n = np.array([-(b - a)[1], (b - a)[0]])
            n /= np.linalg.norm(n)
            for sg in arr:
                u = np.linspace(sg[:2], sg[2:], 4)
                res.extend(((u - a) @ n).tolist())
        dp = desk_points(q)
        for k, uv in pts.items():
            res.extend((cam.project(dp[k])[0] - uv).tolist())
        return np.array(res)

    p0 = np.array([500, -0.38, 0.15, 0.0, 75.0, 140.0, 420.0, 7.0, 227.0, 150.0, 5.0, 72.0,
                   140.0, 135.0, 265.0, 268.0, XW])
    sol = least_squares(residuals, p0, method="lm", max_nfev=60000)
    r = residuals(sol.x)
    q = {k: float(v) for k, v in unpack(sol.x).items()}
    q["rms"] = float(np.sqrt((r ** 2).mean()))
    q["max"] = float(np.abs(r).max())
    return q, r


def load_camera(scale=1.0, name="camera.json"):
    return Camera(json.load(open(os.path.join(HERE, name))), scale)


def scan_ceiling(values=(230.0, 240.0, 250.0, 260.0, 270.0)):
    """Calibrează cu tavanul fixat pe rând la mai multe valori: eroarea, biroul și unde ar sta lipit de perete."""
    global H
    keep, rows = H, []
    for h in values:
        H = h
        q, _ = calibrate()
        rows.append((h, q["rms"], q["xd"], q["zb"], q["hd"]))
    H = keep
    print(" tavan   eroare   biroul: de la colț   de la perete   blatul")
    for h, rms, xd, zb, hd in rows:
        print(f"{h:6.0f} {rms:8.4f} {xd:16.1f} {zb:14.1f} {hd:9.1f}")
    hs, zs = np.array([r[0] for r in rows]), np.array([r[3] for r in rows])
    k = np.polyfit(zs, hs, 1)
    print(f"biroul lipit de perete (Z = 0) cere un tavan de ~{np.polyval(k, 0.0):.1f} cm")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "tavan":
        scan_ceiling()
        sys.exit(0)
    q, r = calibrate(free_xw=mode == "liber")
    out = "camera_xw_liber.json" if mode == "liber" else "camera.json"
    json.dump(q, open(os.path.join(HERE, out), "w"), indent=1)
    for k, v in q.items():
        print(f"{k:6s} {np.degrees(v):8.3f}°" if k in ("yaw", "pitch", "roll") else f"{k:6s} {v:9.3f}")
    cam = Camera(q)
    print("marginea din stânga a fotografiei pe perete (Y = 100):",
          np.round(cam.backproject([0, cam.project([[150, 100, 0]])[0][1]], "Z", 0), 1))
    for v in (60, 200, 340):
        print(f"  pixelul (0, {v}) pe perete:", np.round(cam.backproject([0, v], "Z", 0), 1))
