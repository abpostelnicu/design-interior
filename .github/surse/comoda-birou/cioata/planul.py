"""Planul tehnic A3 al variantelor C și D: bufetele Cioata Raya 116 și Veneto 116, în stânga biroului (Dormitor 2).

Vederea frontală, cu varianta C lângă birou, și planul, cu ușile deschise și sertarul VE390, la 1:15; secțiunea
prin bufet și fața variantei D, tot la 1:15; planul camerei la 1:50. Pagina, cotele și notele vin din trusa comună
(`unelte.plan`), ușile din `unelte.usi`; biroul, priza și întrerupătorul, din planul variantelor A și B
(`../drawing.py`), ca să fie desenate la fel.

    python planul.py                                    # out/plan_tehnic_comoda_birou_cioata.pdf și .png
    python ../../../unelte/plan.py verifica planul.py   # textele: în pagină, fără suprapuneri
"""
import os

import matplotlib.patches as mp
import numpy as np

from varianta import (BUF, DESK, GAP_CORNER, GAP_DESK, POLITA_Y, SERTAR, SERTAR_SCOS, SITE, X0, X1, Z0, Z1,
                      doors, lamele)  # pune și `..` și `.github` în sys.path

from drawing import DESK_LEGS, SOCKET, SWITCH, X_CUT, desk_front  # noqa: E402,F401  (planul variantelor A și B)
from unelte import plan, usi  # noqa: E402
from unelte.plan import (C, K15, K50, MM15, MM50, break_h, break_v, dim_h, dim_v, fmt, hatch, label,  # noqa: E402
                         legend, make_axes, rect, text_block)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

BLACK, MICRO, MICRO_E = "#1f1f21", "#3d3e41", "#161617"
DESK_C, FRAME, GLASS, PLUG = "#2a2b2e", "#3a3a3a", "#dce8f2", "#f4f4f4"
OAK_IN = "#f3e7d3"                              # interiorul corpului, văzut dincolo de secțiune

XB, XE, XM = X0, X1, (X0 + X1) / 2
XI0, XI1 = XB + BUF["side_t"], XE - BUF["side_t"]
DX0, DX1 = DESK["x0"], DESK["x0"] + DESK["w"]
WIN = SITE["win_x"]
Y_CUT = 200.0                                   # vederea frontală se oprește aici: mai sus nu e nimic de mobilat
YB = BUF["body_y0"]                             # dedesubtul corpului (20)
YD0 = YB + BUF["bottom_t"]                      # ușile, jos (22,2)
YD1 = YD0 + BUF["door_h"]                       # ușile, sus (77,2)
YT0 = BUF["h"] - BUF["top_t"]                   # blatul, dedesubt (79,8)
YH = (YD0 + YD1) / 2                            # centrul mânerului Veneto
RH = BUF["handle_d"] / 2
R_LEG = BUF["leg_d"] / 2
LEGS_X = (XB + BUF["leg_in_x"], XE - BUF["leg_in_x"])
LEGS_Z = (Z0 + BUF["leg_in_z"], Z1 - BUF["leg_in_z"])
Z_DOOR = Z1 - BUF["door_t"]                     # fața din spate a ușilor
Z_DR1 = Z_DOOR - 1.0                            # sertarul VE390: fața ansamblului, chiar în spatele ușilor  # est.
Z_DR0 = Z_DR1 - SERTAR["d"]
BOX_W = SERTAR["in_w"] + 4.0                    # cutia sertarului, cu pereții  # est.
SEC_OFF = 8.0                                   # secțiunea trece la 8 cm în dreapta rostului: prin ușă și mâner


