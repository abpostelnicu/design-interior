"""Planul tehnic A3: pagina, cotele, notele rupte singure pe rânduri și verificarea automată a textelor.

Un plan nou, `.github/surse/<proiect>/drawing.py`, are funcția `build()`, care întoarce figura, și o salvare:

    from unelte import plan
    from unelte.plan import C, K5, K15, MM5, MM15, dim_h, dim_v, label, make_axes, rect, text_block

    def build():
        fig = plan.pagina("Titlul proiectului", "ce conține, cu dimensiunile principale")
        ax = make_axes(fig, 5, 72, (-30, 450), (-26, 266), "VEDERE FRONTALĂ (1:15)", MM15)
        rect(ax, 0, 0, 419, 262, C["wall"])                 # desenul, în cm reali
        dim_h(ax, 0, 419, -12, ref=0, k=K15)
        y = 114.5
        for titlu, paragrafe in notes():                     # paragrafe întregi, nu rânduri rupte de mână
            y = text_block(fig, 327, y, titlu, paragrafe)
        return fig

    if __name__ == "__main__":
        plan.save(build(), os.path.join(HERE, "out", "plan_tehnic_<proiect>"))   # PDF A3 vectorial + PNG 220 dpi

Verificarea, după fiecare schimbare: `python .github/unelte/plan.py verifica .github/surse/<proiect>/drawing.py`
construiește pagina și caută textele care ies din pagină, se suprapun, intră peste un desen sau sunt tăiate de o
linie de indicație; iese cu codul 1 la probleme. Apoi te uiți pe PNG (unealta `view`), mărit pe detalii.

Unitățile: pe pagină, mm de hârtie, cu originea în colțul din stânga jos (make_axes, text_block, legend); în
desene, cm reali (MM15 = mm de hârtie pe cm, la 1:15). Cotele au virgulă zecimală (`fmt`).
Preluat din `drawing.py` și `verifica_plan.py` din `.github/surse/polite-viniluri/beton/` și din
`.github/surse/polite-viniluri/drawing.py`.
"""
import itertools
import os
import re
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mp  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.text import Annotation, Text  # noqa: E402

PAGE = (420.0, 297.0)                               # A3 culcat, mm
MM15, MM5, MM3 = 10.0 / 15.0, 10.0 / 5.0, 10.0 / 3.0  # mm de hârtie pe cm real, la 1:15, 1:5 și 1:3
K15, K5, K3 = 1.5, 0.5, 0.3                         # scalarea liniuțelor de cotă (k), după scară
MM50, K50 = 10.0 / 50.0, 5.0                        # planul camerei, la 1:50 (de exemplu din planul PDF)
FS = 5.6                                            # corpul de literă al cotelor (pt)
NOTE_FS, NOTE_STEP, NOTE_W = 4.7, 2.25, 88.0        # notele: corp (pt), distanța dintre rânduri și lățimea (mm)
NB = "\u00a0"                                       # spațiu de nedespărțit
TOL = 0.05                                          # mm: atingerile mai mici nu contează la verificare
A3_PT = (1190.55, 841.89)                           # A3 culcat, în puncte PDF

C = dict(wall="#ecebe7", hatch="#8f8f8f", oak="#c9a06a", oak_e="#7b5b37", tv="#202124", tv_e="#000000",
         cab="#5a5c5e", spk="#26272b", base="#ffffff", dim="#1a1a1a", note="#555555", floor="#efe3cf",
         dev="#f3efe6", steel="#3a3a3a", anchor="#b9b9b9",
         conc="#aaa69e", conc_e="#66625b",     # microcimentul gri (RGB 170, 166, 158)
         ply="#efe3c4", ply_e="#9c8150",       # placajul de mesteacăn
         beech="#f2cf86", glue="#a0522d")      # cepurile din fag și adezivul


# ------------------------------------------------------------------ pagina și desenele

def pagina(titlu, subtitlu="", nota="cote în cm  ·  scara 1:15 (A3), detalii 1:5  ·  cotele cu „~” sunt din "
           "fotografie, de verificat"):
    """Pagina A3 culcată, cu titlul, subtitlul și rândul despre cote, la 8 mm de marginile din stânga și de sus."""
    fig = plt.figure(figsize=(PAGE[0] / 25.4, PAGE[1] / 25.4))
    fig.text(8 / PAGE[0], 1 - 8 / PAGE[1], titlu, fontsize=13, weight="bold", ha="left", va="top")
    if subtitlu:
        fig.text(8 / PAGE[0], 1 - 15 / PAGE[1], subtitlu, fontsize=7, color=C["note"], ha="left", va="top")
    if nota:
        fig.text(8 / PAGE[0], 1 - 19.5 / PAGE[1], nota, fontsize=7, color=C["note"], ha="left", va="top")
    return fig


