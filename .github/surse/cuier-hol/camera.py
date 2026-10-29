"""Camera model of the hall photo, calibrated from straight room edges.

World frame (cm): X along the back wall (positive right, X=0 at the right corner),
Y up (Y=0 floor), Z out of the back wall towards the camera (Z=0 back wall plane).
The absolute scale comes from an assumed ceiling height H.
"""
import json
import os

import numpy as np
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
PP = np.array([384.0, 512.0])
RN = 640.0

NAMES = ["f", "k1", "yaw", "pitch", "roll", "cx", "cy", "cz",
         "W", "hb", "ywt", "xwl", "xwr", "ys", "yd", "xl", "zc", "t93"]
SILL_PROTRUSION = 3.0


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
        d = self.ray(uv)
        i = "XYZ".index(axis)
        t = (value - self.C[i]) / d[i]
        return self.C + t * d


def _line3d(name, q, H):
    W = q["W"]
    return np.array({
        "floor_back": ([-400, 0, 1.5], [100, 0, 1.5]),
        "base_top_back": ([-400, q["hb"], 1.5], [100, q["hb"], 1.5]),
        "ceil_back": ([-400, H, 0], [100, H, 0]),
        "corner_right": ([0, 0, 0], [0, H, 0]),
        "corner_left": ([-W, 0, 0], [-W, H, 0]),
        "ceil_right": ([0, H, 0], [0, H, 150]),
        "ceil_left": ([-W, H, 0], [-W, H, 150]),
        "win_top": ([-400, q["ywt"], 0], [100, q["ywt"], 0]),
        "win_left": ([q["xwl"], 0, 0], [q["xwl"], H, 0]),
        "win_right": ([q["xwr"], 0, 0], [q["xwr"], H, 0]),
        "sill_front": ([-400, q["ys"], SILL_PROTRUSION], [100, q["ys"], SILL_PROTRUSION]),
        "door_head": ([-1.2, q["yd"], 0], [-1.2, q["yd"], 150]),
        "door_leaf_bottom": ([q["xl"], 0, 0], [q["xl"], 0, 150]),
        "jamb_near": ([0, 0, q["zc"]], [0, H, q["zc"]]),
        "jamb_far": ([q["t93"], 0, q["zc"]], [q["t93"], H, q["zc"]]),
    }[name], float)


def calibrate(H):
    segs = {k: np.array(v, float) for k, v in json.load(open(os.path.join(HERE, "segments.json"))).items()}
    s = H / 270.0

    def residuals(p):
        q = dict(zip(NAMES, p))
        cam = Camera(q)
        res = []
        for name, arr in segs.items():
            a, b = cam.project(_line3d(name, q, H), distort=False)
            n = np.array([-(b - a)[1], (b - a)[0]])
            n /= np.linalg.norm(n)
            for sg in arr:
                u = cam.undistort(np.linspace(sg[:2], sg[2:], 4))
                res.extend(((u - a) @ n).tolist())
        res.append(q["k1"] * 5)
        res.append(q["roll"] * 20)
        return np.array(res)

    p0 = np.array([380, 0.0, 0.1, 0.1, 0.0, -97 * s, 137 * s, 200 * s,
                   171 * s, 7 * s, 233 * s, -116 * s, -65 * s, 37 * s, 192 * s, 14 * s, 12 * s, 17 * s])
    sol = least_squares(residuals, p0, method="lm", max_nfev=20000)
    r = residuals(sol.x)[:-2]
    q = dict(zip(NAMES, map(float, sol.x)))
    q["H"] = H
    q["rms"] = float(np.sqrt((r ** 2).mean()))
    q["max"] = float(np.abs(r).max())
    return q


def load_camera(H=280.0, scale=1.0):
    path = os.path.join(HERE, f"camera_H{int(H)}.json")
    if not os.path.exists(path):
        json.dump(calibrate(H), open(path, "w"), indent=1)
    return Camera(json.load(open(path)), scale)


if __name__ == "__main__":
    import sys
    H = float(sys.argv[1]) if len(sys.argv) > 1 else 280.0
    q = calibrate(H)
    json.dump(q, open(os.path.join(HERE, f"camera_H{int(H)}.json"), "w"), indent=1)
    for k, v in q.items():
        print(f"{k:6s} {np.degrees(v):8.2f} deg" if k in ("yaw", "pitch", "roll") else f"{k:6s} {v:8.2f}")
