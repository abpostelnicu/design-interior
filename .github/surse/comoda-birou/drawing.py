"""Planul tehnic A3, la scara 1:15, al comodei BoConcept Element din stânga biroului (Dormitor 2).

Vedere frontală și plan la 1:15, ca la cuier și la polițe; secțiune prin comodă la 1:15; detaliul A
(prinderea anti-răsturnare) și detaliul B (plinta și picioarele) la 1:5; planul camerei la 1:50, cu ușa.
"""
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mp
import matplotlib.pyplot as plt
import numpy as np

from design import (ANCHOR_DROP, ANCHOR_Y, BACK_T, DESK, EL, FIX_T, GAP_DESK, GAP_WALL, HOLE_DEPTH, SCREW_L,
                    SITE, TOP_T, Layout)

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = (420.0, 297.0)
MM15 = 10.0 / 15.0   # mm de hârtie pe cm real, la 1:15
MM5 = 10.0 / 5.0
MM50 = 10.0 / 50.0
K15, K5, K50 = 1.5, 0.5, 5.0   # scalarea liniuțelor de cotă pentru fiecare scară

C = dict(wall="#ecebe7", hatch="#8f8f8f", oak="#c9a06a", oak_e="#7b5b37", desk="#2a2b2e", desk_e="#000000",
         base="#ffffff", dim="#1a1a1a", note="#555555", floor="#efe3cf", steel="#222222", glass="#dce8f2",
         frame="#3a3a3a", plug="#f4f4f4", anchor="#b9b9b9", pull="#7b5b37")
FS = 5.6
L = Layout()
XB, XE = L.x0, L.x1                           # capetele comodei
DX0, DX1 = DESK["x0"], DESK["x0"] + DESK["w"]   # capetele biroului
WIN = SITE["win_x"]
X_CUT = 308.0                                   # vederile se opresc aici, cu linie de întrerupere
PULL = 40.0                                     # cât iese un sertar (extracție totală)  # est.
SWITCH = (233.8, 246.3, 116.3, 125.5)           # întrerupătorul de deasupra biroului, din fotografie  # est.
SOCKET = (232.8, 244.6, 26.6, 36.5)             # priza de sub birou, din fotografie  # est.
DESK_LEGS = (DX0 + 8.0, DX1 - 8.0)              # axele coloanelor biroului (schematic)


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


def callout(ax, x, y, r, name, tx, ty):
    ax.add_patch(mp.Circle((x, y), r, fc="none", ec=C["dim"], lw=0.5, zorder=24))
    ax.text(tx, ty, name, fontsize=7, weight="bold", ha="center", va="center", zorder=24,
            bbox=dict(fc="white", ec="none", pad=0.3))


def break_line(ax, x, y0, y1, z=6):
    """Linie de întrerupere verticală, în zigzag."""
    ym = (y0 + y1) / 2
    ys = [y0, ym - 6, ym - 2, ym + 2, ym + 6, y1]
    xs = [x, x, x - 3, x + 3, x, x]
    ax.plot(xs, ys, color="k", lw=0.5, zorder=z)


# ------------------------------------------------------------------ vedere frontală, 1:15
def dresser_front(ax, z=6, reed=True):
    y0, y1, fr = EL["leg_h"], EL["h"], EL["frame"]
    rect(ax, XB, y0, XE, y1, C["oak"], C["oak_e"], 0.5, z=z)
    for (a, b) in L.drawers:
        rect(ax, XB + fr, a, XE - fr, b, C["oak"], C["oak_e"], 0.35, z=z + 1)
        if reed:
            for x in np.arange(XB + fr + EL["reed"], XE - fr, EL["reed"] * 2):
                ax.plot([x, x], [a + 0.4, b - 0.4], color=C["oak_e"], lw=0.12, alpha=0.55, zorder=z + 2)
    # picioarele duble: din față, perechea din spate e ascunsă de cea din față
    r = EL["leg_rod"] / 2
    for xc in (XB + EL["leg_in_x"], XE - EL["leg_in_x"]):
        for dx in (-EL["leg_pair"] / 2, EL["leg_pair"] / 2):
            rect(ax, xc + dx - r, 0, xc + dx + r, y0, C["steel"], z=z)


