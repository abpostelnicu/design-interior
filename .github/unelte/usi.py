"""Ușile de mobilier: cât loc îi trebuie unei uși de dulap, bufet sau comodă care se deschide lângă un perete
sau lângă alt obiect.

    python usi.py --latime 34 --grosime 2.5 --balama dreapta --distanta 3.6 --fata 51.5 --obstacol-pana-la 70
    python usi.py --latime 51 --grosime 2.5 --balama stanga --distanta 3.6 --fata 51.5 --imagine out/usa_51.png
    python usi.py --json --latime 34 --balama dreapta --distanta 3.6      # rezultatul ca JSON

Opțiunile, toate în cm, cu adâncimile măsurate de la perete:
    --latime        lățimea ușii (obligatorie)
    --grosime       grosimea ușii (implicit 2)
    --balama        stanga sau dreapta, privind corpul din față; obstacolul e în aceeași parte (obligatorie)
    --distanta      de la laterala corpului, dinspre balama, până la obstacol (obligatorie)
    --fata          adâncimea feței corpului (implicit 0)
    --obstacol-de-la, --obstacol-pana-la
                    adâncimile între care e obstacolul (implicit de la perete până departe în cameră, ca un perete;
                    un blat de birou de 70 cm: --obstacol-pana-la 70)
    --unghi-max     unghiul maxim al balamalelor, în grade (implicit 110)
    --imagine CALE  planul ușii, ca PNG
    --json          rezultatul ca JSON

Modelul, în plan (vedere de sus): ușa e aplicată pe fața corpului și se rotește în jurul muchiei din față a
lateralei dinspre balama. La 90°, grosimea ei iese în lateral cu `grosime` cm; peste 90°, muchia liberă trece de
laterală și merge spre obstacol. Unghiul de contact e primul unghi la care ușa atinge obstacolul; spațiul necesar
pentru un unghi e cel mai mare spațiu lateral pe care îl ocupă ușa până la acel unghi, în dreptul obstacolului.
Balamalele aplicate, cu cupă, mută ușa puțin în afară: păstrezi o rezervă de 0,5–1 cm.

Exemplu: dulapul Cioata Galla 120 (119 × 51 × 150 cm), centrat între colț și birou, are 3,6 cm liberi de fiecare
parte, iar fața lui e la 51,5 cm de perete. Ușa din dreapta, de 34 cm, are 1,1 cm liberi la 90° și ar intra
~5,8 cm în blatul biroului la 110°; cea din stânga, de 51 cm, are tot 1,1 cm liberi la 90°, până la perete.
Ușile se deschid deci până la ~90°, nu până la cei 110° ai balamalelor.

În planul tehnic, `deseneaza` pune ușa într-o vedere în plan făcută cu `plan.make_axes(..., invert=True)`; cu
`nume` și `obstacol`, legenda spune care ușă e și în ce ar intra, ca să deosebești două uși din aceeași vedere.
Codul de ieșire: 0 dacă ușa ajunge la unghiul maxim fără să atingă obstacolul, 1 dacă îl atinge înainte, 2 la
argumente greșite. Generalizat din `door_check` din `.github/surse/comoda-birou/render_galla.py`.
"""
import json
import math
import os
import sys

INF = math.inf

# copiate din plan.py (culorile, cota orizontală, hașura), ca modulul să meargă singur
_C = dict(oak="#c9a06a", oak_e="#7b5b37", dim="#1a1a1a", note="#555555", hatch="#8f8f8f")


def colturi_usa(unghi, latime, grosime):
    """Colțurile ușii la unghiul dat (grade), față de balama: dx spre obstacol, dz spre cameră, în cm.

    Închisă (0°), ușa acoperă dx de la −latime la 0, cu fața interioară pe fața corpului (dz = 0) și cea
    exterioară la dz = grosime; la 90°, ocupă dx de la 0 la grosime și dz de la 0 la latime.
    """
    t = math.radians(unghi)
    c, s = math.cos(t), math.sin(t)
    return [(dx * c + dz * s, -dx * s + dz * c)
            for dx, dz in ((-latime, 0.0), (0.0, 0.0), (0.0, grosime), (-latime, grosime))]


