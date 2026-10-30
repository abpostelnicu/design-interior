"""Planul tehnic A3, la scara 1:15, al polițelor din beton decorativ și stejar pentru viniluri, de pe peretele cu
televizorul.

Vedere frontală, secțiune prin verticală și vedere de sus la 1:15; la 1:5, detaliul A (tija ascunsă), detaliul B
(opritorul îmbrăcat în stejar) și detaliul C (piciorul verticalei, lipit de polița de jos, și rostul de umbră de
sub polița de sus). Toate cotele vin din design.py.
"""
import os
import re
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mp
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties

from design import (CABINET, CENTER, D, LP, SITE, TOWER, TV, capacity, gfrc_kg, loads, pieces_kg, rod_check,
                    rod_pull, row_extents, shelf_kg, shelves, vertical_kg, verticals)

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = (420.0, 297.0)
MM15 = 10.0 / 15.0   # mm de hârtie pe cm real, la 1:15
MM5 = 10.0 / 5.0
K15, K5 = 1.5, 0.5   # scalarea liniuțelor de cotă pentru fiecare scară

C = dict(wall="#ecebe7", hatch="#8f8f8f", oak="#c9a06a", oak_e="#7b5b37", tv="#202124", tv_e="#000000",
         cab="#5a5c5e", spk="#26272b", base="#ffffff", lp="#7f9db8", dim="#1a1a1a", note="#555555",
         floor="#efe3cf", dev="#f3efe6", steel="#3a3a3a", anchor="#b9b9b9",
         conc="#aaa69e", conc_e="#66625b",     # microcimentul, tonul „beton gri” din beton.py (RGB 170, 166, 158)
         ply="#efe3c4", ply_e="#9c8150",       # miezul din placaj de mesteacăn
         beech="#f2cf86", glue="#a0522d")      # cepurile din fag și adezivul epoxidic
FS = 5.6
H_WALL = SITE["wall_h_photo"]
XL, XR = 0.0, SITE["wall_w"]
X0, X1 = D["x_right"], D["x_right"] + D["L"]   # capetele polițelor
Y_REC_LO = D["top_lo"] + LP["size"]               # sus discuri pe polița de jos
REC_BACK = 0.7                                    # discurile stau la 7 mm de perete
DOW_IN, DOW_OUT = D["dowel_in"], D["dowel_out"]   # cât intră cepul în poliță și cât în verticală
N_SH = len(shelves())
N_RODS = D["rods"] * N_SH
N_DOW = len(D["dowel_z"]) * len(verticals())      # cepurile sunt doar la piciorul verticalei
N_BOOK = sum(int(bl) + int(br) for (_, lv, x0, _, _) in shelves() for (_, _, bl, br) in row_extents(lv, x0))
Y_FOOT = round(D["top_lo"] - D["coat_t"], 1)       # fundul locașului de pe polița de jos: placajul curat
NB = "\u00a0"                                     # spațiu de nedespărțit, pentru ruperea rândurilor din note


def fmt(v):
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


def rods_around(xc):
    """Tijele cele mai apropiate de un ax (cm de la capătul din stânga al poliței): (din stânga, din dreapta)."""
    left = max((r for r in D["rod_x"] if r < xc), default=None)
    right = min((r for r in D["rod_x"] if r > xc), default=None)
    return left, right


def vert_local():
    """Verticalele în cm de la capătul din stânga al poliței: [(fața din stânga, fața din dreapta, axul)]."""
    return [(round(a - X0, 1), round(b - X0, 1), round((a + b) / 2 - X0, 1)) for (a, b, _, _, _) in verticals()]


def make_axes(fig, x_mm, y_mm, xr, yr, title, mm_per_cm, invert=False):
    w = (xr[1] - xr[0]) * mm_per_cm
    h = (yr[1] - yr[0]) * mm_per_cm
    ax = fig.add_axes([x_mm / PAGE[0], y_mm / PAGE[1], w / PAGE[0], h / PAGE[1]])
    ax.set_xlim(*xr)
    ax.set_ylim(*(yr[::-1] if invert else yr))
    ax.set_aspect("equal")
    ax.axis("off")
    if title:
        fig.text(x_mm / PAGE[0], (y_mm + h + 2.5) / PAGE[1], title, fontsize=8.5, weight="bold", ha="left",
                 va="bottom")
    return ax


def rect(ax, x0, y0, x1, y1, fc, ec="none", lw=0.4, z=1, **kw):
    ax.add_patch(mp.Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=fc, edgecolor=ec, lw=lw, zorder=z, **kw))


def hatch(ax, x0, y0, x1, y1, z=1):
    ax.add_patch(mp.Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#f4f4f4", edgecolor=C["hatch"],
                              hatch="////", lw=0.5, zorder=z))


def tick(ax, x, y, s):
    ax.plot([x - s / 2, x + s / 2], [y - s / 2, y + s / 2], color=C["dim"], lw=0.6, zorder=20)


def dim_h(ax, x0, x1, y, ref=None, text=None, dy=None, fs=FS, txt_dx=0.0, k=1.0):
    """Cotă orizontală; k scalează liniuțele și depășirile pentru alte scări."""
    dy = 1.2 * k if dy is None else dy
    ax.plot([x0 - 1.6 * k, x1 + 1.6 * k], [y, y], color=C["dim"], lw=0.35, zorder=20)
    for x in (x0, x1):
        tick(ax, x, y, 1.6 * k)
        if ref is not None:
            s = 1 if y > ref else -1
            ax.plot([x, x], [ref + s * 1.0 * k, y + s * 1.6 * k], color=C["dim"], lw=0.25, zorder=20)
    up = (dy >= 0) != ax.yaxis_inverted()
    ax.text((x0 + x1) / 2 + txt_dx, y + dy, text or fmt(abs(x1 - x0)), ha="center",
            va="bottom" if up else "top", fontsize=fs, zorder=21,
            bbox=dict(fc="white", ec="none", pad=0.15, alpha=0.85))


def dim_v(ax, y0, y1, x, ref=None, text=None, dx=None, fs=FS, txt_dy=0.0, rot=False, k=1.0):
    dx = 1.2 * k if dx is None else dx
    ax.plot([x, x], [y0 - 1.6 * k, y1 + 1.6 * k], color=C["dim"], lw=0.35, zorder=20)
    for y in (y0, y1):
        tick(ax, x, y, 1.6 * k)
        if ref is not None:
            s = 1 if x > ref else -1
            ax.plot([ref + s * 1.0 * k, x + s * 1.6 * k], [y, y], color=C["dim"], lw=0.25, zorder=20)
    ax.text(x + dx, (y0 + y1) / 2 + txt_dy, text or fmt(abs(y1 - y0)), ha="left" if dx >= 0 else "right",
            va="center", rotation=90 if rot else 0, fontsize=fs, zorder=21,
            bbox=dict(fc="white", ec="none", pad=0.15, alpha=0.85))


