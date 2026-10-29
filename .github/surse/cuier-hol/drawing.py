"""Technical drawing (A3, 1:15) for the hall coat-rack proposal (wall left of the window)."""
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mp
import matplotlib.pyplot as plt
import numpy as np

from design import D, N_SLATS, SITE, X0, X1, ZF, ZS, entry_door, hooks, slat_x

HERE = os.path.dirname(os.path.abspath(__file__))
SCALE = 15.0
PAGE = (420.0, 297.0)
MM = 10.0 / SCALE  # paper mm per real cm

C = dict(wall="#ece9e2", hatch="#8f8f8f", slat="#bf9a6c", slat_e="#7b5b37", felt="#2b2b2b",
         hook="#151515", frame="#3b3f45", glass="#d6e5ee", sill="#c9c9c9", base="#ffffff",
         coat="#5d8fb3", dim="#1a1a1a", note="#555555", door="#9a9a9a", floor="#efe3cf")
FS = 6.2


def fmt(v):
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


def make_axes(fig, x_mm, y_mm, xr, yr, title, mm_per_cm=MM):
    w = (xr[1] - xr[0]) * mm_per_cm
    h = (yr[1] - yr[0]) * mm_per_cm
    ax = fig.add_axes([x_mm / PAGE[0], y_mm / PAGE[1], w / PAGE[0], h / PAGE[1]])
    ax.set_xlim(*xr)
    ax.set_ylim(*yr)
    ax.set_aspect("equal")
    ax.axis("off")
    if title:
        fig.text(x_mm / PAGE[0], (y_mm + h + 3) / PAGE[1], title, fontsize=8.5, weight="bold", ha="left",
                 va="bottom")
    return ax


def rect(ax, x0, y0, x1, y1, fc, ec="none", lw=0.4, z=1, **kw):
    ax.add_patch(mp.Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=fc, edgecolor=ec, lw=lw, zorder=z, **kw))


def hatch(ax, x0, y0, x1, y1, z=1):
    ax.add_patch(mp.Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#f4f4f4", edgecolor=C["hatch"],
                              hatch="////", lw=0.5, zorder=z))


def tick(ax, x, y, s=1.2):
    ax.plot([x - s / 2, x + s / 2], [y - s / 2, y + s / 2], color=C["dim"], lw=0.6, zorder=20)


# k scales the fixed dimension-line geometry (ticks, overshoot, extension gaps) for views drawn at another scale
def dim_h(ax, x0, x1, y, ref=None, text=None, dy=1.0, fs=FS, txt_dx=0.0, k=1.0):
    ax.plot([x0 - 1.2 * k, x1 + 1.2 * k], [y, y], color=C["dim"], lw=0.35, zorder=20)
    for x in (x0, x1):
        tick(ax, x, y, 1.2 * k)
        if ref is not None:
            s = 1 if y > ref else -1
            ax.plot([x, x], [ref + s * 0.8 * k, y + s * 1.2 * k], color=C["dim"], lw=0.25, zorder=20)
    up = (dy >= 0) != ax.yaxis_inverted()
    ax.text((x0 + x1) / 2 + txt_dx, y + dy, text or fmt(abs(x1 - x0)), ha="center",
            va="bottom" if up else "top", fontsize=fs, zorder=21,
            bbox=dict(fc="white", ec="none", pad=0.15, alpha=0.85))


def dim_v(ax, y0, y1, x, ref=None, text=None, dx=1.0, fs=FS, txt_dy=0.0, rot=False, k=1.0):
    ax.plot([x, x], [y0 - 1.2 * k, y1 + 1.2 * k], color=C["dim"], lw=0.35, zorder=20)
    for y in (y0, y1):
        tick(ax, x, y, 1.2 * k)
        if ref is not None:
            s = 1 if x > ref else -1
            ax.plot([ref + s * 0.8 * k, x + s * 1.2 * k], [y, y], color=C["dim"], lw=0.25, zorder=20)
    ax.text(x + dx, (y0 + y1) / 2 + txt_dy, text or fmt(abs(y1 - y0)), ha="left" if dx >= 0 else "right",
            va="center", rotation=90 if rot else 0, fontsize=fs, zorder=21,
            bbox=dict(fc="white", ec="none", pad=0.15, alpha=0.85))


