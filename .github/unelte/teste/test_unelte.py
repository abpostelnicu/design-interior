"""Testele uneltelor comune din `.github/unelte/`. Din rădăcina depozitului:

    python -B -m unittest discover -s .github/unelte/teste -v

(-B: fără __pycache__). Folosesc doar unittest din biblioteca standard și scriu numai în foldere temporare.
Unde se poate, compară uneltele cu scripturile proiectelor din `.github/surse/`, care au produs imaginile
publicate: aceleași intrări trebuie să dea aceleași rezultate.

Testele pentru variantele din beton ale polițelor (C și D) rulează când sursele lor, `.github/surse/polite-viniluri/beton/`,
există sau când variabila UNELTE_BETON arată spre o copie a lor. Pe o ramură fără acel folder, se sar.
"""
import contextlib
import http.server
import importlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import warnings
from unittest import mock

sys.dont_write_bytecode = True

AICI = os.path.dirname(os.path.abspath(__file__))
UNELTE = os.path.dirname(AICI)
GITHUB = os.path.dirname(UNELTE)
RADACINA = os.path.dirname(GITHUB)
SURSE = os.path.join(GITHUB, "surse")
POLITE = os.path.join(SURSE, "polite-viniluri")
CUIER = os.path.join(SURSE, "cuier-hol")
BETON = os.environ.get("UNELTE_BETON", os.path.join(POLITE, "beton"))
if GITHUB not in sys.path:
    sys.path.insert(0, GITHUB)

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageCms, ImageDraw  # noqa: E402

from unelte import (camera, comparatie, foto, materiale, plan, preturi, randare, rezistenta,  # noqa: E402
                    segmente, verificari)


@contextlib.contextmanager
def scripturi(folder):
    """Importă scripturile unui proiect și le scoate apoi din sys.modules: proiectele au module cu aceleași nume
    (camera, core, design), care altfel s-ar amesteca între ele. Avertismentele lor despre fișiere lăsate deschise
    (ResourceWarning, din `json.load(open(...))`) nu țin de unelte și nu se afișează."""
    sys.path.insert(0, folder)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ResourceWarning)
            yield importlib.import_module
    finally:
        sys.path.remove(folder)
        for k, m in list(sys.modules.items()):
            f = getattr(m, "__file__", None)
            if f and os.path.dirname(os.path.abspath(f)) == folder:
                del sys.modules[k]


@contextlib.contextmanager
def liniste():
    with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()):
        yield out


def puncte_aleatoare(lo, hi, n=60, seed=0):
    return np.random.RandomState(seed).uniform(lo, hi, (n, 3))


def jpg_cu_gps(path, size=(160, 120), culoare=(200, 100, 50), orientare=1):
    """O fotografie JPEG cu EXIF (inclusiv GPS), comentariu și profil de culoare, ca de pe un telefon."""
    ex = Image.Exif()
    ex[0x0112] = orientare
    ex[0x010F] = "Telefon"
    ex[0x8825] = {1: "N", 2: (12.0, 34.0, 56.0), 3: "E", 4: (65.0, 43.0, 21.0)}
    icc = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    Image.new("RGB", size, culoare).save(path, exif=ex, comment=b"acasa", icc_profile=icc)
    return path


# ------------------------------------------------------------------ geometria polițelor (camera.json din proiect)

WALL_W, TV_W, TV_H, CAB_W, CAB_D, CAB_H, BASE_T = 419.0, 216.6, 123.6, 242.0, 48.0, 67.0, 1.5


def dreapta_polite(name, q):
    """Dreptele 3D ale grupurilor din segments.json, ca `_line3d` din polite-viniluri/camera.py."""
    H = q["H"]
    ytt, xr, zb = q["ytv"] + TV_H, q["xtv"] + TV_W, q["zc"] - CAB_D
    return {
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
    }[name]


def dreapta_cuier(name, q):
    """Ca `_line3d` din cuier-hol/camera.py (X = 0 în colțul din dreapta, H fixat)."""
    H, W = q["H"], q["W"]
    return {
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
        "sill_front": ([-400, q["ys"], 3.0], [100, q["ys"], 3.0]),
        "door_head": ([-1.2, q["yd"], 0], [-1.2, q["yd"], 150]),
        "door_leaf_bottom": ([q["xl"], 0, 0], [q["xl"], 0, 150]),
        "jamb_near": ([0, 0, q["zc"]], [0, H, q["zc"]]),
        "jamb_far": ([q["t93"], 0, q["zc"]], [q["t93"], H, q["zc"]]),
    }[name]


def cam_polite(scale=1.0):
    return camera.incarca(os.path.join(POLITE, "camera.json"), scale, size=(1024, 768))


def cam_cuier(scale=1.0):
    return camera.incarca(os.path.join(CUIER, "camera_H270.json"), scale, size=(768, 1024))


# ------------------------------------------------------------------ camera și segmentele

