"""Testele uneltelor aduse din variantele C și D ale proiectului „Comodă birou”, bufetele Cioata Raya 116 și
Veneto 116: lamelele ușilor Raya (`materiale.lamele`, `lamela_la`, `lamele_umbrire`), legenda ușilor cu nume și
obstacol (`usi.deseneaza`) și umbrele pieselor pe picioare (`randare.umbre_pe_picioare`). Din rădăcina depozitului:

    python -B -m unittest discover -s .github/unelte/teste -v

Testele de paritate rulează funcțiile din `.github/surse/comoda-birou/cioata/` (și metoda `shadows` din
`render_galla.py`, din folderul de deasupra), fără randarea întreagă și fără planul întreg; pe o ramură fără acel
folder, se sar.
"""
import contextlib
import importlib
import os
import sys
import types
import unittest
import warnings

sys.dont_write_bytecode = True

AICI = os.path.dirname(os.path.abspath(__file__))
UNELTE = os.path.dirname(AICI)
GITHUB = os.path.dirname(UNELTE)
COMODA = os.path.join(GITHUB, "surse", "comoda-birou")
CIOATA = os.path.join(COMODA, "cioata")
if GITHUB not in sys.path:
    sys.path.insert(0, GITHUB)

import numpy as np  # noqa: E402

from unelte import camera, materiale, plan, randare, usi  # noqa: E402

ARE_CIOATA = os.path.isdir(CIOATA)
FARA_CIOATA = "sursele variantelor C și D din „Comodă birou” nu sunt în această copie"


@contextlib.contextmanager
def surse_cioata():
    """Importă scripturile din `.github/surse/comoda-birou/cioata/`; `varianta` pune singur în sys.path și folderul
    de deasupra. La ieșire, sys.path revine cum era, iar modulele celor două foldere ies din sys.modules: proiectele
    au module cu aceleași nume (camera, core, design), care altfel s-ar amesteca între ele."""
    cale = list(sys.path)
    sys.path.insert(0, CIOATA)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ResourceWarning)
            yield importlib.import_module
    finally:
        sys.path[:] = cale
        for k, m in list(sys.modules.items()):
            f = getattr(m, "__file__", None)
            if f and os.path.dirname(os.path.abspath(f)) in (CIOATA, COMODA):
                del sys.modules[k]


class _Panza:
    """Ține minte funcțiile date lui `multiply_plane`, ca umbrele din proiect să se compare fără randare."""

    def __init__(self):
        self.f = {}

    def multiply_plane(self, fac_fn, axis, value, a0, a1, b0, b1):
        self.f[axis] = (fac_fn, (a0, a1, b0, b1))


def _grila(a0, a1, b0, b1, n=(301, 211)):
    return np.meshgrid(np.linspace(a0, a1, n[0]), np.linspace(b0, b1, n[1]))


# ------------------------------------------------------------------ lamelele ușilor Raya

