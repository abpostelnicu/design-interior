"""Planul tehnic A3, la scara 1:15, al polițelor flotante pentru viniluri de pe peretele cu televizorul.

Vedere frontală, secțiune laterală și plan la 1:15, ca la cuier; detaliul A (prinderea ascunsă) la 1:3 și
detaliul B (opritorul de la capătul rândului de discuri) la 1:5.
"""
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mp
import matplotlib.pyplot as plt
import numpy as np

from design import CABINET, CENTER, D, LP, SITE, TOWER, TV, capacity, loads, rod_check, row_extent, shelves

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = (420.0, 297.0)
MM15 = 10.0 / 15.0   # mm de hârtie pe cm real, la 1:15
MM5 = 10.0 / 5.0
MM3 = 10.0 / 3.0
K15, K5, K3 = 1.5, 0.5, 0.3   # scalarea liniuțelor de cotă pentru fiecare scară

C = dict(wall="#ecebe7", hatch="#8f8f8f", oak="#c9a06a", oak_e="#7b5b37", tv="#202124", tv_e="#000000",
         cab="#5a5c5e", spk="#26272b", base="#ffffff", lp="#7f9db8", dim="#1a1a1a", note="#555555",
         floor="#efe3cf", dev="#f3efe6", steel="#222222", anchor="#b9b9b9")
FS = 5.6
H_WALL = SITE["wall_h_photo"]
XL, XR = 0.0, SITE["wall_w"]
X0, X1 = D["x_right"], D["x_right"] + D["L"]   # capetele polițelor
Y_REC_LO = D["top_lo"] + LP["size"]               # sus discuri pe polița de jos
REC_BACK = 0.7                                    # discurile stau la 7 mm de perete


def fmt(v):
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


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



def records(ax, xs, xe, yt, lw=0.25, step=1.1):
    """Rândul de discuri în vedere frontală: conturul și cotoarele."""
    rect(ax, xs, yt, xe, yt + LP["size"], "#e9eef3", C["lp"], 0.35, z=7, ls=(0, (3, 1.5)))
    for x in np.arange(xs + step / 2, xe, step):
        ax.plot([x, x], [yt + 0.3, yt + LP["size"] - 0.3], color=C["lp"], lw=lw, zorder=8)


def bookend_front(ax, x_rec, yt, toward):
    """Opritorul din varianta A, din față: placa de oțel lipită de discuri și placa de stejar spre exterior.

    x_rec e capătul rândului de discuri; toward = -1 la capătul din stânga al rândului, +1 la cel din dreapta.
    """
    t, o, h = D["bookend_t"], D["oak_t"], D["bookend_h"]
    xs = x_rec if toward > 0 else x_rec - t
    xo = x_rec + t if toward > 0 else x_rec - t - o
    rect(ax, xs, yt, xs + t, yt + h, C["steel"], z=9)
    rect(ax, xo, yt, xo + o, yt + h, C["oak"], C["oak_e"], 0.35, z=9)


def shelf_front(ax, x0, yb, yt, z=6):
    rect(ax, x0, yb, x0 + D["L"], yt, C["oak"], C["oak_e"], 0.45, z=z)


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
    ax.text((cx0 + cx1) / 2, 40, "comodă Cioata Veneto 242", color="#e8e8e8", fontsize=5.2, ha="center",
            va="center", zorder=6)
    cc = TV["axis"]
    rect(ax, cc - CENTER["w"] / 2, CABINET["h"], cc + CENTER["w"] / 2, CABINET["h"] + CENTER["h"], C["spk"], z=6)
    for (a, b) in (TOWER["xl"], TOWER["xr"]):
        rect(ax, a, 0, b, TOWER["h"], C["spk"], "#000000", 0.4, z=6)
        ax.text((a + b) / 2, 55, "Klipsch RP-8000F II", rotation=90, color="#bdbdbd", fontsize=4.6,
                ha="center", va="center", zorder=7)
    rect(ax, SITE["device_x"][0], SITE["device_y"][0], SITE["device_x"][1], SITE["device_y"][1], C["dev"],
         "#9a9a9a", 0.4, z=6)
    # noi: cele două polițe, cu discurile, opritoarele din varianta A și tijele ascunse (cercuri)
    for (side, level, x0, yb, yt) in shelves():
        shelf_front(ax, x0, yb, yt)
        xs, xe = row_extent(side, level, x0)
        records(ax, xs, xe, yt)
        bookend_front(ax, xs, yt, -1)
        bookend_front(ax, xe, yt, +1)
        ym = (yb + yt) / 2
        for rx in D["rod_x"]:
            ax.add_patch(mp.Circle((x0 + rx, ym), D["rod_d"] / 2, fc="none", ec=C["steel"], lw=0.35, zorder=8))
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
    ax.text(X0 + D["L"] / 2, yb_lo - 13.0, "tijele M12, ascunse în poliță", fontsize=4.6, color=C["note"],
            ha="center", va="center", zorder=7)
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
    ax.text(357.0, 90.0, f"2 polițe flotante din stejar\n{fmt(D['L'])} × {fmt(D['P'])} × {fmt(D['T'])} cm, "
            "prinse ascuns", fontsize=5.4, color="#5b3f1d", ha="center", va="center", zorder=7, weight="bold")
    label(ax, SITE["device_x"][0], 0.5 * sum(SITE["device_y"]), 300, 236, "dispozitiv alb existent", fs=5.0,
          ha="right")
    # trimiterea la detaliul B: opritorul de la capătul exterior al poliței de sus
    yt_up = D["top_up"]
    ax.add_patch(mp.Circle((X1 - 1.0, yt_up + 9.0), 6.5, fc="none", ec=C["dim"], lw=0.5, zorder=12))
    ax.text(X1 + 7.0, yt_up + 19.0, "B", fontsize=7, weight="bold", ha="center", va="center", zorder=12)