# ------------------------------------------------------------------ fața bufetului (C sau D), 1:15
def bufet_fata(ax, var, z=6):
    """Fața bufetului, la X-urile reale: rama de stejar, banda neagră de sub blat, ușile, traversa și picioarele."""
    rect(ax, XB, YB, XE, BUF["h"], C["oak"], C["oak_e"], 0.5, z=z)
    ax.plot([XB, XE], [YT0, YT0], color=C["oak_e"], lw=0.3, zorder=z + 4)
    rect(ax, XI0, YD1, XI1, YT0, BLACK, z=z + 1)
    g = BUF["gap"]
    lam = lamele()
    for k, (a, b) in enumerate(((XI0 + g, XM - g / 2), (XM + g / 2, XI1 - g))):
        if var == "C":
            rect(ax, a, YD0 + 0.2, b, YD1, C["oak"], C["oak_e"], 0.4, z=z + 1)
            s = (b - a) / BUF["door_w"]
            for e in lam[k][0][1:-1]:
                ax.plot([a + e * s] * 2, [YD0 + 0.6, YD1 - 0.4], color=C["oak_e"], lw=0.25, zorder=z + 2)
            if k == 0:                              # mânerul: o lamelă neagră, pe muchia dinspre rost
                rect(ax, b - BUF["strip_w"], YD0 + 0.2, b, YD1, BLACK, z=z + 3)
        else:
            rect(ax, a, YD0 + 0.2, b, YD1, MICRO, MICRO_E, 0.4, z=z + 1)
    if var == "D":
        ax.add_patch(mp.Circle((XM, YH), RH, fc=C["oak"], ec=C["oak_e"], lw=0.5, zorder=z + 3))
        ax.plot([XM, XM], [YH - RH, YH + RH], color=C["oak_e"], lw=0.3, zorder=z + 4)
    rect(ax, LEGS_X[0], BUF["leg_h"], LEGS_X[1], YB, C["oak"], C["oak_e"], 0.35, z=z - 1)
    for xc in LEGS_X:
        rect(ax, xc - R_LEG, 0, xc + R_LEG, YB, C["steel"], z=z)


# ------------------------------------------------------------------ vedere frontală, 1:15
FRONT_X = (-38.0, 334.0)
FRONT_Y = (-30.0, Y_CUT + 6.0)


def vedere_frontala(ax):
    k = K15
    ws = SITE["win_sill"]
    rect(ax, 0, 0, X_CUT, Y_CUT, C["wall"], z=0)
    hatch(ax, -15, -6, 0, Y_CUT, z=2)
    rect(ax, -15, -6, X_CUT, 0, "#f6efe3", z=1)
    ax.plot([-15, X_CUT], [0, 0], color="k", lw=1.0, zorder=5)
    ax.plot([0, 0], [0, Y_CUT], color="k", lw=0.9, zorder=5)
    break_v(ax, X_CUT, -6, Y_CUT)
    break_h(ax, Y_CUT, -15, X_CUT)
    ax.text(-7.5, 130, "perete spre Dormitor 1", rotation=90, fontsize=4.8, color=C["note"], ha="center",
            va="center", zorder=6, bbox=dict(fc="#f4f4f4", ec="none", pad=0.4))
    rect(ax, 0, 0, X_CUT, SITE["base_h"], C["base"], "#9a9a9a", 0.3, z=3)
    # fereastra Fe-06 (de colț), cu toc negru; capul ei e deasupra tăieturii
    rect(ax, WIN, ws, X_CUT, Y_CUT, FRAME, z=3)
    rect(ax, WIN + 5, ws + 5, X_CUT, Y_CUT, GLASS, z=4)
    ax.text((WIN + X_CUT) / 2 + 2, 130, "fereastra Fe-06", rotation=90, fontsize=4.8, color="#3a4a5a",
            ha="center", va="center", zorder=5)
    for (a, b, c, d), name in ((SWITCH, "întrerupător"), (SOCKET, "priză")):
        rect(ax, a, c, b, d, PLUG, "#666666", 0.35, z=6)
        ax.text((a + b) / 2, d + 2.5, name, fontsize=4.4, color=C["note"], ha="center", va="bottom", zorder=6)
    desk_front(ax)
    ax.text((DX0 + DX1) / 2, DESK["h"] + 4.0, "birou Secretlab MAGNUS Pro 1,5 m (existent)", fontsize=5.0,
            color="#333333", ha="center", va="bottom", zorder=7)
    for yy in (DESK["h_min"], DESK["h_max"]):
        ax.plot([DX0, DX0 + 46], [yy, yy], color="#555555", lw=0.5, ls=(0, (3, 1.5)), zorder=7)
    ax.text(DX0 + 47, DESK["h_max"], f"blatul, sus ({fmt(DESK['h_max'])})", fontsize=4.4, color=C["note"],
            va="center", zorder=7)
    ax.text(DX0 + 47, DESK["h_min"] - 0.5, f"jos ({fmt(DESK['h_min'])})", fontsize=4.4, color=C["note"],
            va="center", zorder=7, bbox=dict(fc=C["wall"], ec="none", pad=0.2))
    bufet_fata(ax, "C")
    ax.text(XM, BUF["h"] + 3.0, f"C: Cioata Raya 116 (RA340), {fmt(BUF['w'])} × {fmt(BUF['d'])} × "
            f"{fmt(BUF['h'])} cm\nD: același corp, cu ușile Veneto (fața lui, în dreapta paginii)", fontsize=5.0,
            color="#4a3216", ha="center", va="bottom", zorder=9, linespacing=1.5)

    # cote orizontale, sub pardoseală
    stops = [0, XB, XE, DX0, DX1, WIN]
    texts = [f"~{fmt(XB)}", None, f"~{fmt(GAP_DESK)}", None, f"~{fmt(WIN - DX1)}"]
    shift = [-4.5, 0.0, 0.0, 0.0, 4.5]          # cotele mici de la capete, mutate spre exterior
    for (p, q), t, sx in zip(zip(stops[:-1], stops[1:]), texts, shift):
        dim_h(ax, p, q, -9, ref=0, k=k, fs=5.0, text=t, txt_dx=sx)
    dim_h(ax, 0, DX0, -17, ref=0, k=k, fs=5.0, text=f"~{fmt(DX0)}  perete liber, de la colț la birou")
    dim_h(ax, 0, WIN, -25, ref=0, k=k, fs=5.0, text=f"{fmt(WIN)}  de la colț la fereastra Fe-06 (din plan)")
    # cote verticale, în stânga: bufetul
    dim_v(ax, 0, YB, -21, ref=XB, dx=-1.2 * k, k=k, fs=5.0)
    dim_v(ax, YB, BUF["h"], -21, ref=XB, dx=-1.2 * k, k=k, fs=5.0, rot=True, text=f"{fmt(BUF['h'] - YB)} corp")
    dim_v(ax, 0, BUF["h"], -30, ref=-21, dx=-1.2 * k, k=k, fs=5.0, rot=True, text=f"{fmt(BUF['h'])} bufet")
    # biroul și fereastra
    dim_v(ax, 0, DESK["h"], DX0 + 52, ref=DX0 + 46, k=k, fs=5.0, rot=True, text=f"~{fmt(DESK['h'])}")
    dim_v(ax, 0, ws, X_CUT + 8, ref=X_CUT, k=k, fs=4.8, rot=True, text=f"{fmt(ws)} parapet (plan)")