class TestLamele(unittest.TestCase):
    LATIMI = (5.5, 7.0, 8.5, 10.0, 12.0)

    def test_marginile(self):
        for latime in (55.0, 40.3, 12.0, 3.0):
            m, ton, dec, rel = materiale.lamele(latime, np.random.RandomState(4))
            self.assertEqual(m[0], 0.0)
            self.assertEqual(m[-1], latime)                     # ultima lamelă se taie exact la marginea frontului
            self.assertTrue(np.all(np.diff(m) > 0))
            for d in np.diff(m)[:-1]:
                self.assertIn(d, self.LATIMI)
            self.assertLessEqual(np.diff(m)[-1], max(self.LATIMI))
            n = len(m)
            self.assertEqual((ton.shape, dec.shape, rel.shape), ((n,), (n, 2), (n,)))
            self.assertTrue(np.all((dec >= 0) & (dec <= 25)))
            self.assertTrue(set(rel.tolist()) <= {0.0, 0.25})

    def test_latimea_fixa(self):
        m, *_ = materiale.lamele(10.0, np.random.RandomState(0), latimi=(3.0,))
        np.testing.assert_array_equal(m, [0, 3, 6, 9, 10])

    def test_cu_generator(self):
        a = materiale.lamele(55.0, np.random.default_rng(3))
        b = materiale.lamele(55.0, np.random.default_rng(3))
        self.assertEqual(a[0][-1], 55.0)
        for x, y in zip(a, b):
            np.testing.assert_array_equal(x, y)
        self.assertAlmostEqual(float(np.mean(materiale.lamele(5000.0, np.random.default_rng(1))[1])), 1.0, delta=0.02)

    def test_latimi_gresite(self):
        for latime, latimi in ((55.0, (0.0, 5.0)), (55.0, (-2.0,)), (0.0, (5.5,))):
            with self.assertRaises(ValueError):
                materiale.lamele(latime, np.random.RandomState(0), latimi=latimi)

    def test_lamela_la(self):
        m = np.array([0.0, 5.5, 12.5, 22.5])
        np.testing.assert_array_equal(materiale.lamela_la(np.array([-1.0, 0.0, 5.49, 5.5, 22.0, 22.5, 30.0]), m),
                                      [0, 0, 0, 1, 2, 2, 2])

    def test_rosturile_sunt_intunecate(self):
        m = np.array([0.0, 5.5, 12.5, 22.5, 30.0])
        f = materiale.lamele_umbrire
        for a, b in zip(m[:-1], m[1:]):
            self.assertEqual(f((a + b) / 2, m), 1.0)           # mijlocul lamelei
            for u in (a + 0.02, b - 0.02):
                self.assertLess(f(u, m), 0.7)                  # rostul
        self.assertAlmostEqual(float(f(12.5, m)), 0.55)        # pe margine: 1 − 0,45
        u = np.linspace(12.5, 12.7, 21)
        self.assertTrue(np.all(np.diff(f(u, m)) >= 0))         # se luminează spre mijlocul lamelei
        self.assertEqual(f(np.array([[3.0, 12.55]]), m).shape, (1, 2))

    def test_lamelele_care_ies(self):
        m = np.array([0.0, 10.0, 20.0, 30.0])
        rel = np.array([0.0, 0.25, 0.0, 0.0])
        f = materiale.lamele_umbrire
        self.assertLess(f(10.3, m, rel), f(10.3, m))            # umbra pe muchia din stânga a lamelei care iese
        self.assertGreater(f(19.7, m, rel), f(19.7, m))         # lumina pe muchia din dreapta
        self.assertEqual(f(5.0, m, rel), f(5.0, m))             # lamelele plate rămân cum sunt
        self.assertEqual(f(25.0, m, rel), 1.0)

    @unittest.skipUnless(ARE_CIOATA, FARA_CIOATA)
    def test_ca_in_varianta(self):
        """Cu același RandomState, două uși la rând: aceleași margini, tonuri, decalaje și relief."""
        with surse_cioata() as imp:
            v = imp("varianta")
            for seed in (30, 7, 2026):
                rl = np.random.RandomState(seed)
                noi = [materiale.lamele(v.BUF["door_w"], rl) for _ in range(2)]
                for ref, nou in zip(v.lamele(seed), noi):
                    self.assertEqual(len(ref), len(nou))
                    for a, b in zip(ref, nou):
                        np.testing.assert_array_equal(b, a)

    @unittest.skipUnless(ARE_CIOATA, FARA_CIOATA)
    def test_umbrirea_ca_in_randeaza(self):
        """`door_raya` pentru ușa din dreapta (fără banda neagră), cu textura, tonurile și lumina egale cu 1: culoarea
        e stejarul înmulțit cu umbrirea, deci trebuie să fie exact stejarul × `lamele_umbrire`."""
        with surse_cioata() as imp:
            r = imp("randeaza")
            s = np.linspace(-1, 56, 5701)[None, :]
            zero = np.zeros(s.shape, int)
            for m, ton, dec, rel in imp("varianta").lamele(30):
                scena = types.SimpleNamespace(lams=[None, (m, np.ones_like(ton), np.zeros_like(dec), rel)],
                                              M=np.ones((1, 1), np.float32), E0=1.0, wb=np.ones(3, np.float32),
                                              tex_lam=np.ones((40, 40), np.float32))
                culoare = r.BufetScene.door_raya(scena, 1)(s, np.full_like(s, 20.0), None, zero, zero)
                f = materiale.lamele_umbrire(s, m, rel)
                for c in range(3):
                    np.testing.assert_array_equal(culoare[..., c], np.float64(r.OAK_NO[c]) * f)