# ------------------------------------------------------------------ secțiune laterală, 1:15
SEC_Y = (100.0, 214.0)
SEC_Z = (-15.0, 45.0)


def side_section(ax):
    """Secțiune prin polițe, prin tija dinspre capătul peretelui, privind spre televizor: peretele în stânga."""
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
    for (side, level, x0, yb, yt) in shelves():
        rect(ax, 0, yb, D["P"], yt, C["oak"], C["oak_e"], 0.6, z=5, hatch="....")
        rect(ax, REC_BACK, yt, REC_BACK + LP["size"], yt + LP["size"], "none", C["lp"], 0.6, z=6, ls=(0, (3, 2)))
        ym = (yb + yt) / 2
        ax.plot([-D["rod_wall"], D["rod_shelf"]], [ym, ym], color=C["steel"], lw=0.8, ls=(0, (4, 1.5)), zorder=7)
    ax.text(LP["size"] / 2 + REC_BACK, D["top_up"] + 16, "LP 31,4", fontsize=4.8, color="#2f4f6f", ha="center",
            zorder=8)
    # trimiterea la detaliul A
    ya = (D["bot_up"] + D["top_up"]) / 2
    ax.add_patch(mp.Circle((0.0, ya), 4.5, fc="none", ec=C["dim"], lw=0.5, zorder=9))
    ax.text(-8.5, ya + 7.5, "A", fontsize=7, weight="bold", ha="center", va="center", zorder=9,
            bbox=dict(fc="white", ec="none", pad=0.3))
    # cote
    dim_h(ax, 0, D["P"], y1 - 3, ref=TV["y1"], k=k, fs=5.0)
    levels = [TOWER["h"], D["bot_lo"], D["top_lo"], Y_REC_LO, D["bot_up"], D["top_up"], TV["y1"]]
    for p, q in zip(levels[:-1], levels[1:]):
        dim_v(ax, p, q, 38.0, ref=D["P"], dx=1.2 * k, k=k, fs=4.8)


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
    # polițele (deasupra planului de secționare, punctat) și tijele, care intră 13 cm în perete
    rect(ax, X0, 0, X1, D["P"], C["oak"], "none", 0, z=8, alpha=0.35)
    rect(ax, X0, 0, X1, D["P"], "none", "#5b3f1d", 0.8, z=11, ls=(0, (4, 2)))
    for rx in D["rod_x"]:
        ax.plot([X0 + rx] * 2, [-D["rod_wall"], D["rod_shelf"]], color=C["steel"], lw=0.7, ls=(0, (3, 1.5)),
                zorder=12)
    ax.text(X0 + 30, 29.3, f"2 polițe, una peste alta (la {fmt(D['bot_lo'])}\nși {fmt(D['bot_up'])} cm), "
            f"câte {D['rods']} tije M12", fontsize=4.4, ha="center", va="center", zorder=12, color="#3b2a14",
            bbox=dict(fc="white", ec="none", pad=0.3, alpha=0.75))
    dim_v(ax, 0, D["P"], XR + 6, ref=X1, dx=1.2 * k, k=k, fs=5.0)
    dim_v(ax, 0, cz, CABINET["x0"] - 4, ref=CABINET["x0"], dx=-1.2 * k, k=k, fs=5.0, text=f"~{fmt(cz)}")
    dim_v(ax, 0, zb, XR + 16, ref=TOWER["xr"][1], dx=1.0 * k, k=k, fs=4.6, text=f"~{fmt(zb)}")
    ax.text(TOWER["xl"][0], zb + TOWER["d"] + 3.0, "portul boxei e în spate: ~8 cm până la perete", fontsize=4.6,
            color=C["note"], ha="left", va="center", zorder=12)