def desk_front(ax, z=5):
    top, t = DESK["h"], DESK["top_t"]
    for xc in DESK_LEGS:
        rect(ax, xc - 3.25, 2.5, xc + 3.25, top - t, C["desk"], z=z)
        rect(ax, xc - 3.6, 0, xc + 3.6, 2.5, C["desk"], z=z)
    rect(ax, DX0, top - t, DX1, top, C["desk"], C["desk_e"], 0.4, z=z + 1)
    rect(ax, DX0 + 14, top - t - 7, DX1 - 14, top - t, C["desk"], z=z)   # tava de cabluri, dedesubt


def wall_elevation(ax):
    k = K15
    H = SITE["H"]
    rect(ax, 0, 0, X_CUT, H, C["wall"], z=0)
    hatch(ax, -15, -6, 0, H + 4, z=2)
    rect(ax, -15, -6, X_CUT, 0, "#f6efe3", z=1)
    ax.plot([-15, X_CUT], [0, 0], color="k", lw=1.0, zorder=5)
    ax.plot([0, X_CUT], [H, H], color="k", lw=0.8, zorder=5)
    ax.plot([0, 0], [0, H], color="k", lw=0.9, zorder=5)
    break_line(ax, X_CUT, -6, H + 4)
    ax.text(-7.5, 150, "perete spre Dormitor 1", rotation=90, fontsize=4.8, color=C["note"], ha="center",
            va="center", zorder=6, bbox=dict(fc="#f4f4f4", ec="none", pad=0.4))
    rect(ax, 0, 0, X_CUT, SITE["base_h"], C["base"], "#9a9a9a", 0.3, z=3)
    # fereastra Fe-06 (de colț), cu toc negru
    wh, ws = SITE["win_head"], SITE["win_sill"]
    rect(ax, WIN, ws, X_CUT, wh, C["frame"], z=3)
    rect(ax, WIN + 5, ws + 5, X_CUT, wh - 5, C["glass"], z=4)
    ax.text((WIN + X_CUT) / 2 + 2, 150, "fereastra Fe-06", rotation=90, fontsize=4.8, color="#3a4a5a",
            ha="center", va="center", zorder=5)
    # existente: întrerupătorul și priza
    for (a, b, c, d), name in ((SWITCH, "întrerupător"), (SOCKET, "priză")):
        rect(ax, a, c, b, d, C["plug"], "#666666", 0.35, z=6)
        ax.text((a + b) / 2, d + 2.5, name, fontsize=4.4, color=C["note"], ha="center", va="bottom", zorder=6)
    desk_front(ax)
    ax.text((DX0 + DX1) / 2, DESK["h"] + 4.0, "birou Secretlab MAGNUS Pro 1,5 m (existent)", fontsize=5.0,
            color="#333333", ha="center", va="bottom", zorder=7)
    # blatul urcă și coboară: pozițiile extreme, punctat
    for yy in (DESK["h_min"], DESK["h_max"]):
        ax.plot([DX0, DX0 + 46], [yy, yy], color="#555555", lw=0.5, ls=(0, (3, 1.5)), zorder=7)
    ax.text(DX0 + 47, DESK["h_max"], f"blatul, sus ({fmt(DESK['h_max'])})", fontsize=4.4, color=C["note"],
            va="center", zorder=7)
    ax.text(DX0 + 47, DESK["h_min"] - 0.5, f"jos ({fmt(DESK['h_min'])})", fontsize=4.4, color=C["note"],
            va="center", zorder=7, bbox=dict(fc=C["wall"], ec="none", pad=0.2))
    dresser_front(ax)
    ax.text((XB + XE) / 2, L.drawers[1][0] + 12.2, "BoConcept Element, 3 sertare\n"
            f"{fmt(EL['w'])} × {fmt(EL['d'])} × {fmt(EL['h'])} cm", fontsize=5.4, color="#4a3216", ha="center",
            va="center", weight="bold", zorder=9, bbox=dict(fc=C["oak"], ec="none", pad=0.4, alpha=0.9))
    # trimiterea la detaliul A: prinderea e în spate, sus (se vede din secțiune)
    ax.plot([XB + 30, XE - 30], [ANCHOR_Y] * 2, color=C["dim"], lw=0.4, ls=(0, (2, 1.5)), zorder=10)
    ax.text((XB + XE) / 2, EL["h"] + 3.0, "prinderea anti-răsturnare, în spate (detaliul A)", fontsize=4.4,
            color=C["note"], ha="center", va="bottom", zorder=10)

    # cote orizontale, sub pardoseală
    stops = [0, XB, XE, DX0, DX1, WIN]
    texts = [f"~{fmt(XB)}", None, fmt(GAP_DESK), None, f"~{fmt(WIN - DX1)}"]
    shift = [-4.5, 0.0, 0.0, 0.0, 4.5]          # cotele mici de la capete, mutate spre exterior
    for (p, q), t, sx in zip(zip(stops[:-1], stops[1:]), texts, shift):
        dim_h(ax, p, q, -9, ref=0, k=k, fs=5.0, text=t, txt_dx=sx)
    dim_h(ax, 0, DX0, -17, ref=0, k=k, fs=5.0, text=f"~{fmt(DX0)}  perete liber, de la colț la birou")
    dim_h(ax, 0, WIN, -25, ref=0, k=k, fs=5.0, text=f"{fmt(WIN)}  de la colț la fereastra Fe-06 (din plan)")
    # cote verticale, în stânga: comoda
    dim_v(ax, 0, EL["leg_h"], -21, ref=XB, dx=-1.2 * k, k=k, fs=5.0)
    dim_v(ax, EL["leg_h"], EL["h"], -21, ref=XB, dx=-1.2 * k, k=k, fs=5.0, rot=True,
          text=f"{fmt(EL['h'] - EL['leg_h'])} corp")
    dim_v(ax, 0, EL["h"], -30, ref=-21, dx=-1.2 * k, k=k, fs=5.0, rot=True, text=f"{fmt(EL['h'])} comoda")
    # biroul: înălțimea din fotografie
    dim_v(ax, 0, DESK["h"], DX0 + 52, ref=DX0 + 46, k=k, fs=5.0, rot=True, text=f"~{fmt(DESK['h'])}")
    # cote verticale, în dreapta: fereastra și tavanul
    xd = X_CUT + 8
    for p, q, t in ((0, SITE["win_sill"], f"{fmt(SITE['win_sill'])} parapet (plan)"),
                    (SITE["win_sill"], SITE["win_head"], f"~{fmt(SITE['win_head'] - SITE['win_sill'])}"),
                    (SITE["win_head"], SITE["H"], f"~{fmt(SITE['H'] - SITE['win_head'])}")):
        dim_v(ax, p, q, xd, ref=X_CUT, k=k, fs=4.8, rot=(q - p) > 25, text=t)
    dim_v(ax, 0, SITE["H"], X_CUT + 17, ref=xd, k=k, fs=5.0, rot=True, text=f"{fmt(SITE['H'])} tavan (dat)")