# ------------------------------------------------------------------ legenda ușilor

STANGA = "ușa din stânga (spre colț)"
DREAPTA = "ușa din dreapta (spre birou)"


class TestLegendaUsilor(unittest.TestCase):
    """Bufetul Cioata de 116 cm, centrat între colț și birou: 5,1 cm liberi de fiecare parte, fața la 48 cm."""

    @classmethod
    def setUpClass(cls):
        cls.st = usi.analizeaza(55, 2.2, 5.1, fata=48)
        cls.dr = usi.analizeaza(55, 2.2, 5.1, fata=48, obstacol_pana_la=70)

    def tearDown(self):
        plan.plt.close("all")

    @staticmethod
    def deseneaza(rez, balama, **kw):
        fig = plan.plt.figure(figsize=(4, 3))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(-80, 200)
        ax.set_ylim(130, -20)
        usi.deseneaza(ax, rez, balama, 60.0, k=plan.K15, fs=4.6, **kw)
        return ax

    def legenda(self, rez, balama, **kw):
        ax = self.deseneaza(rez, balama, **kw)
        return [t.get_text() for t in ax.texts if t.get_transform() == ax.transAxes]

    def test_fara_nume_e_neschimbata(self):
        self.assertEqual(self.legenda(self.st, "stanga"), [
            "ușa de 55 cm la 90° (plin); la 110° (punctat) intră 15,8 cm în obstacol; atinge obstacolul la 93° (roșu)"])
        self.assertEqual(self.legenda(self.dr, "dreapta"), [
            "ușa de 55 cm la 90° (plin); la 110° (punctat) intră 5,2 cm în obstacol; atinge obstacolul la 97,5° (roșu)"])
        galla = usi.analizeaza(34, 2.5, 3.6, fata=51.5, obstacol_pana_la=70)
        self.assertEqual(self.legenda(galla, "dreapta"), [
            "ușa de 34 cm la 90° (plin); la 110° (punctat) intră 5,8 cm în obstacol; atinge obstacolul la 93,4° (roșu)"])
        departe = usi.analizeaza(34, 2.5, 25.0, fata=51.5, obstacol_pana_la=70)
        self.assertEqual(self.legenda(departe, "dreapta"), ["ușa de 34 cm la 90° (plin); la 110° (punctat)"])
        self.assertEqual(self.legenda(self.st, "stanga", legenda=False, nume=STANGA), [])

    def test_cu_nume_si_obstacol(self):
        self.assertEqual(self.legenda(self.st, "stanga", nume=STANGA, obstacol=("perete", "peretele")), [
            "ușa din stânga (spre colț): la 90° (plin); la 110° (punctat) ar intra 15,8 cm în perete; "
            "atinge peretele la ~93° (roșu)"])
        self.assertEqual(self.legenda(self.dr, "dreapta", nume=DREAPTA, obstacol=("blat", "blatul")), [
            "ușa din dreapta (spre birou): la 90° (plin); la 110° (punctat) ar intra 5,2 cm în blat; "
            "atinge blatul la ~97,5° (roșu)"])
        departe = usi.analizeaza(34, 2.5, 25.0, fata=51.5, obstacol_pana_la=70)
        self.assertEqual(self.legenda(departe, "dreapta", nume="ușa mică", obstacol=("blat", "blatul")),
                         ["ușa mică: la 90° (plin); la 110° (punctat)"])

    def test_doar_unul_dintre_ele(self):
        self.assertEqual(self.legenda(self.st, "stanga", nume=STANGA), [
            "ușa din stânga (spre colț): la 90° (plin); la 110° (punctat) intră 15,8 cm în obstacol; "
            "atinge obstacolul la 93° (roșu)"])
        self.assertEqual(self.legenda(self.st, "stanga", obstacol=["perete", "peretele"]), [
            "ușa de 55 cm la 90° (plin); la 110° (punctat) ar intra 15,8 cm în perete; atinge peretele la ~93° (roșu)"])

    def test_obstacolul_e_o_pereche(self):
        for gresit in ("perete", ("perete",), ("un", "doi", "trei")):
            with self.assertRaises(ValueError):
                self.deseneaza(self.st, "stanga", obstacol=gresit)

    def test_restul_desenului_nu_se_schimba(self):
        def restul(ax):
            return [(t.get_text(), t.get_position()) for t in ax.texts if t.get_transform() != ax.transAxes]
        a = self.deseneaza(self.dr, "dreapta")
        b = self.deseneaza(self.dr, "dreapta", nume=DREAPTA, obstacol=("blat", "blatul"))
        self.assertEqual(restul(a), restul(b))
        self.assertEqual(len(a.patches), len(b.patches))
        self.assertEqual(len(a.lines), len(b.lines))

    @unittest.skipUnless(ARE_CIOATA, FARA_CIOATA)
    def test_ca_in_planul_c_si_d(self):
        """Legenda scrisă de mână în `vedere_plan` din `planul.py` iese la fel din `usi.deseneaza`, cu aceleași uși."""
        with surse_cioata() as imp:
            v, planul = imp("varianta"), imp("planul")
            fig = plan.pagina("Probă – planul C și D")
            ax = plan.make_axes(fig, 4, 4, planul.PLAN_X, planul.PLAN_Z, "PLAN (1:15)", plan.MM15, invert=True)
            planul.vedere_plan(ax)
            ref = [t for t in ax.texts if t.get_text().startswith("ușa din")]
            fig2 = plan.pagina("Probă – trusa")
            ax2 = plan.make_axes(fig2, 4, 4, planul.PLAN_X, planul.PLAN_Z, "PLAN (1:15)", plan.MM15, invert=True)
            st, dr = v.doors()
            usi.deseneaza(ax2, st, "stanga", v.X0, k=plan.K15, fs=4.6, legenda=(0.52, 0.105), latime_obstacol=15.0,
                          nume=STANGA, obstacol=("perete", "peretele"))
            usi.deseneaza(ax2, dr, "dreapta", v.X1, k=plan.K15, fs=4.6, legenda=(0.52, 0.105 - 0.07),
                          nume=DREAPTA, obstacol=("blat", "blatul"))
            noi = [t for t in ax2.texts if t.get_transform() == ax2.transAxes]
            self.assertEqual(len(ref), 2)
            self.assertEqual([t.get_text() for t in noi], [t.get_text() for t in ref])
            for a, b in zip(ref, noi):
                self.assertEqual((b.get_position(), b.get_fontsize(), b.get_color(), b.get_ha(), b.get_va(),
                                  b.get_zorder()),
                                 (a.get_position(), a.get_fontsize(), a.get_color(), a.get_ha(), a.get_va(),
                                  a.get_zorder()))
                self.assertEqual(b.get_bbox_patch().get_facecolor(), a.get_bbox_patch().get_facecolor())