class TestCamera(unittest.TestCase):
    def test_proiectiile_sunt_ca_in_proiecte(self):
        cazuri = [(POLITE, "camera.json", (1024, 768), dict(), ([0, 0, 0], [419, 262, 150])),
                  (CUIER, "camera_H270.json", (768, 1024), dict(), ([-170, 0, 0], [0, 270, 150]))]
        for folder, nume, size, _, (lo, hi) in cazuri:
            with scripturi(folder) as imp:
                pc = imp("camera")
                with open(os.path.join(folder, nume)) as f:
                    q = json.load(f)
                P = puncte_aleatoare(lo, hi)
                for scale in (1.0, 4.0):
                    ref, noi = pc.Camera(q, scale), camera.Camera(q, scale, size)
                    for distort in (True, False):
                        np.testing.assert_allclose(noi.project(P, distort), ref.project(P, distort), atol=1e-9)
                    uv = ref.project(P)
                    np.testing.assert_allclose(noi.undistort(uv), ref.undistort(uv), atol=1e-9)
                    np.testing.assert_allclose(noi.backproject(uv[0], "Z", 0.0), ref.backproject(uv[0], "Z", 0.0),
                                               atol=1e-9)

    def test_backproject_intoarce_punctul(self):
        P = puncte_aleatoare([20, 20, 0], [400, 240, 0])
        cam = cam_polite()
        np.testing.assert_allclose(camera.puncte(cam, cam.project(P), "Z", 0.0), P, atol=1e-6)
        P = puncte_aleatoare([-160, 10, 0], [-10, 260, 0])
        cam = cam_cuier()                                   # cu distorsiune: inversarea e iterativă
        np.testing.assert_allclose(camera.puncte(cam, cam.project(P), "Z", 0.0), P, atol=1e-3)

    def test_scaled_mareste_proiectiile(self):
        for cam in (cam_polite(), cam_cuier()):
            P = puncte_aleatoare([-100, 0, 0], [100, 200, 100])
            np.testing.assert_allclose(cam.scaled(4).project(P), 4 * cam.project(P), atol=1e-9)

    def test_fara_punct_principal(self):
        with open(os.path.join(POLITE, "camera.json")) as f:
            q = json.load(f)
        with self.assertRaises(ValueError):
            camera.Camera(q)

    def test_recalibrarea_polite(self):
        segs = camera.citeste_segmente(os.path.join(POLITE, "segments.json"))
        p0 = dict(f=780, yaw=0, pitch=0, roll=0, cx=208, cy=97, cz=365, H=262, hb=8, ztv=6, xtv=99, ytv=84.5,
                  xc=88, zc=50)
        q = camera.calibreaza(segs, dreapta_polite, p0, (1024, 768))
        with open(os.path.join(POLITE, "camera.json")) as f:
            ref = json.load(f)
        self.assertAlmostEqual(q["rms"], ref["rms"], places=4)
        self.assertAlmostEqual(q["H"], ref["H"], places=2)
        self.assertEqual(set(q["rms_grupuri"]), set(segs))
        P = puncte_aleatoare([0, 0, 0], [419, 262, 150])
        np.testing.assert_allclose(camera.Camera(q).project(P), cam_polite().project(P), atol=0.01)
        with tempfile.TemporaryDirectory() as tmp:          # pp se salvează: nu mai trebuie size la încărcare
            camera.salveaza(q, os.path.join(tmp, "camera.json"))
            np.testing.assert_allclose(camera.incarca(os.path.join(tmp, "camera.json")).project(P),
                                       camera.Camera(q).project(P), atol=1e-9)
        self.assertIn("yaw", camera.rezumat(q))

    def test_recalibrarea_cuier(self):
        segs = camera.citeste_segmente(os.path.join(CUIER, "segments.json"))
        p0 = dict(f=380, k1=0.0, yaw=0.1, pitch=0.1, roll=0.0, cx=-97, cy=137, cz=200, W=171, hb=7, ywt=233,
                  xwl=-116, xwr=-65, ys=37, yd=192, xl=14, zc=12, t93=17)
        q = camera.calibreaza(segs, dreapta_cuier, p0, (768, 1024), fixe={"H": 270.0}, k1_liber=True,
                              regularizare={"roll": 20}, max_nfev=20000)
        with open(os.path.join(CUIER, "camera_H270.json")) as f:
            ref = json.load(f)
        self.assertAlmostEqual(q["rms"], ref["rms"], places=4)
        self.assertAlmostEqual(q["k1"], ref["k1"], places=6)
        P = puncte_aleatoare([-170, 0, 0], [0, 270, 150])
        np.testing.assert_allclose(camera.Camera(q).project(P), cam_cuier().project(P), atol=0.01)

    def test_lipsesc_valorile_de_pornire(self):
        with self.assertRaises(ValueError):
            camera.calibreaza({}, dreapta_polite, dict(yaw=0, pitch=0, roll=0, cx=0, cy=0, cz=300), (1024, 768))


class TestSegmente(unittest.TestCase):
    def test_detecteaza_alege_deseneaza(self):
        img = foto.citeste(os.path.join(POLITE, "original.jpg"))
        segs = segmente.detecteaza(img, 20)
        self.assertGreater(len(segs), 100)
        L = np.hypot(segs[:, 2] - segs[:, 0], segs[:, 3] - segs[:, 1])
        self.assertTrue(np.all(L >= 20) and np.all(np.diff(L) <= 1e-3))
        ales = segmente.alege(segs, {"ceil": [0, 1]})
        self.assertEqual(len(ales["ceil"]), 2)
        self.assertEqual(len(ales["ceil"][0]), 4)
        with self.assertRaises(IndexError):
            segmente.alege(segs, {"ceil": [len(segs)]})
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(segmente.deseneaza(img, segs, os.path.join(tmp, "z.png"), (600, 0, 1000, 300)),
                             (800, 600))
            with liniste():
                self.assertEqual(segmente.main([os.path.join(POLITE, "original.jpg"), tmp]), 0)
            with open(os.path.join(tmp, "grupuri.json"), "w") as f:
                json.dump({"ceil": [0], "floor": [2, 3]}, f)
            with liniste():
                self.assertEqual(segmente.main(["--alege", os.path.join(tmp, "segmente_toate.json"),
                                                os.path.join(tmp, "grupuri.json"),
                                                os.path.join(tmp, "segments.json")]), 0)
            s = camera.citeste_segmente(os.path.join(tmp, "segments.json"))
            self.assertEqual({k: v.shape for k, v in s.items()}, {"ceil": (1, 4), "floor": (2, 4)})


# ------------------------------------------------------------------ fotografia