# ------------------------------------------------------------------ plan (vedere de sus), 1:15
PLAN_Z = (-20.0, 92.0)


def plan_view(ax):
    k = K15
    zmax = 90.0
    rect(ax, 0, 0, X_CUT, zmax, C["floor"], z=0)
    hatch(ax, -15, -18, WIN, 0, z=1)
    hatch(ax, -15, 0, 0, zmax, z=1)
    # golul ferestrei în perete: tocul și geamul
    rect(ax, WIN, -18, X_CUT, 0, "white", z=1)
    for zz in (-12.0, -10.5):
        ax.plot([WIN, X_CUT], [zz, zz], color="#5a6a7a", lw=0.5, zorder=2)
    ax.plot([WIN, WIN], [-18, 0], color="k", lw=0.8, zorder=3)
    ax.text((WIN + X_CUT) / 2, -4.5, "Fe-06", fontsize=4.6, color="#3a4a5a", ha="center", va="center", zorder=3)
    ax.plot([0, WIN], [0, 0], color="k", lw=0.9, zorder=3)
    ax.plot([0, 0], [0, zmax], color="k", lw=0.9, zorder=3)
    break_line(ax, X_CUT, -18, zmax)
    # plinta, de-a lungul pereților
    rect(ax, 0, 0, X_CUT, SITE["base_t"], C["base"], "#9a9a9a", 0.3, z=2)
    rect(ax, 0, 0, SITE["base_t"], zmax, C["base"], "#9a9a9a", 0.3, z=2)
    # biroul
    rect(ax, DX0, DESK["z0"], DX1, DESK["z0"] + DESK["d"], C["desk"], C["desk_e"], 0.5, z=4)
    ax.text((DX0 + DX1) / 2, 35, f"birou {fmt(DESK['w'])} × {fmt(DESK['d'])} (existent)", fontsize=5.2,
            color="#d8d8d8", ha="center", va="center", zorder=5)
    # comoda și sertarul scos
    rect(ax, XB, L.z0, XE, L.z1, C["oak"], C["oak_e"], 0.6, z=6)
    fr = EL["frame"]
    rect(ax, XB + fr, L.z1, XE - fr, L.z1 + PULL, "none", C["pull"], 0.6, z=7, ls=(0, (4, 2)))
    ax.text((XB + XE) / 2, L.z1 + PULL / 2, f"sertar scos (~{fmt(PULL)} cm, push-to-open)", fontsize=4.8,
            color=C["pull"], ha="center", va="center", zorder=7)
    r = EL["leg_rod"] / 2
    for (x, zz) in L.legs:
        ax.add_patch(mp.Circle((x, zz), r, fc="none", ec=C["steel"], lw=0.35, ls=(0, (1.5, 1)), zorder=8))
    ax.text((XB + XE) / 2, (L.z0 + L.z1) / 2, "comoda Element (picioarele, punctat)", fontsize=5.0,
            color="#4a3216", ha="center", va="center", zorder=8, weight="bold")
    # cote
    dim_v(ax, L.z0, L.z1, -24, ref=XB, dx=-1.2 * k, k=k, fs=5.0)
    dim_v(ax, L.z1, L.z1 + PULL, -24, ref=XB + fr, dx=-1.2 * k, k=k, fs=5.0, text=f"~{fmt(PULL)}")
    dim_v(ax, 0, DESK["d"], X_CUT + 8, ref=DX1, k=k, fs=5.0)
    ax.text(XB + 1.0, L.z0 + 1.0, "lipită de perete", fontsize=4.2, color=C["note"], ha="left",
            va="top", zorder=9)