def make_axes(fig, x_mm, y_mm, xr, yr, title, mm_per_cm, invert=False):
    """Un desen la scară: colțul din stânga jos la (x_mm, y_mm) pe pagină, xr × yr în cm reali.

    invert=True întoarce axa verticală (vederea de sus: peretele sus, camera jos). Titlul stă la 2,5 mm deasupra.
    """
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
    """Hașura peretelui sau a pardoselii, în secțiune."""
    ax.add_patch(mp.Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#f4f4f4", edgecolor=C["hatch"],
                              hatch="////", lw=0.5, zorder=z))


def tick(ax, x, y, s):
    ax.plot([x - s / 2, x + s / 2], [y - s / 2, y + s / 2], color=C["dim"], lw=0.6, zorder=20)


def dim_h(ax, x0, x1, y, ref=None, text=None, dy=None, fs=FS, txt_dx=0.0, k=1.0):
    """Cotă orizontală la înălțimea y; ref = y-ul piesei, pentru liniile ajutătoare; k = K15, K5 sau K3."""
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
    """Cotă verticală la abscisa x; ref = x-ul piesei, pentru liniile ajutătoare."""
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
    """Text cu linie de indicație spre punctul (x, y); textul stă la (tx, ty), tot în cm ai desenului."""
    ax.annotate(text, xy=(x, y), xytext=(tx, ty), fontsize=fs, color=C["note"], ha=ha, va="center",
                arrowprops=dict(arrowstyle="-", lw=0.35, color=C["note"], shrinkA=0, shrinkB=0), zorder=22,
                bbox=dict(fc="white", ec="none", pad=0.2, alpha=0.9))


def callout(ax, x, y, r, name, tx, ty):
    """Trimiterea la un detaliu: cercul de rază r (cm) în jurul punctului (x, y) și litera detaliului la (tx, ty),
    lângă cerc, de exemplu „A” pentru „DETALIU A”. Preluat din `.github/surse/comoda-birou/drawing.py`."""
    ax.add_patch(mp.Circle((x, y), r, fc="none", ec=C["dim"], lw=0.5, zorder=24))
    ax.text(tx, ty, name, fontsize=7, weight="bold", ha="center", va="center", zorder=24,
            bbox=dict(fc="white", ec="none", pad=0.3))


def scara(n):
    """Pentru scara 1:n: (mm de hârtie pe cm real, k pentru cote); scara(15) = (MM15, K15), scara(50) = (MM50, K50)."""
    return 10.0 / n, n / 10.0


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


def legend(fig, x, y, items, title="LEGENDĂ"):
    """Legenda materialelor: items = [(culoare, contur, hașură sau None, text)]; întoarce y-ul de sub ea (mm)."""
    fig.text(x / PAGE[0], y / PAGE[1], title, fontsize=6.4, weight="bold", ha="left", va="top")
    y -= 4.2
    for fc, ec, ht, txt in items:
        fig.add_artist(mp.Rectangle((x / PAGE[0], (y - 1.7) / PAGE[1]), 4.0 / PAGE[0], 2.0 / PAGE[1],
                                    transform=fig.transFigure, fc=fc, ec=ec, lw=0.4, hatch=ht))
        fig.text((x + 5.5) / PAGE[0], (y - 0.7) / PAGE[1], txt, fontsize=4.6, ha="left", va="center")
        y -= 2.9
    return y


# ------------------------------------------------------------------ numere și note

def fmt(v):
    """12.5 -> „12,5”; 12.0 -> „12”."""
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


def kn(v):
    """Două zecimale, cu virgulă: forțele în kN."""
    return f"{v:.2f}".replace(".", ",")


def seq(vals):
    """„a, b și c”, cu virgulă zecimală."""
    vals = [fmt(v) for v in vals]
    return vals[0] if len(vals) == 1 else ", ".join(vals[:-1]) + f" și {vals[-1]}"


def dims(*vals):
    """„120 × 25 × 3,6”."""
    return " × ".join(fmt(v) for v in vals)


