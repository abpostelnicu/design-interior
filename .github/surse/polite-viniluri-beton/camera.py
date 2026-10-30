"""Modelul aparatului foto pentru fotografia din living (peretele cu televizorul), calibrat din muchiile
drepte ale unor obiecte cu dimensiuni cunoscute.

Coordonate (cm): X de-a lungul peretelui cu televizorul (X = 0 în colțul din stânga, pozitiv spre dreapta),
Y în sus (Y = 0 pardoseala), Z din perete spre aparatul foto (Z = 0 fața peretelui).
Dimensiuni cunoscute: peretele are 419 cm lățime; televizorul TCL 98C8L 216,6 × 123,6 cm; comoda Cioata
Veneto 242 × 48 × 67 cm. Înălțimea tavanului H rămâne necunoscută, ca să se poată compara cu cea dată
de utilizator (250 cm): `python camera.py` o lasă liberă, `python camera.py 250` o fixează.
"""
import json
import os

import numpy as np
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
PP = np.array([512.0, 384.0])
RN = 640.0

WALL_W = 419.0
TV_W, TV_H = 216.6, 123.6
CAB_W, CAB_D, CAB_H = 242.0, 48.0, 67.0
BASE_T = 1.5

NAMES = ["f", "k1", "yaw", "pitch", "roll", "cx", "cy", "cz",
         "H", "hb", "ztv", "xtv", "ytv", "xc", "zc"]


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
        # scale > 1 dă aceeași cameră pentru o imagine mărită (randarea se face la 4x)
        self.q = dict(q)
        self.f = q["f"] * scale
        self.pp = PP * scale
        self.k1 = q["k1"]
        self.scale = scale
        self.R = rot(q["yaw"], q["pitch"], q["roll"])
        self.C = np.array([q["cx"], q["cy"], q["cz"]])

    def to_cam(self, P):
        return (self.R @ (np.atleast_2d(P) - self.C).T).T

    def project(self, P, distort=True):
        Pc = self.to_cam(P)
        uv = self.f * Pc[:, :2] / Pc[:, 2:3] + self.pp
        if distort and abs(self.k1) > 1e-9:
            uv = self._distort(uv)
        return uv

    def _distort(self, uv):
        d_u = uv - self.pp
        d = d_u.copy()
        rn = RN * self.scale
        for _ in range(10):
            r2 = (d ** 2).sum(1, keepdims=True) / rn ** 2
            d = d_u / (1 + self.k1 * r2)
        return self.pp + d

    def undistort(self, uv):
        d = np.atleast_2d(uv) - self.pp
        r2 = (d ** 2).sum(1, keepdims=True) / (RN * self.scale) ** 2
        return self.pp + d * (1 + self.k1 * r2)

    def ray(self, uv):
        u = self.undistort(np.array(uv, float))[0]
        d = self.R.T @ np.array([(u[0] - self.pp[0]) / self.f, (u[1] - self.pp[1]) / self.f, 1.0])
        return d / np.linalg.norm(d)

    def backproject(self, uv, axis, value):
        """Punctul 3D al pixelului uv pe planul axis = value, de ex. ("Z", 0) = fața peretelui."""
        d = self.ray(uv)
        i = "XYZ".index(axis)
        t = (value - self.C[i]) / d[i]
        return self.C + t * d


def _line3d(name, q):
    H = q["H"]
    ytt = q["ytv"] + TV_H
    xr = q["xtv"] + TV_W
    zb = q["zc"] - CAB_D
    return np.array({
        "ceil": ([0, H, 0], [WALL_W, H, 0]),
        "corner_left": ([0, 0, 0], [0, H, 0]),
        "wall_right": ([WALL_W, 0, 0], [WALL_W, H, 0]),
        "floor": ([0, 0, BASE_T], [WALL_W, 0, BASE_T]),
        "base_top": ([0, q["hb"], BASE_T], [WALL_W, q["hb"], BASE_T]),
        "tv_top": ([q["xtv"], ytt, q["ztv"]], [xr, ytt, q["ztv"]]),
        "tv_bottom": ([q["xtv"], q["ytv"], q["ztv"]], [xr, q["ytv"], q["ztv"]]),
        "tv_left": ([q["xtv"], q["ytv"], q["ztv"]], [q["xtv"], ytt, q["ztv"]]),
        "tv_right": ([xr, q["ytv"], q["ztv"]], [xr, ytt, q["ztv"]]),
        "cab_top_front": ([q["xc"], CAB_H, q["zc"]], [q["xc"] + CAB_W, CAB_H, q["zc"]]),
        "cab_top_back": ([q["xc"], CAB_H, zb], [q["xc"] + CAB_W, CAB_H, zb]),
        "cab_top_left": ([q["xc"], CAB_H, zb], [q["xc"], CAB_H, q["zc"]]),
        "cab_top_right": ([q["xc"] + CAB_W, CAB_H, zb], [q["xc"] + CAB_W, CAB_H, q["zc"]]),
        "cab_right": ([q["xc"] + CAB_W, 20, q["zc"]], [q["xc"] + CAB_W, CAB_H, q["zc"]]),
        "cab_left": ([q["xc"], 20, q["zc"]], [q["xc"], CAB_H, q["zc"]]),
    }[name], float)


def calibrate(fix_H=None, free_k1=False):
    segs = {k: np.array(v, float) for k, v in json.load(open(os.path.join(HERE, "segments.json"))).items()}

    # fără H fixat, scara vine doar din peretele, televizorul și comoda cunoscute
    def unpack(p):
        q = dict(zip(NAMES, p))
        if fix_H is not None:
            q["H"] = fix_H
        if not free_k1:
            q["k1"] = 0.0
        return q

    def residuals(p):
        q = unpack(p)
        cam = Camera(q)
        res = []
        for name, arr in segs.items():
            a, b = cam.project(_line3d(name, q), distort=False)
            n = np.array([-(b - a)[1], (b - a)[0]])
            n /= np.linalg.norm(n)
            for sg in arr:
                u = cam.undistort(np.linspace(sg[:2], sg[2:], 4))
                res.extend(((u - a) @ n).tolist())
        res.append(q["k1"] * 5)
        return np.array(res)

    p0 = np.array([780, 0.0, 0.0, 0.0, 0.0, 208.0, 97.0, 365.0,
                   262.0, 8.0, 6.0, 99.0, 84.5, 88.0, 50.0])
    sol = least_squares(residuals, p0, method="lm", max_nfev=40000)
    r = residuals(sol.x)[:-1]
    q = unpack(sol.x)
    q = {k: float(v) for k, v in q.items()}
    q["rms"] = float(np.sqrt((r ** 2).mean()))
    q["max"] = float(np.abs(r).max())
    return q


def load_camera(scale=1.0, name="camera.json"):
    return Camera(json.load(open(os.path.join(HERE, name))), scale)


if __name__ == "__main__":
    import sys
    fix = float(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] != "free" else None
    q = calibrate(fix)
    out = "camera.json" if fix is None else f"camera_H{int(fix)}.json"
    json.dump(q, open(os.path.join(HERE, out), "w"), indent=1)
    for k, v in q.items():
        print(f"{k:6s} {np.degrees(v):8.3f}°" if k in ("yaw", "pitch", "roll") else f"{k:6s} {v:9.3f}")
