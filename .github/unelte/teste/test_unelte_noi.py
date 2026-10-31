"""Testele uneltelor aduse din trusa proiectului „Comodă birou”: planul PDF (`plan_pdf.py`), ușile de mobilier
(`usi.py`) și funcțiile noi din modulele existente. Din rădăcina depozitului:

    python -B -m unittest discover -s .github/unelte/teste -v

Nu folosesc rețeaua: prețurile și foaia de produse au un server local, ca în `test_unelte.py`. Nu folosesc nici
planuri reale, care au date personale în cartuș: PDF-urile sunt sintetice, făcute aici cu PyMuPDF, iar fără
PyMuPDF testele lor se sar. Testele de paritate cu sursele din `.github/surse/comoda-birou/` se sar pe o ramură
fără acel folder.
"""
import contextlib
import http.server
import importlib
import io
import json
import math
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
POLITE = os.path.join(GITHUB, "surse", "polite-viniluri")
COMODA = os.path.join(GITHUB, "surse", "comoda-birou")
if GITHUB not in sys.path:
    sys.path.insert(0, GITHUB)

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from unelte import camera, foto, materiale, plan, plan_pdf, preturi, segmente, usi  # noqa: E402

try:
    with warnings.catch_warnings():                 # PyMuPDF (SWIG) dă avertismente de depreciere la import
        warnings.simplefilter("ignore", DeprecationWarning)
        import pymupdf
except ImportError:
    pymupdf = None
ARE_PYMUPDF = pymupdf is not None


@contextlib.contextmanager
def liniste():
    with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()):
        yield out


@contextlib.contextmanager
def surse_comoda():
    """Importă `materials.py` și `drawing.py` din `.github/surse/comoda-birou/` și le scoate apoi din sys.modules."""
    sys.path.insert(0, COMODA)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ResourceWarning)
            yield importlib.import_module
    finally:
        sys.path.remove(COMODA)
        for k, m in list(sys.modules.items()):
            f = getattr(m, "__file__", None)
            if f and os.path.dirname(os.path.abspath(f)) == COMODA:
                del sys.modules[k]


# ------------------------------------------------------------------ ușile de mobilier

class TestUsi(unittest.TestCase):
    """Cazul Cioata Galla 120: dulapul are 3,6 cm liberi de fiecare parte, iar fața lui e la 51,5 cm de perete."""

    def tearDown(self):
        plan.plt.close("all")

    def test_usa_din_dreapta_langa_blat(self):
        r = usi.analizeaza(34, 2.5, 3.6, fata=51.5, obstacol_pana_la=70)
        self.assertAlmostEqual(r["la_90"]["liber"], 1.1, places=3)
        self.assertAlmostEqual(-r["la_max"]["liber"], 5.8, delta=0.05)       # ~5,8 cm în blat, la 110°
        self.assertAlmostEqual(r["contact"], 93.4, delta=0.05)
        self.assertTrue(r["atinge"])
        self.assertAlmostEqual(r["necesar_90"], 2.5, places=3)
        self.assertAlmostEqual(r["in_fata_la_90"], 34.0, places=3)

    def test_usa_din_stanga_langa_perete(self):
        r = usi.analizeaza(51, 2.5, 3.6, fata=51.5)
        self.assertAlmostEqual(r["la_90"]["liber"], 1.1, places=3)
        self.assertAlmostEqual(r["contact"], 91.2, delta=0.05)
        self.assertAlmostEqual(-r["la_max"]["liber"], 16.2, delta=0.05)
        self.assertIsNone(r["obstacol"][1])

    def test_fara_contact(self):
        r = usi.analizeaza(34, 2.5, 25.0, fata=51.5, obstacol_pana_la=70)
        self.assertFalse(r["atinge"])
        self.assertGreater(r["la_max"]["liber"], 0)
        r = usi.analizeaza(34, 2.5, 3.6, fata=51.5, obstacol_pana_la=40)     # blatul se termină în spatele feței
        self.assertIsNone(r["contact"])
        self.assertIsNone(r["la_90"]["ocupat"])

    def test_colturile(self):
        np.testing.assert_allclose(usi.colturi_usa(0, 34, 2.5), [(-34, 0), (0, 0), (0, 2.5), (-34, 2.5)], atol=1e-9)
        np.testing.assert_allclose(usi.colturi_usa(90, 34, 2.5), [(0, 34), (0, 0), (2.5, 0), (2.5, 34)], atol=1e-9)

    def test_desenul_in_planul_tehnic(self):
        fig = plan.pagina("Probă – ușile dulapului", "plan la 1:15")
        ax = plan.make_axes(fig, 20, 40, (-20, 220), (-12, 130), "PLAN – VEDERE DE SUS (1:15)", plan.MM15,
                            invert=True)
        plan.hatch(ax, -12, -12, 220, 0)
        plan.rect(ax, 126.2, 0, 220, 70, plan.C["tv"], z=3)
        plan.rect(ax, 3.6, 0.5, 122.6, 51.5, plan.C["oak"], plan.C["oak_e"], 0.5, z=4)
        usi.deseneaza(ax, usi.analizeaza(34, 2.5, 3.6, fata=51.5, obstacol_pana_la=70), "dreapta", x_balama=122.6,
                      k=plan.K15, legenda=(0.30, 0.01))
        usi.deseneaza(ax, usi.analizeaza(51, 2.5, 3.6, fata=51.5), "stanga", x_balama=3.6, k=plan.K15,
                      legenda=(0.30, 0.06))
        bad, look, info = plan.verifica_figura(fig)
        self.assertEqual(bad, [])
        texte = [t.get_text() for t in ax.texts]
        self.assertIn("5,8", texte)                       # cât intră ușa din dreapta în blat
        self.assertIn("16,2", texte)
        self.assertTrue(any("ușa de 51 cm" in t for t in texte))

    def test_imaginea_si_linia_de_comanda(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "usa.png")
            w, h = usi.imagine(usi.analizeaza(34, 2.5, 3.6, fata=51.5, obstacol_pana_la=70), "dreapta", p)
            with Image.open(p) as im:
                self.assertEqual(im.size, (w, h))
            baza = ["--latime", "34", "--grosime", "2,5", "--balama", "dreapta", "--distanta", "3.6", "--fata", "51.5"]
            with liniste() as out:
                self.assertEqual(usi.main(baza + ["--obstacol-pana-la", "70", "--json"]), 1)
            self.assertAlmostEqual(json.loads(out.getvalue())["la_90"]["liber"], 1.1, places=3)
            with liniste() as out:
                self.assertEqual(usi.main(baza + ["--obstacol-pana-la", "70", "--imagine", p]), 1)
            self.assertIn("rămân 1,1 cm liberi", out.getvalue())
            self.assertIn("ar intra 5,8 cm în obstacol", out.getvalue())
            with liniste():
                self.assertEqual(usi.main(baza + ["--unghi-max", "90"]), 0)
                self.assertEqual(usi.main(baza + ["--balama", "sus"]), 2)
                self.assertEqual(usi.main(["--latime", "34"]), 2)
                self.assertEqual(usi.main(baza + ["--necunoscut"]), 2)
                self.assertEqual(usi.main([]), 2)
                self.assertEqual(usi.main(["--help"]), 0)