# ------------------------------------------------------------------ secțiune laterală, 1:15
SEC_Z = (-12.0, 90.0)
SEC_Y = (-8.0, 136.0)


def side_section(ax):
    """Secțiune prin mijlocul comodei, privind spre colț: peretele cu biroul în stânga, camera în dreapta."""
    k = K15
    y0, y1 = SEC_Y
    hatch(ax, -12, y0, 0, y1, z=1)
    rect(ax, 0, y0, SEC_Z[1], 0, "#f6efe3", z=1)
    ax.plot([0, SEC_Z[1]], [0, 0], color="k", lw=0.9, zorder=3)
    ax.plot([0, 0], [0, y1], color="k", lw=0.9, zorder=3)
    rect(ax, 0, 0, SITE["base_t"], SITE["base_h"], C["base"], "#9a9a9a", 0.35, z=3)
    # dincolo de secțiune: biroul (punctat), cu blatul jos și sus
    gz0, gz1 = DESK["z0"], DESK["z0"] + DESK["d"]
    for yy, ls in ((DESK["h"], "-"), (DESK["h_max"], (0, (3, 1.5)))):
        rect(ax, gz0, yy - DESK["top_t"], gz1, yy, "none", "#7a7a7a", 0.5, z=2, ls=ls)
    rect(ax, gz0 + 31.75, 2.5, gz0 + 38.25, DESK["h"] - DESK["top_t"], "#d9d9d9", "#8a8a8a", 0.35, z=2)
    rect(ax, gz0, 0, gz1, 2.5, "#d9d9d9", "#8a8a8a", 0.35, z=2)
    ax.text(gz1 - 1, DESK["h"] + 2.0, "biroul, dincolo", fontsize=4.4, color="#555555", ha="right",
            va="bottom", zorder=3)
    ax.text(gz1 - 1, DESK["h_max"] + 1.5, "blatul, sus", fontsize=4.4, color="#555555", ha="right",
            va="bottom", zorder=3)
    # comoda, în secțiune: blat, fund, spate și cele 3 sertare
    z0, z1, fr = L.z0, L.z1, EL["frame"]
    yb, yt = EL["leg_h"], EL["h"]
    rect(ax, z0, yb, z1, yt, "#f3e7d3", C["oak_e"], 0.6, z=4)
    rect(ax, z0, yt - fr, z1, yt, C["oak"], C["oak_e"], 0.5, z=5, hatch="....")
    rect(ax, z0, yb, z1, yb + fr, C["oak"], C["oak_e"], 0.5, z=5, hatch="....")
    rect(ax, z0, yb + fr, z0 + max(BACK_T, 0.6), yt - fr, C["oak"], C["oak_e"], 0.4, z=5)
    for (a, b) in L.drawers:
        rect(ax, z1 - fr, a, z1, b, C["oak"], C["oak_e"], 0.5, z=6, hatch="....")
        rect(ax, z0 + 2.5, a + 1.5, z1 - fr, b - 3.0, "none", C["oak_e"], 0.35, z=6)
    # sertarul de sus, scos (punctat)
    a, b = L.drawers[-1]
    rect(ax, z1 - fr + PULL, a, z1 + PULL, b, "none", C["pull"], 0.6, z=7, ls=(0, (4, 2)))
    rect(ax, z0 + 2.5 + PULL, a + 1.5, z1 - fr + PULL, b - 3.0, "none", C["pull"], 0.4, z=7, ls=(0, (4, 2)))
    # picioarele (perechea din spate și cea din față)
    r = EL["leg_rod"] / 2
    for zc in (z0 + EL["leg_in_z"], z1 - EL["leg_in_z"]):
        rect(ax, zc - r, 0, zc + r, yb, C["steel"], z=6)
    # prinderea anti-răsturnare: banda AA în comodă, sub blat, cu capătul îndoit pe spate
    zb_in = z0 + max(BACK_T, 0.6) + 0.15
    ax.plot([zb_in, zb_in, 10.0], [ANCHOR_Y - 1.2, yt - fr - 0.15, yt - fr - 0.15], color=C["steel"], lw=1.0,
            zorder=8)
    ax.plot([-HOLE_DEPTH + 0.5, zb_in + 0.3], [ANCHOR_Y, ANCHOR_Y], color="#333333", lw=0.8, zorder=8)
    callout(ax, 1.5, yt - fr - 1.0, 5.0, "A", -6.5, yt + 6.5)
    callout(ax, 4.0, 7.0, 7.5, "B", -6.5, 19.0)
    # cote
    dim_h(ax, z0, z1, yt + 6.0, ref=yt, k=k, fs=5.0)
    dim_h(ax, gz0, gz1, DESK["h_max"] + 5.0, ref=DESK["h_max"], k=k, fs=5.0)
    xr = z1 + 3.5
    dim_v(ax, 0, yb, xr, ref=z1, k=k, fs=4.8)
    dim_v(ax, yb, yt, xr, ref=z1, k=k, fs=4.8, rot=True)
    dim_v(ax, 0, DESK["h"], gz1 + 5.0, ref=gz1, k=k, fs=4.8, rot=True, text=f"~{fmt(DESK['h'])}")
    dim_v(ax, DESK["h"], DESK["h_max"], gz1 + 5.0, ref=gz1, k=k, fs=4.8, rot=True,
          text=f"până la {fmt(DESK['h_max'])}")