class TestFoto(unittest.TestCase):
    def test_pregateste_scoate_metadatele(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = jpg_cu_gps(os.path.join(tmp, "telefon.jpg"), size=(1600, 1200), orientare=6)
            m = foto.metadate(src)
            self.assertTrue(m["gps"])
            self.assertIn("comment", m["altele"])
            dst = os.path.join(tmp, "original.jpg")
            self.assertEqual(foto.pregateste(src, dst), (768, 1024))   # rotită după EXIF: verticală
            self.assertEqual(foto.metadate(dst), {"exif": 0, "gps": False, "altele": []})
            with Image.open(dst) as im:
                self.assertNotIn("icc_profile", im.info)
                self.assertEqual(im.size, (768, 1024))
                np.testing.assert_allclose(im.getpixel((10, 10)), (200, 100, 50), atol=3)
            with liniste():
                self.assertEqual(foto.main(["exif", src]), 1)
                self.assertEqual(foto.main(["exif", dst]), 0)

    def test_scrie_fara_metadate(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = foto.scrie(os.path.join(tmp, "a.jpg"), np.full((20, 30, 3), 0.5, np.float32))
            self.assertEqual(foto.metadate(p), {"exif": 0, "gps": False, "altele": []})
            self.assertEqual(foto.citeste(p).shape, (20, 30, 3))

    def test_stinge_ecran(self):
        img = np.random.RandomState(1).uniform(0.5, 1.0, (200, 300, 3)).astype(np.float32)
        out = foto.stinge_ecran(img, [(50, 40), (250, 40), (250, 160), (50, 160)])
        ecran = out[50:150, 60:240]
        self.assertLess(ecran.mean(), 0.3)
        self.assertGreater(ecran.mean(), 0.02)
        np.testing.assert_array_equal(out[:30], img[:30])

    def test_umple_de_sus(self):
        img = np.full((100, 80, 3), 0.8, np.float32)
        img[40:90, 20:60] = (0.1, 0.2, 0.3)                  # „persoana” din golul ușii
        out = foto.umple_de_sus(img, 20, 40, 60, 90)
        np.testing.assert_allclose(out[40:90, 20:60], 0.8, atol=0.06)
        np.testing.assert_array_equal(out[:40], img[:40])

    def test_sterge_si_estompeaza(self):
        img8 = np.full((80, 200, 3), 178, np.uint8)
        cv2.putText(img8, "B 123 ABC", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
        img = img8.astype(np.float32) / 255
        zona = [(5, 20), (190, 20), (190, 62), (5, 62)]
        self.assertLess(foto.sterge(img, zona)[25:58, 10:185].std(), 0.03)
        self.assertLess(foto.estompeaza(img, zona, 10)[25:58, 10:185].std(), img[25:58, 10:185].std() / 2)

    def test_grila(self):
        img = foto.citeste(os.path.join(POLITE, "original.jpg"))
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "zoom.png")
            self.assertEqual(foto.grila(img, p, (100, 50, 300, 150), 3), (644, 344))
            self.assertEqual(cv2.imread(p).shape, (344, 644, 3))


# ------------------------------------------------------------------ randarea

class TestRandare(unittest.TestCase):
    def test_canvas_ca_polite(self):
        """Fețele și umbrele pe perete, comparate cu Canvas din polite-viniluri/core.py, la rezoluția pozei."""
        with scripturi(POLITE) as imp:
            core = imp("core")
            c1 = core.cam1                                   # core lucrează la 4x; aici, la 1x, ca să fie repede
            core.cam, core.W, core.H = c1, 1024, 768
            core.KINV = np.linalg.inv(np.array([[c1.f, 0, c1.pp[0]], [0, c1.f, c1.pp[1]], [0, 0, 1.0]]))
            core.proj = lambda P, c=c1: c.project(np.atleast_2d(np.asarray(P, float)), distort=False)
            ref = core.Canvas(core.PHOTO)
            noi = randare.Canvas(core.PHOTO, cam_polite())

            def culoare(s, t, X, yy, xx):
                return np.stack([s / 100, t / 50, np.full_like(s, 0.4)], -1).astype(np.float32)

            fete = [((300, 120, 0.0), (1, 0, 0), (0, 1, 0), 100, 3.6),        # fața poliței
                    ((300, 120, 0.0), (1, 0, 0), (0, 0, 1), 100, 25),         # deasupra
                    ((250, 100, 10.0), (1, 0, 0), (0, 1, 0), 120, 60)]        # o placă în fața ei
            for O, eu, ev, wu, hv in fete:
                ref.face(O, eu, ev, wu, hv, culoare)
                noi.face(O, eu, ev, wu, hv, culoare)
            ref.face((50, 0, 30), (1, 0, 0), (0, 1, 0), 40, 100, None)         # doar în bufferul de adâncime
            noi.face((50, 0, 30), (1, 0, 0), (0, 1, 0), 40, 100, None)

            def umbra(X, Y):
                return 1 - 0.3 * np.exp(-((X - 350) ** 2 + (Y - 110) ** 2) / 400)

            ref.multiply_wall(umbra, 280, 419, 60, 160)
            noi.multiply_wall(umbra, 280, 419, 60, 160)
            np.testing.assert_allclose(noi.img, ref.img, atol=1e-6)
            np.testing.assert_array_equal(noi.z, ref.z)
            np.testing.assert_array_equal(noi.touch, ref.touch)

    def test_adancimea_nu_depinde_de_ordine(self):
        cam = cam_polite()
        bg = np.zeros((768, 1024, 3), np.float32)
        rosu, verde = randare.solid((0, 0, 1)), randare.solid((0, 1, 0))
        a, b = randare.Canvas(bg, cam), randare.Canvas(bg, cam)
        a.face((150, 100, 5), (1, 0, 0), (0, 1, 0), 100, 60, rosu)
        a.face((180, 120, 20), (1, 0, 0), (0, 1, 0), 100, 60, verde)
        b.face((180, 120, 20), (1, 0, 0), (0, 1, 0), 100, 60, verde)
        b.face((150, 100, 5), (1, 0, 0), (0, 1, 0), 100, 60, rosu)
        np.testing.assert_array_equal(a.img, b.img)
        u, v = cam.project([[200, 140, 20]])[0].astype(int)  # în suprapunere: se vede placa din față (verde)
        np.testing.assert_array_equal(a.img[v, u], (0, 1, 0))

    def test_box_deseneaza_doar_fetele_vizibile(self):
        cv = randare.Canvas(np.zeros((768, 1024, 3), np.float32), cam_polite())
        cerute = []

        def culori(n):
            cerute.append(tuple(int(v) for v in n))
            return randare.solid((0.5, 0.5, 0.5), shade=randare.SHADE[tuple(int(v) for v in n)])

        randare.box(cv, (100, 150), (40, 67), (10, 50), culori)   # sub aparat, în stânga lui
        self.assertEqual(set(cerute), {(0, 0, 1), (0, 1, 0), (1, 0, 0)})
        self.assertGreater(cv.touch.sum(), 1000)

    def test_multiply_floor(self):
        cv = randare.Canvas(np.ones((768, 1024, 3), np.float32), cam_polite())
        cv.multiply_floor(lambda X, Z: np.full_like(X, 0.5), 0, 419, 0, 300)
        u, v = cam_polite().project([[200, 0, 150]])[0].astype(int)
        np.testing.assert_allclose(cv.img[v, u], 0.5)
        np.testing.assert_allclose(cv.img[100, 512], 1.0)

    def test_wall_light_map_ca_polite(self):
        with scripturi(POLITE) as imp:
            core = imp("core")
            core.W, core.H = 2048, 1536
            q = core.cam1.q
            masti = [[[q["xtv"] - 3, q["ytv"] - 3, 6], [q["xtv"] + 219.6, q["ytv"] - 3, 6],
                      [q["xtv"] + 219.6, q["ytv"] + 126.6, 6], [q["xtv"] - 3, q["ytv"] + 126.6, 6]],
                     [[380, 0, 50], [425, 0, 50], [425, 115, 50], [380, 115, 50]]]
            M_ref, v_ref = core.wall_light_map(masti)
            perete = [[0.5, 9, 0], [418.5, 9, 0], [418.5, q["H"] - 0.5, 0], [0.5, q["H"] - 0.5, 0]]
            M, v = randare.wall_light_map(core.PHOTO, cam_polite(), perete, masti, exclude_px=[(985, 0, 1024, 768)],
                                          size=(2048, 1536))
            self.assertAlmostEqual(v, float(v_ref), places=6)
            np.testing.assert_allclose(M, M_ref, atol=1e-5)

    def test_finish_tone_ca_polite(self):
        with scripturi(POLITE) as imp:
            render = imp("render")
            render.W, render.H = 64, 48
            rng = np.random.RandomState(3)
            img = rng.uniform(0, 1, (48, 64, 3)).astype(np.float32)
            touch = (rng.uniform(0, 1, (48, 64)) > 0.5).astype(np.float32)
            np.testing.assert_array_equal(randare.finish(img, touch, ss=2), render.finish(img, touch))
            x = np.linspace(0, 1.4, 50)
            np.testing.assert_allclose(randare.tone(x), render.tone(x))
            np.testing.assert_allclose(randare.smooth(x), render.smooth(x))

    def test_canvas_refuza_distorsiunea(self):
        bg = np.zeros((1024, 768, 3), np.float32)
        with self.assertRaises(ValueError):
            randare.Canvas(bg, cam_cuier())
        cam0 = cam_cuier().fara_distorsiune()               # ca scriptul „Cuier hol”: proj(..., distort=False)
        cv = randare.Canvas(bg, cam0)
        cv.face((-60, 100, 2), (1, 0, 0), (0, 1, 0), 50, 40, randare.solid((1, 1, 1)))
        u, v = cam_cuier().project([[-35, 120, 2]], distort=False)[0].astype(int)
        np.testing.assert_array_equal(cv.img[v, u], (1, 1, 1))
        with scripturi(CUIER) as imp:
            ref = imp("camera").load_camera(270, scale=4)
            P = puncte_aleatoare([-170, 0, 0], [0, 270, 150])
            np.testing.assert_allclose(cam_cuier(4).fara_distorsiune().project(P), ref.project(P, distort=False),
                                       atol=1e-9)
            self.assertEqual(cam_cuier(4).fara_distorsiune().scale, 4)

    def test_din_foto(self):
        with open(os.path.join(POLITE, "camera.json")) as f:
            q = json.load(f)
        cam1 = camera.Camera(q, size=(64, 48))
        cv = randare.Canvas.din_foto(np.zeros((48, 64, 3), np.float32), cam1, out=2, ss=2)
        self.assertEqual((cv.W, cv.H, cv.ss), (256, 192, 2))
        self.assertAlmostEqual(cv.cam.f, 4 * cam1.f)
        self.assertEqual(randare.finish(cv.img, cv.touch, cv.ss).shape, (96, 128, 3))
        self.assertEqual(randare.current_photo(np.zeros((48, 64, 3), np.float32)).shape, (96, 128, 3))


# ------------------------------------------------------------------ materialele

class TestMateriale(unittest.TestCase):
    def test_stejar_ca_polite(self):
        with scripturi(POLITE) as imp:
            mat, core = imp("materials"), imp("core")
            src = materiale.oak_source(core.PHOTO, cam_polite(), (40, 86), (70, 116))
            np.testing.assert_allclose(src, mat.OAK_SRC, atol=1e-6)
            np.testing.assert_array_equal(materiale.glued_panel(mat.OAK_SRC, 30, 12, np.random.RandomState(5)),
                                          mat.glued_panel(30, 12, np.random.RandomState(5)))
            np.testing.assert_array_equal(materiale.end_grain(12, 3.6, np.random.RandomState(6)),
                                          mat.end_grain(12, 3.6, np.random.RandomState(6)))

    def test_stejar_procedural(self):
        src = materiale.oak_procedural(np.random.RandomState(1))
        self.assertEqual(src.shape, (460, 460, 3))
        np.testing.assert_allclose(src.reshape(-1, 3).mean(0), materiale.OAK_REF, atol=3e-3)
        p = materiale.glued_panel(src, 40, 20, np.random.RandomState(2))
        self.assertEqual(p.shape, (402, 202, 3))

    def test_microciment_are_media_tonului(self):
        for ton in ("gri", "antracit", materiale.din_rgb(120, 110, 100)):
            ref = materiale.TONES[ton] if isinstance(ton, str) else ton
            p = materiale.concrete_panel(20, 10, np.random.RandomState(2), ton)
            self.assertEqual(p.shape, (202, 102, 3))
            np.testing.assert_allclose(p.reshape(-1, 3).mean(0), ref, atol=2e-3)
            self.assertGreater(p.std(), 0.005)                # are textură, nu e o culoare plată
        e = materiale.concrete_edge(20, 3.6, np.random.RandomState(2), "gri", cut_cm=25)
        self.assertEqual(e.shape, (202, 38, 3))
        np.testing.assert_allclose(e.reshape(-1, 3).mean(0), materiale.TONES["gri"], atol=2e-3)
        self.assertEqual(materiale.concrete_end(25, 3.6, np.random.RandomState(2), "gri").shape, (38, 252, 3))

    def test_microciment_erori(self):
        with self.assertRaises(ValueError):
            materiale.concrete_panel(5, 5, np.random.RandomState(0), "verde")
        with self.assertRaises(ValueError):
            materiale.concrete_panel(5, 5, np.random.RandomState(0), "gri", gain={"nu_exista": 2})

    @unittest.skipUnless(os.path.isdir(BETON), "sursele variantelor din beton nu sunt în această copie")
    def test_microciment_si_culoarea_ca_beton(self):
        with scripturi(BETON) as imp:
            b, core = imp("beton"), imp("core")
            for fn, args, kw in [("concrete_panel", (30, 8, None, "gri"), dict(gain=dict(vein=1.5))),
                                 ("concrete_edge", (30, 3.6, None, "antracit"), dict(cut_cm=25)),
                                 ("concrete_end", (8, 3.6, None, "gri"), dict())]:
                a1 = list(args)
                a1[2] = np.random.RandomState(4)
                a2 = list(args)
                a2[2] = np.random.RandomState(4)
                np.testing.assert_array_equal(getattr(materiale, fn)(*a1, **kw), getattr(b, fn)(*a2, **kw))
            cam1 = camera.incarca(os.path.join(BETON, "camera.json"), size=(1024, 768))
            np.testing.assert_allclose(materiale.rectify_z(core.PHOTO, cam1, (100, 150), (22, 65), 50.0, 4),
                                       b.rectify_z((100, 150), (22, 65), 50.0, 4), atol=1e-6)
            for c1, c2 in [((0.2, 0.3, 0.4), (0.25, 0.3, 0.38)), ((0.62, 0.65, 0.67), (0.29, 0.29, 0.29))]:
                np.testing.assert_allclose(materiale.bgr_to_lab(c1), b.bgr_to_lab(np.array(c1)), atol=1e-9)
                self.assertAlmostEqual(materiale.diferenta(c1, c2),
                                       b.delta_e2000(b.bgr_to_lab(np.array(c1)), b.bgr_to_lab(np.array(c2))))

    def test_delta_e2000_ca_in_articolul_lui_sharma(self):
        perechi = [((50, 2.6772, -79.7751), (50, 0, -82.7485), 2.0425),
                   ((50, -1.3802, -84.2814), (50, 0, -82.7485), 1.0000),
                   ((50, 0, 0), (50, -1, 2), 2.3669),
                   ((50, 2.49, -0.001), (50, -2.49, 0.0009), 7.1792),
                   ((50, 2.49, -0.001), (50, -2.49, 0.0011), 7.2195),
                   ((50, -0.001, 2.49), (50, 0.0009, -2.49), 4.8045),
                   ((50, -0.001, 2.49), (50, 0.0011, -2.49), 4.7461),
                   ((50, 2.5, 0), (50, 0, -2.5), 4.3065),
                   ((50, 2.5, 0), (73, 25, -18), 27.1492),
                   ((50, 2.5, 0), (50, 3.1736, 0.5854), 1.0000),
                   ((60.2574, -34.0099, 36.2677), (60.4626, -34.1751, 39.4387), 1.2644)]
        for a, b, de in perechi:
            self.assertAlmostEqual(materiale.delta_e2000(a, b), de, places=4, msg=f"{a} {b}")
            self.assertAlmostEqual(materiale.delta_e2000(b, a), de, places=4)

    def test_lab_si_rgb(self):
        np.testing.assert_allclose(materiale.bgr_to_lab((1, 1, 1)), (100, 0, 0), atol=1e-3)
        np.testing.assert_allclose(materiale.bgr_to_lab((0, 0, 1)), (53.24, 80.09, 67.20), atol=0.05)
        self.assertEqual(materiale.rgb255(materiale.din_rgb(170, 166, 158)), (170, 166, 158))
        self.assertLess(materiale.delta_e76(materiale.bgr_to_lab((0.5, 0.5, 0.5)),
                                            materiale.bgr_to_lab((0.5, 0.5, 0.5))), 1e-9)

    def test_masoara(self):
        poza = np.empty((768, 1024, 3), np.float32)
        poza[:] = (0.3, 0.5, 0.7)
        med, medie = materiale.masoara(poza, cam_polite(), (150, 200), (150, 200))
        np.testing.assert_allclose(med, (0.3, 0.5, 0.7), atol=1e-6)
        np.testing.assert_allclose(medie, (0.3, 0.5, 0.7), atol=1e-6)

    def test_sample_in_oglinda(self):
        tex = np.random.RandomState(0).uniform(0, 1, (20, 30, 3)).astype(np.float32)
        u, v = np.meshgrid(np.arange(30, dtype=np.float32), np.arange(20, dtype=np.float32))
        np.testing.assert_allclose(materiale.sample(tex, u, v), tex, atol=1e-6)
        np.testing.assert_allclose(materiale.sample(tex, 58 - u, v), tex, atol=1e-6)   # 2·(w − 1) − u


# ------------------------------------------------------------------ planul tehnic

class TestPlan(unittest.TestCase):
    def tearDown(self):
        plan.plt.close("all")

    def test_numere(self):
        self.assertEqual(plan.fmt(12.5), "12,5")
        self.assertEqual(plan.fmt(12.0), "12")
        self.assertEqual(plan.fmt(120), "120")
        self.assertEqual(plan.kn(1.0702), "1,07")
        self.assertEqual(plan.seq([1, 2.5, 3]), "1, 2,5 și 3")
        self.assertEqual(plan.seq([4]), "4")
        self.assertEqual(plan.dims(120, 25, 3.6), "120 × 25 × 3,6")

    def test_wrap_tine_numerele_cu_unitatile(self):
        fig = plan.pagina("Probă")
        para = "1. " + " ".join(["Polița de 12 cm stă pe tije M12 de 20 cm, adică 3 × 4 mm la fiecare capăt."] * 5)
        rows = plan.wrap(fig, para, width=60)
        self.assertGreater(len(rows), 3)
        for r in rows:
            self.assertLessEqual(plan.width_mm(fig, r, plan.NOTE_FS), 60.5)
        for r in rows[1:]:
            self.assertTrue(r.startswith(" "))               # rândurile de continuare, aliniate după „1. ”
            self.assertNotRegex(r.strip(), r"^(cm|mm|×)")
        text = " ".join(rows)
        self.assertEqual(text.count(f"12{plan.NB}cm"), 5)
        self.assertEqual(text.count(f"3{plan.NB}×{plan.NB}4{plan.NB}mm"), 5)

    def _pagina_curata(self):
        fig = plan.pagina("Plan de probă", "un desen și o notă")
        ax = plan.make_axes(fig, 20, 60, (-10, 110), (-20, 70), "VEDERE (1:15)", plan.MM15)
        plan.rect(ax, 0, 0, 100, 60, plan.C["wall"])
        plan.dim_h(ax, 0, 100, -10, ref=0, k=plan.K15)
        plan.dim_v(ax, 0, 60, 105, ref=100, k=plan.K15)
        plan.text_block(fig, 300, 150, "NOTE", ["1. Un paragraf scurt, de verificat cu wrap: 12 cm și 3,6 cm."])
        return fig

    def test_verifica_figura(self):
        bad, look, info = plan.verifica_figura(self._pagina_curata())
        self.assertEqual(bad, [])
        self.assertEqual(info["desene"], 1)
        fig = self._pagina_curata()
        fig.text(8 / 420, 1 - 8 / 297, "titlu peste titlu", fontsize=13, va="top")
        fig.text(419 / 420, 0.5, "iese din pagină", fontsize=8)
        fig.text(40 / 420, 90 / 297, "notă în desen", fontsize=6)
        bad = plan.verifica_figura(fig)[0]
        self.assertTrue(any(b.startswith("suprapunere") for b in bad), bad)
        self.assertTrue(any(b.startswith("iese din pagină") for b in bad), bad)
        self.assertTrue(any(b.startswith("text de pagină în desenul") for b in bad), bad)

    def test_save_a3(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf, png = plan.save(self._pagina_curata(), os.path.join(tmp, "out", "plan_tehnic_proba"))
            self.assertTrue(plan.e_a3(pdf))
            w, h = plan.dimensiuni_pdf(pdf)
            self.assertAlmostEqual(w, 420, delta=0.5)
            self.assertAlmostEqual(h, 297, delta=0.5)
            with Image.open(png) as im:
                self.assertAlmostEqual(im.size[0], 420 / 25.4 * 220, delta=2)

    def test_linia_de_comanda(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "drawing.py")
            with open(p, "w", encoding="utf-8") as f:
                f.write(f"import sys\nsys.path.insert(0, {GITHUB!r})\nfrom unelte import plan\n\n"
                        "def build():\n    return plan.pagina('Plan de probă')\n\n"
                        "def build_rau():\n    fig = plan.pagina('Plan de probă')\n"
                        "    fig.text(8 / 420, 1 - 8 / 297, 'suprapus', fontsize=13, va='top')\n    return fig\n")
            try:
                with liniste():
                    self.assertEqual(plan.main(["verifica", p]), 0)
                    self.assertEqual(plan.main(["verifica", p, "build_rau"]), 1)
                    self.assertEqual(plan.main(["verifica", p, "lipsa"]), 2)
                    self.assertEqual(plan.main([]), 2)
            finally:
                if tmp in sys.path:
                    sys.path.remove(tmp)
        pdfs = [os.path.join(RADACINA, "Cuier hol", "plan_tehnic_cuier.pdf"),
                os.path.join(RADACINA, "Polite viniluri", "plan_tehnic_polite_viniluri.pdf")]
        with liniste():
            self.assertEqual(plan.main(["a3"] + pdfs), 0)

    @unittest.skipUnless(os.path.isdir(BETON), "sursele variantelor din beton nu sunt în această copie")
    def test_planul_beton_trece_verificarea(self):
        with scripturi(BETON) as imp:
            bad, look, info = plan.verifica_figura(imp("drawing").build())
        self.assertEqual(bad, [])
        self.assertGreater(info["texte"], 100)


# ------------------------------------------------------------------ comparația

class TestComparatie(unittest.TestCase):
    def test_marimile_sunt_ca_in_proiecte(self):
        cazuri = [((2048, 1536), os.path.join(RADACINA, "Polite viniluri", "comparatie_acum_vs_propuneri.jpg")),
                  ((1536, 2048), os.path.join(RADACINA, "Cuier hol", "comparatie_acum_vs_propuneri.jpg"))]
        with tempfile.TemporaryDirectory() as tmp:
            for size, existenta in cazuri:
                panouri = [(Image.new("RGB", size, (90 * k, 120, 160)), f"Titlul {k}", "subtitlu") for k in range(3)]
                dest = os.path.join(tmp, "comparatie.jpg")
                marime = comparatie.compune(panouri, dest)
                with Image.open(existenta) as im:
                    self.assertEqual(marime, im.size)
                with Image.open(dest) as im:
                    self.assertEqual(im.size, marime)

    def test_titlurile_lungi(self):
        d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
        bold = comparatie._fonturi()[0]
        f = comparatie.font_care_incape(d, "Propunere A – stejar masiv încleiat, ulei mat", bold, 30, 600, 20)
        self.assertLess(f.size, 30)
        with self.assertRaises(ValueError):
            comparatie.font_care_incape(d, "x" * 400, bold, 30, 1016, 20)
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(ValueError):
            comparatie.compune([(Image.new("RGB", (64, 48)), "x" * 400, "")], os.path.join(tmp, "c.jpg"))


# ------------------------------------------------------------------ rezistența

class TestRezistenta(unittest.TestCase):
    def test_tijele_ca_polite(self):
        with scripturi(POLITE) as imp:
            d = imp("design")
            self.assertEqual(rezistenta.rod_check(d.loads()[2], d.D["P"], d.D["rods"]), d.rod_check())

    @unittest.skipUnless(os.path.isdir(BETON), "sursele variantelor din beton nu sunt în această copie")
    def test_tijele_ca_beton(self):
        with scripturi(BETON) as imp:
            d = imp("design")
            for full in (True, False):
                kg = max(d.loads(lv, full)[3] for lv in ("jos", "sus"))
                self.assertEqual(rezistenta.rod_check(kg, d.D["P"], d.D["rods"], fy=d.D["rod_fy"]),
                                 d.rod_check(None, full))
                self.assertEqual(rezistenta.rod_pull(kg, d.D["P"], d.D["T"], d.D["rods"]), d.rod_pull(full))

    def test_formule(self):
        self.assertAlmostEqual(rezistenta.moment(10, 30), 14715.0)
        self.assertAlmostEqual(rezistenta.kg_placa(100, 30, 3.6, "stejar"), 7.776)
        self.assertAlmostEqual(rezistenta.greutate(1000, 2.0), 2.0)
        self.assertEqual(rezistenta.rod_pull(10, 30, 3, 2), 0.49)
        sigma, rez = rezistenta.rod_check(10, 30, 2, fy=rezistenta.FY["8.8"])
        self.assertEqual(rez, round(640 / (14715 / 2 / rezistenta.modul()), 2))


# ------------------------------------------------------------------ prețurile

class _Magazin(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/produs":
            corp = ('<html><head><title>Șurub</title><meta property="og:title" content="Șurub M12 zincat">'
                    '</head><body><span itemprop="price" content="19.49"></span>'
                    '<p>Se livrează la: cutie (10 buc)</p></body></html>').encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(corp)
        else:
            self.send_error(403 if self.path == "/blocat" else 404)

    def log_message(self, *args):
        pass


class TestPreturi(unittest.TestCase):
    def test_numar(self):
        for s, v in [("1.065,50", 1065.5), ("1065.50", 1065.5), ("1 065,50", 1065.5), ("19,49", 19.49),
                     ("19.49", 19.49), ("1,065.50", 1065.5), ("1\u00a0065", 1065.0)]:
            self.assertEqual(preturi.numar(s), v, s)
        self.assertIsNone(preturi.numar("la cerere"))

    def test_analizeaza(self):
        cazuri = [
            ('<meta itemprop="price" content="19.49">', 19.49, "microdata"),
            ('<meta content="19.49" itemprop="price"><meta itemprop="priceCurrency" content="RON">', 19.49,
             "microdata"),
            ('<span itemprop="price">1.065,50</span> lei', 1065.5, "microdata"),
            ('<meta property="product:price:amount" content="145.00">'
             '<meta property="product:price:currency" content="RON">', 145.0, "open graph"),
            ('<script type="application/ld+json">{"@type": "Product", "offers": {"@type": "Offer", '
             '"price": "205.00", "priceCurrency": "RON"}}</script>', 205.0, "json-ld"),
        ]
        for page, pret, sursa in cazuri:
            r = preturi.analizeaza(f"<html><body>{page}</body></html>")
            self.assertEqual((r["stare"], r["pret"], r["sursa"]), ("ok", pret, sursa), page)
        self.assertEqual(preturi.analizeaza(cazuri[3][0])["moneda"], "RON")
        self.assertEqual(preturi.analizeaza(cazuri[4][0])["moneda"], "RON")
        r = preturi.analizeaza("<html><title>Just a moment...</title></html>")
        self.assertEqual(r["stare"], "blocat")
        r = preturi.analizeaza("<html><head><title> Polița  Lack </title></head></html>")
        self.assertEqual((r["stare"], r["titlu"]), ("fara_pret", "Polița Lack"))

    def test_ambalajul(self):
        r = preturi.analizeaza('<span itemprop="price" content="19.49"></span><div>Se livrează la: cutie '
                               '(10 buc)</div>', "https://www.dedeman.ro/ro/produs")
        self.assertEqual(r["cutie"], {"ambalaj": "cutie", "bucati": 10})
        self.assertIn("1,95 pe bucată", preturi.rand(r))

    def test_citeste_offline(self):
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Magazin)
        port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        fara_proxy = {"no_proxy": "127.0.0.1,localhost", "NO_PROXY": "127.0.0.1,localhost"}
        try:
            with mock.patch.dict(os.environ, fara_proxy):
                r = preturi.citeste(f"http://127.0.0.1:{port}/produs", timeout=5)
                self.assertEqual((r["stare"], r["pret"], r["cod_http"]), ("ok", 19.49, 200))
                self.assertEqual(r["titlu"], "Șurub M12 zincat")
                self.assertEqual(r["cutie"]["bucati"], 10)
                self.assertRegex(r["data"], r"^\d{2}\.\d{2}\.\d{4}$")
                self.assertEqual(preturi.citeste(f"http://127.0.0.1:{port}/blocat", timeout=5)["stare"], "blocat")
                r = preturi.citeste(f"http://127.0.0.1:{port}/lipsa", timeout=5)
                self.assertEqual((r["stare"], r["mesaj"]), ("eroare", "HTTP 404"))
        finally:
            srv.shutdown()
            srv.server_close()
        with mock.patch.dict(os.environ, fara_proxy):
            r = preturi.citeste(f"http://127.0.0.1:{port}/produs", timeout=5)
        self.assertEqual(r["stare"], "eroare")

    def test_linkurile_din_lista(self):
        rows = preturi.linkuri_din_lista(os.path.join(RADACINA, "Polite viniluri", "lista_materiale.md"))
        self.assertGreaterEqual(len(rows), 3)
        self.assertTrue(all(u.startswith("https://") for _, _, u in rows))
        self.assertTrue(any("lei" in p for _, p, _ in rows))


# ------------------------------------------------------------------ verificările proiectelor

LISTA_CURATA = """# Listă de materiale

Prețurile au fost verificate pe 30.10.2026.

| Produs | Cant. | Preț | Subtotal |
|---|---|---|---|
| [Tijă M12](https://www.dedeman.ro/ro/tija) | 2 buc | 10,00 lei | 20,00 lei |
| Ancoră chimică | 1 | 45,50 lei | 45,50 lei |
| **Total** | | | **65,50 lei** |

| Ce | Cât |
|---|---|
| Feronerie | 65,50 lei |
| Polițe | la cerere |
"""

README_CURAT = """# Proiect de probă

![Comparație](comparatie_acum_vs_propuneri.jpg)

## Conținutul folderului

- [Lista de materiale](lista_materiale.md) și [planul tehnic](plan_tehnic_proba.pdf) ([PNG](plan_tehnic_proba.png)); [montajul](#montaj-pas-cu-pas).
- Randările: [propunerea A](propunere_A_stejar.jpg) și [varianta B](varianta_B_negru.jpg).

## Cote măsurate

Peretele are 419 cm; polița, 3,6 cm.

## Montaj pas cu pas

### 1. Trasarea

### 2. Găurirea

## Întreținere

Se șterge cu o lavetă umedă.
"""


def proiect_de_proba(root, nume="Proiect proba", readme=README_CURAT, lista=LISTA_CURATA):
    folder = os.path.join(root, nume)
    os.makedirs(folder)
    with open(os.path.join(folder, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)
    with open(os.path.join(folder, "lista_materiale.md"), "w", encoding="utf-8") as f:
        f.write(lista)
    for n in ("comparatie_acum_vs_propuneri.jpg", "propunere_A_stejar.jpg", "varianta_B_negru.jpg",
              "plan_tehnic_proba.png"):
        Image.new("RGB", (32, 24), (120, 120, 120)).save(os.path.join(folder, n))
    with open(os.path.join(folder, "plan_tehnic_proba.pdf"), "wb") as f:
        f.write(b"%PDF-1.4\n1 0 obj << /Type /Page /MediaBox [ 0 0 1190.55 841.89 ] >> endobj\n%%EOF\n")
    surse = os.path.join(root, ".github", "surse", verificari.slug(nume))
    os.makedirs(surse)
    with open(os.path.join(surse, "README.md"), "w", encoding="utf-8") as f:
        f.write(f"# Surse\n\nImaginile din [proiect](../../../{nume.replace(' ', '%20')}/README.md).\n")
    with open(os.path.join(root, "README.md"), "a", encoding="utf-8") as f:
        f.write(f"| [{nume}]({nume.replace(' ', '%20')}/) | descriere |\n")
    return folder, surse


class TestVerificari(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.radacina = mock.patch.object(verificari, "RADACINA", self.tmp)
        self.radacina.start()

    def tearDown(self):
        self.radacina.stop()
        shutil.rmtree(self.tmp)

    def test_proiectele_din_depozit(self):
        self.radacina.stop()
        try:
            gasite = verificari.proiecte()
            self.assertIn("Cuier hol", gasite)
            self.assertIn("Polite viniluri", gasite)
            for p in gasite:
                rap, surse = verificari.verifica(p)
                self.assertEqual(rap.probleme, [], p)
                self.assertIsNotNone(surse, p)
            with liniste():
                self.assertEqual(verificari.main(["--toate"]), 0)
        finally:
            self.radacina.start()

    def test_proiect_curat(self):
        proiect_de_proba(self.tmp)
        self.assertEqual(verificari.proiecte(), ["Proiect proba"])
        rap, surse = verificari.verifica("Proiect proba")
        self.assertEqual((rap.probleme, rap.avertismente), ([], []))
        self.assertIn("lista de materiale: 2 rânduri și 1 total verificate", rap.ok)

    def test_proiect_cu_greseli(self):
        lista = (LISTA_CURATA.replace("| 2 buc | 10,00 lei | 20,00 lei |", "| 2 buc | 10,00 lei | 25,00 lei |")
                 .replace("verificate pe 30.10.2026", "verificate de curând"))
        readme = (README_CURAT.replace("### 2. Găurirea", "### 3. Găurirea")
                  .replace("Peretele are 419 cm", "Peretele are 419.5 cm, la /Users/nume/poze, 12.3456, 65.4321")
                  .replace("Se șterge", "Se şterge")
                  .replace("(#montaj-pas-cu-pas)", "(#montaj)"))
        folder, surse = proiect_de_proba(self.tmp, readme=readme, lista=lista)
        jpg_cu_gps(os.path.join(folder, "propunere_A_stejar.jpg"))
        os.remove(os.path.join(folder, "varianta_B_negru.jpg"))
        with open(os.path.join(folder, "plan_tehnic_proba.pdf"), "wb") as f:
            f.write(b"%PDF-1.4\n<< /MediaBox [0 0 595.28 841.89] >>\n")
        with open(os.path.join(surse, "segments.json"), "w") as f:
            json.dump({"ceil": [[12.3456, 65.4321, 300.5, 20.25]]}, f)      # pixeli, nu GPS
        with open(os.path.join(surse, "note.md"), "w", encoding="utf-8") as f:
            f.write("[lipsă](nu-exista.md) · mașina B 123 ABC · nume@example.com · "
                    "abpostelnicu@users.noreply.github.com\n```\ncod: 2.5 cm, /home/x\n```\n")
        rap, _ = verificari.verifica("Proiect proba")
        # confidențialitatea se verifică și în blocurile de cod (/home/x), stilul nu („2.5 cm” din cod e în regulă)
        asteptate = ["lipsește varianta_B_<material>.jpg", "are coordonate GPS", "nu A3",
                     "nu scrie când au fost verificate", "2 × 10,00 = 20,00 lei, dar subtotalul e 25,00 lei",
                     "totalul e 65,50 lei, dar subtotalurile dau 70,50 lei", "ancora #montaj nu există",
                     "linkul 'varianta_B_negru.jpg' duce la un fișier care nu există",
                     "linkul 'nu-exista.md' duce la un fișier care nu există", "litere cu sedilă",
                     "cale absolută de pe calculator: /Users/", "pare o coordonată GPS",
                     "note.md:3: cale absolută de pe calculator: /home/"]
        for a in asteptate:
            self.assertTrue(any(a in p for p in rap.probleme), f"{a!r} lipsește din {rap.probleme}")
        self.assertEqual(len(rap.probleme), len(asteptate), rap.probleme)
        avert = ["pasul 3 vine după pasul 1", "punct zecimal: '419.5 cm'", "pare un număr de înmatriculare",
                 "adresă de email: nume@example.com"]
        for a in avert:
            self.assertTrue(any(a in p for p in rap.avertismente), f"{a!r} lipsește din {rap.avertismente}")
        self.assertEqual(len(rap.avertismente), len(avert), rap.avertismente)
        with liniste() as out:
            self.assertEqual(verificari.main(["Proiect proba"]), 1)
        self.assertIn("PROBLEMĂ", out.getvalue())

    def test_proiect_fara_link_in_radacina(self):
        proiect_de_proba(self.tmp)
        with open(os.path.join(self.tmp, "README.md"), "w", encoding="utf-8") as f:
            f.write("# Proiecte\n")
        rap, _ = verificari.verifica("Proiect proba")
        self.assertEqual(rap.probleme, ["README.md: nu are link spre proiectul „Proiect proba” (tabelul de proiecte)"])

    def test_variantele_in_acelasi_folder(self):
        # C și D intră lângă A și B, cu fișiere cu sufix; listele și planurile lor se verifică la fel
        folder, surse = proiect_de_proba(self.tmp)
        for n in ("propunere_C_beton.jpg", "varianta_D_beton.jpg", "comparatie_acum_vs_propuneri_beton.jpg"):
            Image.new("RGB", (32, 24), (90, 90, 90)).save(os.path.join(folder, n))
        shutil.copy(os.path.join(folder, "plan_tehnic_proba.pdf"), os.path.join(folder, "plan_tehnic_proba_beton.pdf"))
        with open(os.path.join(folder, "lista_materiale_beton.md"), "w", encoding="utf-8") as f:
            f.write(LISTA_CURATA.replace("| 1 | 45,50 lei | 45,50 lei |", "| 2 | 45,50 lei | 45,50 lei |"))
        os.makedirs(os.path.join(surse, "beton"))
        jpg_cu_gps(os.path.join(surse, "beton", "original.jpg"))
        rap, _ = verificari.verifica("Proiect proba")
        asteptate = ["lipsește plan_tehnic_proba_beton.png: fiecare plan se publică în PDF și în PNG",
                     "lista_materiale_beton.md:", "2 × 45,50 = 91,00 lei, dar subtotalul e 45,50 lei",
                     "beton/original.jpg: are coordonate GPS"]
        for a in asteptate:
            self.assertTrue(any(a in p for p in rap.probleme), f"{a!r} lipsește din {rap.probleme}")
        self.assertEqual(len(rap.probleme), 3, rap.probleme)
        fara_link = sorted(a.rsplit("nu are link spre ", 1)[1].split(":")[0] for a in rap.avertismente)
        self.assertEqual(fara_link, ["comparatie_acum_vs_propuneri_beton.jpg", "lista_materiale_beton.md",
                                     "plan_tehnic_proba_beton.pdf", "propunere_C_beton.jpg", "varianta_D_beton.jpg"])
        self.assertIn("plan_tehnic_proba_beton.pdf e A3", rap.ok)

        Image.new("RGB", (32, 24), (90, 90, 90)).save(os.path.join(folder, "plan_tehnic_proba_beton.png"))
        foto.pregateste(os.path.join(surse, "beton", "original.jpg"), os.path.join(surse, "beton", "original.jpg"))
        with open(os.path.join(folder, "lista_materiale_beton.md"), "w", encoding="utf-8") as f:
            f.write(LISTA_CURATA)
        with open(os.path.join(folder, "README.md"), "a", encoding="utf-8") as f:
            f.write("\n## Variantele C și D\n\n[C](propunere_C_beton.jpg), [D](varianta_D_beton.jpg), "
                    "[comparația](comparatie_acum_vs_propuneri_beton.jpg), [lista](lista_materiale_beton.md), "
                    "[planul](plan_tehnic_proba_beton.pdf) ([PNG](plan_tehnic_proba_beton.png)).\n")
        rap, _ = verificari.verifica("Proiect proba")
        self.assertEqual((rap.probleme, rap.avertismente), ([], []))
        self.assertIn("lista_materiale_beton.md: 2 rânduri și 1 total verificate", rap.ok)

    def test_avertismentele_si_strict(self):
        proiect_de_proba(self.tmp, readme=README_CURAT.replace("## Întreținere", "## Altceva"))
        with liniste():
            self.assertEqual(verificari.main(["Proiect proba"]), 0)
            self.assertEqual(verificari.main(["--strict", "Proiect proba"]), 1)

    def test_bucatile_mici(self):
        self.assertEqual(verificari.ancora("3. Montaj pas cu pas"), "3-montaj-pas-cu-pas")
        self.assertEqual(verificari.ancora("Cote măsurate (cm)"), "cote-măsurate-cm")
        self.assertEqual(verificari.ancora("A & B"), "a--b")
        self.assertEqual(verificari.ancore("## Pas\n## Pas\n## Alt titlu {#alt}\n"), {"pas", "pas-1", "alt-titlu", "alt"})
        self.assertEqual(verificari.suma("19,49 lei/buc"), (19.49, False))
        self.assertEqual(verificari.suma("**1 065 lei**"), (1065.0, False))
        self.assertEqual(verificari.suma("1\u00a0065,50 lei"), (1065.5, False))
        self.assertEqual(verificari.suma("≈ 440 lei"), (440.0, True))
        self.assertEqual(verificari.suma("[Dedeman](https://x.ro/12) 12,50 lei"), (12.5, False))
        self.assertIsNone(verificari.suma("145 sau 205 lei"))
        self.assertIsNone(verificari.suma("la cerere"))
        self.assertEqual(verificari.cantitate("2 buc"), 2.0)
        self.assertEqual(verificari.cantitate("1,5 m"), 1.5)
        self.assertIsNone(verificari.cantitate("un set"))
        self.assertEqual(verificari.tabele("| a | b \\| c |\n|---|---|\n| 1 | 2 |\n")[0][1:],
                         (["a", "b | c"], [(3, ["1", "2"])]))
        self.assertEqual(verificari.slug("Polite viniluri"), "polite-viniluri")
        self.assertEqual(verificari.slug("Cuier hol"), "cuier-hol")
        for n, text in [(0, "0 rânduri"), (1, "1 rând"), (2, "2 rânduri"), (19, "19 rânduri"), (20, "20 de rânduri"),
                        (101, "101 rânduri"), (120, "120 de rânduri"), (200, "200 de rânduri")]:
            self.assertEqual(verificari.numar_de(n, "rând", "rânduri"), text)


# ------------------------------------------------------------------ scripturile, rulate ca programe

class TestLiniaDeComanda(unittest.TestCase):
    def rul(self, *args):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", MPLBACKEND="Agg")
        return subprocess.run([sys.executable, "-B"] + list(args), capture_output=True, text=True, env=env,
                              cwd=RADACINA, timeout=300)

    def test_fara_argumente_arata_folosirea(self):
        for m in ("foto", "segmente", "comparatie", "preturi", "plan"):
            r = self.rul(os.path.join(UNELTE, f"{m}.py"))
            self.assertEqual(r.returncode, 2, f"{m}: {r.stderr}")
            self.assertIn("python", r.stdout, m)

    def test_verificari_pe_tot_depozitul(self):
        r = self.rul(os.path.join(UNELTE, "verificari.py"), "--toate")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("probleme: 0", r.stdout)

    def test_importul_ca_pachet(self):
        r = self.rul("-c", f"import sys; sys.path.insert(0, {GITHUB!r}); import unelte; "
                           "from unelte import camera, randare, materiale, plan, verificari; print(unelte.__doc__[:10])")
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
