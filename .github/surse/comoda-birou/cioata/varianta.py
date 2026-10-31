"""Variantele C și D ale comodei de lângă birou: bufetele Cioata Raya 116 și Veneto 116, cu sertarul opțional.

Cele două bufete au același corp (116 × 48 × 82 cm, pe picioare de 14 cm, cu corpul de la 20 cm) și diferă doar
prin uși: Raya are lamele verticale din stejar și o bandă neagră la mijloc (mânerul ușii din stânga), Veneto are
uși din microciment antracit (C9) și un mâner rotund din stejar, ca la comoda TV Veneto din living. Cotele vin din
desenul cotat și din fișa Cioata (RA340, VE340, VE390); ce e măsurat pe fotografiile producătorului e `# est.`.

Coordonatele sunt cele ale proiectului (`../design.py`): X de-a lungul peretelui, de la colț; Y în sus; Z din perete.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)                                   # .github/surse/comoda-birou
GH = os.path.dirname(os.path.dirname(SRC))                    # .github
for p in (GH, SRC):
    if p not in sys.path:
        sys.path.insert(0, p)

from design import DESK, SITE  # noqa: E402,F401  (cotele camerei și ale biroului, din proiect)
from unelte import usi  # noqa: E402

# Corpul comun Raya / Veneto (desenul cotat Cioata: 116 × 48 × 82, corp 62, uși 55 × 55, picioare 14, corp de la 20).
BUF = {
    "w": 116.0, "d": 48.0, "h": 82.0,
    "body_y0": 20.0,            # dedesubtul corpului
    "leg_h": 14.0,              # picioarele, până la traversa de stejar
    "top_t": 2.2,               # blatul  # est.
    "side_t": 2.2,              # lateralele  # est.
    "bottom_t": 2.2,            # fundul corpului  # est.
    "door_w": 55.0, "door_h": 55.0,
    "door_t": 2.2,              # grosimea ușii (MDF cu microciment sau PAL cu lamele)  # est.
    "gap": 0.3,                 # rostul dintre uși și față de ramă  # est.
    "reveal": 2.3,              # banda neagră de sub blat, deasupra ușilor  # est.
    "rail_h": 6.0,              # traversa de stejar retrasă, între picioare (de la 14 la 20 cm)
    "rail_in": 5.0,             # cât e retrasă traversa: e prinsă între picioarele din față, în planul lor  # est.
    "leg_d": 2.4,               # picioarele rotunde, negre  # est.
    "leg_in_x": 12.5,           # axul picioarelor, de la laterale (desenul: ~12,7)  # est.
    "leg_in_z": 5.0,            # axul picioarelor, de la față și de la spate  # est.
    "strip_w": 6.0,             # Raya: banda neagră de pe muchia ușii din stânga  # est.
    "handle_d": 28.0,           # Veneto: mânerul rotund din stejar (desenul: ~28,6)  # est.
    "handle_t": 1.5,            # cât iese mânerul din ușă  # est.
}
# Sertarul opțional VE390, în compartimentul cu uși: ansamblul 95 × 39 × 22, sertarul 85 × 27 × 11 (interior).
SERTAR = {"w": 95.0, "d": 39.0, "h": 22.0, "in_w": 85.0, "in_d": 27.0, "in_h": 11.0}

# Așezarea: centrat în peretele liber dintre colț și birou, ca ambele uși să ajungă la 90°.
FREE = DESK["x0"]                                             # ~126,2 cm, din fotografie (de măsurat)
X0 = (FREE - BUF["w"]) / 2.0
X1 = X0 + BUF["w"]
Z0, Z1 = 0.0, BUF["d"]                                        # spatele lipit de perete (corpul e peste plintă)
GAP_DESK = FREE - X1
GAP_CORNER = X0

VARIANTE = {
    "C": dict(nume="Raya", cod="RA340", usa="lamele", pret=5668.00, prp=7085.0,
              link="https://www.cioata.eu/bufet-2-usi-raya-116cm.html",
              fisier="propunere_C_cioata_raya.jpg", titlu="Propunere C – Cioata Raya, stejar"),
    "D": dict(nume="Veneto", cod="VE340", usa="microciment", pret=6156.00, prp=7695.0,
              link="https://www.cioata.eu/bufet-2-usi-veneto-116cm.html",
              fisier="varianta_D_cioata_veneto.jpg", titlu="Varianta D – Cioata Veneto, microciment"),
}
SERTAR_PRET = 1341.00
SERTAR_LINK = "https://www.cioata.eu/sertar-optional-veneto.html"
SERTAR_SCOS = 30.0      # cât iese sertarul din corp (sertarul util are 27 cm adâncime)  # est.
POLITA_Y = 52.0         # polița, mutată deasupra sertarului (fața de jos, de la pardoseală)  # est.


def lamele(seed=30):
    """Lamelele ușilor Raya (C), aceleași în randare și în plan: pentru fiecare ușă (stânga, dreapta), marginile
    lamelelor în cm de la marginea din stânga a ușii, tonul, decalajul texturii și cât iese lamela (0 sau 0,25 cm)."""
    rl = np.random.RandomState(seed)
    rez = []
    for _ in range(2):
        edges, x = [0.0], 0.0
        while x < BUF["door_w"]:
            x += float(rl.choice([5.5, 7.0, 8.5, 10.0, 12.0]))
            edges.append(min(x, BUF["door_w"]))
        tones = 1 + 0.09 * rl.randn(len(edges))
        offs = rl.uniform(0, 25, size=(len(edges), 2))
        relief = rl.choice([0.0, 0.0, 0.25], size=len(edges))
        rez.append((np.array(edges), tones, offs, relief))
    return rez


def doors():
    """Ușile la deschidere: cea din stânga spre peretele din colț, cea din dreapta spre blatul biroului."""
    st = usi.analizeaza(BUF["door_w"], BUF["door_t"], GAP_CORNER, fata=Z1)
    dr = usi.analizeaza(BUF["door_w"], BUF["door_t"], GAP_DESK, fata=Z1, obstacol_pana_la=DESK["d"])
    return st, dr


if __name__ == "__main__":
    print(f"peretele liber: ~{FREE:.1f} cm; bufetul: X {X0:.1f} … {X1:.1f} (la ~{GAP_CORNER:.1f} cm de colț "
          f"și ~{GAP_DESK:.1f} cm de birou), {BUF['w']} × {BUF['d']} × {BUF['h']} cm")
    print(f"corpul de la {BUF['body_y0']} la {BUF['h']} cm; ușile de la {BUF['body_y0'] + BUF['bottom_t']:.1f} "
          f"la {BUF['body_y0'] + BUF['bottom_t'] + BUF['door_h']:.1f} cm; blatul biroului la ~{DESK['h']} "
          f"(între {DESK['h_min']} și {DESK['h_max']})")
    st, dr = doors()
    for nume, r in (("stânga (spre colț)", st), ("dreapta (spre birou)", dr)):
        print(f"ușa din {nume}: la 90° rămân {r['la_90']['liber']:.1f} cm; contact la "
              f"{r['contact'] if r['contact'] is not None else 'niciodată'}°; la {r['unghi_max']:.0f}°: "
              f"{r['la_max']['liber']:.1f} cm (negativ = ar intra în obstacol)")
    for k, v in VARIANTE.items():
        print(f"{k}: {v['nume']} {v['cod']} {v['pret']:.2f} lei + sertarul {SERTAR_PRET:.2f} = "
              f"{v['pret'] + SERTAR_PRET:.2f} lei")