# ------------------------------------------------------------------ planul camerei, 1:50
ROOM_X = (-40.0, 408.0)
ROOM_Z = (-55.0, 350.0)
DOOR = (SITE["door_x0"], SITE["door_x0"] + SITE["door_w"])
LEAF = 82.0   # foaia ușii de 90 (golul de lumină ~82 cm)  # est.


def room_plan(ax):
    k = K50
    W, D = SITE["wall_len"], SITE["room_w"]
    ext, inn = 38.5, 15.0
    rect(ax, 0, 0, W, D, C["floor"], z=0)
    g = "#b5b5b5"
    rect(ax, -inn, -ext, W + ext, 0, g, z=1)              # peretele exterior cu biroul (est)
    rect(ax, W, -ext, W + ext, D + inn, g, z=1)           # peretele exterior spre fațadă
    rect(ax, -inn, 0, 0, D + inn, g, z=1)                 # peretele spre Dormitor 1
    rect(ax, -inn, D, W + ext, D + inn, g, z=1)           # peretele spre hol, cu ușa
    # fereastra de colț: Fe-06 pe peretele cu biroul și Fe-07 pe fațadă
    rect(ax, WIN, -ext, W + ext, 0, "white", z=2)
    rect(ax, W, -ext, W + ext, 154.7, "white", z=2)
    for o in (-22.0, -18.0):
        ax.plot([WIN, W - o], [o, o], color="#5a6a7a", lw=0.5, zorder=3)
        ax.plot([W - o, W - o], [o, 154.7], color="#5a6a7a", lw=0.5, zorder=3)
    # ușa UI-02, cu balamaua spre peretele din stânga și deschiderea în cameră
    rect(ax, DOOR[0], D, DOOR[1], D + inn, C["floor"], z=2)
    hx, hz = DOOR[0], D
    ax.plot([hx, hx], [hz, hz - LEAF], color="k", lw=0.9, zorder=4)
    ang = np.linspace(-np.pi / 2, 0, 40)
    ax.plot(hx + LEAF * np.cos(ang + np.pi / 2), hz - LEAF * np.sin(ang + np.pi / 2), color="#555555", lw=0.4,
            zorder=4)
    ax.text(hx + 48, hz - 22, "ușa UI-02", fontsize=4.6, color=C["note"], ha="left", va="center", zorder=5)
    # mobilierul
    rect(ax, DX0, DESK["z0"], DX1, DESK["z0"] + DESK["d"], C["desk"], z=4)
    rect(ax, XB, L.z0, XE, L.z1, C["oak"], C["oak_e"], 0.5, z=5)
    rect(ax, XB + EL["frame"], L.z1, XE - EL["frame"], L.z1 + PULL, "none", C["pull"], 0.5, z=5,
         ls=(0, (3, 1.5)))
    ax.text((XB + XE) / 2, 23, "comoda", fontsize=4.6, color="#4a3216", ha="center", va="center", zorder=6)
    ax.text((DX0 + DX1) / 2, 35, "birou", fontsize=4.6, color="#d8d8d8", ha="center", va="center", zorder=6)
    ax.text(W / 2, 205, "Dormitor 2 (E 03)\nrestul camerei rămâne\ncum e", fontsize=4.6, color=C["note"],
            ha="center", va="center", zorder=6)
    ax.text(W / 2, -ext / 2, "peretele cu biroul (exterior)", fontsize=4.2, color="#333333", ha="center",
            va="center", zorder=6)
    # cote
    dim_h(ax, 0, W, -48, ref=-ext, k=k, fs=4.8, text=f"{fmt(round(W))} (din plan)")
    dim_v(ax, 0, D, -30, ref=-inn, dx=-1.0 * k, k=k, fs=4.8, rot=True, text=f"{fmt(D)} (din plan)")