def _taie(poligon, z, pastreaza_peste):
    """Partea poligonului cu dz ≥ z (pastreaza_peste=True) sau cu dz ≤ z (Sutherland–Hodgman)."""
    rez = []
    for i, a in enumerate(poligon):
        b = poligon[(i + 1) % len(poligon)]
        ina = a[1] >= z if pastreaza_peste else a[1] <= z
        inb = b[1] >= z if pastreaza_peste else b[1] <= z
        if ina:
            rez.append(a)
        if ina != inb:
            k = (z - a[1]) / (b[1] - a[1])
            rez.append((a[0] + k * (b[0] - a[0]), z))
    return rez


def ocupat(unghi, latime, grosime, de_la=-INF, pana_la=INF):
    """Cât iese ușa în lateral, spre obstacol (dx maxim, în cm), în banda de adâncime [de_la, pana_la], măsurată
    de la fața corpului; None dacă la acest unghi ușa nu ajunge în bandă."""
    p = colturi_usa(unghi, latime, grosime)
    if math.isfinite(de_la):
        p = _taie(p, de_la, True)
    if p and math.isfinite(pana_la):
        p = _taie(p, pana_la, False)
    return max(x for x, _ in p) if p else None


def analizeaza(latime, grosime, distanta, fata=0.0, obstacol_de_la=0.0, obstacol_pana_la=INF, unghi_max=110.0,
               pas=0.05):
    """Unghiul de contact și spațiul lateral ocupat și necesar la 90° și la unghiul maxim (dict, în cm și grade).

    Adâncimile (fata, obstacol_de_la, obstacol_pana_la) sunt măsurate de la perete. În rezultat:
    - contact: primul unghi la care ușa atinge obstacolul; None dacă nu-l atinge până la 180°;
    - atinge: True dacă îl atinge până la unghi_max;
    - la_90 și la_max: {"unghi", "ocupat" (cm în lateral, sau None), "liber" (cm până la obstacol; negativ = cât
      ar intra în el)};
    - necesar_90 și necesar_max: spațiul lateral necesar ca ușa să ajungă la acel unghi;
    - in_fata_la_90: cât iese ușa în fața corpului la 90°; raza: arcul măturat de muchia liberă.
    """
    a, b = obstacol_de_la - fata, obstacol_pana_la - fata  # banda obstacolului, față de fața corpului

    def oc(u):
        v = ocupat(u, latime, grosime, a, b)
        return -INF if v is None else v

    n = int(round(180.0 / pas))
    unghiuri = [i * pas for i in range(n + 1)]
    valori = [oc(u) for u in unghiuri]
    contact = None
    for i, v in enumerate(valori):
        if v >= distanta:
            if i == 0:
                contact = 0.0
            else:
                lo, hi = unghiuri[i - 1], unghiuri[i]
                for _ in range(50):
                    mij = (lo + hi) / 2
                    lo, hi = (lo, mij) if oc(mij) >= distanta else (mij, hi)
                contact = hi
            break

    def necesar(u):
        k = int(math.floor(u / pas + 1e-9))
        return max([0.0, oc(u)] + valori[:k + 1])

    def la(u):
        v = ocupat(u, latime, grosime, a, b)
        return {"unghi": u, "ocupat": None if v is None else round(v, 3),
                "liber": round(distanta - (v if v is not None else 0.0), 3)}

    return {"latime": latime, "grosime": grosime, "distanta": distanta, "fata": fata,
            "obstacol": [obstacol_de_la, None if math.isinf(obstacol_pana_la) else obstacol_pana_la],
            "unghi_max": unghi_max, "contact": None if contact is None else round(contact, 2),
            "atinge": contact is not None and contact <= unghi_max,
            "la_90": la(90.0), "la_max": la(unghi_max),
            "necesar_90": round(necesar(90.0), 3), "necesar_max": round(necesar(unghi_max), 3),
            "in_fata_la_90": round(max(z for _, z in colturi_usa(90.0, latime, grosime)), 3),
            "raza": round(math.hypot(latime, grosime), 3)}