def label(ax, x, y, tx, ty, text, fs=FS, ha="left"):
    ax.annotate(text, xy=(x, y), xytext=(tx, ty), fontsize=fs, color=C["note"], ha=ha, va="center",
                arrowprops=dict(arrowstyle="-", lw=0.35, color=C["note"], shrinkA=0, shrinkB=0), zorder=22,
                bbox=dict(fc="white", ec="none", pad=0.2, alpha=0.9))


# ------------------------------------------------------------------ views
WX0, WX1 = SITE["window_x"]
XL = SITE["left_wall_x"]
TOP = D["panel_top"]
BOT = D["panel_bottom"]
PH = D["panel_h"]
BB_H, BB_T = SITE["baseboard_h"], SITE["baseboard_t"]
DOOR = entry_door()
TRANSOM = (99.0, 112.0)


def coat_outline(z0):
    d = D["coat_depth"]
    return np.array([[z0, 186], [z0 + d * 0.75, 182], [z0 + d, 150], [z0 + d * 0.8, 85], [z0, 80]])


def window_elev(ax):
    rect(ax, WX0, SITE["sill_top"], WX1, SITE["window_top"], "#5b6066", z=2)
    fr = 5.5
    rect(ax, WX0 + fr, SITE["sill_top"] + 7, WX1 - fr, TRANSOM[0], C["glass"], z=3)
    rect(ax, WX0 + fr, TRANSOM[1], WX1 - fr, SITE["window_top"] - 8, C["glass"], z=3)
    rect(ax, WX0 - 1.5, SITE["sill_top"] - 2.5, WX1 + 1.5, SITE["sill_top"], C["sill"], "#8a8a8a", 0.4, z=4)
    ax.text((WX0 + WX1) / 2, 175, "fereastră\n(existent)", ha="center", va="center", fontsize=6, color=C["note"], zorder=5)