# ------------------------------------------------------------------ plan (vedere de sus), 1:15
PLAN_X = (-38.0, 334.0)
PLAN_Z = (-20.0, 121.0)


def vedere_plan(ax):
    k = K15
    zmax = PLAN_Z[1] - 1.0
    rect(ax, 0, 0, X_CUT, zmax, C["floor"], z=0)
    hatch(ax, -15, -18, WIN, 0, z=1)
    hatch(ax, -15, 0, 0, zmax, z=1)
    rect(ax, WIN, -18, X_CUT, 0, "white", z=1)
    for zz in (-12.0, -10.5):
        ax.plot([WIN, X_CUT], [zz, zz], color="#5a6a7a", lw=0.5, zorder=2)
    ax.plot([WIN, WIN], [-18, 0], color="k", lw=0.8, zorder=3)
    ax.text((WIN + X_CUT) / 2, -4.5, "Fe-06", fontsize=4.6, color="#3a4a5a", ha="center", va="center", zorder=3)
    ax.plot([0, WIN], [0, 0], color="k", lw=0.9, zorder=3)
    ax.plot([0, 0], [0, zmax], color="k", lw=0.9, zorder=3)
    break_v(ax, X_CUT, -18, zmax)
    rect(ax, 0, 0, X_CUT, SITE["base_t"], C["base"], "#9a9a9a", 0.3, z=2)
    rect(ax, 0, 0, SITE["base_t"], zmax, C["base"], "#9a9a9a", 0.3, z=2)
    # ușile: cea din stânga spre peretele din colț, cea din dreapta spre blatul biroului (unelte.usi)
    st, dr = doors()
    usi.deseneaza(ax, st, "stanga", XB, k=k, fs=4.6, legenda=False, latime_obstacol=15.0)
    usi.deseneaza(ax, dr, "dreapta", XE, k=k, fs=4.6, legenda=False)
    for i, (rez, cine, ce, cel) in enumerate(((st, "stânga (spre colț)", "perete", "peretele"),
                                              (dr, "dreapta (spre birou)", "blat", "blatul"))):
        intra = rez["la_max"]["ocupat"] - rez["distanta"]
        ax.text(0.52, 0.105 - 0.07 * i, f"ușa din {cine}: la 90° (plin); la {fmt(rez['unghi_max'])}° (punctat) ar "
                f"intra {fmt(intra)} cm în {ce}; atinge {cel} la ~{fmt(rez['contact'])}° (roșu)",
                transform=ax.transAxes, fontsize=4.6, color=C["note"], ha="left", va="bottom", zorder=9,
                bbox=dict(fc="white", ec="none", pad=0.2, alpha=0.9))
    # biroul, peste hașura obstacolului
    rect(ax, DX0, DESK["z0"], DX1, DESK["z0"] + DESK["d"], DESK_C, "#000000", 0.5, z=4)
    ax.text((DX0 + DX1) / 2, 35, f"birou {fmt(DESK['w'])} × {fmt(DESK['d'])} (existent)", fontsize=5.2,
            color="#d8d8d8", ha="center", va="center", zorder=5)
    # bufetul, cu sertarul VE390 în corp și scos (punctat) și picioarele
    rect(ax, XB, Z0, XE, Z1, C["oak"], C["oak_e"], 0.6, z=4)
    rect(ax, XM - SERTAR["w"] / 2, Z_DR0, XM + SERTAR["w"] / 2, Z_DR1, "none", C["oak_e"], 0.5, z=8,
         ls=(0, (3, 1.5)))
    rect(ax, XM - BOX_W / 2, Z1, XM + BOX_W / 2, Z1 + SERTAR_SCOS, "none", C["oak_e"], 0.6, z=8, ls=(0, (4, 2)))
    ax.text(XM, Z1 + SERTAR_SCOS / 2, f"sertarul VE390, scos (~{fmt(SERTAR_SCOS)} cm)\ncu ușile deschise",
            fontsize=4.6, color=C["oak_e"], ha="center", va="center", zorder=9, linespacing=1.4)
    for x in LEGS_X:
        for zz in LEGS_Z:
            ax.add_patch(mp.Circle((x, zz), R_LEG, fc="none", ec=C["steel"], lw=0.35, ls=(0, (1.5, 1)), zorder=8))
    ax.text(XM, (Z_DR0 + Z_DR1) / 2, "bufetul C / D\n(sertarul și picioarele, punctat)", fontsize=4.8,
            color="#4a3216", ha="center", va="center", zorder=9, weight="bold", linespacing=1.4)
    # cote
    dim_v(ax, Z0, Z1, -24, ref=XB, dx=-1.2 * k, k=k, fs=5.0)
    dim_v(ax, Z1, Z1 + SERTAR_SCOS, -24, ref=XM - BOX_W / 2, dx=-1.2 * k, k=k, fs=5.0, text=f"~{fmt(SERTAR_SCOS)}")
    dim_v(ax, 0, DESK["d"], X_CUT + 8, ref=DX1, k=k, fs=5.0)


