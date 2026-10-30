"""Verifică textele planului tehnic, fără să scrie fișiere.

Construiește pagina din drawing.build() și caută, în mm de hârtie:
  - textele care ies din pagină (margine de 2 mm; jos, 5 mm);
  - textele care se suprapun;
  - notele și legenda (textele de pagină) care intră într-un desen;
  - liniile de indicație care trec printr-un text străin.
Cotele care ies puțin din chenarul propriului desen doar se afișează, fără să fie numărate ca probleme.
La adnotări se măsoară doar textul: Annotation.get_window_extent ar include și linia de indicație.
Iese cu codul 1 dacă găsește probleme.
"""
import itertools
import sys

import matplotlib

matplotlib.use("Agg")
from matplotlib.text import Annotation, Text  # noqa: E402

import drawing  # noqa: E402

TOL = 0.05   # mm: atingerile mai mici nu contează


def main():
    fig = drawing.build()
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    k = 25.4 / fig.dpi
    W, H = drawing.PAGE

    def mm(bb):
        return bb.x0 * k, bb.y0 * k, bb.x1 * k, bb.y1 * k

    def name(t):
        return t.get_text().split("\n")[0][:50]

    texts = []      # (sursa, text, chenar în mm, indicele desenului sau None)
    leaders = []    # (indicele textului, capătul de la text, capătul de la obiect), în mm
    frames = [mm(ax.get_window_extent(r)) for ax in fig.axes]
    for t in fig.texts:
        if t.get_text().strip():
            texts.append(("pagină", name(t), mm(t.get_window_extent(r)), None))
    for i, ax in enumerate(fig.axes):
        for t in ax.texts:
            if not (t.get_text().strip() and t.get_visible()):
                continue
            texts.append((f"desen {i}", name(t), mm(Text.get_window_extent(t, r)), i))
            if isinstance(t, Annotation) and t.arrow_patch is not None:
                leaders.append((len(texts) - 1, ax.transData.transform(t.xyann) * k,
                                ax.transData.transform(t.xy) * k))

    bad = []
    for src, s, (x0, y0, x1, y1), _ in texts:
        if x0 < 2 or y0 < 5 or x1 > W - 2 or y1 > H - 2:
            bad.append(f"iese din pagină ({src}): {s!r}")
    for a, b in itertools.combinations(texts, 2):
        (ax0, ay0, ax1, ay1), (bx0, by0, bx1, by1) = a[2], b[2]
        if min(ax1, bx1) - max(ax0, bx0) > TOL and min(ay1, by1) - max(ay0, by0) > TOL:
            bad.append(f"suprapunere: {a[0]} {a[1]!r} și {b[0]} {b[1]!r}")
    for src, s, (x0, y0, x1, y1), own in texts:
        if own is not None:
            continue
        for i, (fx0, fy0, fx1, fy1) in enumerate(frames):
            if min(x1, fx1) - max(x0, fx0) > TOL and min(y1, fy1) - max(y0, fy0) > TOL:
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
            print(f"de privit în PNG: {s!r} ({src}) iese puțin din chenarul desenului")
    low = min(y0 for src, _, (_, y0, _, _), own in texts if own is None)
    print(f"{len(texts)} texte; cel mai de jos text de pagină: la {low:.1f} mm de marginea de jos")
    for b in bad:
        print("PROBLEMĂ:", b)
    print("probleme:", len(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