def front_elevation(ax):
    H = SITE["ceiling"]
    xr = -52.0
    rect(ax, XL, 0, xr, H, C["wall"], z=0)
    rect(ax, XL - 22, -6, xr, 0, "#f6efe3", z=0)
    hatch(ax, XL - 22, -6, XL, H + 4, z=2)
    ax.plot([XL, XL], [0, H], color="k", lw=0.9, zorder=5)
    ax.plot([XL - 22, xr], [0, 0], color="k", lw=1.1, zorder=5)
    ax.plot([XL, xr], [H, H], color="k", lw=0.8, zorder=5)
    ax.text(XL - 11, 150, "perete stânga\n(cu ușa de intrare)", rotation=90, fontsize=5.4, color=C["note"],
            ha="center", va="center", zorder=6, bbox=dict(fc="#f4f4f4", ec="none", pad=0.6))
    window_elev(ax)
    # the baseboard stays uncut along the whole wall; the panel stands on it
    rect(ax, XL, 0, xr, BB_H, C["base"], "#9a9a9a", 0.35, z=3)

    env = np.array([[X0 - 4, 186], [X1 + 4, 186], [X1 + 9, 120], [X1 + 6, 80], [X0 - 4, 80]])
    ax.add_patch(mp.Polygon(env, closed=True, fc=C["coat"], alpha=0.10, ec="none", zorder=8))
    ax.add_patch(mp.Polygon(env, closed=True, fc="none", ec="#2f6f9f", ls=(0, (4, 3)), lw=0.7, zorder=14))
    ax.text(0.5 * (X0 + X1), 100, "contur haine\n(orientativ)", ha="center", va="center", fontsize=5.4,
            color="#2f6f9f", zorder=15, bbox=dict(fc="white", ec="none", pad=0.3, alpha=0.85))

    rect(ax, X0, BOT, X1, TOP, C["felt"], z=5)
    for i in range(N_SLATS):
        a, b = slat_x(i)
        rect(ax, a, BOT, b, TOP, C["slat"], C["slat_e"], 0.25, z=7)
    for (x, y) in hooks():
        ax.add_patch(mp.Circle((x, y), D["hook_r"] + 0.7, fc="#3a3a3a", ec="none", zorder=12))
        ax.add_patch(mp.Circle((x, y), D["hook_r"], fc=C["hook"], ec="#000", lw=0.3, zorder=13))

    ax.plot([X0, xr], [SITE["window_top"]] * 2, color=C["door"], lw=0.5, ls=(0, (5, 2)), zorder=6)
    ax.text(WX1 + 2, SITE["window_top"] + 2.5, "panou aliniat cu golul ferestrei", fontsize=5.2, color=C["note"],
            ha="left", va="bottom", zorder=6)

    # horizontal dimensions
    y = -13
    dim_h(ax, XL, X0, y, ref=0, dy=-1.2)
    dim_h(ax, X0, X1, y, ref=0, text=f"{fmt(D['panel_w'])} panou")
    dim_h(ax, X1, WX0, y, ref=0, dy=-1.2)
    dim_h(ax, XL, WX0, y - 10, ref=0, text=f"{fmt(WX0 - XL)}  perete liber (măsurat)")
    dim_h(ax, WX0, WX1, y, ref=SITE["sill_top"] - 2.5, text=f"{fmt(WX1 - WX0)} gol fereastră")
    up = [h for h in hooks() if h[1] == D["hooks_up_y"]]
    lo = [h for h in hooks() if h[1] == D["hooks_lo_y"]]
    xs = [X0] + [h[0] for h in up]
    for a, b in zip(xs[:-1], xs[1:]):
        dim_h(ax, a, b, D["hooks_up_y"] + 9, ref=D["hooks_up_y"] + 2.5)
    xs = [X0] + [h[0] for h in lo]
    for a, b in zip(xs[:-1], xs[1:]):
        dim_h(ax, a, b, D["hooks_lo_y"] - 9, ref=D["hooks_lo_y"] - 2.5, dy=-1.0)

    # vertical dimensions (left of the entrance-door wall)
    xd = XL - 40
    levels = [0, D["hooks_lo_y"], D["hooks_up_y"], TOP]
    for a, b in zip(levels[:-1], levels[1:]):
        dim_v(ax, a, b, xd, ref=X0, dx=-1.2)
    dim_v(ax, 0, BOT, xd - 10, ref=X0, dx=-1.0)
    dim_v(ax, BOT, TOP, xd - 10, ref=X0, dx=-1.0, text=f"{fmt(PH)} panou (de pe plintă)", rot=True)
    dim_v(ax, 0, TOP, xd - 20, ref=X0, dx=-1.0, text=f"{fmt(TOP)} sus panou = sus fereastră", rot=True)
    dim_v(ax, 0, SITE["ceiling"], xd - 30, ref=XL - 22, dx=-1.0, text=f"{fmt(SITE['ceiling'])} tavan (măsurat)",
          rot=True)
    dim_v(ax, SITE["window_top"], SITE["ceiling"], WX1 + 6, ref=WX1, dx=1.2)

    lx = XL - 106
    label(ax, X0 + 6, 222, lx, 222, "panou riflaj stejar\npe pâslă neagră\n(11 lamele, 44 cm)", fs=5.8)
    label(ax, up[0][0], up[0][1] + 1.5, lx, 192, "cârlige negre mat\n3 sus + 2 jos,\nfiecare pe o lamelă", fs=5.8)
    label(ax, X0 + 3, BB_H / 2, lx, 30, "plinta 8 × 1,6\nrămâne întreagă;\npanoul stă pe ea\n(detaliul A)", fs=5.8)
    label(ax, XL - 4, 60, lx, 75, "perete cu ușa\nde intrare (vezi plan)", fs=5.8)