# ------------------------------------------------------------------ secțiune prin bufet, 1:15
SEC_Z = (-12.0, 92.0)
SEC_Y = (-8.0, 104.0)


def sectiune(ax):
    """Secțiune la 8 cm în dreapta rostului dintre uși, privind spre birou: peretele în stânga, camera în dreapta."""
    k = K15
    y0, y1 = SEC_Y
    hatch(ax, -12, y0, 0, y1, z=1)
    rect(ax, 0, y0, SEC_Z[1], 0, "#f6efe3", z=1)
    ax.plot([0, SEC_Z[1]], [0, 0], color="k", lw=0.9, zorder=3)
    ax.plot([0, 0], [0, y1], color="k", lw=0.9, zorder=3)
    rect(ax, 0, 0, SITE["base_t"], SITE["base_h"], C["base"], "#9a9a9a", 0.35, z=3)
    # dincolo: biroul, cu blatul la înălțimea din fotografie
    gz0, gz1 = DESK["z0"], DESK["z0"] + DESK["d"]
    rect(ax, gz0, DESK["h"] - DESK["top_t"], gz1, DESK["h"], "none", "#8a8a8a", 0.45, z=2)
    rect(ax, gz0 + 31.75, 2.5, gz0 + 38.25, DESK["h"] - DESK["top_t"], "#ececec", "#9a9a9a", 0.3, z=2)
    rect(ax, gz0, 0, gz1, 2.5, "#ececec", "#9a9a9a", 0.3, z=2)
    ax.text(gz1 - 1, 4.0, "biroul, dincolo", fontsize=4.4, color="#555555", ha="right", va="bottom", zorder=3)
    # dincolo de secțiune: lateralul bufetului, traversa laterală și picioarele
    rect(ax, Z0, YB, Z1, BUF["h"], OAK_IN, C["oak_e"], 0.6, z=4)
    rect(ax, LEGS_Z[0], BUF["leg_h"], LEGS_Z[1], YB, C["oak"], C["oak_e"], 0.35, z=4)
    for zc in LEGS_Z:
        rect(ax, zc - R_LEG, 0, zc + R_LEG, YB, C["steel"], z=5)
    # în secțiune: blatul, fundul, spatele, polița, ușa, banda neagră, traversa din față și mânerul D
    rect(ax, Z0, YT0, Z1, BUF["h"], C["oak"], C["oak_e"], 0.5, z=6, hatch="....")
    rect(ax, Z0, YB, Z1, YD0, C["oak"], C["oak_e"], 0.5, z=6, hatch="....")
    rect(ax, Z0, YD0, Z0 + 0.8, YT0, C["oak_e"], C["oak_e"], 0.3, z=6)
    rect(ax, Z0 + 0.8, POLITA_Y, Z_DR1, POLITA_Y + 2.2, C["oak"], C["oak_e"], 0.5, z=6, hatch="....")
    rect(ax, Z_DOOR, YD0 + 0.2, Z1, YD1, "#e2cfae", C["oak_e"], 0.5, z=6, hatch="////")
    rect(ax, Z1 - 2.6, YD1, Z1 - 0.6, YT0, BLACK, z=6)
    zr = Z1 - BUF["rail_in"]
    rect(ax, zr - 2.0, BUF["leg_h"], zr, YB, C["oak"], C["oak_e"], 0.5, z=6, hatch="....")
    hh = float(np.sqrt(RH ** 2 - SEC_OFF ** 2))
    rect(ax, Z1, YH - hh, Z1 + BUF["handle_t"], YH + hh, C["oak"], C["oak_e"], 0.5, z=6, hatch="....")
    # sertarul VE390, pe fundul corpului: ansamblul (punctat), fața, fundul și spatele cutiei
    rect(ax, Z_DR0, YD0, Z_DR1, YD0 + SERTAR["h"], "none", C["oak_e"], 0.45, z=7, ls=(0, (3, 1.5)))
    zf = Z_DR1 - 2.0
    zb = zf - SERTAR["in_d"] - 1.6
    rect(ax, zf, YD0 + 2.0, Z_DR1, YD0 + 19.0, C["oak"], C["oak_e"], 0.5, z=8, hatch="....")
    rect(ax, zb, YD0 + 3.0, zf, YD0 + 3.8, C["oak_e"], C["oak_e"], 0.3, z=8)
    rect(ax, zb, YD0 + 3.0, zb + 1.6, YD0 + 3.0 + SERTAR["in_h"] + 1.0, C["oak"], C["oak_e"], 0.5, z=8,
         hatch="....")
    ax.text((Z_DR0 + Z_DR1) / 2 + 3, YD0 + 12.0, f"sertarul VE390\n{fmt(SERTAR['w'])} × {fmt(SERTAR['d'])} × "
            f"{fmt(SERTAR['h'])}", fontsize=4.3, color="#4a3216", ha="center", va="center", zorder=9,
            linespacing=1.35, bbox=dict(fc=OAK_IN, ec="none", pad=0.2))
    ax.text(22.0, POLITA_Y + 4.0, "polița, mutată deasupra sertarului", fontsize=4.3, color="#4a3216",
            ha="center", va="bottom", zorder=9)
    label(ax, Z1 + BUF["handle_t"], YH + 6.0, 54.0, 96.0, f"mânerul D (Ø{fmt(BUF['handle_d'])}) iese "
          f"{fmt(BUF['handle_t'])} cm", fs=4.4, ha="left")
    label(ax, Z1 - 1.0, YD1 - 8.0, 58.0, 90.0, "ușa", fs=4.4, ha="left")
    # cote
    dim_h(ax, Z0, Z1, BUF["h"] + 6.0, ref=BUF["h"], k=k, fs=5.0)
    xr = 78.0
    dim_v(ax, 0, BUF["leg_h"], xr, ref=LEGS_Z[1] + R_LEG, k=k, fs=4.8)
    dim_v(ax, BUF["leg_h"], YB, xr, ref=zr, k=k, fs=4.8, txt_dy=0.6)
    dim_v(ax, YB, BUF["h"], xr, ref=Z1 + BUF["handle_t"], k=k, fs=4.8, rot=True, text=f"{fmt(BUF['h'] - YB)} corp")
    dim_v(ax, 0, BUF["h"], xr + 8.0, ref=xr, k=k, fs=4.8, rot=True, text=f"{fmt(BUF['h'])}")