# ------------------------------------------------------------------ detaliul A (prinderea ascunsă), 1:3
def detail_rod(ax):
    k = K3
    yb, yt = D["bot_up"], D["top_up"]
    ym = (yb + yt) / 2
    hatch(ax, -13.5, yb - 3, 0, yt + 5, z=1)
    ax.plot([0, 0], [yb - 3, yt + 5], color="k", lw=0.9, zorder=3)
    zc = 9.5
    rect(ax, 0, yb, zc, yt, C["oak"], C["oak_e"], 0.6, z=4, hatch="....")
    ax.plot([zc, zc], [yb - 0.4, yt + 0.4], color="white", lw=2.0, zorder=5)
    ax.plot([zc - 0.25, zc + 0.25, zc - 0.25, zc + 0.25], [yb - 0.4, ym - 0.6, ym + 0.6, yt + 0.4], color="k",
            lw=0.5, zorder=6)
    # gaura din perete cu ancoră chimică, tija și gaura din poliță
    rw, rh, rr = D["wall_hole_d"] / 2, D["hole_d"] / 2, D["rod_d"] / 2
    rect(ax, -D["rod_wall"], ym - rw, 0, ym + rw, C["anchor"], "#666666", 0.4, z=4)
    rect(ax, 0, ym - rh, zc, ym + rh, "#f3e2c6", "#8a6a45", 0.3, z=5, ls=(0, (2, 1)))
    rect(ax, -D["rod_wall"] + 0.5, ym - rr, zc, ym + rr, "#5a5a5a", "#222222", 0.4, z=6)
    ax.text(zc - 0.6, yb - 1.9, f"tija intră {fmt(D['rod_shelf'])} cm în poliță →\n(gaură Ø{fmt(D['hole_d'] * 10)} "
            f"× {fmt(D['hole_len'])} cm)", fontsize=4.6, ha="right", va="center", zorder=7)
    rect(ax, REC_BACK, yt, zc - 0.3, yt + 4.5, "none", C["lp"], 0.6, z=6, ls=(0, (3, 2)))
    dim_h(ax, -D["rod_wall"], 0, yb - 1.6, ref=ym - rw, k=k, fs=4.8, dy=-0.25)
    dim_v(ax, yb, yt, zc + 1.0, ref=zc, dx=0.3, k=k, fs=4.8)
    label(ax, -6.0, ym + 0.4, -6.0, yt + 3.5, f"tijă filetată M12, {fmt(D['rod_wall'] + D['rod_shelf'])} cm,\n"
          f"în ancoră chimică (gaură Ø{fmt(D['wall_hole_d'] * 10)})", fs=4.8, ha="center")
    label(ax, 4.0, yt - 1.0, 4.0, yt + 3.2, "disc", fs=4.6, ha="center")


# ------------------------------------------------------------------ detaliul B (opritorul), 1:5
DB_X = (391.0, 413.0)


def db_y():
    return D["bot_up"] - 3.0, D["top_up"] + 26.0