def side_section(ax):
    H = SITE["ceiling"]
    hatch(ax, -12, -6, 0, H + 4, z=1)
    hatch(ax, -12, -6, 128, 0, z=1)
    ax.plot([0, 0], [0, H], color="k", lw=0.9, zorder=3)
    ax.plot([0, 128], [0, 0], color="k", lw=0.9, zorder=3)
    ax.plot([0, 128], [H, H], color="k", lw=0.6, zorder=3)
    z0, z1 = SITE["entry_open_z"]
    ax.add_patch(mp.Rectangle((z0, 0), z1 - z0, SITE["entry_head"], fc="none", ec=C["door"], ls=(0, (5, 2)),
                              lw=0.6, zorder=2))
    ax.text((z0 + z1) / 2 + 6, 150, "golul ușii de intrare\n(în peretele din stânga,\nîn spatele secțiunii)",
            fontsize=5.4, color=C["note"], ha="center", va="center", zorder=2)
    # entrance door open at 90 degrees, cut by the section plane
    lz = DOOR["open_face_z"]
    rect(ax, lz, 1.0, lz + DOOR["t"], SITE["entry_head"] - 3, "#b9b9b9", "#555555", 0.6, z=6)
    rect(ax, DOOR["handle_z"], DOOR["handle_y"] - 2, lz, DOOR["handle_y"] + 2, "none", "#222222", 0.6, z=7,
         ls=(0, (2, 1)))
    ax.text(lz + DOOR["t"] + 2, 185, "ușa de intrare\ndeschisă la 90°", fontsize=5.6, color="#333333", ha="left",
            va="center", zorder=7, bbox=dict(fc="white", ec="none", pad=0.3, alpha=0.9))
    label(ax, DOOR["handle_z"] + 1, DOOR["handle_y"] - 2, lz + 16, 92, "mâner (în afara\nsecțiunii)", fs=5.4)

    env = coat_outline(ZS)
    ax.add_patch(mp.Polygon(env, closed=True, fc=C["coat"], alpha=0.10, ec="none", zorder=4))
    ax.add_patch(mp.Polygon(env, closed=True, fc="none", ec="#2f6f9f", ls=(0, (4, 3)), lw=0.7, zorder=5))
    ax.text(ZS + 10, 112, "haine", fontsize=5.6, color="#2f6f9f", ha="center", zorder=5)
    rect(ax, 0, BOT, ZF, TOP, C["felt"], z=5)
    rect(ax, ZF, BOT, ZS, TOP, C["slat"], C["slat_e"], 0.3, z=6)
    rect(ax, 0, 0, BB_T, BB_H, C["base"], "#555555", 0.45, z=6)
    # callout for detail A (panel resting on the baseboard)
    ax.add_patch(mp.Circle((ZS / 2, BB_H), 6.0, fc="none", ec=C["dim"], lw=0.5, zorder=9))
    ax.plot([ZS / 2 + 4.3, 9.2], [BB_H + 4.2, 17.0], color=C["dim"], lw=0.4, zorder=9)
    ax.text(9.6, 17.6, "A", fontsize=7.5, weight="bold", ha="left", va="center", zorder=9)
    tilt = np.radians(D["hook_tilt_deg"])
    for y in (D["hooks_up_y"], D["hooks_lo_y"]):
        rect(ax, ZS, y - D["hook_r"] - 0.7, ZS + 0.5, y + D["hook_r"] + 0.7, "#3a3a3a", z=7)
        p0 = np.array([ZS + 0.5, y])
        d = np.array([np.cos(tilt), np.sin(tilt)])
        nrm = np.array([-d[1], d[0]]) * D["hook_r"]
        p1 = p0 + d * D["hook_len"]
        ax.add_patch(mp.Polygon([p0 - nrm, p1 - nrm, p1 + nrm, p0 + nrm], closed=True, fc=C["hook"], zorder=8))
    # dimensions
    yd = TOP + 10
    dim_h(ax, 0, ZS, yd, ref=TOP, fs=5.6, txt_dx=-3.2)
    dim_h(ax, ZS, ZS + 0.5 + D["hook_len"] * np.cos(tilt), D["hooks_up_y"] + 9, ref=D["hooks_up_y"] + 2, fs=5.6)
    dim_h(ax, 0, ZS + D["coat_depth"], 62, ref=80, fs=5.6, text=f"~{fmt(ZS + D['coat_depth'])}", dy=-1.0)
    dim_h(ax, 0, lz, 40, ref=1.0, fs=5.6, text=f"~{fmt(lz)} ușa deschisă", dy=-1.0)
    dim_h(ax, 0, z0, -12, ref=0, text=f"{fmt(z0)}", dy=-1.2)
    ax.text(z0 + 2, -15.5, f"← golul ușii începe la ~{round(z0)} cm de perete", fontsize=5.4, color=C["note"], ha="left",
            va="center")
    dim_v(ax, 0, BOT, -16, ref=0, dx=-1.0, fs=5.6)
    dim_v(ax, BOT, TOP, -16, ref=0, dx=-1.0, fs=5.6, rot=True)