# ------------------------------------------------------------------ fața variantei D, 1:15
D_X = (XB - 4.0, XE + 12.0)
D_Y = (-9.0, 100.0)


def fata_d(ax):
    k = K15
    ax.plot([D_X[0], D_X[1]], [0, 0], color="k", lw=0.9, zorder=3)
    bufet_fata(ax, "D")
    dim_h(ax, XB, XE, -6.0, ref=0, k=k, fs=5.0)
    dim_v(ax, YD0, YD1, XE + 5.0, ref=XE, k=k, fs=5.0, rot=True, text=f"{fmt(BUF['door_h'])} ușile")
    label(ax, XB + 18.0, YD1 - 10.0, XB + 1.0, 95.0, "uși din MDF cu microciment C9 (antracit spre negru)", fs=4.6)
    label(ax, XM + 6.0, YH + RH - 1.0, XB + 32.0, 88.0,
          f"mâner rotund din stejar masiv, Ø ~{fmt(BUF['handle_d'])}, pe rostul dintre uși", fs=4.6)


# ------------------------------------------------------------------ planul camerei, 1:50
ROOM_X = (-40.0, 408.0)
ROOM_Z = (-55.0, 350.0)
DOOR = (SITE["door_x0"], SITE["door_x0"] + SITE["door_w"])
LEAF = 82.0   # foaia ușii de 90 (golul de lumină ~82 cm)  # est.