UNITATI = r"cm|mm|m²|m|kg|kN|N|MPa|ori|lei|buc|l|%|°"


def width_mm(fig, s, fs):
    """Lățimea pe hârtie (mm) a unui text scris cu DejaVu Sans."""
    w = fig.canvas.get_renderer().get_text_width_height_descent(s, FontProperties(family="DejaVu Sans", size=fs),
                                                                 ismath=False)[0]
    return w * 25.4 / fig.dpi


def wrap(fig, para, fs=NOTE_FS, width=NOTE_W):
    """Rupe un paragraf în rânduri care încap pe lățimea dată (mm), măsurate cu fontul real.

    Numerele rămân lipite de unități și de semnul „×”; rândurile de continuare se aliniază după numărul sau
    semnul de la începutul paragrafului („1.”, „1)”, „a)”, „•”).
    """
    para = para.replace(" × ", f"{NB}×{NB}")
    para = re.sub(rf"(\d) ({UNITATI})(?!\w)", rf"\1{NB}\2", para)
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


def text_block(fig, x, y, title, paras, fs=NOTE_FS, step=NOTE_STEP, width=NOTE_W):
    """Un grup de note: titlul și paragrafele rupte cu wrap, de la (x, y) mm în jos; întoarce y-ul de sub el."""
    fig.text(x / PAGE[0], y / PAGE[1], title, fontsize=6.2, weight="bold", ha="left", va="top")
    y -= 3.3
    for para in paras:
        for ln in wrap(fig, para, fs, width):
            fig.text(x / PAGE[0], y / PAGE[1], ln, fontsize=fs, ha="left", va="top", family="DejaVu Sans")
            y -= step
    return y - 1.1


def save(fig, base, dpi=220):
    """base.pdf (vectorial, A3) și base.png (220 dpi, pentru README și site); închide figura."""
    d = os.path.dirname(base)
    if d:
        os.makedirs(d, exist_ok=True)
    fig.savefig(base + ".pdf")
    fig.savefig(base + ".png", dpi=dpi)
    plt.close(fig)
    return base + ".pdf", base + ".png"


# ------------------------------------------------------------------ verificarea

def verifica_figura(fig, tol=TOL):
    """Verifică textele paginii, fără să scrie fișiere. Întoarce (probleme, de_privit, informatii).

    Probleme, în mm de hârtie: texte care ies din pagină (margine de 2 mm; jos, 5 mm), texte care se suprapun,
    texte de pagină (note, legendă) care intră peste un desen și linii de indicație care trec printr-un text
    străin. De privit în PNG: texte care ies puțin din chenarul propriului desen (cotele de la margine).
    La adnotări se măsoară doar textul: Annotation.get_window_extent ar include și linia de indicație.
    """
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    k = 25.4 / fig.dpi
    W, H = (float(v) * 25.4 for v in fig.get_size_inches())

    def mm(bb):
        return bb.x0 * k, bb.y0 * k, bb.x1 * k, bb.y1 * k

    def name(t):
        return t.get_text().split("\n")[0][:50]

    texts = []      # (sursa, text, chenar în mm, indicele desenului sau None)
    leaders = []    # (indicele textului, capătul de la text, capătul de la obiect), în mm
    frames = [mm(ax.get_window_extent(r)) for ax in fig.axes]
    for t in fig.texts:
        if t.get_text().strip() and t.get_visible():
            texts.append(("pagină", name(t), mm(t.get_window_extent(r)), None))
    for i, ax in enumerate(fig.axes):
        for t in ax.texts:
            if not (t.get_text().strip() and t.get_visible()):
                continue
            texts.append((f"desen {i}", name(t), mm(Text.get_window_extent(t, r)), i))
            if isinstance(t, Annotation) and t.arrow_patch is not None:
                leaders.append((len(texts) - 1, ax.transData.transform(t.xyann) * k,
                                ax.transData.transform(t.xy) * k))

    bad, look = [], []
    for src, s, (x0, y0, x1, y1), _ in texts:
        if x0 < 2 or y0 < 5 or x1 > W - 2 or y1 > H - 2:
            bad.append(f"iese din pagină ({src}): {s!r}")
    for a, b in itertools.combinations(texts, 2):
        (ax0, ay0, ax1, ay1), (bx0, by0, bx1, by1) = a[2], b[2]
        if min(ax1, bx1) - max(ax0, bx0) > tol and min(ay1, by1) - max(ay0, by0) > tol:
            bad.append(f"suprapunere: {a[0]} {a[1]!r} și {b[0]} {b[1]!r}")
    for src, s, (x0, y0, x1, y1), own in texts:
        if own is not None:
            continue
        for i, (fx0, fy0, fx1, fy1) in enumerate(frames):
            if min(x1, fx1) - max(x0, fx0) > tol and min(y1, fy1) - max(y0, fy0) > tol:
                bad.append(f"text de pagină în desenul {i}: {s!r}")
    for idx, p_text, p_obj in leaders:
        tx0, ty0, tx1, ty1 = texts[idx][2]
        for j, (src, s, (x0, y0, x1, y1), _) in enumerate(texts):
            if j == idx:
                continue
            for n in range(201):
                x = p_text[0] + (p_obj[0] - p_text[0]) * n / 200
                y = p_text[1] + (p_obj[1] - p_text[1]) * n / 200
                if tx0 <= x <= tx1 and ty0 <= y <= ty1:
                    continue
                if x0 + 0.1 <= x <= x1 - 0.1 and y0 + 0.1 <= y <= y1 - 0.1:
                    bad.append(f"indicația pentru {texts[idx][1]!r} trece prin {s!r}")
                    break

    for src, s, (x0, y0, x1, y1), own in texts:
        if own is None:
            continue
        fx0, fy0, fx1, fy1 = frames[own]
        if x0 < fx0 - 0.3 or x1 > fx1 + 0.3 or y0 < fy0 - 0.3 or y1 > fy1 + 0.3:
            look.append(f"{s!r} ({src}) iese puțin din chenarul desenului")
    page = [y0 for src, _, (_, y0, _, _), own in texts if own is None]
    info = {"texte": len(texts), "desene": len(frames), "jos_mm": round(min(page), 1) if page else None}
    return bad, look, info