# ------------------------------------------------------------------ detaliul A (anti-răsturnare), 1:5
DA_Z = (-7.0, 17.0)
DA_Y = (80.5, 94.0)


def detail_anchor(ax):
    """Secțiune prin prindere: peretele în stânga, spatele comodei lipit de el, banda AA în interior."""
    k = K5
    y0, y1 = DA_Y
    yt = EL["h"]
    yu = yt - TOP_T                                   # fața de jos a blatului
    hatch(ax, DA_Z[0], y0, 0, y1, z=1)
    ax.plot([0, 0], [y0, y1], color="k", lw=0.9, zorder=3)
    z0 = L.z0
    zb = z0 + BACK_T
    rect(ax, z0, yu, DA_Z[1], yt, C["oak"], C["oak_e"], 0.5, z=4, hatch="....")        # blatul comodei
    rect(ax, z0, y0, zb, yu, C["oak_e"], C["oak_e"], 0.3, z=4)                          # spatele, subțire
    t = 0.15                                                                            # banda AA
    rect(ax, zb, yu - t, 9.5, yu, C["steel"], z=6)
    rect(ax, zb, ANCHOR_Y - 1.4, zb + t, yu, C["steel"], z=6)
    # șurubul din cutie, în sus, prin bandă, în blat; cu șaibă
    rect(ax, 7.6, yu - t - 0.12, 8.4, yu - t, "#777777", z=7)
    ax.plot([8.0, 8.0], [yu - t - 0.35, yu + 1.2], color="#333333", lw=1.2, zorder=7)
    # șurubul diblului, prin șaibă, bandă și spate, în perete
    rect(ax, -3.0, ANCHOR_Y - 0.3, 0, ANCHOR_Y + 0.3, C["anchor"], "#666666", 0.4, z=5)    # diblul 6 × 30
    rect(ax, -HOLE_DEPTH, ANCHOR_Y - 0.3, -3.0, ANCHOR_Y + 0.3, "white", "#999999", 0.3, z=5, ls=(0, (2, 1)))
    rect(ax, zb + t, ANCHOR_Y - 0.45, zb + t + 0.1, ANCHOR_Y + 0.45, "#777777", z=7)        # șaiba
    ax.plot([zb + t + 0.1 - SCREW_L, zb + t + 0.25], [ANCHOR_Y, ANCHOR_Y], color="#333333", lw=1.2, zorder=8)
    label(ax, 6.0, yu - t, 8.5, 83.4, "banda AA, în comodă: prinsă sub blat\ncu șurubul și o șaibă din cutie",
          fs=4.5, ha="left")
    label(ax, -1.5, ANCHOR_Y, -3.5, 81.7, f"diblu Ø6 × 30 cu șurub 4,5 × 40\n(separat), gaura {fmt(HOLE_DEPTH * 10)} mm",
          fs=4.5, ha="center")
    label(ax, zb, 85.0, 4.5, 85.6, "spatele, găurit cu burghiul BB", fs=4.5, ha="left")
    dim_v(ax, ANCHOR_Y, yu, -5.6, ref=0, dx=-0.3, k=k, fs=4.6, text=fmt(ANCHOR_DROP))
    dim_v(ax, yu, yt, 15.6, ref=DA_Z[1] - 1.5, dx=0.3, k=k, fs=4.6, text=f"~{fmt(TOP_T)}")


