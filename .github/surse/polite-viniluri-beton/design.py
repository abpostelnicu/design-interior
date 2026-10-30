"""Sursa unică pentru cote (cm): polițele din beton decorativ și stejar pentru viniluri, de pe peretele cu
televizorul (living).

Aceleași 2 polițe flotante ca în proiectul „Polite viniluri”, în aceleași locuri și pe tije ascunse, dar
orizontalele sunt din microciment pe miez de placaj de mesteacăn, iar între ele stă o verticală din stejar
masiv, ca la comoda Cioata Veneto (rama din stejar, fronturile din microciment). Fiecare poliță se montează
separat, pe tijele ei; verticala vine lipită din atelier de polița de jos și se oprește la 3 mm sub polița de
sus (rost de umbră), deci nu duce nimic din polița de sus.

Coordonate: X de-a lungul peretelui (X = 0 în colțul din stânga), Y în sus de la pardoseală, Z din perete
spre cameră. Valorile marcate „# est.” vin din fotografia calibrată (camera.py) și trebuie verificate cu
ruleta. Lățimea (419) și înălțimea peretelui (250) sunt date de utilizator.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "camera.json")) as _f:
    _cam = json.load(_f)

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

# densități (g/cm³), # est.: placajul de mesteacăn ~0,68; microcimentul întărit ~1,8; stejarul ~0,72; betonul
# GFRC (armat cu fibră de sticlă) ~2,1, doar pentru comparația cu o poliță turnată din beton masiv
RHO = dict(ply=0.68, micro=1.8, oak=0.72, gfrc=2.1)

D = dict(
    L=80.0, P=33.0, T=4.0,                # poliță flotantă din microciment pe miez de placaj: lungime, adâncime, grosime
    core_t=3.6, coat_t=0.2,               # miezul: 2 plăci de placaj de mesteacăn de 18 mm, lipite; microcimentul: ~2 mm
    edge_r=0.3,                           # muchiile care se văd, rotunjite cu R3, ca microcimentul să nu se ciobească
    gap_tv=10.0,                          # perete liber între marginea televizorului și polițe
    clear=8.0,                            # între discurile de pe polița de jos și polița de sus
    bookend_h=18.0, bookend_d=11.0, bookend_t=0.25,   # opritor L din oțel, 180 × 110 mm, sub placa de stejar
    oak_t=2.0, oak_d=12.0,                # placa de stejar de 2 cm lipită pe fața exterioară a opritorului
    vert_t=4.0,                           # verticala: panou din stejar masiv încleiat, cu fibra pe verticală
    vert_gap=0.3,                         # rostul de umbră dintre capătul de sus al verticalei și polița de sus
    dowel_d=0.8, dowel_len=4.0,           # cepuri din fag Ø8 × 40 mm:
    dowel_in=1.5, dowel_out=2.5,          # 1,5 cm în poliță, 2,5 cm în verticală
    dowel_z=(6.0, 16.5, 27.0),            # cele 3 cepuri de la piciorul verticalei, de la perete; doar cel din mijloc
                                          # e lipit și în verticală, celelalte stau în găuri ovale (stejarul lucrează)
    dowel_slot=1.1,                       # găurile ovale din verticală: 8 × 11 mm, lungi pe adâncime
    glue_w=10.0,                          # adezivul de la piciorul verticalei: doar pe ~10 cm în jurul cepului din mijloc
    rods=4, rod_d=1.2, rod_wall=13.0, rod_shelf=25.0,  # prinderea ascunsă: 4 tije M12 pe poliță
    rod_x=(8.0, 29.0, 51.0, 72.0),        # tijele, de la capătul din stânga al poliței
    rod_fy=640.0,                         # tijă de clasa 8.8: curge la 640 MPa (cea obișnuită, de 4.8, la 320)
    hole_d=1.4, hole_len=26.0,            # canalele din poliță: două semicanale frezate în plăcile miezului, înainte
                                          # de lipire, ca să iasă drepte și paralele
    rod_glue=8.0,                         # adezivul epoxidic din canal: doar pe ultimii ~8 cm ai tijei, lângă perete
    wall_hole_d=1.4, wall_hole_len=14.0,  # gaura din perete pentru ancora chimică (M12), în zidărie plină; în
                                          # cărămidă cu goluri sau în BCA, cu manșon-sită, cum cere producătorul
    jig_d=20.0,                           # șablonul: 80 × 20 × 4 cm, din același miez, cu aceleași canale
    test_kg=55.0,                         # proba de încărcare, înainte de discuri: peste polița cu discurile ticsite
    rod_len_buy=100.0,                    # tija filetată se vinde la 1 m: 2 bucăți de 38 cm din fiecare
)
D["bookend_a"] = D["bookend_t"] + D["oak_t"]   # grosimea opritorului îmbrăcat în stejar, la capătul rândului
# discurile de sus se termină la nivelul marginii de sus a televizorului
D["top_up"] = round(TV["y1"] - LP["size"], 1)
D["bot_up"] = round(D["top_up"] - D["T"], 1)
D["top_lo"] = round(D["bot_up"] - D["clear"] - LP["size"], 1)
D["bot_lo"] = round(D["top_lo"] - D["T"], 1)
D["x_right"] = round(TV["x1"] + D["gap_tv"], 1)
# verticalele: fața din stânga a fiecăreia, în cm de la capătul din stânga al poliței. Una singură, cu fața din
# stânga în dreptul marginii din stânga a boxei de podea de dedesubt, ca linia boxei să urce mai departe; stă
# între tijele de la 51 și 72 cm, deci cepurile nu întâlnesc găurile tijelor
VERTS = [round(TOWER["xr"][0] - D["x_right"], 1)]
# verticala stă în locașul de 2 mm lăsat în microcimentul poliței de jos și se oprește la 3 mm sub polița de sus
D["vert_h"] = round(D["bot_up"] - D["vert_gap"] - (D["top_lo"] - D["coat_t"]), 1)   # lungimea piesei


def compartments(level):
    """Golurile unei polițe (cm, de la capătul din stânga): jos, despărțite de verticale; sus, unul singur."""
    if level != "jos":
        return [(0.0, D["L"])]
    edges = [0.0] + [v for x in VERTS for v in (x, round(x + D["vert_t"], 1))] + [D["L"]]
    return [(edges[i], edges[i + 1]) for i in range(0, len(edges), 2)]


# rândurile de discuri, cum apar în randări: (golul, partea spre care e împins rândul, cât din gol ocupă).
# Jos, rândul mare se sprijină în verticală, iar lângă televizor rămâne loc liber; golul mic de la capăt e plin.
# Capătul lipit de verticală nu are opritor; capetele libere au câte unul.
ROWS = {"jos": [(0, "dreapta", 0.65), (1, "stânga", 1.0)], "sus": [(0, "dreapta", 0.68)]}


def row_extents(level, x0):
    """Rândurile de discuri ale unei polițe: (x început, x sfârșit, opritor în stânga, opritor în dreapta), în cm."""
    bt = D["bookend_a"]
    out = []
    for k, toward, fill in ROWS[level]:
        a, b = compartments(level)[k]
        if toward == "dreapta":
            stop = b == D["L"]                      # capăt liber al poliței: și acolo stă un opritor
            xe = b - (bt if stop else 0.0)
            length = (b - a - bt * (1 + stop)) * fill
            out.append((x0 + xe - length, x0 + xe, True, stop))
        else:
            stop = a == 0.0
            xs = a + (bt if stop else 0.0)
            length = (b - a - bt * (1 + stop)) * fill
            out.append((x0 + xs, x0 + xs + length, stop, True))
    return out


def verticals():
    """Verticalele din stejar, cum se văd, în coordonatele peretelui: [(x stânga, x dreapta, y jos, y sus, adâncimea)].

    Jos pornesc de pe fața poliței de jos (piciorul intră 2 mm, în locașul din microciment), iar sus se opresc
    la rostul de umbră de sub polița de sus.
    """
    x0 = D["x_right"]
    y1 = round(D["bot_up"] - D["vert_gap"], 1)
    return [(round(x0 + v, 1), round(x0 + v + D["vert_t"], 1), D["top_lo"], y1, D["P"]) for v in VERTS]


def shelves():
    """Cele două polițe, doar în dreapta televizorului: (partea, nivelul, x0, y jos, y sus)."""
    x0 = D["x_right"]
    return [("dreapta", "jos", x0, D["bot_lo"], D["top_lo"]),
            ("dreapta", "sus", x0, D["bot_up"], D["top_up"])]


def capacity(level=None):
    """Discuri pe poliță: comod (~90 % din golurile dintre opritoare și verticală, 5 mm pe disc) și ticsit (4 mm).

    Fără nivel, întoarce totalul pe cele două polițe.
    """
    if level is None:
        lo = [capacity(lv) for lv in ("jos", "sus")]
        return lo[0][0] + lo[1][0], lo[0][1] + lo[1][1]
    usable = -1.0
    for a, b in compartments(level):
        usable += b - a - D["bookend_a"] * ((a == 0.0) + (b == D["L"]))   # opritor doar la capetele libere
    return int(usable * 0.9 / 0.5), int(usable / 0.4)


def shelf_kg():
    """Polița goală (kg): miezul de placaj și microcimentul de pe fețele care se văd (spatele doar se sigilează)."""
    L, P, T, c = D["L"], D["P"], D["T"], D["coat_t"]
    core = (L - 2 * c) * (P - c) * D["core_t"] * RHO["ply"]
    coat = (2 * L * P + L * T + 2 * P * T) * c * RHO["micro"]
    return round((core + coat) / 1000.0, 1)


def vertical_kg():
    """Verticalele din stejar masiv (kg), toate la un loc."""
    return round(len(VERTS) * D["vert_t"] * D["P"] * D["vert_h"] * RHO["oak"] / 1000.0, 1)


def loads(level="jos", full=False):
    """Greutăți aproximative (kg) pentru o poliță: polița, discurile, verticala care stă pe ea, total.

    Discurile sunt așezate comod sau, cu full=True, ticsite. Verticala e lipită doar de polița de jos.
    """
    shelf = shelf_kg()
    recs = round(capacity(level)[1 if full else 0] * LP["kg"], 1)
    vert = vertical_kg() if level == "jos" else 0.0
    return shelf, recs, vert, round(shelf + recs + vert, 1)


def pieces_kg():
    """Piesele goale (kg), cum se ridică la montaj: polița de jos cu verticala lipită și polița de sus."""
    return round(shelf_kg() + vertical_kg(), 1), shelf_kg()


def unit_kg():
    """Toate piesele la un loc (kg): cele două polițe și verticala."""
    return round(2 * shelf_kg() + vertical_kg(), 1)


def gfrc_kg():
    """Cât ar cântări o poliță de aceleași dimensiuni turnată din beton GFRC masiv (kg), pentru comparație."""
    return round(D["L"] * D["P"] * D["T"] * RHO["gfrc"] / 1000.0, 1)


def _moment(full=True):
    """Momentul (N·mm) din dreptul peretelui, la polița cea mai încărcată, cu sarcina în mijlocul adâncimii."""
    kg = max(loads(lv, full)[3] for lv in ("jos", "sus"))
    return kg * 9.81 * D["P"] / 2 * 10.0


def rod_check(fy=None, full=True):
    """Verificarea tijelor, în cazul cel mai defavorabil: polița de jos, cu discurile ticsite, stă doar în tijele
    ei, ca o consolă.

    Momentul din dreptul peretelui se împarte egal la tije; secțiunea e cea din fundul filetului M12
    (d3 = 9,85 mm). Clasa 8.8 curge la 640 MPa, iar tija zincată obișnuită, de 4.8, la 320 MPa. E doar
    verificarea oțelului: ancora și peretele se verifică separat (rod_pull) și cu o probă de încărcare.
    """
    import math
    w = math.pi * 9.853 ** 3 / 32.0                       # mm³
    sigma = _moment(full) / D["rods"] / w
    return round(sigma), round((fy or D["rod_fy"]) / sigma, 2)


def rod_pull(full=True):
    """Forța de smulgere pe tijă (kN) când polița se sprijină pe perete, la muchia de jos a spatelui.

    Brațul e de la muchia de jos până la axa tijelor, la jumătatea grosimii. E sarcina pe care trebuie s-o țină
    ancora chimică din fiecare gaură, fără coeficienți de siguranță.
    """
    return round(_moment(full) / (D["T"] / 2 * 10.0) / D["rods"] / 1000.0, 2)


if __name__ == "__main__":
    print("televizor", TV)
    print("comodă", CABINET)
    print("polițe", D)
    for sh in shelves():
        print("poliță", sh, "tije la X", [sh[2] + r for r in D["rod_x"]], "Y", round((sh[3] + sh[4]) / 2, 1))
        print("   goluri", compartments(sh[1]), "rânduri", [tuple(round(v, 1) if isinstance(v, float) else v
                                                                for v in r) for r in row_extents(sh[1], sh[2])])
    print("verticale (x0, x1, y0, y1, adâncime):", verticals(), "·", vertical_kg(), "kg")
    print("perete liber până la capătul din dreapta:", round(SITE["wall_w"] - D["x_right"] - D["L"], 1), "cm")
    print("discuri (comod, ticsit): jos", capacity("jos"), "sus", capacity("sus"), "total", capacity())
    print("greutăți (poliță, discuri, verticală, total): jos", loads("jos"), "sus", loads("sus"),
          "· ticsite: jos", loads("jos", True), "sus", loads("sus", True))
    print("piese la montaj (jos cu verticala, sus):", pieces_kg(), "kg · toate:", unit_kg(), "kg · o poliță din GFRC "
          "masiv:", gfrc_kg(), "kg")
    print("tije, discuri ticsite: efort (MPa) și rezervă față de curgere, 8.8:", rod_check(), "· 4.8:",
          rod_check(320.0), "· comod, 8.8:", rod_check(full=False))
    print("smulgere pe tijă (kN), polița sprijinită pe perete: ticsit", rod_pull(), "· comod", rod_pull(False))
    print("între boxa de podea și polița de jos:", round(D["bot_lo"] - TOWER["h"], 1), "cm")
    print("între discurile de sus și dispozitivul alb:", round(SITE["device_y"][0] - TV["y1"], 1), "cm")