def dimensiuni_pdf(path):
    """(lățime, înălțime) a primei pagini din PDF, în mm, după /MediaBox."""
    with open(path, "rb") as f:
        data = f.read()
    m = re.search(rb"/MediaBox\s*\[\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\]", data)
    if not m:
        raise ValueError(f"{path}: nu găsesc /MediaBox")
    x0, y0, x1, y1 = (float(v) for v in m.groups())
    return (x1 - x0) * 25.4 / 72, (y1 - y0) * 25.4 / 72


def e_a3(path):
    w, h = dimensiuni_pdf(path)
    return abs(max(w, h) - 420) < 1 and abs(min(w, h) - 297) < 1


def incarca_modul(path, nume="_plan_verificat"):
    """Importă drawing.py-ul unui proiect din calea lui (cu folderul lui pe sys.path, pentru design.py)."""
    import importlib.util
    path = os.path.abspath(path)
    sys.dont_write_bytecode = True
    folder = os.path.dirname(path)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    spec = importlib.util.spec_from_file_location(nume, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


USAGE = """folosire:
  python plan.py verifica <drawing.py> [funcția care întoarce figura, implicit build]
  python plan.py a3 <plan.pdf> [...]"""


def main(argv):
    if len(argv) >= 2 and argv[0] == "verifica":
        mod = incarca_modul(argv[1])
        fn = argv[2] if len(argv) > 2 else "build"
        if not hasattr(mod, fn):
            print(f"{argv[1]} nu are funcția {fn}() care să întoarcă figura; adaug-o (vezi docstringul lui plan.py)")
            return 2
        bad, look, info = verifica_figura(getattr(mod, fn)())
        for s in look:
            print("de privit în PNG:", s)
        print(f"{info['texte']} texte în {info['desene']} desene; cel mai de jos text de pagină: la "
              f"{info['jos_mm']} mm de marginea de jos")
        for b in bad:
            print("PROBLEMĂ:", b)
        print("probleme:", len(bad))
        return 1 if bad else 0
    if len(argv) >= 2 and argv[0] == "a3":
        bad = 0
        for p in argv[1:]:
            w, h = dimensiuni_pdf(p)
            ok = e_a3(p)
            bad += not ok
            print(f"{'ok ' if ok else 'NU '} {p}: {fmt(w)} × {fmt(h)} mm" + ("" if ok else " (A3 = 420 × 297 mm)"))
        return 1 if bad else 0
    print(USAGE)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