def detail_bookend(ax):
    """Capătul exterior al poliței de sus, din față: opritorul L de oțel și placa de stejar din varianta A."""
    k = K5
    yb, yt = D["bot_up"], D["top_up"]
    (xa, xb), (y0, y1) = DB_X, db_y()
    rect(ax, xa, y0, xb, y1, C["wall"], z=0)
    rect(ax, xa - 1, yb, X1, yt, C["oak"], C["oak_e"], 0.6, z=4)
    xs, xe = row_extent("dreapta", "sus", X0)
    records(ax, xa - 1.0, xe, yt, lw=0.4)
    t, o, h = D["bookend_t"], D["oak_t"], D["bookend_h"]
    rect(ax, xe - 10.0, yt, xe + t, yt + t, C["steel"], z=9)      # talpa, sub discuri
    rect(ax, xe, yt, xe + t, yt + h, C["steel"], z=9)              # placa verticală de oțel
    rect(ax, xe + t, yt, xe + t + o, yt + h, C["oak"], C["oak_e"], 0.6, z=9)
    dim_v(ax, yt, yt + h, xb - 2.0, ref=xe + t + o, dx=0.3, k=k, fs=4.6)
    dim_h(ax, xe + t, xe + t + o, yt + h + 2.5, ref=yt + h, k=k, fs=4.6)
    label(ax, xe + t + o / 2, yt + h - 4.0, 398.5, yt + h + 4.5,
          f"placă de stejar {fmt(o)} × {fmt(D['oak_d'])} × {fmt(h)} cm,\nlipită pe opritor (doar în A)", fs=4.6,
          ha="center")
    label(ax, xe + t / 2, yt + 8.0, 398.5, yt + 13.0,
          f"opritor L din oțel negru mat,\n{fmt(h)} × {fmt(D['bookend_d'])} cm (A și B)", fs=4.6, ha="center")
    label(ax, xe - 5.0, yt + 0.1, 398.0, yb - 1.6, "talpa stă sub discuri", fs=4.6, ha="center")


# ------------------------------------------------------------------ notele
def notes():
    lo, hi = capacity()
    shelf_kg, rec_kg, tot = loads()
    sigma, reserve = rod_check()
    rods_tv = ", ".join(fmt(X0 + r - TV["x1"]) for r in D["rod_x"][:-1]) + f" și {fmt(X0 + D['rod_x'][-1] - TV['x1'])}"
    ys = [round(TV["y1"] - (yb + yt) / 2, 1) for (_, _, _, yb, yt) in shelves()]
    return [
        ("MATERIALE ȘI FERONERIE", [
            f"1. 2 polițe flotante din stejar masiv, {fmt(D['L'])} × {fmt(D['P'])} × {fmt(D['T'])} cm, în finisajul "
            "comodei, fără console,",
            "   laterale sau spate; de la tâmplar sau de la Cioata, la comandă.",
            f"2. Prinderea ascunsă, pe poliță: {D['rods']} tije filetate M12 de "
            f"{fmt(D['rod_wall'] + D['rod_shelf'])} cm, {fmt(D['rod_wall'])} cm în perete, în ancoră",
            f"   chimică (găuri Ø{fmt(D['wall_hole_d'] * 10)}), și {fmt(D['rod_shelf'])} cm în poliță, în găuri "
            f"Ø{fmt(D['hole_d'] * 10)} × {fmt(D['hole_len'])} din cant (detaliul A).",
            f"3. 4 opritoare L din oțel negru mat, {fmt(D['bookend_h'])} × {fmt(D['bookend_d'])} cm, câte două pe "
            "poliță, mobile (detaliul B).",
            f"4. A: pe fiecare opritor, o placă de stejar de {fmt(D['oak_t'])} × {fmt(D['oak_d'])} × "
            f"{fmt(D['bookend_h'])} cm, lipită spre exterior.",
            "   B: opritoarele rămân negre, ca picioarele comodei.",
        ]),
        ("DE CE AȘA", [
            "• Doar linii de stejar: tijele intră în poliță și nu se vede nicio prindere.",
            f"• {fmt(D['P'])} cm adâncime: discul de {fmt(LP['size'])} cm încape întreg; {fmt(D['T'])} cm grosime "
            "ascund tijele M12.",
            f"• Discurile de sus se termină la nivelul marginii de sus a televizorului (~{fmt(TV['y1'])} cm);",
            f"  între rânduri rămân {fmt(D['clear'])} cm, iar deasupra boxei {fmt(D['bot_lo'] - TOWER['h'])} cm.",
            f"• La {fmt(D['gap_tv'])} cm de televizor; discurile stau spre capătul peretelui, lângă ecran rămâne loc.",
            f"• ~{lo} de discuri pe poliță (max ~{hi}), ~{2 * lo} în total; plină, o poliță are ~{fmt(round(tot))} kg.",
            f"• Chiar dacă polița ar sta doar în tije, efortul e ~{sigma} MPa, de ~{fmt(round(reserve, 1))} ori sub curgere.",
        ]),
        ("COTE", [
            f"Date: perete {fmt(SITE['wall_w'])} × {fmt(SITE['wall_h'])}; TV {fmt(TV['w'])} × {fmt(TV['h'])}; comodă "
            f"{fmt(CABINET['w'])} × {fmt(CABINET['d'])} × {fmt(CABINET['h'])};",
            f"boxe {fmt(TOWER['w'])} × {fmt(TOWER['h'])} × {fmt(TOWER['d'])}; disc {fmt(LP['size'])} × {fmt(LP['size'])}.",
            f"Din fotografie (~): tavan ~{fmt(H_WALL)}; TV de la ~{fmt(TV['y0'])} la ~{fmt(TV['y1'])} cm, la "
            f"~{fmt(TV['x0'])} cm de colț;",
            f"boxele la ~{fmt(TOWER['z_back'])} cm de perete; dispozitivul alb de la ~{fmt(SITE['device_y'][0])} cm.",
            "Polițele se măsoară de la televizor, nu de la tavan. Găurile din perete: la",
            f"{rods_tv} cm de marginea din dreapta a televizorului și la {fmt(ys[1])} și {fmt(ys[0])} cm",
            "sub marginea lui de sus.",
        ]),
        ("COTE DE MĂSURAT", [
            f"a) înălțimea camerei (poza dă ~{fmt(round(H_WALL))}, nu {fmt(SITE['wall_h'])});",
            "b) marginile televizorului: cea de sus, de la pardoseală, și cea din dreapta, de la colț;",
            "c) din ce e peretele și cât e de gros (pentru ancoră și adâncimea găurilor);",
            "d) codul de finisaj al comodei (CS, NO, FE sau SO), de pe comandă sau factură;",
            f"e) dacă trecerea din dreapta are ușă care se deschide spre perete (polița e la {fmt(XR - X1)} cm);",
            "f) cablurile din perete, cu detectorul, mai ales sub dispozitivul alb.",
        ]),
    ]