def label(ax, x, y, tx, ty, text, fs=FS, ha="left"):
    ax.annotate(text, xy=(x, y), xytext=(tx, ty), fontsize=fs, color=C["note"], ha=ha, va="center",
                arrowprops=dict(arrowstyle="-", lw=0.35, color=C["note"], shrinkA=0, shrinkB=0), zorder=22,
                bbox=dict(fc="white", ec="none", pad=0.2, alpha=0.9))


def break_v(ax, x, y0, y1, a=0.25):
    """Linie de rupere verticală (piesa continuă dincolo de ea)."""
    ym = (y0 + y1) / 2
    ax.plot([x, x], [y0 - 0.5, y1 + 0.5], color="white", lw=2.6, zorder=15)
    ax.plot([x - a, x + a, x - a, x + a], [y0 - 0.5, ym - 0.6, ym + 0.6, y1 + 0.5], color="k", lw=0.5, zorder=16)


def break_h(ax, y, x0, x1, a=0.25):
    """Linie de rupere orizontală."""
    xm = (x0 + x1) / 2
    ax.plot([x0 - 0.5, x1 + 0.5], [y, y], color="white", lw=2.6, zorder=15)
    ax.plot([x0 - 0.5, xm - 0.6, xm + 0.6, x1 + 0.5], [y - a, y + a, y - a, y + a], color="k", lw=0.5, zorder=16)


def shelf_layers(ax, x0, x1, yb, yt, front=None, z=5, hatch_core=True):
    """Polița secționată: microcimentul de pe fețele care se văd și miezul din 2 plăci de placaj de mesteacăn.

    front: coordonata fețe din față (dacă secțiunea o prinde), ca să primească și ea microciment.
    """
    c = D["coat_t"]
    rect(ax, x0, yb, x1, yt, C["conc"], C["conc_e"], 0.5, z=z)
    cx1 = x1 - c if front is not None and front >= x1 else x1
    cx0 = x0 + c if front is not None and front <= x0 else x0
    rect(ax, cx0, yb + c, cx1, yt - c, C["ply"], "none", 0, z=z + 0.1, hatch="...." if hatch_core else None)
    ym = (yb + yt) / 2
    ax.plot([cx0, cx1], [ym, ym], color=C["ply_e"], lw=0.35, zorder=z + 0.2)   # lipitura plăcilor: semicanalele


def records(ax, xs, xe, yt, lw=0.25, step=1.1):
    """Rândul de discuri în vedere frontală: conturul și cotoarele."""
    rect(ax, xs, yt, xe, yt + LP["size"], "#e9eef3", C["lp"], 0.35, z=7, ls=(0, (3, 1.5)))
    for x in np.arange(xs + step / 2, xe, step):
        ax.plot([x, x], [yt + 0.3, yt + LP["size"] - 0.3], color=C["lp"], lw=lw, zorder=8)


def bookend_front(ax, x_rec, yt, toward):
    """Opritorul, din față: placa de oțel lipită de discuri și placa de stejar spre exterior.

    x_rec e capătul rândului de discuri; toward = -1 la capătul din stânga al rândului, +1 la cel din dreapta.
    """
    t, o, h = D["bookend_t"], D["oak_t"], D["bookend_h"]
    xs = x_rec if toward > 0 else x_rec - t
    xo = x_rec + t if toward > 0 else x_rec - t - o
    rect(ax, xs, yt, xs + t, yt + h, C["steel"], z=9)
    rect(ax, xo, yt, xo + o, yt + h, C["oak"], C["oak_e"], 0.35, z=9)


def shelf_front(ax, x0, yb, yt, z=6):
    rect(ax, x0, yb, x0 + D["L"], yt, C["conc"], C["conc_e"], 0.45, z=z)