def plan_view(ax):
    ax.invert_yaxis()
    zt = 128.0
    rect(ax, XL, 0, -50, zt, C["floor"], z=0)
    hatch(ax, XL - 37, -24, -50, 0, z=1)
    hatch(ax, XL - 37, 0, XL, zt, z=1)
    z0, z1 = SITE["entry_open_z"]
    rect(ax, XL - 37.2, z0, XL + 0.2, z1, "#ffffff", z=2)
    for zz in (z0, z1):
        ax.plot([XL - 37, XL], [zz, zz], color="k", lw=0.6, zorder=3)
    fx = XL - SITE["entry_reveal_d"]
    rect(ax, fx - 2.0, z0, fx + 0.0, z1, "#555555", z=3)
    hx, hz = DOOR["hinge"]
    rect(ax, hx - DOOR["t"], hz, hx, hz + DOOR["w"], "#9a9a9a", "#555555", 0.4, z=4)
    ax.text(XL - 6.5, (z0 + z1) / 2, "ușa de intrare (închisă)", rotation=90, fontsize=5.0, color=C["note"],
            ha="center", va="center", zorder=5)
    # open position + swing
    rect(ax, hx, hz, hx + DOOR["w"], hz + DOOR["t"], "#b9b9b9", "#555555", 0.5, z=6, alpha=0.85)
    th = np.radians(np.linspace(0, 90, 60))
    ax.plot(hx + DOOR["w"] * np.sin(th), hz + DOOR["w"] * np.cos(th), color=C["door"], lw=0.6, ls=(0, (4, 2)), zorder=5)
    rect(ax, DOOR["handle_x"] - 13, DOOR["handle_z"], DOOR["handle_x"], hz, "none", "#222222", 0.5, z=7,
         ls=(0, (2, 1)))
    label(ax, DOOR["handle_x"] - 6, DOOR["handle_z"], -100, 56, "mânerul ușii", fs=5.4)
    ax.text(hx + 40, hz + DOOR["t"] + 3.5, "ușa deschisă la 90° (maxim)", fontsize=5.4, color="#333333",
            ha="center", va="top", zorder=8)
    # window in the back wall
    rect(ax, WX0, -24, WX1, 0, "#ffffff", z=2)
    rect(ax, WX0, -12, WX1, -9, C["frame"], z=3)
    rect(ax, WX0 - 1.5, -9, WX1 + 1.5, SITE["sill_protrusion"], C["sill"], "#8a8a8a", 0.4, z=3)
    ax.text((WX0 + WX1) / 2, -17.5, "fereastră", fontsize=5.6, ha="center", va="center", color=C["note"], zorder=4)
    # coat zone, panel and hooks
    ax.add_patch(mp.Rectangle((X0 - 2, ZS), X1 - X0 + 10, D["coat_depth"], fc=C["coat"], alpha=0.10,
                              ec="#2f6f9f", ls=(0, (4, 3)), lw=0.6, zorder=4))
    ax.text(0.5 * (X0 + X1), ZS + D["coat_depth"] - 4, "haine (~25 cm)", fontsize=5.4, color="#2f6f9f",
            ha="center", va="center", zorder=5)
    rect(ax, X0, 0, X1, ZF, C["felt"], z=6)
    for i in range(N_SLATS):
        a, b = slat_x(i)
        rect(ax, a, ZF, b, ZS, C["slat"], C["slat_e"], 0.2, z=7)
    tilt = np.radians(D["hook_tilt_deg"])
    for x in sorted({h[0] for h in hooks()}):
        rect(ax, x - D["hook_r"], ZS, x + D["hook_r"], ZS + 0.5 + D["hook_len"] * np.cos(tilt), "#222222", z=8)
    # dimensions
    dim_h(ax, XL, X0, -30, ref=0, fs=5.6, dy=-1.0)
    dim_h(ax, X0, X1, -30, ref=0, fs=5.6, dy=-1.0, text=f"{fmt(D['panel_w'])}")
    dim_h(ax, X1, WX0, -30, ref=0, fs=5.6, dy=-1.0)
    dim_v(ax, 0, z0, XL + 2.4, dx=1.0, fs=5.6)
    dim_v(ax, 0, hz, -58, ref=hx + DOOR["w"], dx=1.0, fs=5.6, text=f"~{fmt(hz)}")