# ------------------------------------------------------------------ planul în PDF

K_PLAN = 327 / 177.6        # cm pe pt, ca la planul etajului din „Comodă birou” (~1:52,2, nu 1:50)


def plan_sintetic(dest, rotatie=0):
    """Un plan de probă: o cameră de 327 × 366 cm cu pereți gri, un gol de ușă în dreptul etichetei, o cameră
    vecină, un pat alb, o axă întreruptă și o linie de cotă. Întoarce fețele interioare (x0, y0, x1, y1), în pt."""
    doc = pymupdf.open()
    pg = doc.new_page(width=842, height=595)
    x0, y0 = 200.0, 150.0
    x1, y1 = x0 + 327 / K_PLAN, y0 + 366 / K_PLAN

    def zid(a, b, c, d):
        pg.draw_rect(pymupdf.Rect(a, b, c, d), color=None, fill=(0.6, 0.6, 0.6))

    zid(x0 - 10, y0 - 10, (x0 + x1) / 2, y0)            # peretele de sus, din două bucăți
    zid((x0 + x1) / 2, y0 - 10, x1 + 10, y0)
    zid(x0 - 10, y1, x1 + 10, y1 + 10)
    zid(x1, y0 - 10, x1 + 10, y1 + 10)
    zid(x0 - 10, y0 - 10, x0, y0 + 40)                   # peretele din stânga, cu golul ușii în dreptul etichetei
    zid(x0 - 10, y1 - 30, x0, y1 + 10)
    zid(90, y0 - 10, 100, y1 + 10)                       # peretele camerei vecine
    pg.draw_rect(pymupdf.Rect(x0 + 20, y0 + 20, x0 + 100, y0 + 70), color=(0, 0, 0), fill=(1, 1, 1), width=0.3)
    pg.draw_line((x0 - 30, y0 + 100), (x1 + 30, y0 + 100), color=(0, 0, 0), width=0.2, dashes="[4 2] 0")
    pg.draw_line((x0, y0 - 25), (x1, y0 - 25), color=(0, 0, 0), width=0.3)
    pg.insert_text((x0 + 70, y0 - 28), "327", fontsize=8)
    pg.insert_text((x0 + 60, y0 + 100), "DORMITOR 2", fontsize=9)
    pg.insert_text((x0 + 75, y0 + 112), "E 03", fontsize=9)
    import matplotlib
    font = os.path.join(matplotlib.get_data_path(), "fonts", "ttf", "DejaVuSans.ttf")
    pg.insert_text((600, 100), "CAMERĂ DE ZI", fontsize=9, fontfile=font, fontname="dejavu")
    pg.insert_text((600, 130), "BAIE 10", fontsize=9)
    if rotatie:
        pg.set_rotation(rotatie)
    doc.save(dest)
    doc.close()
    return x0, y0, x1, y1