# ------------------------------------------------------------------ vedere frontală, 1:15
def wall_elevation(ax):
    k = K15
    H = H_WALL
    rect(ax, XL, 0, XR, H, C["wall"], z=0)
    hatch(ax, XL - 12, -6, XL, H + 4, z=2)
    hatch(ax, XR, -6, XR + 10, H + 4, z=2)
    rect(ax, XL - 12, -6, XR + 10, 0, "#f6efe3", z=1)
    ax.plot([XL - 12, XR + 10], [0, 0], color="k", lw=1.0, zorder=5)
    ax.plot([XL, XR], [H, H], color="k", lw=0.8, zorder=5)
    for x in (XL, XR):
        ax.plot([x, x], [0, H], color="k", lw=0.9, zorder=5)
    ax.text(XL - 6, 60, "perete stânga", rotation=90, fontsize=4.8, color=C["note"], ha="center", va="center",
            zorder=6, bbox=dict(fc="#f4f4f4", ec="none", pad=0.4))
    ax.text(XR + 5, 60, "trecere", rotation=90, fontsize=4.8, color=C["note"], ha="center", va="center",
            zorder=6, bbox=dict(fc="#f4f4f4", ec="none", pad=0.4))
    rect(ax, XL, 0, XR, SITE["baseboard_h"], C["base"], "#9a9a9a", 0.3, z=3)
    # existente: televizorul, comoda, boxele, dispozitivul alb
    rect(ax, TV["x0"], TV["y0"], TV["x1"], TV["y1"], C["tv"], C["tv_e"], 0.5, z=4)
    ax.text(TV["axis"], 150, f"TV {TV['model']} (98\")\n{fmt(TV['w'])} × {fmt(TV['h'])} cm", color="#d8d8d8",
            fontsize=6.0, ha="center", va="center", zorder=5)
    cx0, cx1, legs = CABINET["x0"], CABINET["x1"], CABINET["legs"]
    rect(ax, cx0, legs, cx1, CABINET["h"], C["oak"], C["oak_e"], 0.4, z=4)
    rect(ax, cx0 + 3, legs + 3, cx1 - 3, CABINET["h"] - 3, C["cab"], "none", z=5)
    for lx in (cx0 + 28, cx1 - 28):
        rect(ax, lx - 1, 0, lx + 1, legs, "#111111", z=5)
    ax.text((cx0 + cx1) / 2, 40, "comodă Cioata Veneto 242 (stejar și microciment antracit)", color="#e8e8e8",
            fontsize=5.2, ha="center", va="center", zorder=6)
    cc = TV["axis"]
    rect(ax, cc - CENTER["w"] / 2, CABINET["h"], cc + CENTER["w"] / 2, CABINET["h"] + CENTER["h"], C["spk"], z=6)
    for (a, b) in (TOWER["xl"], TOWER["xr"]):
        rect(ax, a, 0, b, TOWER["h"], C["spk"], "#000000", 0.4, z=6)
        ax.text((a + b) / 2, 55, "Klipsch RP-8000F II", rotation=90, color="#bdbdbd", fontsize=4.6,
                ha="center", va="center", zorder=7)
    rect(ax, SITE["device_x"][0], SITE["device_y"][0], SITE["device_x"][1], SITE["device_y"][1], C["dev"],
         "#9a9a9a", 0.4, z=6)
    # noi: polițele din microciment, verticala din stejar, discurile, opritoarele și tijele ascunse (cercuri)
    for (side, level, x0, yb, yt) in shelves():
        shelf_front(ax, x0, yb, yt)
        for xs, xe, bl, br in row_extents(level, x0):
            records(ax, xs, xe, yt)
            if bl:
                bookend_front(ax, xs, yt, -1)
            if br:
                bookend_front(ax, xe, yt, +1)
        ym = (yb + yt) / 2
        for rx in D["rod_x"]:
            ax.add_patch(mp.Circle((x0 + rx, ym), D["rod_d"] / 2, fc="none", ec=C["steel"], lw=0.35, zorder=8))
    for (vx0, vx1, vy0, vy1, _) in verticals():
        rect(ax, vx0, vy0, vx1, vy1, C["oak"], C["oak_e"], 0.45, z=6)
        ax.plot([vx0, vx0], [0, vy0], color="#9a9a9a", lw=0.4, ls=(0, (2, 2)), zorder=7)   # linia boxei
    ax.plot([TV["x1"], X1], [TV["y1"]] * 2, color="#9a9a9a", lw=0.45, ls=(0, (5, 2)), zorder=3)

    # cote orizontale, sub pardoseală
    stops = [XL, TV["x0"], TV["x1"], X0, X1, XR]
    texts = [f"~{fmt(TV['x0'] - XL)}", None, None, None, f"~{fmt(XR - X1)}"]
    for (p, q), t in zip(zip(stops[:-1], stops[1:]), texts):
        dim_h(ax, p, q, -12, ref=0, k=k, fs=5.2, text=t)
    dim_h(ax, XL, XR, -23, ref=0, text=f"{fmt(XR - XL)}  lățimea peretelui (măsurat)", k=k, fs=5.4)
    # pozițiile tijelor, sub polița de jos, de la capătul din stânga al poliței
    yb_lo = D["bot_lo"]
    rx = [X0] + [X0 + r for r in D["rod_x"]] + [X1]
    for p, q in zip(rx[:-1], rx[1:]):
        dim_h(ax, p, q, yb_lo - 6.5, ref=yb_lo, k=k, fs=4.8)
    ax.text(X0 + D["L"] / 2, yb_lo - 13.0, f"{N_RODS} tije M12 (câte {D['rods']} pe poliță), ascunse",
            fontsize=4.6, color=C["note"], ha="center", va="center", zorder=7)
    # poziția verticalei, în golul de deasupra discurilor de jos
    yv = Y_REC_LO + 1.6
    vx = [X0] + [v for (a, b, _, _, _) in verticals() for v in (a, b)] + [X1]
    for p, q in zip(vx[:-1], vx[1:]):
        dim_h(ax, p, q, yv, k=k, fs=4.8, dy=0.5)
    # cote verticale, în dreapta: nivelurile polițelor și ale discurilor
    xd = XR + 14
    levels = [0, TOWER["h"], D["bot_lo"], D["top_lo"], Y_REC_LO, D["bot_up"], D["top_up"], TV["y1"]]
    for p, q in zip(levels[:-1], levels[1:]):
        dim_v(ax, p, q, xd, ref=X1, dx=1.2 * k, k=k, fs=5.0, rot=(q - p) > 40)
    dim_v(ax, TV["y1"], SITE["device_y"][0], xd, ref=SITE["device_x"][1], dx=1.2 * k, k=k, fs=5.0,
          text=f"~{fmt(SITE['device_y'][0] - TV['y1'])}")
    dim_v(ax, 0, H_WALL, XR + 24, ref=XR + 10, dx=1.0 * k, k=k, fs=5.0, rot=True,
          text=f"~{fmt(H_WALL)} tavan (foto; dat: {fmt(SITE['wall_h'])})")
    # cote verticale, în stânga: televizorul
    for p, q, t in ((0, TV["y0"], f"~{fmt(TV['y0'])}"), (TV["y0"], TV["y1"], None),
                    (TV["y1"], H_WALL, f"~{fmt(H_WALL - TV['y1'])}")):
        dim_v(ax, p, q, XL - 15, ref=TV["x0"], dx=-1.2 * k, k=k, fs=5.0, rot=True, text=t)
    dim_v(ax, 0, TV["y1"], XL - 24, ref=XL - 12, dx=-1.0 * k, k=k, fs=5.0, rot=True,
          text=f"~{fmt(TV['y1'])} sus TV = sus discuri")
    ax.text(354.0, 91.0, "2 polițe din microciment pe placaj,\n"
            f"{fmt(D['L'])} × {fmt(D['P'])} × {fmt(D['T'])} cm, prinse ascuns,\nși o verticală din stejar, lipită\n"
            "doar de polița de jos", fontsize=5.2, color="#3f3a33", ha="center", va="center", zorder=7,
            weight="bold")
    label(ax, SITE["device_x"][0], 0.5 * sum(SITE["device_y"]), 300, 236, "dispozitiv alb existent", fs=5.0,
          ha="right")
    # trimiterile la detaliile B (opritorul de la capătul poliței de sus) și C (îmbinarea de jos a verticalei)
    yt_up = D["top_up"]
    ax.add_patch(mp.Circle((X1 - 1.0, yt_up + 9.0), 6.5, fc="none", ec=C["dim"], lw=0.5, zorder=12))
    ax.text(X1 + 7.0, yt_up + 19.0, "B", fontsize=7, weight="bold", ha="center", va="center", zorder=12)
    vx0, vx1 = verticals()[0][:2]
    ax.add_patch(mp.Circle(((vx0 + vx1) / 2, D["top_lo"]), 5.0, fc="none", ec=C["dim"], lw=0.5, zorder=12))
    ax.text(vx1 + 6.0, D["top_lo"] + 9.5, "C", fontsize=7, weight="bold", ha="center", va="center", zorder=12,
            bbox=dict(fc="white", ec="none", pad=0.3))