# ------------------------------------------------------------------ umbrele pieselor pe picioare

class TestUmbrePePicioare(unittest.TestCase):
    """Bufetul Cioata de 116 × 48 × 82 cm, cu corpul de la 20 cm, la 5,1 cm de colț; picioarele, de 2,4 cm."""
    X0, X1, Z0, Z1, SUS, DEDESUBT = 5.1, 121.1, 0.0, 48.0, 82.0, 20.0
    PICIOARE = [(x, z) for x in (17.6, 108.6) for z in (5.0, 43.0)]

    def umbre(self, **kw):
        return randare.umbre_pe_picioare(self.X0, self.X1, self.Z0, self.Z1, self.SUS, self.DEDESUBT, self.PICIOARE,
                                         1.2, **kw)

    def test_peretele(self):
        perete, _ = self.umbre()
        xm = (self.X0 + self.X1) / 2
        self.assertAlmostEqual(float(perete(xm, 5.0)), 1 - 0.62)                 # banda de sub corp, plină
        self.assertAlmostEqual(float(perete(xm, 40.0)), 1.0)                      # în spatele corpului
        self.assertAlmostEqual(float(perete(xm, 120.0)), 1.0, places=4)           # departe, deasupra blatului
        self.assertAlmostEqual(float(perete(300.0, 50.0)), 1.0, places=6)
        self.assertLess(perete(xm, 82.5), 1.0)                                    # umbra fină de deasupra blatului
        self.assertLess(perete(self.X1 + 1, 50.0), 0.9)                           # umbra laterală, în dreapta
        self.assertEqual(perete(self.X0 - 1, 50.0), 1.0)
        X, Y = _grila(self.X0 - 15, self.X1 + 20, 0, self.SUS + 25)
        f = perete(X, Y)
        self.assertTrue(np.all((f >= 1 - 0.68 - 1e-12) & (f <= 1)))

    def test_pardoseala(self):
        _, pard = self.umbre()
        xm = (self.X0 + self.X1) / 2
        sub, fata, departe = pard(xm, 24.0), pard(xm, self.Z1 + 1), pard(xm, self.Z1 + 70)
        self.assertTrue(sub < fata < departe)
        self.assertGreater(departe, 0.999)
        self.assertAlmostEqual(float(pard(17.6 + 1.2, 43.0)), 1 - 0.68)          # lângă picior: ocluzia de contact
        self.assertLess(pard(17.6, 48.0 + 1.0), pard(xm, 48.0 + 1.0))             # și în fața lui, în afara corpului
        self.assertLess(pard(xm, 2.0), sub)                                       # spre perete, mai închis
        X, Z = _grila(self.X0 - 20, self.X1 + 25, 0, self.Z1 + 30)
        f = pard(X, Z)
        self.assertTrue(np.all((f >= 1 - 0.68 - 1e-12) & (f <= 1)))

    def test_in_afara_peretelui_si_a_pardoselii(self):
        perete, pard = self.umbre()
        xm = (self.X0 + self.X1) / 2
        np.testing.assert_array_equal(perete(np.array([xm, xm]), np.array([-0.5, -30.0])), [1.0, 1.0])
        np.testing.assert_array_equal(pard(np.array([xm, xm]), np.array([-0.5, -1e9])), [1.0, 1.0])

    def test_latura(self):
        dreapta, _ = self.umbre()
        stanga, _ = self.umbre(latura="stanga")
        xm = (self.X0 + self.X1) / 2
        X, Y = _grila(self.X0 - 15, self.X1 + 15, 0, self.SUS + 25)
        np.testing.assert_allclose(stanga(2 * xm - X, Y), dreapta(X, Y), atol=1e-12)    # în oglindă
        with self.assertRaises(ValueError):
            self.umbre(latura="sus")

    def test_in_panza_trusei(self):
        """Pe pânza din trusă, peretele și pardoseala primesc fiecare doar factorul lor, și în fâșia în care
        dreptunghiurile de pixeli ale celor două se suprapun."""
        q = dict(f=200.0, yaw=0.0, pitch=0.0, roll=0.0, cx=63.1, cy=100.0, cz=300.0)
        cam = camera.Camera(q, size=(320, 240))
        cv = randare.Canvas(np.ones((240, 320, 3), np.float32), cam)
        perete, pard = self.umbre()
        cv.multiply_wall(perete, self.X0 - 15, self.X1 + 20, 0, self.SUS + 25)
        cv.multiply_floor(pard, self.X0 - 20, self.X1 + 25, 0, self.Z1 + 30)
        u = 160                                                                   # mijlocul bufetului
        for v in (150, 175, 180, 185, 187, 200):                                  # perete, apoi pardoseală
            P = cam.backproject([u + 0.5, v + 0.5], "Z", 0.0)
            ok = P[1] >= 0
            if not ok:
                P = cam.backproject([u + 0.5, v + 0.5], "Y", 0.0)
            asteptat = perete(P[0], P[1]) if ok else pard(P[0], P[2])
            self.assertAlmostEqual(float(cv.img[v, u, 0]), float(asteptat), places=5)
        self.assertAlmostEqual(float(cv.img[180, u, 0]), 1 - 0.62, places=5)     # banda de sub corp, pe perete

    @unittest.skipUnless(ARE_CIOATA, FARA_CIOATA)
    def test_ca_in_randeaza(self):
        """Cu coeficienții impliciți, aceleași valori ca `shadows` din `cioata/randeaza.py`, pe zonele de acolo."""
        with surse_cioata() as imp:
            r, v = imp("randeaza"), imp("varianta")
            p = _Panza()
            r.BufetScene.shadows(None, p)
            b = v.BUF
            legs = [(x, z) for x in (v.X0 + b["leg_in_x"], v.X1 - b["leg_in_x"])
                    for z in (v.Z0 + b["leg_in_z"], v.Z1 - b["leg_in_z"])]
            perete, pard = randare.umbre_pe_picioare(v.X0, v.X1, v.Z0, v.Z1, b["h"], b["body_y0"], legs,
                                                     b["leg_d"] / 2)
            for axa, f in (("Z", perete), ("Y", pard)):
                ref, zona = p.f[axa]
                A, B = _grila(*zona)
                np.testing.assert_array_equal(f(A, B), ref(A, B))

    @unittest.skipUnless(ARE_CIOATA, FARA_CIOATA)
    def test_ca_in_render_galla(self):
        """Cu coeficienții dulapului Galla, aceleași valori ca `shadows` din `render_galla.py`."""
        with surse_cioata() as imp:
            imp("varianta")                                     # pune `comoda-birou/` în sys.path
            rg = imp("render_galla")
            g = rg.Galla()
            p = _Panza()
            rg.GallaScene.shadows(types.SimpleNamespace(g=g), p)
            legs = [(x, z) for x in (g.x0 + 3, g.x1 - 3) for z in (g.z0 + 3, g.z1 - 3)]
            perete, pard = randare.umbre_pe_picioare(
                g.x0, g.x1, g.z0, g.z1, rg.G["h"], rg.G["leg_h"], legs, 1.0,
                perete_margine=2.5, perete_lateral=0.22, perete_sub=0.42, perete_sub_peste=1.0,
                perete_sub_inaltime=4.0, perete_max=0.6, pardoseala_retras=0.0, pardoseala_contur=0.36,
                pardoseala_contur_lungime=5.0, pardoseala_perete=0.14, contact=0.35, contact_lungime=1.3,
                pardoseala_max=0.62)
            for axa, f in (("Z", perete), ("Y", pard)):
                ref, zona = p.f[axa]
                A, B = _grila(*zona, n=(401, 251))
                np.testing.assert_array_equal(f(A, B), ref(A, B))


if __name__ == "__main__":
    unittest.main()