def planul_camerei(ax):
    """Camera din planul etajului, ca la variantele A și B; mobila: biroul și bufetul."""
    k = K50
    W, D = SITE["wall_len"], SITE["room_w"]
    ext, inn = 38.5, 15.0
    rect(ax, 0, 0, W, D, C["floor"], z=0)
    g = "#b5b5b5"
    rect(ax, -inn, -ext, W + ext, 0, g, z=1)
    rect(ax, W, -ext, W + ext, D + inn, g, z=1)
    rect(ax, -inn, 0, 0, D + inn, g, z=1)
    rect(ax, -inn, D, W + ext, D + inn, g, z=1)
    rect(ax, WIN, -ext, W + ext, 0, "white", z=2)
    rect(ax, W, -ext, W + ext, 154.7, "white", z=2)
    for o in (-22.0, -18.0):
        ax.plot([WIN, W - o], [o, o], color="#5a6a7a", lw=0.5, zorder=3)
        ax.plot([W - o, W - o], [o, 154.7], color="#5a6a7a", lw=0.5, zorder=3)
    rect(ax, DOOR[0], D, DOOR[1], D + inn, C["floor"], z=2)
    hx, hz = DOOR[0], D
    ax.plot([hx, hx], [hz, hz - LEAF], color="k", lw=0.9, zorder=4)
    ang = np.linspace(0, np.pi / 2, 40)
    ax.plot(hx + LEAF * np.sin(ang), hz - LEAF * np.cos(ang), color="#555555", lw=0.4, zorder=4)
    ax.text(hx + 48, hz - 22, "ușa UI-02", fontsize=4.6, color=C["note"], ha="left", va="center", zorder=5)
    rect(ax, DX0, DESK["z0"], DX1, DESK["z0"] + DESK["d"], DESK_C, z=4)
    rect(ax, XB, Z0, XE, Z1, C["oak"], C["oak_e"], 0.5, z=5)
    ax.text(XM, 23, "bufet", fontsize=4.6, color="#4a3216", ha="center", va="center", zorder=6)
    ax.text((DX0 + DX1) / 2, 35, "birou", fontsize=4.6, color="#d8d8d8", ha="center", va="center", zorder=6)
    ax.text(W / 2, 205, "Dormitor 2 (E 03)\nrestul camerei rămâne\ncum e", fontsize=4.6, color=C["note"],
            ha="center", va="center", zorder=6)
    ax.text(W / 2, -ext / 2, "peretele cu biroul (exterior)", fontsize=4.2, color="#333333", ha="center",
            va="center", zorder=6)
    dim_h(ax, 0, W, -48, ref=-ext, k=k, fs=4.8, text=f"{fmt(round(W))} (din plan)")
    dim_v(ax, 0, D, -30, ref=-inn, dx=-1.0 * k, k=k, fs=4.8, rot=True, text=f"{fmt(D)} (din plan)")