@unittest.skipUnless(ARE_PYMUPDF, "PyMuPDF nu e instalat (pip install pymupdf)")
class TestPlanPdf(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.pdf = os.path.join(cls.tmp, "plan.pdf")
        cls.rotit = os.path.join(cls.tmp, "plan_rotit.pdf")
        cls.camera = plan_sintetic(cls.pdf)
        plan_sintetic(cls.rotit, 90)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def setUp(self):
        self.doc = plan_pdf.deschide(self.pdf)

    def tearDown(self):
        self.doc.close()

    def test_info(self):
        p = plan_pdf.info(self.doc)["detalii"][0]
        self.assertEqual((p["format"], p["rotatie"], p["latime_pt"]), ("A4 orizontal", 0, 842.0))
        with plan_pdf.deschide(self.rotit) as doc:
            p = plan_pdf.info(doc)["detalii"][0]
        self.assertEqual((p["format"], p["rotatie"]), ("A4 orizontal", 90))     # pagina nerotită

    def test_cauta(self):
        pg = plan_pdf.pagina(self.doc, 1)
        g = plan_pdf.gaseste(pg, "dormitor2")
        self.assertEqual([x["text"] for x in g], ["DORMITOR 2"])
        g = plan_pdf.gaseste(pg, "DORMITOR 2 E 03")                            # pe două rânduri
        self.assertEqual((len(g), g[0]["randuri"]), (1, 2))
        self.assertEqual(len(plan_pdf.gaseste(pg, "camera de zi")), 1)         # fără diacritice
        self.assertEqual(len(plan_pdf.gaseste(pg, "BAIE 1")), 1)
        self.assertEqual(plan_pdf.gaseste(pg, "BAIE 1", cuvinte_intregi=True), [])
        self.assertEqual(plan_pdf.simplu("Șanț ţânţar"), "sant tantar")

    def test_cuvinte_si_linii(self):
        pg = plan_pdf.pagina(self.doc, 1)
        z = plan_pdf.dreptunghi((180, 130, 400, 370))
        self.assertEqual([w[4] for w in plan_pdf.cuvinte(pg, z)], ["DORMITOR", "2", "E", "03"])
        self.assertEqual(plan_pdf.dreptunghi((360, 260, 800, 740), px=144), z)       # zona din pixeli, la 144 dpi
        oriz, vert = plan_pdf.linii(pg, z, lungime_min=20, unite=True)
        sus = [s for s in oriz if abs(s.c - 150) < 0.01]
        self.assertEqual((len(sus), sus[0].bucati), (1, 2))                    # peretele de sus, unit
        self.assertFalse(any(s.intrerupt for s in oriz))                      # axa întreruptă nu apare
        oriz, _ = plan_pdf.linii(pg, z, din="linii", lungime_min=20, cu_intrerupte=True)
        self.assertTrue(any(s.intrerupt and abs(s.c - 250) < 0.01 for s in oriz))

    def test_camera_cu_scara_reala(self):
        rez = plan_pdf.masoara_camera(self.doc, "DORMITOR 2", cota_cm=327, verifica_cm=366, scara=50)
        self.assertTrue(rez["gata"])
        x0, y0, x1, y1 = self.camera
        f = rez["fete"]
        self.assertEqual([round(f[k].c, 2) for k in plan_pdf.LATURI], [round(v, 2) for v in (x0, x1, y0, y1)])
        self.assertAlmostEqual(rez["cm_pe_pt"], 1.8412, places=4)
        self.assertAlmostEqual(rez["scara_echivalenta"], 52.19, places=2)       # nu 1:50, cât scrie în cartuș
        self.assertAlmostEqual(rez["abatere_fata_de_cartus_pct"], 4.38, places=2)
        self.assertEqual(rez["interior_cm"], (327.0, 366.0))
        self.assertLess(abs(rez["verificare"]["diferenta_cm"]), 0.1)
        doar_cartus = plan_pdf.masoara_camera(self.doc, "DORMITOR 2", scara=50)
        self.assertAlmostEqual(doar_cartus["interior_cm"][0], 313.3, places=1)  # scara din cartuș greșește cu 14 cm
        self.assertIsNone(plan_pdf.masoara_camera(self.doc, "BUCĂTĂRIE"))
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "camera.png")
            w, h = plan_pdf.imagine_camera(self.doc, rez, p, dpi=100)
            with Image.open(p) as im:
                self.assertEqual(im.size, (w, h))
            self.assertFalse(plan_pdf.avertizeaza_daca_nu_e_ignorat(p))    # nu e într-un depozit git

    def test_randarea_paginii_rotite(self):
        with plan_pdf.deschide(self.rotit) as doc:
            pg = plan_pdf.pagina(doc, 1)
            z = plan_pdf.dreptunghi((180, 130, 400, 370))
            img, ox, oy, k = plan_pdf.randeaza(pg, z, 100)
            self.assertEqual(pg.rotation, 90)                                   # rotația rămâne neschimbată
            plan_pdf.grila(img, ox, oy, k, z, 50)
        self.assertEqual(img.size, (306, 334))                                  # zona nerotită, la 100 dpi
        self.assertEqual((ox, oy), (250, 180))
        self.assertAlmostEqual(k, 100 / 72)
        with plan_pdf.deschide(self.rotit) as doc:
            rez = plan_pdf.masoara_camera(doc, "DORMITOR 2", cota_cm=327)
        self.assertEqual(rez["interior_cm"], (327.0, 366.0))

    @unittest.skipUnless(shutil.which("git"), "git nu e instalat")
    def test_avertismentul_in_depozit(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "init", "-q", tmp], check=True)
            with open(os.path.join(tmp, ".gitignore"), "w") as f:
                f.write("out/\n")
            os.makedirs(os.path.join(tmp, "out"))
            with liniste():
                self.assertTrue(plan_pdf.avertizeaza_daca_nu_e_ignorat(os.path.join(tmp, "plan.png")))
                self.assertFalse(plan_pdf.avertizeaza_daca_nu_e_ignorat(os.path.join(tmp, "out", "plan.png")))

    def test_linia_de_comanda(self):
        with tempfile.TemporaryDirectory() as tmp:
            png = os.path.join(tmp, "zona.png")
            with liniste() as out:
                self.assertEqual(plan_pdf.main(["camera", self.pdf, "DORMITOR 2", "--cota-cm", "327",
                                                "--verifica-cm", "366", "--scara", "50", "--json"]), 0)
            rez = json.loads(out.getvalue())
            self.assertEqual(rez["interior_cm"], [327.0, 366.0])
            self.assertEqual(rez["fete"]["stânga"]["c"], 200.0)
            with liniste() as out:
                self.assertEqual(plan_pdf.main(["camera", self.pdf, "DORMITOR 2", "--cota-cm", "327,0",
                                                "--verifica-cm", "366", "--imagine", os.path.join(tmp, "c.png")]), 0)
            self.assertIn("1:52,2", out.getvalue())
            self.assertIn("Camera: 327,0 cm pe x × 366,0 cm pe y", out.getvalue())
            with liniste() as out:
                self.assertEqual(plan_pdf.main(["randeaza", self.pdf, png, "--zona", "180", "130", "400", "370",
                                                "--dpi", "100", "--grila", "50"]), 0)
                self.assertEqual(plan_pdf.main(["info", self.pdf]), 0)
                self.assertEqual(plan_pdf.main(["cauta", self.pdf, "E 03"]), 0)
                self.assertEqual(plan_pdf.main(["cauta", self.pdf, "LIPSĂ"]), 1)
                self.assertEqual(plan_pdf.main(["cuvinte", self.pdf, "--zona", "180", "130", "400", "370"]), 0)
                self.assertEqual(plan_pdf.main(["linii", self.pdf, "--zona", "180", "130", "400", "370",
                                                "--uneste", "--json"]), 0)
            self.assertTrue(os.path.isfile(png))
            with liniste() as out:
                self.assertEqual(plan_pdf.main([]), 2)
                self.assertEqual(plan_pdf.main(["--help"]), 0)
                self.assertEqual(plan_pdf.main(["nimic", self.pdf]), 2)
                self.assertEqual(plan_pdf.main(["camera", self.pdf]), 2)
                self.assertEqual(plan_pdf.main(["info", os.path.join(tmp, "lipsa.pdf")]), 2)
                self.assertEqual(plan_pdf.main(["randeaza", self.pdf, png, "--dpi", "multe"]), 2)
                self.assertEqual(plan_pdf.main(["linii", self.pdf, "--din", "toate-toate"]), 2)
            self.assertIn("python plan_pdf.py", out.getvalue())


