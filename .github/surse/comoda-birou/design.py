"""Sursa unică pentru cote: camera, biroul existent, comoda propusă și așezarea ei.

Coordonate (cm), ca în camera.py: X de-a lungul peretelui cu biroul, cu X = 0 în colțul din stânga (cu peretele
dinspre Dormitor 1); Y în sus, de la pardoseala finită; Z din perete spre cameră.
Valorile marcate `# est.` sunt estimate din fotografia calibrată sau din plan și trebuie măsurate.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_cam = json.load(open(os.path.join(HERE, "camera.json")))

# Camera: Dormitor 2 (E 03) din planul etajului: 327 × 366 cm între fețele pereților, 12,01 m².
SITE = {
    "H": 250.0,                 # tavanul, dat de utilizator
    "room_w": 327.0,            # de la peretele cu biroul până la peretele cu ușa (din plan)
    "wall_len": 366.2,          # peretele cu biroul, de la colț la fereastra de colț (din plan)
    "win_x": 278.9,             # începutul golului ferestrei Fe-06, de la colț (din plan)  # est.
    "win_sill": 47.0,           # parapetul ferestrelor (din plan, HP = 47)
    "win_head": round(_cam["ywt"], 1),  # capul golului, din fotografie (planul dă 227)  # est.
    "base_h": round(_cam["hb"], 1),     # plinta, din fotografie  # est.
    "base_t": 1.5,              # grosimea plintei  # est.
    "door_x0": 20.8,            # ușa UI-02, pe peretele opus (90 × 210): golul începe la 20,8 cm de peretele din stânga (din plan)
    "door_w": 98.7,             # golul ușii, din plan
}

# Biroul existent: Secretlab MAGNUS Pro 1,5 m Metal (fișa oficială: 1500 × 700 mm, înălțime 650–1250 mm).
DESK = {
    "w": 150.0, "d": 70.0, "h_min": 65.0, "h_max": 125.0,
    "x0": round(_cam["xd"], 1),          # capătul din stânga, de la colț  # est.
    "z0": max(0.0, round(_cam["zb"], 1)),  # spatele blatului lipit de perete  # est.
    "h": round(_cam["hd"], 1),           # înălțimea blatului în fotografie  # est.
    "top_t": 3.0,                        # grosimea blatului  # est.
}

# Comoda propusă: BoConcept Element, comodă cu 3 sertare. Pe site, rotunjit: 115 × 46½ × 91 cm, 59 kg.
# Instrucțiunile de montaj (379_AB00): pe picioare 90,8 × 115 × 46,2 cm, corpul 77,8 cm, sarcină maximă 40 kg.
# Rama, rosturile și picioarele sunt măsurate pe vederea frontală a producătorului (1071 px = 115 cm).
EL = {
    "w": 115.0, "d": 46.2, "h": 90.8,
    "leg_h": 13.0,        # 90,8 − 77,8: corpul începe la 13 cm
    "frame": 1.9,         # rama din jurul fronturilor (măsurată: 1,9–2,0 cm)
    "gap": 0.3,           # rostul dintre fronturi (măsurat: ~0,3 cm)
    "n_drawers": 3,
    "reed": 1.3,          # pasul riflajului de pe fronturi  # est.
    "leg_rod": 1.8,       # diametrul unui tub al piciorului dublu (măsurat: 1,83 cm)
    "leg_pair": 3.3,      # distanța dintre axele celor două tuburi (măsurată: 3,33 cm)
    "leg_in_x": 7.5,      # axul perechii de tuburi, de la lateral (măsurat: 7,47 cm)
    "leg_in_z": 6.0,      # axul perechii, de la față și de la spate  # est.
}

# Așezarea: lângă birou, cu un rost fix față de el; restul rămâne spre colț.
GAP_DESK = 8.0            # între comodă și capătul din stânga al biroului
GAP_WALL = 0.0            # spatele corpului lipit de perete (corpul începe la 13 cm, deasupra plintei)

# Prinderea anti-răsturnare (instrucțiunile BoConcept, pagina 7): banda AA stă în comodă, prinsă sub blat;
# capătul ei îndoit coboară pe spate, iar prin el și prin spate trece în perete un șurub cu diblu.
BACK_T = 0.3              # grosimea spatelui (placă subțire, bătută în cuie)  # est.
TOP_T = 1.9               # grosimea blatului comodei (ca rama)  # est.
ANCHOR_DROP = 1.0         # gaura prin spate, la 10 mm sub blat (din instrucțiuni)
ANCHOR_Y = EL["h"] - TOP_T - ANCHOR_DROP   # înălțimea găurii din perete
SCREW_L = 4.0             # șurubul diblului Fischer DuoPower 6 × 30 (4,5 × 40 mm)
FIX_T = 0.1 + 0.15 + BACK_T   # șaiba, banda și spatele, pe care le străbate șurubul până la perete  # est.
HOLE_DEPTH = 5.0          # adâncimea găurii din perete (min. 4,5 cm, după fișa diblului)


class Layout:
    def __init__(self, site=SITE, desk=DESK, el=EL):
        self.free = desk["x0"]                       # peretele liber dintre colț și birou
        self.x1 = desk["x0"] - GAP_DESK              # latura dreaptă a comodei
        self.x0 = self.x1 - el["w"]                  # latura stângă
        self.gap_corner = self.x0                    # cât rămâne până în colț
        self.z0 = GAP_WALL
        self.z1 = GAP_WALL + el["d"]
        self.body_y0 = el["leg_h"]
        self.top = el["h"]
        # fronturile sertarelor, de jos în sus: (y0, y1)
        fr, g = el["frame"], el["gap"]
        inner = el["h"] - el["leg_h"] - 2 * fr
        hd = (inner - (el["n_drawers"] - 1) * g) / el["n_drawers"]
        self.drawer_h = hd
        self.drawers = [(el["leg_h"] + fr + i * (hd + g), el["leg_h"] + fr + i * (hd + g) + hd)
                        for i in range(el["n_drawers"])]
        # axele barelor picioarelor: (x, z)
        xs = [self.x0 + el["leg_in_x"], self.x1 - el["leg_in_x"]]
        zs = [self.z0 + el["leg_in_z"], self.z1 - el["leg_in_z"]]
        self.legs = []
        for x in xs:
            for z in zs:
                for dx in (-el["leg_pair"] / 2, el["leg_pair"] / 2):
                    self.legs.append((x + dx, z))


if __name__ == "__main__":
    L = Layout()
    print(f"perete liber între colț și birou: ~{L.free:.1f} cm")
    print(f"comoda: X {L.x0:.1f} … {L.x1:.1f} (până în colț ~{L.gap_corner:.1f} cm, până la birou {GAP_DESK} cm)")
    print(f"        Z {L.z0:.1f} … {L.z1:.1f}; corpul de la {L.body_y0} la {L.top} cm")
    print(f"sertare: {EL['n_drawers']} × {L.drawer_h:.1f} cm: " + ", ".join(f"{a:.1f}–{b:.1f}" for a, b in L.drawers))
    print(f"biroul: X {DESK['x0']} … {DESK['x0'] + DESK['w']:.1f}, blatul la {DESK['h']} cm (între {DESK['h_min']} și {DESK['h_max']})")
    print(f"față de birou: comoda e cu {EL['h'] - DESK['h']:.1f} cm mai sus decât blatul în poziția din fotografie")
    print(f"fereastra Fe-06 începe la {SITE['win_x']} cm; capătul din dreapta al biroului: {DESK['x0'] + DESK['w']:.1f}")
    pen = SCREW_L - FIX_T - GAP_WALL
    print(f"anti-răsturnare: gaura din perete la ~{ANCHOR_Y:.1f} cm; șurubul de {SCREW_L * 10:.0f} mm intră "
          f"{pen * 10:.1f} mm în perete (diblul are 30 mm; se cer cel puțin 30 + 4,5 mm)")