# ------------------------------------------------------------------ notele
def notes():
    st, dr = doors()
    free = DX0
    need = BUF["w"] + 2 * BUF["door_t"]
    return [
        ("MATERIALE ȘI FERONERIE", [
            f"1. C: bufet Cioata Raya 116 (RA340), {fmt(BUF['w'])} × {fmt(BUF['d'])} × {fmt(BUF['h'])} cm, 56 kg. "
            "Din stejar masiv: lateralele, blatul, fundul, polița, mânerul și traversele dintre picioare; spatele "
            "din MDF furniruit; ușile din PAL furniruit, cu lamele de stejar masiv aplicate. Finisaj Natural Oak "
            "(NO); mânerul ușii din stânga e o lamelă neagră.",
            "2. D: bufet Cioata Veneto 116 (VE340), același corp: ușile din MDF acoperit cu microciment C9 "
            f"(antracit spre negru), cu un mâner rotund din stejar masiv, Ø ~{fmt(BUF['handle_d'])} cm.",
            f"3. Sertarul opțional VE390, la amândouă: ansamblul {fmt(SERTAR['w'])} × {fmt(SERTAR['d'])} × "
            f"{fmt(SERTAR['h'])} cm, sertarul util {fmt(SERTAR['in_w'])} × {fmt(SERTAR['in_d'])} × "
            f"{fmt(SERTAR['in_h'])} cm, 11 kg; stejar masiv, glisiere cu închidere lentă. Se fixează pe fundul "
            "corpului cu șablonul și cele 2 șuruburi din cutie; polița se mută deasupra lui.",
            f"4. Picioare din oțel Nero (RAL 9005), de {fmt(BUF['leg_h'])} cm, cu piciorușe reglabile; balamale "
            "cu închidere lentă. Producătorul nu cere prinderea de perete.",
        ]),
        ("DE CE AȘA", [
            "• Cioata, ca piesa Veneto din living: stejar masiv, cu noduri, pe picioare negre, ca biroul.",
            "• C e mai caldă: lamelele verticale repetă riflajul de stejar din hol. D leagă bufetul de biroul "
            "negru, iar mânerul rotund de stejar repetă blatul bufetului.",
            f"• {fmt(BUF['w'])} cm în ~{fmt(free)} cm liberi: ~{fmt(GAP_CORNER)} cm până în colț și "
            f"~{fmt(GAP_DESK)} cm până la birou. Ușile ajung la 90°: cea din stânga atinge peretele după "
            f"~{st['contact']:.0f}°, cea din dreapta blatul după ~{dr['contact']:.0f}° (doar cu blatul sub "
            f"~{fmt(round(YD1))} cm).",
            f"• Sus, la {fmt(BUF['h'])} cm: cu ~{fmt(BUF['h'] - DESK['h'])} cm peste blatul biroului când stai jos "
            f"(~{fmt(DESK['h'])}), sub el când lucrezi în picioare.",
            f"• Corpul începe la {fmt(YB)} cm, peste plinta de ~{fmt(SITE['base_h'])} cm: bufetul stă lipit de "
            "perete, iar plinta rămâne întreagă.",
            "• Cioata nu are o comodă cu sertare la vedere de ~115 cm; sertarul VE390, din spatele ușilor, e cea "
            "mai apropiată soluție.",
        ]),
        ("COTE", [
            f"Date: tavan {fmt(SITE['H'])} (de la tine); birou {fmt(DESK['w'])} × {fmt(DESK['d'])}, blat "
            f"{fmt(DESK['h_min'])}…{fmt(DESK['h_max'])} (Secretlab); bufet {fmt(BUF['w'])} × {fmt(BUF['d'])} × "
            f"{fmt(BUF['h'])}, uși {fmt(BUF['door_w'])} × {fmt(BUF['door_h'])}, picioare {fmt(BUF['leg_h'])}, "
            f"corp de la {fmt(YB)} (desenul Cioata).",
            f"Din planul etajului (scalat pe cota de 327, ~1:52,2): camera {fmt(SITE['room_w'])} × "
            f"{fmt(round(SITE['wall_len']))}; fereastra Fe-06 începe la {fmt(WIN)} cm de colț; parapetul are "
            f"{fmt(SITE['win_sill'])} cm.",
            f"Din fotografie (~): biroul de la ~{fmt(DX0)} la ~{fmt(DX1)} cm de colț, cu blatul la "
            f"~{fmt(DESK['h'])} cm; plinta ~{fmt(SITE['base_h'])} cm.",
            "Ușile sunt socotite ca aplicate pe față, cazul cel mai strâns; ușile Cioata stau în ramă și au ceva "
            f"mai mult loc. Sertarul scos (~{fmt(SERTAR_SCOS)}), polița (~{fmt(POLITA_Y)}) și traversa din față "
            "sunt estimate din fotografiile Cioata.",
        ]),
        ("COTE DE MĂSURAT", [
            f"a) peretele liber dintre colț și birou, la nivelul plintei (~{fmt(free)}): bufetul cere cel puțin "
            f"~{fmt(np.ceil(need))} cm, ca ambele uși să ajungă la 90°;",
            f"b) dacă pe perete, de la colț până la birou și până la {fmt(BUF['h'])} cm înălțime, e o priză sau un "
            "întrerupător (colțul nu se vede în fotografie);",
            "c) scara până la etaj, pentru livrare: bufetul vine într-un colet de 58 kg, iar la etaj fără lift "
            "Cioata poate cere o taxă.",
        ]),
    ]