# ------------------------------------------------------------------ detaliul B (plinta și picioarele), 1:5
DB_Z = (-7.0, 15.0)
DB_Y = (-3.0, 18.0)


def detail_base(ax):
    k = K5
    y0, y1 = DB_Y
    hatch(ax, DB_Z[0], 0, 0, y1, z=1)
    hatch(ax, DB_Z[0], y0, DB_Z[1], 0, z=1)
    ax.plot([0, 0], [0, y1], color="k", lw=0.9, zorder=3)
    ax.plot([0, DB_Z[1]], [0, 0], color="k", lw=0.9, zorder=3)
    rect(ax, 0, 0, SITE["base_t"], SITE["base_h"], C["base"], "#777777", 0.5, z=3)
    z0, fr, yb = L.z0, EL["frame"], EL["leg_h"]
    rect(ax, z0, yb, DB_Z[1], yb + fr, C["oak"], C["oak_e"], 0.5, z=4, hatch="....")    # fundul comodei
    rect(ax, z0, yb + fr, z0 + 0.8, y1, C["oak"], C["oak_e"], 0.4, z=4)                 # spatele
    r = EL["leg_rod"] / 2
    zc = z0 + EL["leg_in_z"]
    rect(ax, zc - r, 0, zc + r, yb, C["steel"], z=5)
    dim_v(ax, 0, SITE["base_h"], 3.2, ref=SITE["base_t"], dx=0.3, k=k, fs=4.6, text=f"~{fmt(SITE['base_h'])}")
    dim_v(ax, 0, yb, 10.5, ref=zc + r, dx=0.3, k=k, fs=4.6)
    dim_h(ax, 0, zc, y1 - 1.0, ref=yb + fr, k=k, fs=4.6, text=f"~{fmt(zc)}")
    label(ax, zc, 6.0, 12.0, 4.0, "picior dublu, Ø1,8", fs=4.4, ha="left")
    label(ax, 0.75, 4.0, -3.5, -1.6, "plinta rămâne întreagă", fs=4.4, ha="center")