# ------------------------------------------------------------------ segmentele: mărirea și muchia slabă

def treapta(h, w, c, m, sus, jos, latime=0.6, verticala=False):
    """O treaptă netedă de luminozitate: `sus` deasupra dreptei v = c + m·u, `jos` dedesubt (la verticală,
    u = c + m·v). Centrul pixelului (i, j) e în (i, j), ca la LSD."""
    jj, ii = np.mgrid[0:h, 0:w].astype(float)
    d = (ii - (c + m * jj)) if verticala else (jj - (c + m * ii))
    return sus + (jos - sus) * 0.5 * (1 + np.tanh(d / latime))


class TestSegmenteNoi(unittest.TestCase):
    def test_marirea_nu_schimba_detectia_obisnuita(self):
        img = foto.citeste(os.path.join(POLITE, "original.jpg"))
        np.testing.assert_array_equal(segmente.detecteaza(img, 20), segmente.detecteaza(img, 20, marire=1))

    def test_marirea_pastreaza_coordonatele(self):
        u8 = np.clip(treapta(200, 320, 60.25, 0.1, 0.2, 0.9) * 255 + 0.5, 0, 255).astype(np.uint8)
        muchie = segmente.muchie_slaba(u8, (40, 110), de_la=20, pana_la=300, pas=10)
        abateri = {k: segmente.abateri_segment(muchie, segmente.detecteaza(u8, 50, marire=k)[0]) for k in (1, 2, 3)}
        for k, d in abateri.items():
            self.assertLess(max(map(abs, d)), 0.3, k)
            self.assertLess(abs(d[0] - abateri[1][0]), 0.15, k)    # fără −0,5 la conversie, diferența ar fi 0,25 px

    def test_marirea_prinde_muchiile_fine(self):
        img = np.full((120, 90), 0.8)
        for y in range(20, 100, 9):
            img[y:y + 1, 10:80] = 0.55                                   # linii subțiri, de 1 px
        u8 = cv2.GaussianBlur(np.clip(img * 255, 0, 255).astype(np.uint8), (0, 0), 0.8)
        mic, mare = segmente.detecteaza(u8, 15), segmente.detecteaza(u8, 15, marire=2)
        self.assertGreater(len(mare), len(mic))
        self.assertTrue(np.all(mare >= -0.5) and np.all(mare[:, 0::2] <= 89.5) and np.all(mare[:, 1::2] <= 119.5))

    def test_muchia_slaba(self):
        rng = np.random.RandomState(3)
        img = treapta(200, 320, 80.3, 0.05, 0.80, 0.785)                 # 1,5 % diferență: tavan alb pe perete alb
        img[95:, 200:260] = 0.70                                         # altă muchie, mai tare, pe o porțiune
        bgr = np.repeat((img + rng.normal(0, 0.002, img.shape))[..., None], 3, 2).astype(np.float32)
        for s in segmente.detecteaza(bgr, 20):                           # LSD n-o prinde
            d = (s[1::2] - (80.3 + 0.05 * s[0::2])) / math.hypot(1, 0.05)
            self.assertGreater(np.abs(d).max(), 1.0, s)
        r = segmente.muchie_slaba(bgr, (70, 105), pas=8)
        m, c = r["dreapta"]
        u = np.array([0, 160, 319.0])
        np.testing.assert_allclose(m * u + c, 80.3 + 0.05 * u, atol=0.05)
        self.assertFalse(r["pastrate"][(r["puncte"][:, 0] > 205) & (r["puncte"][:, 0] < 255)].any())
        self.assertLess(r["rms"], 0.2)
        self.assertEqual(len(r["segment"]), 4)
        d = segmente.abateri_segment(r, [230, 80.3 + 0.05 * 230, 300, 80.3 + 0.05 * 300])
        self.assertLess(max(map(abs, d)), 0.05)
        d = segmente.abateri_segment(r, [230, 82.3 + 0.05 * 230, 300, 82.3 + 0.05 * 300])
        self.assertAlmostEqual(d[0], 2.0, delta=0.05)
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "muchie.png")
            w, h = segmente.deseneaza_muchie(bgr, r, p, [[230, 91.8, 300, 95.3]])
            self.assertEqual(cv2.imread(p).shape, (h, w, 3))
        with self.assertRaises(ValueError):
            segmente.muchie_slaba(bgr, (70, 71))

    def test_muchia_verticala(self):
        img = treapta(200, 320, 150.7, -0.03, 0.6, 0.62, verticala=True)
        r = segmente.muchie_slaba(img.astype(np.float32), (130, 170), verticala=True, pas=10, semn=1)
        m, c = r["dreapta"]
        v = np.array([0, 100, 199.0])
        np.testing.assert_allclose(m * v + c, 150.7 - 0.03 * v, atol=0.05)
        self.assertLess(abs(r["segment"][1]), 1e-9)                       # segmentul merge de sus în jos
        gresit = segmente.muchie_slaba(img.astype(np.float32), (130, 170), verticala=True, pas=10, semn=-1)
        self.assertGreater(abs(gresit["dreapta"][1] - 150.7), 5)         # semnul greșit: muchia se luminează

    def test_linia_de_comanda(self):
        u8 = np.clip(treapta(200, 320, 80.3, 0.05, 0.80, 0.785) * 255 + 0.5, 0, 255).astype(np.uint8)
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "slaba.png")
            cv2.imwrite(src, u8)
            ctrl = os.path.join(tmp, "muchie.png")
            with liniste() as out:
                self.assertEqual(segmente.main(["--muchie", src, "--banda", "70", "105", "--pas", "40",
                                                "--segment", "230", "91,8", "300", "95.3", "--imagine", ctrl]), 0)
            self.assertIn("e în prelungirea ei", out.getvalue())
            self.assertIn("Segmentul pentru segments.json: [0.0, 80.", out.getvalue())
            self.assertTrue(os.path.isfile(ctrl))
            with liniste() as out:
                self.assertEqual(segmente.main(["--muchie", src, "--banda", "70", "105", "--segment", "230", "93.8",
                                                "300", "97.3"]), 1)
            self.assertIn("NU e pe aceeași dreaptă", out.getvalue())
            with liniste():
                self.assertEqual(segmente.main(["--muchie", src, "--banda", "70"]), 2)
                self.assertEqual(segmente.main(["--muchie", src, "--banda", "70", "105", "--pas", "x"]), 2)
                self.assertEqual(segmente.main(["--muchie", src, "--banda", "70", "105", "--altceva"]), 2)
                self.assertEqual(segmente.main([src, os.path.join(tmp, "out"), "--marire", "2"]), 0)
            with open(os.path.join(tmp, "out", "segmente_toate.json")) as f:
                self.assertIsInstance(json.load(f), list)