def build():
    fig = plan.pagina(
        "Comodă lângă birou – Dormitor 2: variantele C și D, de la Cioata",
        f"Bufet Cioata Raya 116 (C) sau Veneto 116 (D), {fmt(BUF['w'])} × {fmt(BUF['d'])} × {fmt(BUF['h'])} cm, "
        f"cu sertarul opțional VE390, în stânga biroului, la ~{fmt(GAP_DESK)} cm de el",
        "cote în cm  ·  scara 1:15 (A3), planul camerei 1:50  ·  cotele cu „~” sunt din fotografie, de verificat")
    ax = make_axes(fig, 4, 108, FRONT_X, FRONT_Y, "VEDERE FRONTALĂ – VARIANTA C (1:15)", MM15)
    vedere_frontala(ax)
    ax = make_axes(fig, 4, 4, PLAN_X, PLAN_Z, "PLAN – VEDERE DE SUS, CU UȘILE DESCHISE (1:15)", MM15, invert=True)
    vedere_plan(ax)
    ax = make_axes(fig, 256, 192, SEC_Z, SEC_Y, "SECȚIUNE PRIN BUFET (1:15)", MM15)
    sectiune(ax)
    ax = make_axes(fig, 328, 186, ROOM_X, ROOM_Z, "PLANUL CAMEREI (1:50)", MM50, invert=True)
    planul_camerei(ax)
    ax = make_axes(fig, 256, 100, D_X, D_Y, "VARIANTA D – VENETO, FAȚA (1:15)", MM15)
    fata_d(ax)
    legend(fig, 350, 170, [
        (C["oak"], C["oak_e"], None, "stejar masiv (Natural Oak)"),
        (C["oak"], C["oak_e"], "....", "stejar, în secțiune"),
        (MICRO, MICRO_E, None, "microciment C9 (ușile D)"),
        (BLACK, BLACK, None, "negru: mânerul C, banda de sub blat"),
        (C["steel"], C["steel"], None, "oțel Nero (RAL 9005)"),
        ("#f4f4f4", C["hatch"], "////", "perete, în secțiune"),
        (DESK_C, "#000000", None, "biroul existent"),
    ])
    groups = notes()
    y = 94.0
    for title, paras in groups[:2]:
        y = text_block(fig, 256.0, y, title, paras, width=78.0)
    y = 94.0
    for title, paras in groups[2:]:
        y = text_block(fig, 339.0, y, title, paras, width=77.0)
    return fig


if __name__ == "__main__":
    pdf, png = plan.save(build(), os.path.join(OUT, "plan_tehnic_comoda_birou_cioata"))
    print("salvat", pdf, png, "A3" if plan.e_a3(pdf) else "NU e A3")