# ------------------------------------------------------------------ secțiune laterală, 1:15
SEC_Y = (104.0, 212.0)
SEC_Z = (-15.0, 45.0)


def side_section(ax):
    """Secțiune prin verticală, privind spre televizor: peretele în stânga, camera în dreapta."""
    k = K15
    y0, y1 = SEC_Y
    hatch(ax, -14, y0, 0, y1, z=1)
    ax.plot([0, 0], [y0, y1], color="k", lw=0.9, zorder=3)
    # dincolo de secțiune: televizorul și boxa de podea
    rect(ax, TV["z_front"] - TV["d"], y0, TV["z_front"], TV["y1"], "#d9d9d9", "#8a8a8a", 0.35, z=1)
    zb, zf = TOWER["z_back"], TOWER["z_back"] + TOWER["d"]
    rect(ax, zb, y0, zf, TOWER["h"], "#c9c9cb", "#555555", 0.4, z=2)
    ax.plot([zb - 2, zf + 2], [y0 + 0.6, y0 + 0.6], color="white", lw=2.2, zorder=3)
    ax.text((zb + SEC_Z[1]) / 2, y0 + 5, "boxa RP-8000F II", fontsize=4.6, color="#333333", ha="center",
            va="center", zorder=4)
    P = D["P"]
    for (side, level, x0, yb, yt) in shelves():
        shelf_layers(ax, 0, P, yb, yt, front=P)
        ym = (yb + yt) / 2
        ax.plot([-D["rod_wall"], D["rod_shelf"]], [ym, ym], color=C["steel"], lw=0.8, ls=(0, (4, 1.5)), zorder=7)
    # verticala secționată: piciorul, în locașul poliței de jos, cu cele 3 cepuri; capul, sub rostul de umbră
    vy0, vy1 = Y_FOOT, round(D["bot_up"] - D["vert_gap"], 1)
    rect(ax, 0, vy0, P, vy1, C["oak"], C["oak_e"], 0.6, z=5, hatch="////")
    zm = sorted(D["dowel_z"])[len(D["dowel_z"]) // 2]
    ax.plot([zm - D["glue_w"] / 2, zm + D["glue_w"] / 2], [vy0, vy0], color=C["glue"], lw=0.9, zorder=6)
    for zd in D["dowel_z"]:
        if zd != zm:   # cepurile de pe margini stau în găuri ovale, lungi pe adâncime
            rect(ax, zd - D["dowel_slot"] / 2, vy0, zd + D["dowel_slot"] / 2, vy0 + DOW_OUT + 0.1, "#f7f3ea",
                 C["oak_e"], 0.3, z=6.5)
        rect(ax, zd - D["dowel_d"] / 2, vy0 - DOW_IN, zd + D["dowel_d"] / 2, vy0 + DOW_OUT, C["beech"], "k", 0.3,
             z=7)
    ax.text(P / 2, (vy0 + vy1) / 2 + 6.0, "verticală\ndin stejar", fontsize=4.6, color="#3b2a14", ha="center",
            va="center", zorder=8, bbox=dict(fc="white", ec="none", pad=0.25, alpha=0.85))
    ax.text(P / 2, vy1 - 2.4, f"rost de {fmt(D['vert_gap'] * 10)} mm, fără cep", fontsize=4.2, color="#3b2a14",
            ha="center", va="center", zorder=8, bbox=dict(fc="white", ec="none", pad=0.2, alpha=0.85))
    # cepurile, de la perete
    zs = [0.0] + list(D["dowel_z"]) + [P]
    for p, q in zip(zs[:-1], zs[1:]):
        dim_h(ax, p, q, vy0 + 7.0, k=k * 0.7, fs=4.4, dy=0.5)
    # discurile de sus, prinse de secțiune
    yt = D["top_up"]
    rect(ax, REC_BACK, yt, REC_BACK + LP["size"], yt + LP["size"], "none", C["lp"], 0.6, z=6, ls=(0, (3, 2)))
    ax.text(LP["size"] / 2 + REC_BACK, D["top_up"] + 16, "LP 31,4", fontsize=4.8, color="#2f4f6f", ha="center",
            zorder=8)
    # trimiterea la detaliul A
    ya = (D["bot_up"] + D["top_up"]) / 2
    ax.add_patch(mp.Circle((0.0, ya), 4.5, fc="none", ec=C["dim"], lw=0.5, zorder=9))
    ax.text(-8.5, ya + 7.5, "A", fontsize=7, weight="bold", ha="center", va="center", zorder=9,
            bbox=dict(fc="white", ec="none", pad=0.3))
    # cote
    dim_h(ax, 0, P, y1 - 3, ref=TV["y1"], k=k, fs=5.0)
    levels = [TOWER["h"], D["bot_lo"], D["top_lo"], D["bot_up"], D["top_up"], TV["y1"]]
    for p, q in zip(levels[:-1], levels[1:]):
        dim_v(ax, p, q, 38.0, ref=P, dx=1.2 * k, k=k, fs=4.8)


# ------------------------------------------------------------------ plan (vedere de sus), 1:15
PLAN_Z = (-16.0, 62.0)


def plan_view(ax):
    k = K15
    zmax = 60.0
    rect(ax, XL, 0, XR, zmax, C["floor"], z=0)
    hatch(ax, XL - 12, -15, XR + 10, 0, z=1)
    hatch(ax, XL - 12, 0, XL, zmax, z=1)
    ax.plot([XL, XR], [0, 0], color="k", lw=0.9, zorder=3)
    ax.plot([XL, XL], [0, zmax], color="k", lw=0.9, zorder=3)
    ax.plot([XR, XR], [0, zmax], color="#8a8a8a", lw=0.5, ls=(0, (4, 2)), zorder=3)
    ax.text(XR + 5, 50, "trecere", rotation=90, fontsize=4.6, color=C["note"], ha="center", va="center", zorder=4)
    rect(ax, TV["x0"], TV["z_front"] - TV["d"], TV["x1"], TV["z_front"], C["tv"], z=4)
    cz = CABINET["z_front"]
    rect(ax, CABINET["x0"], cz - CABINET["d"], CABINET["x1"], cz, C["cab"], C["oak_e"], 0.5, z=4)
    ax.text((CABINET["x0"] + CABINET["x1"]) / 2, cz - 24, "comodă (48)", fontsize=5.0, color="#e8e8e8",
            ha="center", va="center", zorder=5)
    zb = TOWER["z_back"]
    for (a, b) in (TOWER["xl"], TOWER["xr"]):
        rect(ax, a, zb, b, zb + TOWER["d"], C["spk"], z=6)
    # polițele (deasupra planului de secționare, punctat), verticala de sub polița de sus și tijele
    rect(ax, X0, 0, X1, D["P"], C["conc"], "none", 0, z=8, alpha=0.55)
    rect(ax, X0, 0, X1, D["P"], "none", C["conc_e"], 0.8, z=11, ls=(0, (4, 2)))
    for (vx0, vx1, _, _, dep) in verticals():
        rect(ax, vx0, 0, vx1, dep, C["oak"], C["oak_e"], 0.6, z=10, ls=(0, (2, 1)))
    for rx in D["rod_x"]:
        ax.plot([X0 + rx] * 2, [-D["rod_wall"], D["rod_shelf"]], color=C["steel"], lw=0.7, ls=(0, (3, 1.5)),
                zorder=12)
    ax.text(X0 + 29.5, 29.3, f"2 polițe, una peste alta (la {fmt(D['bot_lo'])}\nși {fmt(D['bot_up'])} cm), "
            f"și verticala; {N_RODS} tije M12", fontsize=4.4, ha="center", va="center", zorder=12, color="#2f2b25",
            bbox=dict(fc="white", ec="none", pad=0.3, alpha=0.75))
    dim_v(ax, 0, D["P"], XR + 6, ref=X1, dx=1.2 * k, k=k, fs=5.0)
    dim_v(ax, 0, cz, CABINET["x0"] - 4, ref=CABINET["x0"], dx=-1.2 * k, k=k, fs=5.0, text=f"~{fmt(cz)}")
    dim_v(ax, 0, zb, XR + 16, ref=TOWER["xr"][1], dx=1.0 * k, k=k, fs=4.6, text=f"~{fmt(zb)}")
    ax.text(TOWER["xl"][0], zb + TOWER["d"] + 3.0, "portul boxei e în spate: ~8 cm până la perete", fontsize=4.6,
            color=C["note"], ha="left", va="center", zorder=12)


# ------------------------------------------------------------------ detaliul A (prinderea ascunsă), 1:5
DA_Z = (-15.5, 8.0)


def da_y():
    return D["bot_up"] - 8.0, D["top_up"] + 7.0


def detail_rod(ax):
    """Tija din dreptul poliței de sus, în secțiune: ancora chimică din perete și canalul din miezul poliței."""
    k = K5
    yb, yt = D["bot_up"], D["top_up"]
    ym = (yb + yt) / 2
    y1 = da_y()[1]
    yw = yb - 3.6          # zidăria se rupe aici, ca textul de dedesubt să nu stea pe hașură
    hatch(ax, -15.0, yw, 0, y1 - 0.5, z=1)
    ax.plot([0, 0], [yw, y1 - 0.5], color="k", lw=0.9, zorder=3)
    break_h(ax, yw, -15.0, 0)
    zc = 6.5
    shelf_layers(ax, 0, zc, yb, yt, hatch_core=False)
    break_v(ax, zc, yb, yt)
    # gaura din perete cu ancoră chimică, tija și canalul din miezul poliței, cu adeziv epoxidic lângă perete
    rw, rh, rr = D["wall_hole_d"] / 2, D["hole_d"] / 2, D["rod_d"] / 2
    rect(ax, -D["wall_hole_len"], ym - rw, 0, ym + rw, C["anchor"], "#666666", 0.4, z=4)
    rect(ax, 0, ym - rh, min(zc, D["rod_glue"]) - 0.2, ym + rh, "#e8c9ad", C["ply_e"], 0.3, z=6, ls=(0, (2, 1)))
    rect(ax, -D["rod_wall"], ym - rr, zc - 0.2, ym + rr, "#6a6a6a", "#222222", 0.4, z=7)
    rect(ax, REC_BACK, yt, zc - 0.3, y1 - 0.8, "none", C["lp"], 0.6, z=6, ls=(0, (3, 2)))
    dim_h(ax, -D["rod_wall"], 0, yb - 2.2, ref=ym - rw, k=k, fs=4.6, dy=-0.25)
    dim_v(ax, yb, yt, zc + 1.0, ref=zc, dx=0.3, k=k, fs=4.6)
    label(ax, -6.5, ym + 0.3, -7.2, yt + 3.6, f"tijă filetată M12, clasa 8.8, {fmt(D['rod_wall'] + D['rod_shelf'])} cm,"
          f"\nîn ancoră chimică (gaură Ø{fmt(D['wall_hole_d'] * 10)} × {fmt(D['wall_hole_len'])} cm)", fs=4.4,
          ha="center")
    label(ax, 3.2, yt - 0.1, 4.0, yt + 3.6, "microciment\n~2 mm", fs=4.2, ha="center")
    ax.text(zc + 1.4, yb - 6.0, f"tija intră {fmt(D['rod_shelf'])} cm în poliță, în canalul Ø{fmt(D['hole_d'] * 10)} × "
            f"{fmt(D['hole_len'])} cm\nfăcut din două semicanale frezate înainte de lipire;\nadeziv epoxidic doar pe "
            f"ultimii ~{fmt(D['rod_glue'])} cm, lângă perete", fontsize=4.4, ha="right", va="center", zorder=7)


# ------------------------------------------------------------------ detaliul B (opritorul), 1:5
DB_X = (392.5, 412.5)


def db_y():
    return D["bot_up"] - 4.0, D["top_up"] + 25.0


def detail_bookend(ax):
    """Capătul exterior al poliței de sus, din față: opritorul L din oțel, îmbrăcat într-o placă de stejar."""
    k = K5
    yb, yt = D["bot_up"], D["top_up"]
    (xa, xb), (y0, y1) = DB_X, db_y()
    rect(ax, xa, y0, xb, y1, C["wall"], z=0)
    rect(ax, xa - 1, yb, X1, yt, C["conc"], C["conc_e"], 0.6, z=4)
    xs, xe, _, _ = row_extents("sus", X0)[-1]
    records(ax, xa - 1.0, xe, yt, lw=0.4)
    t, o, h = D["bookend_t"], D["oak_t"], D["bookend_h"]
    rect(ax, xe - 10.0, yt, xe + t, yt + t, C["steel"], z=9)      # talpa, sub discuri
    rect(ax, xe, yt, xe + t, yt + h, C["steel"], z=9)              # placa verticală de oțel
    rect(ax, xe + t, yt, xe + t + o, yt + h, C["oak"], C["oak_e"], 0.6, z=9)
    dim_v(ax, yt, yt + h, xb - 1.6, ref=xe + t + o, dx=0.3, k=k, fs=4.6)
    dim_h(ax, xe + t, xe + t + o, yt + h + 2.5, ref=yt + h, k=k, fs=4.6)
    label(ax, xe + t + o / 2, yt + h - 4.0, 399.5, yt + h + 4.6,
          f"placă de stejar {fmt(o)} × {fmt(D['oak_d'])} × {fmt(h)} cm,\nlipită pe fața exterioară", fs=4.4,
          ha="center")
    label(ax, xe + t / 2, yt + 8.0, 399.0, yt + 12.5, f"opritor L din oțel,\n{fmt(h)} × {fmt(D['bookend_d'])} cm",
          fs=4.4, ha="center")
    label(ax, xe - 5.0, yt + 0.1, 399.0, yb - 2.2, "talpa stă sub discuri", fs=4.4, ha="center")


# ------------------------------------------------------------------ detaliul C (îmbinarea verticalei), 1:5
DC_X = (49.0, 74.0)        # cm de la capătul din stânga al poliței
STUB = 5.0                 # cât se vede din verticală la fiecare capăt
GAP_C = 4.0                # golul de rupere dintre cele două capete, pe desen


def dc_shift():
    """Cât coboară, pe desen, capul verticalei și polița de sus, ca verticala să încapă ruptă."""
    _, _, vy0, vy1, _ = verticals()[0]
    return round(vy1 - vy0 - 2 * STUB - GAP_C, 1)


def dc_y():
    return D["bot_lo"] - 5.0, D["top_up"] - dc_shift() + 1.0


def detail_joint(ax):
    """Secțiune paralelă cu peretele, prin cepul din mijloc: piciorul verticalei, lipit în locașul poliței de jos,
    și capul ei, cu rostul de umbră de sub polița de sus. Pe desen, verticala e ruptă și polița de sus, coborâtă."""
    k = K5
    S = dc_shift()
    xa, xb = DC_X
    va, vb, vc = vert_local()[0]
    rl, rr_ = rods_around(vc)
    d2 = D["dowel_d"] / 2
    for yb, yt in ((D["bot_lo"], D["top_lo"]), (D["bot_up"] - S, D["top_up"] - S)):
        shelf_layers(ax, xa + 0.6, xb - 0.6, yb, yt)
        break_v(ax, xa + 0.6, yb, yt)
        break_v(ax, xb - 0.6, yb, yt)
        ym = (yb + yt) / 2
        for r in (rl, rr_):
            ax.add_patch(mp.Circle((r, ym), D["hole_d"] / 2, fc="#f7f3ea", ec="#555555", lw=0.35, zorder=8))
            ax.add_patch(mp.Circle((r, ym), D["rod_d"] / 2 - 0.08, fc="#6a6a6a", ec="#222222", lw=0.3, zorder=9))
            ax.plot([r - 1.1, r + 1.1], [ym, ym], color="#222222", lw=0.25, ls=(0, (6, 2, 1, 2)), zorder=10)
            ax.plot([r, r], [ym - 1.1, ym + 1.1], color="#222222", lw=0.25, ls=(0, (6, 2, 1, 2)), zorder=10)
    # piciorul: intră 2 mm, în locașul din microciment, pe placaj; cepul din mijloc e lipit în ambele piese
    yf, yfe = Y_FOOT, D["top_lo"] + STUB
    rect(ax, va, yf, vb, yfe, C["oak"], C["oak_e"], 0.6, z=6, hatch="////")
    break_h(ax, yfe, va, vb)
    rect(ax, vc - d2, yf - DOW_IN, vc + d2, yf + DOW_OUT, C["beech"], C["glue"], 0.7, z=11)
    ax.plot([va, vb], [yf, yf], color=C["glue"], lw=1.1, zorder=12)
    ax.plot([vc, vc], [yf - DOW_IN - 0.8, yf + DOW_OUT + 0.8], color="#222222", lw=0.25, ls=(0, (6, 2, 1, 2)),
            zorder=12)
    dim_v(ax, yf - DOW_IN, yf, vb + 1.6, ref=vb, dx=0.3, k=k, fs=4.4)
    dim_v(ax, yf, yf + DOW_OUT, vb + 1.6, ref=vb, dx=0.3, k=k, fs=4.4)
    # capul: se oprește la 3 mm sub polița de sus, fără cep
    yh = D["bot_up"] - D["vert_gap"] - S
    rect(ax, va, yh - STUB, vb, yh, C["oak"], C["oak_e"], 0.6, z=6, hatch="////")
    break_h(ax, yh - STUB, va, vb)
    # de la cep la tijele vecine (ax la ax)
    ytk = D["bot_lo"] - 2.4
    dim_h(ax, rl, vc, ytk, ref=D["bot_lo"], k=k, fs=4.4, dy=-0.3)
    dim_h(ax, vc, rr_, ytk, ref=D["bot_lo"], k=k, fs=4.4, dy=-0.3)
    ax.text((xa + xb) / 2, D["bot_lo"] - 4.4, "de la cep la tijele M12 vecine, ax la ax", fontsize=4.0,
            color=C["note"], ha="center", va="center", zorder=12)
    # în stânga, etichetele piciorului; în dreapta, cotele cepului și rostul
    xl, xr = (xa + 0.6 + va) / 2, (vb + 2.4 + xb - 0.6) / 2 + 0.5
    label(ax, va + 0.3, D["top_lo"] - 0.1, xl, yf + 1.9, f"locaș de {fmt(D['coat_t'] * 10)} mm:\nfără microciment",
          fs=4.2, ha="center")
    label(ax, vc - 0.2, yf + 1.0, xl + 0.3, yf + 7.0, f"cepul din mijloc,\nfag Ø{fmt(D['dowel_d'] * 10)} × "
          f"{fmt(D['dowel_len'] * 10)} mm,\nlipit cu epoxid", fs=4.2, ha="center")
    label(ax, vb - 0.4, yh + D["vert_gap"] / 2, xr, yh - 2.4, f"rost de {fmt(D['vert_gap'] * 10)} mm,\nfără cep",
          fs=4.2, ha="center")
    label(ax, va + 0.3, yh - 2.6, xl, yh - 2.6, "verticală\ndin stejar", fs=4.2, ha="center")


# ------------------------------------------------------------------ legenda materialelor
def legend(fig, x, y):
    items = [(C["conc"], C["conc_e"], None, "microciment ~2 mm (C: beton gri; D: antracit)"),
             (C["ply"], C["ply_e"], "....", "miez: 2 plăci de placaj de mesteacăn, 18 mm"),
             (C["oak"], C["oak_e"], None, "stejar masiv: verticala, plăcile opritoarelor"),
             (C["beech"], C["glue"], None, "cep din fag, lipit cu adeziv epoxidic"),
             ("#6a6a6a", "#222222", None, "oțel: tije M12 de clasa 8.8, opritoare L")]
    fig.text(x / PAGE[0], y / PAGE[1], "LEGENDĂ", fontsize=6.4, weight="bold", ha="left", va="top")
    y -= 4.2
    for fc, ec, ht, txt in items:
        fig.patches.append(mp.Rectangle((x / PAGE[0], (y - 1.7) / PAGE[1]), 4.0 / PAGE[0], 2.0 / PAGE[1],
                                        transform=fig.transFigure, fc=fc, ec=ec, lw=0.4, hatch=ht, figure=fig))
        fig.text((x + 5.5) / PAGE[0], (y - 0.7) / PAGE[1], txt, fontsize=4.6, ha="left", va="center")
        y -= 2.9
    return y


# ------------------------------------------------------------------ notele
NOTE_X, NOTE_Y, NOTE_W = 327.0, 114.5, 88.0   # mm: colțul de sus al coloanei de note și lățimea ei
NOTE_FS, NOTE_STEP = 4.7, 2.25                # corpul de literă (pt) și distanța dintre rânduri (mm)


def seq(vals):
    """„a, b și c”, cu virgulă zecimală."""
    vals = [fmt(v) for v in vals]
    return ", ".join(vals[:-1]) + f" și {vals[-1]}"


def dims(*vals):
    return " × ".join(fmt(v) for v in vals)


def notes():
    """Notele, ca paragrafe; text_block le rupe în rânduri după lățimea coloanei."""
    lo_j, lo_s, hi = capacity("jos")[0], capacity("sus")[0], capacity()[1]
    tot_j, tot_s = loads("jos")[3], loads("sus")[3]
    tot_jf, tot_sf = loads("jos", True)[3], loads("sus", True)[3]
    sigma, reserve = rod_check()
    reserve48 = rod_check(320.0)[1]
    kg_lo, kg_up = pieces_kg()
    vc = vert_local()[0][2]
    rl, rr_ = rods_around(vc)
    rods_tv = [X0 + r - TV["x1"] for r in D["rod_x"]]
    ys = [round(TV["y1"] - (yb + yt) / 2, 1) for (_, _, _, yb, yt) in shelves()]
    vx0 = verticals()[0][0]
    gap, coat = fmt(D["vert_gap"] * 10), fmt(D["coat_t"] * 10)
    return [
        ("MATERIALE ȘI EXECUȚIE", [
            f"1. 2 polițe de {dims(D['L'], D['P'], D['T'])} cm (~{fmt(shelf_kg())} kg una): miez din 2 plăci de placaj "
            f"de mesteacăn de {fmt(D['core_t'] * 5)} mm, lipite; ~{coat} mm de microciment, cu muchii "
            f"R{fmt(D['edge_r'] * 10)}, plasă și lac PU mat. Spatele și canalele se sigilează.",
            f"2. Canalele tijelor, Ø{fmt(D['hole_d'] * 10)} × {fmt(D['hole_len'])} cm, la {seq(D['rod_x'])} cm de "
            "capătul din stânga: din semicanale frezate în plăcile miezului înainte de lipire (detaliul A).",
            f"3. Verticala, din stejar masiv, {dims(D['vert_t'], D['P'], D['vert_h'])} cm (~{fmt(vertical_kg())} kg), "
            f"cu fibra pe verticală: stă în locașul de {coat} mm al poliței de jos și se oprește la {gap} mm sub cea "
            "de sus (detaliul C).",
            f"4. {N_DOW} cepuri din fag Ø{fmt(D['dowel_d'] * 10)} × {fmt(D['dowel_len'] * 10)} mm, la "
            f"{seq(D['dowel_z'])} cm de perete, intră {fmt(DOW_IN)} cm în poliță și {fmt(DOW_OUT)} cm în verticală. "
            f"Doar cel din mijloc e lipit, cu adeziv epoxidic pe ~{fmt(D['glue_w'])} cm; celelalte două stau în "
            f"găuri ovale de {dims(D['dowel_d'] * 10, D['dowel_slot'] * 10)} mm.",
            f"5. {N_RODS} tije M12 de clasa 8.8, de {fmt(D['rod_wall'] + D['rod_shelf'])} cm: {fmt(D['rod_wall'])} cm "
            f"în ancoră chimică (găuri Ø{fmt(D['wall_hole_d'] * 10)} × {fmt(D['wall_hole_len'])} cm), "
            f"{fmt(D['rod_shelf'])} cm în poliță.",
            f"6. {N_BOOK} opritoare L din oțel, de {dims(D['bookend_h'], D['bookend_d'])} cm, îmbrăcate în stejar, cu "
            "folie sub talpă (detaliul B).",
            f"7. Șablonul: {dims(D['L'], D['jig_d'], D['T'])} cm, din același miez, cu canalele la "
            f"{fmt(D['T'] / 2)} cm de fața de jos.",
        ]),
        ("DE CE AȘA", [
            "• Beton la orizontale, stejar la verticală, ca la comodă; verticala urcă din marginea boxei.",
            f"• Pe placaj, polița are ~{fmt(shelf_kg())} kg; din beton GFRC masiv, ar avea ~{fmt(round(gfrc_kg()))} kg.",
            f"• Plină, polița de jos are ~{fmt(tot_j)} kg, iar cea de sus ~{fmt(tot_s)} kg (ticsite: ~{fmt(tot_jf)} "
            f"și ~{fmt(tot_sf)} kg). Încap ~{lo_j} de discuri jos și ~{lo_s} sus (ticsite, ~{hi}).",
            f"• Polița de jos ticsită, doar în tije: ~{sigma} MPa, rezervă ~{fmt(round(reserve, 1))} la clasa 8.8; "
            f"la 4.8, doar ~{fmt(round(reserve48, 1))}, deci nu se folosește.",
            f"• Sprijinită pe perete, polița trage de fiecare ancoră cu ~{kn(rod_pull())} kN: fișa ancorei și proba "
            "confirmă că peretele o ține.",
            f"• Cepurile stau la {fmt(vc - rl)} și {fmt(rr_ - vc)} cm de tijele vecine, ax la ax: nu ating canalele.",
        ]),
        ("MONTAJUL", [
            "1) Tijele de jos, prin șablon, în ancora chimică; șablonul stă la nivel până se întărește ancora.",
            f"2) Adeziv epoxidic pe ultimii ~{fmt(D['rod_glue'])} cm ai tijelor; polița de jos, cu verticala "
            f"(~{fmt(kg_lo)} kg), până la perete.",
            f"3) Șablonul, pe verticală, peste distanțiere de {gap} mm: tijele de sus, apoi polița de sus "
            f"(~{fmt(kg_up)} kg).",
            f"4) Proba: {fmt(D['test_kg'])} kg pe fiecare poliță, 24 de ore. Dacă polițele rămân la nivel și rostul de "
            f"{gap} mm e liber, urmează opritoarele și discurile.",
        ]),
        ("COTE", [
            f"Găurile se măsoară de la televizor, nu de la tavan: la {seq(rods_tv)} cm de marginea lui din dreapta "
            f"și la {fmt(ys[1])} și {fmt(ys[0])} cm sub cea de sus.",
        ]),
        ("COTE DE MĂSURAT", [
            f"a) înălțimea camerei (poza dă ~{fmt(round(H_WALL))}, nu {fmt(SITE['wall_h'])});",
            "b) marginile televizorului: cea de sus, de la pardoseală, și cea din dreapta, de la colț;",
            f"c) marginea din stânga a boxei din dreapta, de la colț (~{fmt(vx0)}): locul verticalei;",
            "d) din ce e peretele și cât e de gros: de el depind ancora și manșoanele-sită;",
            "e) codul de finisaj al comodei (CS, NO, FE sau SO), pentru stejar;",
            f"f) dacă trecerea din dreapta are ușă care se deschide spre perete (polița e la {fmt(XR - X1)} cm);",
            "g) cablurile din perete, cu detectorul, mai ales sub dispozitivul alb.",
        ]),
    ]


def kn(v):
    return f"{v:.2f}".replace(".", ",")


def width_mm(fig, s, fs):
    """Lățimea pe hârtie (mm) a unui text scris cu DejaVu Sans."""
    w = fig.canvas.get_renderer().get_text_width_height_descent(s, FontProperties(family="DejaVu Sans", size=fs),
                                                                 ismath=False)[0]
    return w * 25.4 / fig.dpi


def wrap(fig, para, fs, width=NOTE_W):
    """Rupe un paragraf în rânduri care încap pe lățimea dată (mm), măsurate cu fontul real.

    Numerele rămân lipite de unități și de semnul „×”; rândurile de continuare se aliniază după numărul sau
    semnul de la începutul paragrafului.
    """
    para = para.replace(" × ", f"{NB}×{NB}")
    para = re.sub(r"(\d) (cm|mm|kg|kN|MPa|ori)\b", rf"\1{NB}\2", para)
    m = re.match(r"(\d+\.|\d+\)|[a-z]\)|•) ", para)
    pad = " " * round(width_mm(fig, m.group(0), fs) / width_mm(fig, " ", fs)) if m else ""
    lines, cur = [], ""
    for word in para.split(" "):
        cand = f"{cur} {word}" if cur else word
        if cur and width_mm(fig, cand, fs) > width:
            lines.append(cur)
            cur = pad + word
        else:
            cur = cand
    return lines + [cur]


def text_block(fig, x, y, title, paras, fs=NOTE_FS, step=NOTE_STEP):
    fig.text(x / PAGE[0], y / PAGE[1], title, fontsize=6.2, weight="bold", ha="left", va="top")
    y -= 3.3
    for para in paras:
        for ln in wrap(fig, para, fs):
            fig.text(x / PAGE[0], y / PAGE[1], ln, fontsize=fs, ha="left", va="top", family="DejaVu Sans")
            y -= step
    return y - 1.1


def build():
    fig = plt.figure(figsize=(PAGE[0] / 25.4, PAGE[1] / 25.4))
    fig.text(8 / PAGE[0], 1 - 8 / PAGE[1], "Polițe din beton decorativ și stejar pentru viniluri",
             fontsize=13, weight="bold", ha="left", va="top")
    fig.text(8 / PAGE[0], 1 - 15 / PAGE[1],
             f"2 polițe din microciment pe placaj, {dims(D['L'], D['P'], D['T'])} cm, în dreapta televizorului, la "
             f"{fmt(D['bot_lo'])} și {fmt(D['bot_up'])} cm, prinse ascuns în perete, și o verticală din stejar lipită "
             "de cea de jos  ·  varianta C: beton gri și stejar; varianta D: beton antracit și stejar (planul e comun)",
             fontsize=7, color=C["note"], ha="left", va="top")
    fig.text(8 / PAGE[0], 1 - 19.5 / PAGE[1],
             "cote în cm  ·  scara 1:15 (A3), detalii 1:5  ·  cotele cu „~” sunt din fotografie, de verificat",
             fontsize=7, color=C["note"], ha="left", va="top")
    ax1 = make_axes(fig, 5, 72, (-30.0, 450.0), (-26.0, 266.0), "VEDERE FRONTALĂ (1:15)", MM15)
    wall_elevation(ax1)
    ax2 = make_axes(fig, 5, 12, (-30.0, 450.0), PLAN_Z, "PLAN – VEDERE DE SUS (1:15)", MM15, invert=True)
    plan_view(ax2)
    ax3 = make_axes(fig, 327, 194, SEC_Z, SEC_Y, "SECȚIUNE PRIN VERTICALĂ (1:15)", MM15)
    side_section(ax3)
    (ya, yb) = dc_y()
    ax6 = make_axes(fig, 368.5, 258.0 - (yb - ya) * MM5, DC_X, dc_y(), None, MM5)
    fig.text(368.5 / PAGE[0], 260.5 / PAGE[1], "DETALIU C – verticala (1:5)", fontsize=8.5, weight="bold",
             ha="left", va="bottom")
    detail_joint(ax6)
    (ya, yb) = db_y()
    ax4 = make_axes(fig, 376, 182.0 - (yb - ya) * MM5, DB_X, db_y(), "DETALIU B – opritor (1:5)", MM5)
    detail_bookend(ax4)
    (ya, yb) = da_y()
    ax5 = make_axes(fig, 327, 182.0 - (yb - ya) * MM5, DA_Z, da_y(), "DETALIU A – tija (1:5)", MM5)
    detail_rod(ax5)
    legend(fig, 327, 182.0 - (yb - ya) * MM5 - 5.0)
    y = NOTE_Y
    for title, paras in notes():
        y = text_block(fig, NOTE_X, y, title, paras)
    return fig


def main(out_base):
    fig = build()
    fig.savefig(out_base + ".pdf")
    fig.savefig(out_base + ".png", dpi=220)
    plt.close(fig)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "plan_tehnic_polite_viniluri_beton")
    main(out)
    print("salvat", out)