# ------------------------------------------------------------------ desenul în plan

def _fmt(v):
    """12.5 -> „12,5”; 12.0 -> „12”."""
    return f"{v:.1f}".rstrip("0").rstrip(".").replace(".", ",")


def _dim_h(ax, x0, x1, y, text, dy, fs, k):
    """Cotă orizontală, ca `plan.dim_h`, fără liniile ajutătoare."""
    ax.plot([x0 - 1.6 * k, x1 + 1.6 * k], [y, y], color=_C["dim"], lw=0.35, zorder=20)
    for x in (x0, x1):
        s = 1.6 * k
        ax.plot([x - s / 2, x + s / 2], [y - s / 2, y + s / 2], color=_C["dim"], lw=0.6, zorder=20)
    up = (dy >= 0) != ax.yaxis_inverted()
    ax.text((x0 + x1) / 2, y + dy, text, ha="center", va="bottom" if up else "top", fontsize=fs, zorder=21,
            bbox=dict(fc="white", ec="none", pad=0.15, alpha=0.85))


def deseneaza(ax, rez, balama, x_balama=0.0, k=1.0, fs=5.0, cote=True, legenda=True, latime_obstacol=25.0,
              corp=None, nume=None, obstacol=None):
    """Ușa, în plan, pe axele date: X de-a lungul peretelui, Z = adâncimea de la perete (în jos, ca în vederile
    în plan din proiecte, cu `invert=True`), în cm.

    rez: rezultatul lui `analizeaza`; balama: "stanga" sau "dreapta"; x_balama: X-ul lateralei dinspre balama.
    Desenează obstacolul (hașurat, pe `latime_obstacol` cm), ușa închisă (întrerupt), la 90° (plin), la unghiul
    maxim (punctat) și la cel de contact (roșu), arcul muchiei libere și, cu `cote`, distanța până la obstacol și
    cât intră ușa în el la unghiul maxim. `legenda` explică liniile, în colțul din stânga jos al vederii sau la
    (x, y), în fracțiuni din vedere; două uși în aceeași vedere primesc legende în locuri diferite sau False.
    Ca să le deosebești, legenda spune care ușă e, cu `nume` (de exemplu „ușa din stânga (spre colț)”), și în ce
    intră, cu `obstacol`, perechea (nearticulat, articulat): („perete”, „peretele”) sau („blat”, „blatul”). Cu
    amândouă: „ușa din stânga (spre colț): la 90° (plin); la 110° (punctat) ar intra 15,8 cm în perete; atinge
    peretele la ~93° (roșu)”; fără ele: „ușa de 55 cm la 90° (plin); … intră 15,8 cm în obstacol; …”.
    corp: (x0, x1) ale corpului, dacă îl vrei desenat, cu spatele la 0,5 cm de perete, sau (x0, x1, z_spate).
    k scalează cotele, ca în `plan` (K15, K5). Legenda cu `nume` și `obstacol` e preluată din
    `.github/surse/comoda-birou/cioata/` (`vedere_plan` din `planul.py`).
    """
    import matplotlib.patches as mp

    if obstacol is not None and (isinstance(obstacol, str) or len(obstacol) != 2):
        raise ValueError("obstacol: perechea (nearticulat, articulat), de exemplu („perete”, „peretele”)")
    sg = 1.0 if balama == "dreapta" else -1.0
    w, t, g, fata = rez["latime"], rez["grosime"], rez["distanta"], rez["fata"]
    z0, z1 = rez["obstacol"]
    z1_des = fata + w + 12 if z1 is None else z1
    xo0, xo1 = sorted((x_balama + sg * g, x_balama + sg * (g + latime_obstacol)))
    ax.add_patch(mp.Rectangle((xo0, z0), xo1 - xo0, z1_des - z0, facecolor="#f4f4f4", edgecolor=_C["hatch"],
                              hatch="////", lw=0.5, zorder=2))
    if z1 is not None:
        ax.plot([xo0, xo1], [z1, z1], color="k", lw=0.6, zorder=3)
    ax.plot([x_balama + sg * g] * 2, [z0, z1_des], color="k", lw=0.8, zorder=3)
    if corp is not None:
        spate = corp[2] if len(corp) > 2 else (0.5 if fata > 1 else 0.0)
        x0, x1 = min(corp[:2]), max(corp[:2])
        ax.add_patch(mp.Rectangle((x0, spate), x1 - x0, fata - spate, facecolor=_C["oak"], edgecolor=_C["oak_e"],
                                  lw=0.5, zorder=4))

    def poligon(u):
        return [(x_balama + sg * dx, fata + dz) for dx, dz in colturi_usa(u, w, t)]

    ax.add_patch(mp.Polygon(poligon(0.0), closed=True, fc="none", ec=_C["oak_e"], lw=0.35, ls=(0, (2, 1)),
                            zorder=5))
    ax.add_patch(mp.Polygon(poligon(90.0), closed=True, fc=_C["oak"], ec=_C["oak_e"], lw=0.5, zorder=6))
    umax = rez["unghi_max"]
    if abs(umax - 90.0) > 0.01:
        ax.add_patch(mp.Polygon(poligon(umax), closed=True, fc="none", ec=_C["oak_e"], lw=0.5, ls=(0, (3, 1.5)),
                                zorder=6))
    contact = rez["contact"]
    if contact is not None and contact < umax:
        ax.add_patch(mp.Polygon(poligon(contact), closed=True, fc="none", ec="#c0392b", lw=0.6, zorder=7))
    arc = [(x_balama + sg * dx, fata + dz) for dx, dz in (colturi_usa(i * umax / 60, w, t)[3] for i in range(61))]
    ax.plot([p[0] for p in arc], [p[1] for p in arc], color=_C["note"], lw=0.3, ls=(0, (1, 1)), zorder=5)
    # unghiurile, la capătul ușii, doar dacă sunt destul de departe unul de altul; contactul merge în legendă
    for u in [90.0] + ([umax] if abs(umax - 90.0) >= 8.0 else []):
        dx, dz = colturi_usa(u, w + 2.5 * k, t / 2)[3]
        ax.text(x_balama + sg * dx, fata + dz, f"{_fmt(u)}°", fontsize=fs, color=_C["oak_e"],
                ha="left" if sg * dx >= 0 else "right", va="center", zorder=8,
                bbox=dict(fc="white", ec="none", pad=0.1, alpha=0.85))
    oc = rez["la_max"]["ocupat"]
    intra = oc is not None and oc > g + 0.05
    if legenda:
        parti = [f"{nume}: la 90° (plin)" if nume else f"ușa de {_fmt(w)} cm la 90° (plin)"]
        if abs(umax - 90.0) > 0.01:
            if not intra:
                parti.append(f"la {_fmt(umax)}° (punctat)")
            elif obstacol is None:
                parti.append(f"la {_fmt(umax)}° (punctat) intră {_fmt(oc - g)} cm în obstacol")
            else:
                parti.append(f"la {_fmt(umax)}° (punctat) ar intra {_fmt(oc - g)} cm în {obstacol[0]}")
        if contact is not None and contact < umax:
            parti.append(f"atinge obstacolul la {_fmt(contact)}° (roșu)" if obstacol is None
                         else f"atinge {obstacol[1]} la ~{_fmt(contact)}° (roșu)")
        xl, yl = legenda if isinstance(legenda, (tuple, list)) else (0.01, 0.01)
        ax.text(xl, yl, "; ".join(parti), transform=ax.transAxes, fontsize=fs, color=_C["note"], ha="left",
                va="bottom", zorder=9, bbox=dict(fc="white", ec="none", pad=0.2, alpha=0.9))
    if cote:
        _dim_h(ax, *sorted((x_balama, x_balama + sg * g)), fata - 3.0 * k, _fmt(g), -1.2 * k, fs, k)
        if intra:
            # la capătul obstacolului sau, la un perete, dincolo de capătul ușii și de eticheta „90°”
            zc = z1 + 3.0 * k if z1 is not None and z1 - fata < w else fata + w + 6.0 * k
            _dim_h(ax, *sorted((x_balama + sg * g, x_balama + sg * oc)), zc, _fmt(oc - g), 1.2 * k, fs, k)