def text_block(fig, x, y, title, lines, fs=5.3, step=2.75):
    fig.text(x / PAGE[0], y / PAGE[1], title, fontsize=7.0, weight="bold", ha="left", va="top")
    y -= 4.0
    for ln in lines:
        fig.text(x / PAGE[0], y / PAGE[1], ln, fontsize=fs, ha="left", va="top", family="DejaVu Sans")
        y -= step
    return y - 1.8


def main(out_base):
    fig = plt.figure(figsize=(PAGE[0] / 25.4, PAGE[1] / 25.4))
    fig.text(8 / PAGE[0], 1 - 8 / PAGE[1], "Polițe flotante pentru viniluri – peretele cu televizorul (living)",
             fontsize=13, weight="bold", ha="left", va="top")
    fig.text(8 / PAGE[0], 1 - 15 / PAGE[1],
             f"2 polițe din stejar {fmt(D['L'])} × {fmt(D['P'])} × {fmt(D['T'])} cm, în dreapta televizorului, la "
             f"{fmt(D['bot_lo'])} și {fmt(D['bot_up'])} cm, prinse ascuns în perete"
             "      |  cote în cm  ·  scara 1:15 (A3), detalii 1:3 și 1:5  ·  cotele cu „~” sunt din fotografie, de verificat",
             fontsize=7, color=C["note"], ha="left", va="top")
    ax1 = make_axes(fig, 5, 72, (-30.0, 450.0), (-26.0, 266.0), "VEDERE FRONTALĂ (1:15)", MM15)
    wall_elevation(ax1)
    ax2 = make_axes(fig, 5, 12, (-30.0, 450.0), PLAN_Z, "PLAN – VEDERE DE SUS (1:15)", MM15, invert=True)
    plan_view(ax2)
    ax3 = make_axes(fig, 328, 186, SEC_Z, SEC_Y, "SECȚIUNE (1:15)", MM15)
    side_section(ax3)
    ax4 = make_axes(fig, 373, 196, DB_X, db_y(), "DETALIU B – opritor (1:5)", MM5)
    detail_bookend(ax4)
    ax5 = make_axes(fig, 330, 128, (-14.0, 11.5), (D["bot_up"] - 3.5, D["top_up"] + 5.5),
                    "DETALIU A – prinderea ascunsă (1:3)", MM3)
    detail_rod(ax5)
    y = 120.0
    for title, lines in notes():
        y = text_block(fig, 330.0, y, title, lines)
    fig.savefig(out_base + ".pdf")
    fig.savefig(out_base + ".png", dpi=220)
    plt.close(fig)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "plan_tehnic_polite_viniluri")
    main(out)
    print("salvat", out)