# ------------------------------------------------------------------ notele
def notes():
    free = DX0
    return [
        ("MATERIALE ȘI FERONERIE", [
            f"1. Comodă BoConcept Element cu 3 sertare (379AB00), {fmt(EL['w'])} × {fmt(EL['d'])} × {fmt(EL['h'])} cm, "
            "59 kg; sarcină max. 20 kg (site; instrucțiunile: 40 kg):",
            "   furnir de stejar lăcuit, fronturi cu riflaj vertical, sertare push-to-open (fără mânere).",
            "   A: furnir de stejar natur. B: furnir de stejar închis. Picioare duble din oțel negru, de 13 cm.",
            "2. Prinderea anti-răsturnare din cutie: banda AA, cu un șurub și 2 șaibe, și burghiul BB (detaliul A).",
            f"3. Pentru perete, separat: diblu Fischer DuoPower Ø6 × 30 mm cu șurubul lui de 4,5 × 40 mm; gaura "
            f"Ø6 × {fmt(HOLE_DEPTH * 10)} mm.",
        ]),
        ("DE CE AȘA", [
            "• O singură piesă joasă, cu 3 sertare mari, fără mânere: stejar și negru, ca biroul și tâmplăria.",
            "• Riflajul vertical al fronturilor se potrivește cu panoul riflaj de stejar din hol.",
            f"• {fmt(EL['w'])} cm în ~{fmt(free)} cm liberi: {fmt(GAP_DESK)} cm până la birou (blatul urcă și "
            f"coboară liber, trec cablurile), ~{fmt(XB)} cm până în colț.",
            f"• Sus, la {fmt(EL['h'])} cm: deasupra blatului când stai jos (~{fmt(DESK['h'])}), sub el când lucrezi "
            f"în picioare (până la {fmt(DESK['h_max'])}).",
            f"• Corpul începe la {fmt(EL['leg_h'])} cm, peste plinta de ~{fmt(SITE['base_h'])} cm: comoda stă lipită "
            "de perete, iar plinta rămâne întreagă (detaliul B).",
            f"• Sertarele ies ~{fmt(PULL)} cm spre cameră, nu spre birou; ușa camerei e pe peretele opus.",
            "• Producătorul cere prinderea de perete: o comodă cu sertare se poate răsturna când sunt scoase.",
        ]),
        ("COTE", [
            f"Date: tavan {fmt(SITE['H'])} (de la tine); birou {fmt(DESK['w'])} × {fmt(DESK['d'])}, blat "
            f"{fmt(DESK['h_min'])}…{fmt(DESK['h_max'])} (Secretlab); comodă {fmt(EL['w'])} × {fmt(EL['d'])} × "
            f"{fmt(EL['h'])} (BoConcept).",
            f"Din planul etajului, scalat pe cota de 327 (~1:52,2, nu 1:50): camera {fmt(SITE['room_w'])} × "
            f"{fmt(round(SITE['wall_len']))};",
            f"fereastra Fe-06 începe la {fmt(WIN)} cm de colț; parapetul are {fmt(SITE['win_sill'])} cm.",
            f"Din fotografie (~): biroul de la ~{fmt(DX0)} la ~{fmt(DX1)} cm de colț, cu blatul la ~{fmt(DESK['h'])} "
            f"cm; plinta ~{fmt(SITE['base_h'])} cm.",
            f"Comoda se așază față de birou: {fmt(GAP_DESK)} cm între comodă și blat.",
        ]),
        ("COTE DE MĂSURAT", [
            f"a) peretele liber dintre colț și birou, la nivelul plintei (~{fmt(DX0)}); comoda cere cel puțin ~120 cm;",
            "b) dacă pe perete, de la colț până la birou și până la 91 cm înălțime, e o priză, un întrerupător",
            "    sau un termostat (colțul nu se vede în fotografie);",
            f"c) din ce e peretele și dacă trec cabluri la ~{fmt(round(ANCHOR_Y))} cm înălțime (gaura pentru banda AA);",
            "d) plinta: înălțimea și grosimea.",
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
    fig.text(8 / PAGE[0], 1 - 8 / PAGE[1], "Comodă lângă birou – Dormitor 2", fontsize=13, weight="bold",
             ha="left", va="top")
    fig.text(8 / PAGE[0], 1 - 15 / PAGE[1],
             f"BoConcept Element, 3 sertare, {fmt(EL['w'])} × {fmt(EL['d'])} × {fmt(EL['h'])} cm, în stânga biroului, "
             f"la {fmt(GAP_DESK)} cm de el"
             "      |  cote în cm  ·  scara 1:15 (A3), detalii 1:5, planul camerei 1:50  ·  cotele cu „~” sunt din "
             "fotografie, de verificat",
             fontsize=7, color=C["note"], ha="left", va="top")
    ax1 = make_axes(fig, 4, 81, (-38.0, 334.0), (-30.0, 256.0), "VEDERE FRONTALĂ (1:15)", MM15)
    wall_elevation(ax1)
    ax2 = make_axes(fig, 4, 3, (-38.0, 334.0), PLAN_Z, "PLAN – VEDERE DE SUS (1:15)", MM15, invert=True)
    plan_view(ax2)
    ax3 = make_axes(fig, 256, 175, SEC_Z, SEC_Y, "SECȚIUNE PRIN COMODĂ (1:15)", MM15)
    side_section(ax3)
    ax4 = make_axes(fig, 328, 190, ROOM_X, ROOM_Z, "PLANUL CAMEREI (1:50)", MM50, invert=True)
    room_plan(ax4)
    ax5 = make_axes(fig, 256, 132, DA_Z, DA_Y, "DETALIU A – anti-răsturnare (1:5)", MM5)
    detail_anchor(ax5)
    ax6 = make_axes(fig, 318, 124, DB_Z, DB_Y, "DETALIU B – plinta și picioarele (1:5)", MM5)
    detail_base(ax6)
    y = 118.0
    for title, lines in notes():
        y = text_block(fig, 256.0, y, title, lines)
    fig.savefig(out_base + ".pdf")
    fig.savefig(out_base + ".png", dpi=220)
    plt.close(fig)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "plan_tehnic_comoda_birou")
    main(out)
    print("salvat", out)