# ------------------------------------------------------------------ profilul erorii la calibrare

ADEVAR = dict(f=800.0, yaw=0.12, pitch=0.06, roll=0.01, cx=160.0, cy=135.0, cz=330.0, k1=0.0)
SCENA = dict(H=250.0, xw=380.0, xt=110.0, yt=95.0)
TV = (120.0, 70.0)


def dreapta_scena(nume, q):
    """Peretele din față, colțul din stânga cu tavanul și pardoseala lui și, dacă e în q, un televizor de
    120 × 70 cm cu poziția necunoscută."""
    H, xw = q["H"], q["xw"]
    d = {"ceil": ([0, H, 0], [xw, H, 0]), "floor": ([0, 0, 0], [xw, 0, 0]), "corner_left": ([0, 0, 0], [0, H, 0]),
         "wall_right": ([xw, 0, 0], [xw, H, 0]), "ceil_left": ([0, H, 0], [0, H, 100]),
         "floor_left": ([0, 0, 0], [0, 0, 100])}
    if "xt" in q:
        x0, y0 = q["xt"], q["yt"]
        x1, y1 = x0 + TV[0], y0 + TV[1]
        d.update({"tv_top": ([x0, y1, 4], [x1, y1, 4]), "tv_bottom": ([x0, y0, 4], [x1, y0, 4]),
                  "tv_left": ([x0, y0, 4], [x0, y1, 4]), "tv_right": ([x1, y0, 4], [x1, y1, 4])})
    return d[nume]