DET_MM = 10.0 / 3.0  # detail A is drawn at 1:3 (paper mm per real cm)


def detail_baseboard(ax):
    """Detail A (section, 1:3): the panel stands on the top edge of the existing, uncut baseboard."""
    k = MM / DET_MM
    yt = 11.6
    hatch(ax, -1.6, -0.5, 0, yt + 0.6, z=1)
    rect(ax, 0, -0.5, 5.5, 0, C["floor"], z=1)
    ax.plot([0, 0], [-0.5, yt + 0.6], color="k", lw=0.9, zorder=3)
    ax.plot([-1.6, 5.5], [0, 0], color="k", lw=0.9, zorder=3)
    rect(ax, 0, 0, BB_T, BB_H, "#e4e4e4", "#333333", 0.6, z=4)
    rect(ax, 0, BB_H, ZF, yt + 0.5, C["felt"], z=5)
    rect(ax, ZF, BB_H, ZS, yt + 0.5, C["slat"], C["slat_e"], 0.5, z=6)
    zz = np.array([0.0, 0.75, 1.0, 1.3, 1.55, ZS + 0.1])
    yy = np.array([yt, yt, yt + 0.3, yt - 0.3, yt, yt])
    ax.fill_between(zz, yy, yt + 0.7, color="white", zorder=7, lw=0)
    ax.plot(np.r_[-0.3, zz, ZS + 0.4], np.r_[yt, yy, yt], color="k", lw=0.5, zorder=8)

    dim_h(ax, 0, BB_T, -1.2, ref=0, dy=-0.25, fs=5.4, k=k)
    dim_h(ax, BB_T, ZS, -1.2, ref=0, dy=-0.25, fs=5.4, k=k, txt_dx=1.1)
    ax.plot([ZS, ZS], [BB_H - 0.8 * k, 0], color=C["dim"], lw=0.25, zorder=20)
    dim_v(ax, 0, BB_H, 3.4, ref=BB_T, dx=0.3, fs=5.4, k=k)

    tx = 7.5
    ax.text(tx, 12.4, "DETALIU A – panoul pe plintă (secțiune, 1:3)", fontsize=7.2, weight="bold", ha="left",
            va="top")
    label(ax, 1.5, 10.6, tx, 10.6, "panou riflaj 2,1 cm = pâslă 0,9 + lamelă 1,2", fs=5.6)
    label(ax, ZS - 0.15, BB_H + 0.1, tx, 8.3,
          "marginea de jos a panoului stă pe muchia de sus a plintei,\nla 8 cm de la pardoseală; panoul iese cu 0,5 cm"
          "\nîn fața plintei (0,4 cm la varianta B, panou de 2 cm)", fs=5.6)
    label(ax, 0.8, 3.5, tx, 4.4, "plintă existentă 8 × 1,6 cm: rămâne întreagă,\nnu se taie", fs=5.6)