def imagine(rez, balama, dest, dpi=220):
    """Planul ușii, singur, ca PNG la 220 dpi, la 1:5 sau 1:10, după mărime. Întoarce (lățimea, înălțimea) în px."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    w, t, g, fata = rez["latime"], rez["grosime"], rez["distanta"], rez["fata"]
    oc = max(rez["la_max"]["ocupat"] or 0.0, g, t)
    sg = 1.0 if balama == "dreapta" else -1.0
    xa, xb = sorted((-sg * (w + 12), sg * (oc + 30)))
    za = max(-6.0, rez["obstacol"][0] - 4) if fata < 40 else fata - 20
    zb = fata + w + 14
    scara = 5.0 if max(xb - xa, zb - za) <= 110 else 10.0
    mmcm = 10.0 / scara
    lat, inalt = (xb - xa) * mmcm + 20, (zb - za) * mmcm + 26
    fig = plt.figure(figsize=(lat / 25.4, inalt / 25.4))
    ax = fig.add_axes([10 / lat, 10 / inalt, (xb - xa) * mmcm / lat, (zb - za) * mmcm / inalt])
    ax.set_xlim(xa, xb)
    ax.set_ylim(zb, za)
    ax.set_aspect("equal")
    ax.axis("off")
    parte = "dreapta" if sg > 0 else "stânga"
    fig.text(10 / lat, ((zb - za) * mmcm + 12.5) / inalt,
             f"Ușa de {_fmt(w)} cm, balamaua în {parte}, la {_fmt(g)} cm de obstacol (1:{scara:g})",
             fontsize=8.5, weight="bold", ha="left", va="bottom")
    if fata > 0.5 and za < 0:
        ax.plot([xa, xb], [0, 0], color="k", lw=0.8, zorder=3)      # peretele din spatele corpului
    deseneaza(ax, rez, balama, 0.0, k=scara / 10.0, fs=6.0, corp=(0.0, -sg * (w + 12)))
    os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
    fig.savefig(dest, dpi=dpi)
    plt.close(fig)
    return round(lat / 25.4 * dpi), round(inalt / 25.4 * dpi)


# ------------------------------------------------------------------ linia de comandă

OPTIUNI = {"--latime": 1, "--grosime": 1, "--balama": 1, "--distanta": 1, "--fata": 1, "--obstacol-de-la": 1,
           "--obstacol-pana-la": 1, "--unghi-max": 1, "--imagine": 1, "--json": 0}


def _citeste_optiuni(argv):
    """{opțiune: valoare} din argv; ValueError cu mesaj în română la o opțiune necunoscută sau fără valoare."""
    opt, i = {}, 0
    while i < len(argv):
        a = argv[i]
        if a not in OPTIUNI:
            raise ValueError(f"opțiune necunoscută: {a}")
        if OPTIUNI[a] == 0:
            opt[a] = True
            i += 1
            continue
        if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
            raise ValueError(f"{a} cere o valoare")
        opt[a] = argv[i + 1]
        i += 2
    return opt


def _cm(text, nume):
    try:
        return float(str(text).replace(",", "."))
    except ValueError:
        raise ValueError(f"{nume}: „{text}” nu e un număr") from None


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    try:
        o = _citeste_optiuni(argv)
        lipsa = [k for k in ("--latime", "--balama", "--distanta") if k not in o]
        if lipsa:
            raise ValueError(f"lipsesc opțiunile: {', '.join(lipsa)}")
        if o["--balama"] not in ("stanga", "dreapta"):
            raise ValueError("--balama e „stanga” sau „dreapta”")
        latime, distanta = _cm(o["--latime"], "--latime"), _cm(o["--distanta"], "--distanta")
        grosime = _cm(o.get("--grosime", 2.0), "--grosime")
        fata = _cm(o.get("--fata", 0.0), "--fata")
        de_la = _cm(o.get("--obstacol-de-la", 0.0), "--obstacol-de-la")
        pana_la = _cm(o["--obstacol-pana-la"], "--obstacol-pana-la") if "--obstacol-pana-la" in o else INF
        umax = _cm(o.get("--unghi-max", 110.0), "--unghi-max")
        if latime <= 0 or grosime <= 0 or distanta < 0:
            raise ValueError("lățimea și grosimea sunt pozitive, iar distanța e cel puțin 0")
        if not 0 < umax <= 180:
            raise ValueError("--unghi-max e între 0 și 180")
        if pana_la <= de_la:
            raise ValueError("obstacolul se termină după ce începe: --obstacol-pana-la > --obstacol-de-la")
    except ValueError as e:
        print(f"eroare: {e}. Vezi: python usi.py --help", file=sys.stderr)
        return 2

    balama = o["--balama"]
    rez = analizeaza(latime, grosime, distanta, fata, de_la, pana_la, umax)
    rez["balama"] = balama
    if "--imagine" in o:
        marime = imagine(rez, balama, o["--imagine"])
        rez["imagine"] = o["--imagine"]
    cod = 1 if rez["atinge"] else 0
    if "--json" in o:
        print(json.dumps(rez, ensure_ascii=False, indent=1))
        return cod

    parte = "dreapta" if balama == "dreapta" else "stânga"
    z1 = rez["obstacol"][1]
    ob = (f"de la {_fmt(de_la)} " if de_la else "de la perete ") + (
        f"până la {_fmt(z1)} cm de perete" if z1 is not None else "până departe în cameră")
    print(f"Ușa: {_fmt(latime)} cm lățime, {_fmt(grosime)} cm grosime, balamaua în {parte}"
          + (f", fața corpului la {_fmt(fata)} cm de perete." if fata else "."))
    print(f"Obstacolul: la {_fmt(distanta)} cm de laterala din {parte}, {ob}.")
    c = rez["contact"]
    if c is None:
        print("- Nu atinge obstacolul, oricât s-ar deschide.")
    elif c <= umax:
        print(f"- Atinge obstacolul la {_fmt(c)}°" + (", deci nu ajunge la 90°." if c < 90 else "."))
    else:
        print(f"- Nu atinge obstacolul până la {_fmt(umax)}° (l-ar atinge la {_fmt(c)}°).")
    for cheie in ("la_90", "la_max"):
        r = rez[cheie]
        if cheie == "la_max" and abs(umax - 90.0) < 0.01:
            continue
        if r["ocupat"] is None:
            print(f"- La {_fmt(r['unghi'])}°: ușa nu ajunge în dreptul obstacolului.")
        elif r["liber"] >= 0:
            print(f"- La {_fmt(r['unghi'])}°: ocupă {_fmt(r['ocupat'])} cm în lateral; rămân {_fmt(r['liber'])} cm "
                  "liberi.")
        else:
            print(f"- La {_fmt(r['unghi'])}°: ocupă {_fmt(r['ocupat'])} cm în lateral; ar intra {_fmt(-r['liber'])} "
                  "cm în obstacol.")
    print(f"- Spațiul lateral necesar: {_fmt(rez['necesar_90'])} cm pentru 90°"
          + ("" if abs(umax - 90.0) < 0.01 else f" și {_fmt(rez['necesar_max'])} cm pentru {_fmt(umax)}°")
          + "; păstrezi 0,5–1 cm rezervă pentru balamale.")
    print(f"- Deschisă la 90°, ușa iese {_fmt(rez['in_fata_la_90'])} cm în fața corpului"
          + (f" (până la {_fmt(fata + rez['in_fata_la_90'])} cm de perete)" if fata else "")
          + f"; muchia liberă mătură un arc cu raza de {_fmt(rez['raza'])} cm.")
    if "imagine" in rez:
        print(f"Planul ușii: {rez['imagine']} ({marime[0]} × {marime[1]} px)")
    return cod


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