def segmente_sintetice(cu_tv, zgomot=0.3, seed=1):
    rng = np.random.RandomState(seed)
    cam = camera.Camera(dict(ADEVAR, pp=[512, 384]))
    q = dict(ADEVAR, **(SCENA if cu_tv else dict(H=250.0, xw=380.0)))
    nume = ["ceil", "floor", "corner_left", "wall_right", "ceil_left", "floor_left"]
    nume += ["tv_top", "tv_bottom", "tv_left", "tv_right"] if cu_tv else []
    segs = {}
    for n in nume:
        A, B = (np.array(p, float) for p in dreapta_scena(n, q))
        uv = cam.project(np.array([A + t * (B - A) for t in (0.15, 0.85)])) + rng.normal(0, zgomot, (2, 2))
        segs[n] = [list(uv.ravel())]
    return segs


class TestProfilulErorii(unittest.TestCase):
    P0 = dict(f=760, yaw=0.1, pitch=0.05, roll=0, cx=150, cy=130, cz=300, H=240, xw=360)

    def test_fara_obiect_cunoscut_tavanul_nu_e_determinat(self):
        qs = camera.profil(segmente_sintetice(False), dreapta_scena, self.P0, (1024, 768), "H", (230, 250, 270))
        rms = [q["rms"] for q in qs]
        self.assertLess(max(rms) - min(rms), 1e-3)                         # aceeași eroare la orice tavan
        self.assertEqual([q["H"] for q in qs], [230.0, 250.0, 270.0])
        self.assertAlmostEqual(qs[2]["cz"] / qs[0]["cz"], 270 / 230, places=3)   # scena se scalează cu tavanul
        self.assertIn("H nu e determinat", camera.rezumat_profil(qs, "H", arata=("cz", "xw")))

    def test_obiectul_cunoscut_fixeaza_scara(self):
        p0 = dict(self.P0, xt=100, yt=90)
        qs = camera.profil(segmente_sintetice(True), dreapta_scena, p0, (1024, 768), "H", (230, 250, 270),
                           fixe={"roll": 0.01})
        rms = [q["rms"] for q in qs]
        self.assertEqual(int(np.argmin(rms)), 1)
        self.assertGreater(min(rms[0], rms[2]) - rms[1], 1.0)
        self.assertTrue(all(q["roll"] == 0.01 for q in qs))
        text = camera.rezumat_profil(qs, "H", arata=("xt",))
        self.assertIn("e cel mai mic la H = 250,00", text)
        self.assertNotIn("nu e determinat", text)


# ------------------------------------------------------------------ materialele, planul și prețurile

class TestMaterialeNoi(unittest.TestCase):
    def test_furnirul(self):
        t = materiale.veneer(30, 20, np.random.RandomState(5))
        self.assertEqual((t.shape, t.dtype), ((202, 302), np.float32))
        self.assertAlmostEqual(float(t.mean()), 1.0, delta=0.01)
        self.assertTrue(0.7 <= t.min() and t.max() <= 1.3)
        self.assertLess(t.std(axis=0).mean(), t.std(axis=1).mean())      # fibra e verticală: în lungul ei variază puțin
        o = materiale.veneer(30, 20, np.random.default_rng(5), vertical=False)
        self.assertEqual(o.shape, (202, 302))
        self.assertGreater(o.std(axis=0).mean(), o.std(axis=1).mean())

    def test_riflajul(self):
        u = np.linspace(0, 12, 1201)
        f = materiale.reeding(u, 2.4)
        np.testing.assert_allclose(materiale.reeding(u + 2.4, 2.4), f, atol=1e-9)    # se repetă la fiecare baghetă
        self.assertLess(materiale.reeding(0.01, 2.4), 0.5)                            # rostul e întunecat
        self.assertGreater(materiale.reeding(1.2, 2.4), 0.95)                         # mijlocul baghetei e luminat

    @unittest.skipUnless(os.path.isdir(COMODA), "sursele „Comodă birou” nu sunt în această copie")
    def test_ca_in_comoda_birou(self):
        with surse_comoda() as imp:
            m = imp("materials")
            for vertical in (True, False):
                np.testing.assert_array_equal(
                    materiale.veneer(30, 20, np.random.RandomState(5), vertical, 1.3, r=m.R_TEX),
                    m.veneer(30, 20, np.random.RandomState(5), vertical, 1.3))
            u = np.linspace(-10, 30, 2001)
            np.testing.assert_array_equal(materiale.reeding(u, 2.4), m.reeding(u, 2.4))