NOTES = [
    ("MATERIALE ȘI FERONERIE", [
        "1. Panou acustic cu lamele (riflaj), stejar pe pâslă neagră, standard 240 × 60 cm:",
        f"   se taie la 11 lamele (~43–44 cm, după panou) și la {fmt(PH)} cm înălțime.",
        "2. 5 cârlige negre mat: 3 la 178 cm și 2 la 150 cm, fiecare în axul unei lamele,",
        "   cu șurub 4,5 × 60 mm prin lamelă, în diblu Ø6 în perete.",
        "3. Montaj pe cărămidă: adeziv de montaj (ex. Soudal Fix All High Tack) pe spatele",
        "   panoului + 6–8 șuruburi 4,5 × 40 mm prin pâslă (în rosturi), în dibluri Fischer",
        "   DuoPower Ø6 (merg și la cărămida cu goluri). Capetele șuruburilor se înnegresc.",
        "4. Plinta existentă (8 × 1,6 cm) rămâne întreagă: panoul stă pe muchia ei de sus,",
        "   la 8 cm de la pardoseală, și iese cu 0,5 cm în fața ei (vezi detaliul A).",
        f"Varianta B: panou negru / antracit de 40 cm (se taie doar pe lungime, la {fmt(PH)} cm).",
    ]),
    ("DE CE AȘA", [
        "• Panoul e centrat pe peretele de 55 cm (câte 5,5 cm liber pe fiecare parte),",
        "  pornește de pe plintă (8 cm) și se oprește la nivelul părții de sus a golului",
        "  ferestrei (231,5 cm). Plinta nu se taie și rămâne continuă pe tot peretele.",
        "• Fără bancă: dedesubt rămâne loc pentru încălțăminte.",
        "• Ușa de intrare se deschide la 90° spre acest perete și rămâne la ~34 cm de el",
        "  (mânerul la ~28 cm), deci hainele (~20–25 cm) încap în spatele ei.",
        "• Cârligele (150–178 cm) țin hainele deasupra glafului; o haină lată poate",
        "  acoperi câțiva cm din rama ferestrei.",
    ]),
    ("COTE", [
        "Măsurate: tavan 270 · perete colț – gol fereastră 55 · gol fereastră sus la 231,5",
        "(38,5 sub tavan) · plintă 8 × 1,6 · ușa de intrare se deschide la 90° · perete din cărămidă.",
        "Estimate din fotografie (nu schimbă proiectul): golul ușii de intrare la ~30 cm de",
        "perete, mânerul iese ~6,5 cm, glaful la ~39 cm.",
        "La montaj: verifică cu un detector să nu treacă cabluri sau țevi pe unde găurești.",
    ]),
]


def main(out_base):
    fig = plt.figure(figsize=(PAGE[0] / 25.4, PAGE[1] / 25.4))
    fig.text(12 / PAGE[0], 1 - 9 / PAGE[1], "Propunere cuier – peretele din stânga ferestrei (hol intrare)",
             fontsize=13, weight="bold", ha="left", va="top")
    fig.text(12 / PAGE[0], 1 - 16 / PAGE[1],
             f"Panou riflaj stejar {fmt(D['panel_w'])} × {fmt(PH)} cm, pe plintă (de la {fmt(BOT)} la {fmt(TOP)} cm)"
             "  ·  5 cârlige negre mat  ·  fără bancă"
             "      |  cote în cm  ·  scara 1:15 (A3)  ·  cotele principale sunt măsurate pe șantier",
             fontsize=7, color=C["note"], ha="left", va="top")
    ax1 = make_axes(fig, 8, 40, (XL - 108, -45.0), (-30.0, 290.0), "VEDERE FRONTALĂ")
    front_elevation(ax1)
    ax2 = make_axes(fig, 178, 40, (-22.0, 128.0), (-22.0, 290.0), "SECȚIUNE LATERALĂ (prin panou)")
    side_section(ax2)
    ax3 = make_axes(fig, 290, 152, (XL - 40, -48.0), (-36.0, 128.0), "PLAN (vedere de sus)")
    plan_view(ax3)
    ax4 = make_axes(fig, 290, 6.5, (-1.6, 34.0), (-2.2, 12.4), None, mm_per_cm=DET_MM)
    detail_baseboard(ax4)
    y = 145.0
    for title, lines in NOTES:
        fig.text(290 / PAGE[0], y / PAGE[1], title, fontsize=7.2, weight="bold", ha="left", va="top")
        y -= 4.4
        for ln in lines:
            fig.text(290 / PAGE[0], y / PAGE[1], ln, fontsize=5.7, ha="left", va="top", family="DejaVu Sans")
            y -= 3.05
        y -= 2.0
    fig.savefig(out_base + ".pdf")
    fig.savefig(out_base + ".png", dpi=220)
    plt.close(fig)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "plan_tehnic_cuier")
    main(out)
    print("saved", out)
