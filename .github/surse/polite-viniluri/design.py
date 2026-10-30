"""Sursa unică pentru cote (cm): polițele pentru viniluri de pe peretele cu televizorul (living).

Coordonate: X de-a lungul peretelui (X = 0 în colțul din stânga), Y în sus de la pardoseală, Z din perete
spre cameră. Valorile marcate „# est.” vin din fotografia calibrată (camera.py) și trebuie verificate cu
ruleta. Lățimea (419) și înălțimea peretelui (250) sunt date de utilizator.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_cam = json.load(open(os.path.join(HERE, "camera.json")))

SITE = dict(
    wall_w=419.0,
    wall_h=250.0,                       # dată de utilizator
    wall_h_photo=round(_cam["H"], 1),   # est.: din fotografie iese ~262, de remăsurat
    baseboard_h=round(_cam["hb"], 1),   # est.
    baseboard_t=1.5,                    # est.
    wall_material="cărămidă",           # presupus, neconfirmat
    device_x=(348.5, 373.7),            # est.: cutia albă de sus, din dreapta televizorului
    device_y=(222.7, 248.5),            # est.
)

# fișa produsului; poziția (x0, y0, z_front) e # est. din fotografie
TV = dict(model="TCL 98C8L", w=216.6, h=123.6, d=5.4, kg=57.5, vesa=(60.0, 50.0),
          x0=round(_cam["xtv"], 1), y0=round(_cam["ytv"], 1), z_front=round(_cam["ztv"], 1))
TV["x1"] = round(TV["x0"] + TV["w"], 1)
TV["y1"] = round(TV["y0"] + TV["h"], 1)
TV["axis"] = round(0.5 * (TV["x0"] + TV["x1"]), 1)

# cioata.eu; poziția e # est. din fotografie
CABINET = dict(model="Cioata Veneto 242 (VE530)", w=242.0, d=48.0, h=67.0, legs=14.0,
               x0=round(_cam["xc"], 1), z_front=round(_cam["zc"], 1))
CABINET["x1"] = CABINET["x0"] + CABINET["w"]

# fișele Klipsch (cu picioare la RP-8000F II); pozițiile boxelor de podea sunt # est.
CENTER = dict(model="Klipsch RP-504C II", w=81.4, h=17.4, d=38.3, kg=16.45)
TOWER = dict(model="Klipsch RP-8000F II", w=27.5, h=109.5, d=46.3, kg=27.85,
             xl=(14.4, 42.9), xr=(387.6, 415.1), z_back=8.4)

LP = dict(size=31.4, kg=0.23)   # coperta unui disc de 12": 31,4 × 31,4 cm; disc + copertă ~230 g

D = dict(
    L=80.0, P=33.0, T=4.0,                # poliță flotantă din stejar masiv: lungime, adâncime, grosime
    gap_tv=10.0,                          # perete liber între marginea televizorului și polițe
    clear=8.0,                            # între discurile de pe polița de jos și polița de sus
    bookend_h=18.0, bookend_d=11.0, bookend_t=0.25,   # opritor L din oțel negru mat, 180 × 110 mm (varianta B)
    oak_t=2.0, oak_d=12.0,                # varianta A: placă de stejar de 2 cm lipită pe același opritor
    rods=4, rod_d=1.2, rod_wall=13.0, rod_shelf=25.0,  # prinderea ascunsă: 4 tije M12 pe poliță
    rod_x=(8.0, 29.0, 51.0, 72.0),        # tijele, de la capătul din stânga al poliței
    hole_d=1.3, hole_len=26.0,            # găurile din cantul din spate al poliței
    wall_hole_d=1.4,                      # gaura din perete pentru ancora chimică (M12)
    rod_len_buy=100.0,                    # tija filetată se vinde la 1 m: 2 bucăți de 38 cm din fiecare
)
D["bookend_a"] = D["bookend_t"] + D["oak_t"]   # grosimea opritorului din varianta A, la capătul rândului
# discurile de sus se termină la nivelul marginii de sus a televizorului
D["top_up"] = round(TV["y1"] - LP["size"], 1)
D["bot_up"] = round(D["top_up"] - D["T"], 1)
D["top_lo"] = round(D["bot_up"] - D["clear"] - LP["size"], 1)
D["bot_lo"] = round(D["top_lo"] - D["T"], 1)
D["x_right"] = round(TV["x1"] + D["gap_tv"], 1)

# cât din lungimea poliței ocupă discurile în randări și la ce capăt stau: spre capătul peretelui, ca lângă
# televizor să rămână loc liber (True = rândul pornește de la capătul din stânga al poliței)
ROWS = {("dreapta", "jos"): (False, 0.74), ("dreapta", "sus"): (False, 0.68)}


def row_extent(side, level, x0):
    """Capetele rândului de discuri (cm), cum apar în randări; la capete stau opritoarele."""
    outer_left, fill = ROWS[(side, level)]
    length = (D["L"] - 2 * D["bookend_a"]) * fill
    if outer_left:
        xs = x0 + D["bookend_a"]
        return xs, xs + length
    xe = x0 + D["L"] - D["bookend_a"]
    return xe - length, xe


def shelves():
    """Cele două polițe, doar în dreapta televizorului: (partea, nivelul, x0, y jos, y sus)."""
    x0 = D["x_right"]
    return [("dreapta", "jos", x0, D["bot_lo"], D["top_lo"]),
            ("dreapta", "sus", x0, D["bot_up"], D["top_up"])]


def capacity():
    """Discuri pe poliță: comod (~90 % din lungimea dintre opritoare, 5 mm pe disc) și ticsit (4 mm pe disc)."""
    usable = D["L"] - 2 * D["bookend_a"] - 1.0
    return int(usable * 0.9 / 0.5), int(usable / 0.4)


def rod_check():
    """Verificarea tijelor, în cazul cel mai defavorabil: polița plină stă doar în tije, ca o consolă.

    Momentul din dreptul peretelui se împarte egal la tije; secțiunea e cea din fundul filetului M12
    (d3 = 9,85 mm). Clasa 4.8 (tija zincată obișnuită) curge la 320 MPa. În realitate polița se sprijină
    și pe perete, la muchia de jos, așa că tijele lucrează mai puțin.
    """
    import math
    kg = loads()[2]
    moment = kg * 9.81 * D["P"] / 2 * 10.0               # N·mm, sarcina în mijlocul adâncimii
    w = math.pi * 9.853 ** 3 / 32.0                       # mm³
    sigma = moment / D["rods"] / w
    return round(sigma), round(320.0 / sigma, 2)


def loads():
    """Greutăți aproximative (kg) pentru o poliță: polița de stejar masiv, discurile (comod), total."""
    shelf = D["L"] * D["P"] * D["T"] / 1000.0 * 0.72
    recs = capacity()[0] * LP["kg"]
    return round(shelf, 1), round(recs, 1), round(shelf + recs, 1)


if __name__ == "__main__":
    print("televizor", TV)
    print("comodă", CABINET)
    print("polițe", D)
    for sh in shelves():
        print("poliță", sh, "tije la X", [sh[2] + r for r in D["rod_x"]], "Y", round((sh[3] + sh[4]) / 2, 1))
    print("perete liber până la capătul din dreapta:", round(SITE["wall_w"] - D["x_right"] - D["L"], 1), "cm")
    print("discuri pe poliță (comod, ticsit):", capacity(), "· greutăți (poliță, discuri, total):", loads())
    print("tije: efort (MPa) și rezervă față de curgere, cazul cel mai defavorabil:", rod_check())
    print("între boxa de podea și polița de jos:", round(D["bot_lo"] - TOWER["h"], 1), "cm")
    print("între discurile de sus și dispozitivul alb:", round(SITE["device_y"][0] - TV["y1"], 1), "cm")