def _png(fn):
    fig = plan.plt.figure(figsize=(3, 2))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 20)
    ax.axis("off")
    fn(ax, 10, 8, 5, "A", 20, 15)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100)
    plan.plt.close(fig)
    return buf.getvalue()


class TestPlanNoi(unittest.TestCase):
    def test_callout_si_scara(self):
        fig = plan.pagina("Probă")
        ax = plan.make_axes(fig, 20, 60, (-10, 110), (-20, 70), "VEDERE (1:15)", plan.MM15)
        plan.rect(ax, 0, 0, 100, 60, plan.C["wall"])
        plan.callout(ax, 3, 8, 6, "A", -4, 24)
        self.assertEqual([round(p.radius, 3) for p in ax.patches if hasattr(p, "radius")], [6.0])
        self.assertIn("A", [t.get_text() for t in ax.texts])
        self.assertEqual(plan.verifica_figura(fig)[0], [])
        plan.plt.close(fig)
        self.assertEqual(plan.scara(15), (plan.MM15, plan.K15))
        self.assertEqual(plan.scara(50), (plan.MM50, plan.K50))
        self.assertEqual(plan.scara(5), (plan.MM5, plan.K5))

    @unittest.skipUnless(os.path.isdir(COMODA), "sursele „Comodă birou” nu sunt în această copie")
    def test_callout_ca_in_comoda_birou(self):
        with surse_comoda() as imp:
            self.assertEqual(_png(plan.callout), _png(imp("drawing").callout))


class _Magazin(http.server.BaseHTTPRequestHandler):
    PAGINI = {
        "/js": (200, "text/html", '<html><head><title>Element</title></head><body><div id="root"></div>'
                                  "<noscript>You need to enable JavaScript to run this app.</noscript></body></html>"),
        "/cf": (403, "text/html", "<html><head><title>Just a moment...</title></head></html>"),
        "/poza.png": (200, "image/png", None),
        "/pagina.jpg": (200, "text/html", "<html>Just a moment...</html>"),
    }

    def do_GET(self):
        if self.path not in self.PAGINI:
            self.send_error(404)
            return
        cod, tip, corp = self.PAGINI[self.path]
        if corp is None:
            buf = io.BytesIO()
            Image.new("RGBA", (60, 40), (40, 40, 40, 255)).save(buf, "PNG")
            date = buf.getvalue()
        else:
            date = corp.encode("utf-8")
        self.send_response(cod)
        self.send_header("Content-Type", tip)
        self.send_header("Content-Length", str(len(date)))
        self.end_headers()
        self.wfile.write(date)

    def log_message(self, *args):
        pass


@contextlib.contextmanager
def magazin():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Magazin)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        with mock.patch.dict(os.environ, {"no_proxy": "127.0.0.1,localhost", "NO_PROXY": "127.0.0.1,localhost"}), \
                warnings.catch_warnings():
            warnings.simplefilter("ignore", ResourceWarning)
            yield f"http://127.0.0.1:{srv.server_address[1]}"
    finally:
        srv.shutdown()
        srv.server_close()


LUNG = "<p>" + "Descrierea produsului, cu dimensiunile și materialele. " * 80 + "</p>"


class TestPreturiNoi(unittest.TestCase):
    def test_foloseste_browserul(self):
        js = ('<html><head><title>BoConcept</title></head><body><div id="root"></div><noscript>You need to enable '
              "JavaScript to run this app.</noscript></body></html>")
        r = preturi.analizeaza(js)
        self.assertEqual((r["stare"], r["browser"]), ("fara_pret", True))
        self.assertIn("folosește browserul", preturi.rand(r))
        r = preturi.analizeaza("<html><title>Just a moment...</title></html>")
        self.assertEqual((r["stare"], r["browser"]), ("blocat", True))
        r = preturi.analizeaza(f"<html><title>Produs</title><body>{LUNG}</body></html>")
        self.assertEqual((r["stare"], r["browser"]), ("fara_pret", False))
        self.assertNotIn("browser", preturi.rand(r))
        r = preturi.analizeaza(f"<html><body>{LUNG}</body></html>", "https://www.boconcept.com/en-ro/p/element")
        self.assertTrue(r["browser"])

    def test_prp_la_cioata(self):
        pagina = ('<html><head><title>Dulap Galla 120</title><script type="application/ld+json">{"@type": "Product", '
                  '"offers": {"@type": "Offer", "price": "3901.00", "priceCurrency": "RON"}}</script></head><body>'
                  f"<h1>Dulap Galla 120</h1><p>3.901,00 Lei</p><p>Pret recomandat producator (PRP): 4876</p>{LUNG}"
                  "</body></html>")
        r = preturi.analizeaza(pagina)
        self.assertEqual((r["stare"], r["pret"], r["prp"], r["browser"]), ("ok", 3901.0, 4876.0, False))
        self.assertIn("ok         3 901 RON · PRP 4 876 RON", preturi.rand(r))
        r = preturi.analizeaza(pagina.replace('"price": "3901.00", ', "").replace(
            "Pret recomandat producator (PRP): 4876", "Preț recomandat producător (PRP): 4.876,00 lei."))
        self.assertEqual((r["stare"], r["prp"]), ("fara_pret", 4876.0))
        self.assertIn("PRP 4 876", preturi.rand(r))
        for text, v in [("PRP: 4 876 lei", 4876.0), ("Rec. retail price RON 12,345", 12345.0),
                        ("Preț recomandat: 1.065,50 lei", 1065.5)]:
            self.assertEqual(preturi.analizeaza(f"<p>{text}</p>")["prp"], v, text)
        self.assertIsNone(preturi.analizeaza("<p>Preț: 120 lei</p>")["prp"])

    def test_citeste_offline(self):
        with magazin() as url:
            r = preturi.citeste(url + "/js", timeout=5)
            self.assertEqual((r["stare"], r["browser"], r["cod_http"]), ("fara_pret", True, 200))
            r = preturi.citeste(url + "/cf", timeout=5)
            self.assertEqual((r["stare"], r["browser"], r["mesaj"]), ("blocat", True, "HTTP 403"))
            self.assertIn("HTTP 403; folosește browserul", preturi.rand(r))
            r = preturi.citeste(url + "/lipsa", timeout=5)
            self.assertEqual((r["stare"], r["browser"]), ("eroare", False))

    def test_foaia_de_produse(self):
        with tempfile.TemporaryDirectory() as tmp, magazin() as url:
            Image.new("RGB", (400, 300), (200, 160, 110)).save(os.path.join(tmp, "stejar.jpg"))
            lista = os.path.join(tmp, "linkuri.txt")
            with open(lista, "w", encoding="utf-8") as f:
                f.write(f"# finisaje\nNO Natural Oak {os.path.join(tmp, 'stejar.jpg')}\nNero {url}/poza.png\n"
                        f"{url}/pagina.jpg\nFE Ferro {url}/lipsa.png\n")
            surse = preturi.surse_din_fisier(lista)
            self.assertEqual([e for e, _ in surse], ["NO Natural Oak", "Nero", None, "FE Ferro"])
            dest = os.path.join(tmp, "out", "foaie_finisaje.jpg")
            os.makedirs(os.path.dirname(dest))
            size, sarite = preturi.foaie(surse, dest, latura=120)
            self.assertEqual(size, (2 * 120 + 3 * 10, 120 + 20 + 2 * 10))
            self.assertEqual(sarite, [("pagina", "nu e o imagine (poate o pagină de eroare sau de verificare "
                                                  "anti-robot)"), ("FE Ferro", "HTTP 404")])
            self.assertEqual(os.listdir(os.path.join(tmp, "out", "foaie_finisaje")), ["02_Nero.png"])
            self.assertEqual(foto.metadate(dest), {"exif": 0, "gps": False, "altele": []})
            with liniste() as out:
                self.assertEqual(preturi.main(["--foaie", dest, lista]), 1)
                self.assertEqual(preturi.main(["--foaie", dest, os.path.join(tmp, "stejar.jpg")]), 0)
                self.assertEqual(preturi.main(["--foaie", dest, os.path.join(tmp, "lipsa.jpg")]), 1)
                self.assertEqual(preturi.main(["--help"]), 0)
            self.assertIn("2 din 4 imagini", out.getvalue())
            with self.assertRaises(ValueError):
                preturi.foaie([os.path.join(tmp, "lipsa.jpg")], dest)


# ------------------------------------------------------------------ scripturile noi, rulate ca programe

class TestLiniaDeComandaNoi(unittest.TestCase):
    def rul(self, *args):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", MPLBACKEND="Agg")
        return subprocess.run([sys.executable, "-B"] + list(args), capture_output=True, text=True, env=env,
                              cwd=RADACINA, timeout=300)

    def test_fara_argumente_si_ajutorul(self):
        for m in ("plan_pdf", "usi"):
            r = self.rul(os.path.join(UNELTE, f"{m}.py"))
            self.assertEqual(r.returncode, 2, f"{m}: {r.stderr}")
            self.assertIn("python", r.stdout, m)
            r = self.rul(os.path.join(UNELTE, f"{m}.py"), "--help")
            self.assertEqual(r.returncode, 0, f"{m}: {r.stderr}")
        r = self.rul(os.path.join(UNELTE, "usi.py"), "--latime", "51", "--grosime", "2.5", "--balama", "stanga",
                     "--distanta", "3.6", "--fata", "51.5")
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("Atinge obstacolul la 91,2°", r.stdout)

    def test_importul_ca_pachet(self):
        r = self.rul("-c", f"import sys; sys.path.insert(0, {GITHUB!r}); from unelte import plan_pdf, usi; "
                           "print(plan_pdf.__doc__[:5], usi.__doc__[:5])")
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
