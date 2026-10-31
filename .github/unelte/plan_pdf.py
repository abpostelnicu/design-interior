"""Planul de arhitect în PDF: paginile, randările, textele, liniile și dimensiunile unei camere, cu scara reală.

    python plan_pdf.py info <plan.pdf>
    python plan_pdf.py randeaza <plan.pdf> out/plan.png [--zona x0 y0 x1 y1] [--dpi 150] [--grila 50]
    python plan_pdf.py cauta <plan.pdf> "DORMITOR 2" [--cuvinte-intregi]
    python plan_pdf.py cuvinte <plan.pdf> --zona 560 330 780 570
    python plan_pdf.py linii <plan.pdf> --zona 560 330 780 570 [--din toate] [--lungime-min 10] [--uneste]
    python plan_pdf.py camera <plan.pdf> "DORMITOR 2" --cota-cm 327 --verifica-cm 366 [--scara 50]
                                                       [--imagine out/camera.png]

Opțiunile comune:
    --pagina N      pagina, de la 1 (implicit 1; la `cauta` și `camera`, toate)
    --zona x0 y0 x1 y1
                    zona, în pt (implicit pagina întreagă)
    --px DPI        zona e dată în pixeli, citiți pe o randare făcută la acest dpi
    --json          rezultatul ca JSON
Opțiunile liniilor (`linii` și `camera`):
    --din umpluturi|linii|toate
                    din ce desene iau segmentele: marginile umpluturilor colorate (pereții tăiați), liniile
                    trase sau toate (implicit: toate la `linii`, umpluturi la `camera`)
    --lungime-min PT  lungimea minimă (implicit 10 pt la `linii`, 20 pt la `camera`)
    --cu-albe       păstrează și desenele albe: măștile de sub texte, mobilierul umplut cu alb
    --cu-intrerupte păstrează și liniile întrerupte, adică axele (doar la `linii`)
    --uneste        unește segmentele de pe aceeași dreaptă care se ating (doar la `linii`; `camera` unește mereu)
    --toleranta PT  cât se poate abate un segment de la orizontală sau verticală (implicit 0,05)
Opțiunile camerei:
    --cota-cm CM    o cotă scrisă pe plan, pe care se calibrează scara (de exemplu lățimea camerei)
    --cota-pe x|y   axa cotei: x orizontal pe foaie, y vertical (implicit x)
    --verifica-cm CM  a doua cotă scrisă, pe cealaltă axă, ca verificare
    --scara N       scara din cartuș, 1:N; singură, doar dacă nu ai o cotă; cu --cota-cm, arată abaterea
    --banda PT      cât de departe de etichetă poate trece prima căutare (implicit 50)
    --nr N          a câta etichetă găsită (implicit 1)
    --imagine CALE  imaginea de verificare: camera în roșu, eticheta în albastru
    --dpi N         rezoluția randărilor (implicit 150 la `randeaza`, 200 la imaginea camerei)

Coordonatele sunt în puncte tipografice (1 pt = 1/72 inch = 0,3528 mm pe hârtie), pe pagina nerotită, cu
originea în colțul din stânga sus și cu y în jos, ca în PyMuPDF. Numerele se pot scrie și cu virgulă zecimală.

- Scara din cartuș („1:50”) nu e sigură: PDF-ul poate fi scalat la tipărire. La planul etajului din „Comodă
  birou”, 1 pt = 1,8412 cm, adică ~1:52,2. Calibrezi pe o cotă scrisă (`--cota-cm`) și verifici pe a doua
  (`--verifica-cm`): diferența trebuie să fie de câțiva milimetri, nu de centimetri.
- Planurile exportate din Archicad au fonturi compuse (Type0) fără tabel Unicode: textul iese „�”, iar căutarea obișnuită
  nu găsește nimic. Modulul citește textul cu TEXT_CID_FOR_UNKNOWN_UNICODE; `info` arată câte caractere sunt așa.
  `cauta` nu ține cont de majuscule, diacritice și spații și găsește și texte pe mai multe rânduri.
- `camera` caută, de la etichetă spre exterior, cea mai apropiată latură a unei umpluturi colorate pe fiecare
  parte: fețele interioare ale pereților. Liniile de cotă, axele și mobilierul alb nu încurcă. Presupune o
  cameră dreptunghiulară; la camerele în L, la holuri deschise și la balcoane te uiți pe imaginea de verificare.
  Aria scrisă pe plan („A: … m2”) e o verificare bună.
- Confidențialitatea: cartușul are nume, adresă, semnături și cod QR. PDF-ul, calea lui și randările paginii
  întregi nu intră în depozit; modulul te avertizează dacă salvezi o randare într-un loc din depozit neignorat
  de git. În fișiere scrii doar cotele.

Are nevoie de PyMuPDF (`pip install pymupdf`; se importă `pymupdf`, nu `fitz`).
"""
import json
import math
import os
import subprocess
import sys
import unicodedata
import warnings
from dataclasses import dataclass, replace

MM_PE_PT = 25.4 / 72
CM_PE_PT = 2.54 / 72                    # 1 pt de hârtie, în cm, la scara 1:1
FORMATE = {"A0": (841, 1189), "A1": (594, 841), "A2": (420, 594), "A3": (297, 420), "A4": (210, 297),
           "A5": (148, 210)}
LATURI = ("stânga", "dreapta", "sus", "jos")


def _pymupdf():
    try:
        with warnings.catch_warnings():         # PyMuPDF (SWIG) dă avertismente de depreciere la import
            warnings.simplefilter("ignore", DeprecationWarning)
            import pymupdf
    except ImportError:
        raise RuntimeError("lipsește PyMuPDF: pip install pymupdf (se importă `pymupdf`, nu `fitz`)") from None
    return pymupdf


def _cid():
    """Fără acest flag, textul din fonturile fără tabel Unicode iese „�”, iar căutarea nu găsește nimic."""
    return _pymupdf().TEXT_CID_FOR_UNKNOWN_UNICODE


def _fmt(x, zecimale=2):
    """Număr cu virgulă zecimală: 1.84 -> „1,84”."""
    return f"{x:.{zecimale}f}".replace(".", ",")


def _cate(n, unu, mai_multe):
    """Numărul cu substantivul acordat: „1 cuvânt”, „5 cuvinte”, „20 de cuvinte”, „101 cuvinte”."""
    if n == 1:
        return f"1 {unu}"
    return f"{n} {'de ' if n and (n % 100 == 0 or n % 100 >= 20) else ''}{mai_multe}"


# ------------------------------------------------------------------ PDF, pagini, randări

def deschide(cale):
    """Documentul PDF. În mesajele de eroare apare doar numele fișierului, nu calea."""
    pymupdf = _pymupdf()
    if not os.path.isfile(cale):
        raise FileNotFoundError(f"nu găsesc PDF-ul „{os.path.basename(cale)}”")
    try:
        return pymupdf.open(cale)
    except Exception as e:      # PyMuPDF are mai multe tipuri de erori la deschidere
        raise RuntimeError(f"nu pot deschide PDF-ul „{os.path.basename(cale)}”: {e}") from None


def pagina(doc, nr):
    """Pagina nr, de la 1."""
    if not 1 <= nr <= doc.page_count:
        raise ValueError(f"pagina {nr} nu există: documentul are {doc.page_count} pagini")
    return doc[nr - 1]


def intreaga(pg):
    """Pagina întreagă, în coordonatele paginii nerotite, aceleași cu ale textului și ale desenelor."""
    return pg.rect * pg.derotation_matrix


def dreptunghi(zona=None, px=None, pg=None):
    """Zona (x0, y0, x1, y1) ca dreptunghi PyMuPDF, în pt; din pixeli, dacă dai px = dpi-ul randării.

    Fără zonă, întoarce pagina întreagă.
    """
    pymupdf = _pymupdf()
    if zona is None:
        return intreaga(pg)
    x0, y0, x1, y1 = (float(v) for v in zona)
    if px:
        k = 72.0 / px
        x0, y0, x1, y1 = x0 * k, y0 * k, x1 * k, y1 * k
    z = pymupdf.Rect(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
    if z.is_empty:
        raise ValueError("zona e goală: dă colțurile ca x0 y0 x1 y1")
    return z


def info(doc):
    """Paginile: dimensiunea în pt și mm, formatul, rotația, câte cuvinte și desene au."""
    pymupdf = _pymupdf()
    meta = doc.metadata or {}
    rez = {"pagini": doc.page_count,
           "program": list(dict.fromkeys(filter(None, (meta.get("creator"), meta.get("producer"))))),
           "detalii": []}
    for nr, pg in enumerate(doc, 1):
        r = intreaga(pg)
        tipuri = [d.get("type") or "" for d in pg.get_drawings()]
        rez["detalii"].append({
            "pagina": nr, "latime_pt": round(r.width, 2), "inaltime_pt": round(r.height, 2),
            "latime_mm": round(r.width * MM_PE_PT, 1), "inaltime_mm": round(r.height * MM_PE_PT, 1),
            "format": format_hartie(r.width * MM_PE_PT, r.height * MM_PE_PT), "rotatie": pg.rotation,
            "cuvinte": len(pg.get_text("words", flags=pymupdf.TEXTFLAGS_WORDS | _cid())),
            "caractere_fara_unicode": pg.get_text("text", flags=pymupdf.TEXTFLAGS_TEXT & ~_cid()).count("\ufffd"),
            "desene": len(tipuri), "cu_umplere": sum("f" in t for t in tipuri),
            "cu_contur": sum("s" in t for t in tipuri)})
    return rez


def format_hartie(w_mm, h_mm):
    """„A3 orizontal”, „A1 vertical” sau „format nestandard”."""
    a, b = sorted((w_mm, h_mm))
    for nume, (fa, fb) in FORMATE.items():
        if abs(a - fa) <= 2 and abs(b - fb) <= 2:
            return f"{nume} {'orizontal' if w_mm > h_mm else 'vertical'}"
    return "format nestandard"


def randeaza(pg, zona=None, dpi=150):
    """Zona din pagină ca imagine PIL, plus transformarea din pt în pixeli: px = x·k − ox, py = y·k − oy.

    Randează pagina nerotită, ca pixelii să corespundă coordonatelor textului și ale desenelor. Întoarce
    (imaginea, ox, oy, k).
    """
    from PIL import Image
    z = zona if zona is not None else intreaga(pg)
    rot = pg.rotation
    if rot:
        pg.set_rotation(0)          # doar în memorie; se pune la loc mai jos
    try:
        pix = pg.get_pixmap(dpi=dpi, clip=z, alpha=False)
    finally:
        if rot:
            pg.set_rotation(rot)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples), pix.x, pix.y, dpi / 72.0


def _font(marime):
    """DejaVu Sans, care vine cu matplotlib și are diacriticele; fontul implicit din Pillow nu are „ă” și „ț”."""
    from PIL import ImageFont
    try:
        import matplotlib
        return ImageFont.truetype(os.path.join(matplotlib.get_data_path(), "fonts", "ttf", "DejaVuSans.ttf"),
                                  marime)
    except (ImportError, OSError):
        return ImageFont.load_default(size=marime)


def _scrie(d, x, y, text, culoare, f, aliniere="stânga"):
    """Text pe fundal alb, ca să se citească peste desen."""
    l, t, r, b = d.textbbox((0, 0), text, font=f)
    if aliniere == "dreapta":
        x -= r - l
    elif aliniere == "centru":
        x -= (r - l) / 2
    d.rectangle((x - 1, y - 1, x + r - l + 1, y + b - t + 1), fill=(255, 255, 255))
    d.text((x - l, y - t), text, fill=culoare, font=f)


def grila(img, ox, oy, k, zona, pas):
    """Grilă cu coordonatele în pt la fiecare `pas`: x în roșu, y în albastru, scrise pe margini."""
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    f = _font(13)
    zec = 0 if float(pas).is_integer() else 1
    _, _, lat, inalt = d.textbbox((0, 0), _fmt(max(abs(zona.x1), abs(zona.y1)), zec), font=f)
    sari_x = max(1, math.ceil((lat + 6) / (pas * k)))      # o etichetă la câte linii, ca să nu se suprapună
    sari_y = max(1, math.ceil((inalt + 6) / (pas * k)))
    for i, n in enumerate(range(math.ceil(zona.x0 / pas), math.floor(zona.x1 / pas) + 1)):
        x = n * pas * k - ox
        d.line([(x, 0), (x, img.height)], fill=(255, 120, 120), width=1)
        if i % sari_x == 0:
            _scrie(d, x + 2, 2, _fmt(n * pas, zec), (200, 0, 0), f)
            _scrie(d, x + 2, img.height - inalt - 3, _fmt(n * pas, zec), (200, 0, 0), f)
    for i, n in enumerate(range(math.ceil(zona.y0 / pas), math.floor(zona.y1 / pas) + 1)):
        y = n * pas * k - oy
        d.line([(0, y), (img.width, y)], fill=(120, 120, 255), width=1)
        if i % sari_y == 0:
            _scrie(d, 2, y + 2, _fmt(n * pas, zec), (0, 0, 200), f)
            _scrie(d, img.width - 2, y + 2, _fmt(n * pas, zec), (0, 0, 200), f, "dreapta")


def avertizeaza_daca_nu_e_ignorat(cale):
    """True (și un avertisment) dacă fișierul e într-un depozit git și nu e ignorat, deci ar putea ajunge public."""
    cale = os.path.realpath(cale)       # folderele pot fi legături simbolice (pe macOS), iar git vrea calea reală
    try:
        r = subprocess.run(["git", "-C", os.path.dirname(cale), "check-ignore", "-q", cale], capture_output=True)
    except OSError:
        return False
    if r.returncode == 1:           # 0 = ignorat, 128 = nu e într-un depozit git
        print(f"Atenție: „{os.path.basename(cale)}” e în depozit și nu e ignorat de git. Nu-l pune în commit: "
              "randările planului pot arăta cartușul, cu nume, adresă și semnături.", file=sys.stderr)
        return True
    return False


# ------------------------------------------------------------------ textul

def simplu(text):
    """Litere mici, fără diacritice: ș, ş → s; ț, ţ → t; ă, â → a; î → i."""
    d = unicodedata.normalize("NFKD", text)
    return "".join(c for c in d if not unicodedata.combining(c)).casefold()


def _randuri_text(pg):
    """Rândurile de text ale paginii: direcția, dreptunghiul și caracterele, fiecare cu dreptunghiul lui."""
    pymupdf = _pymupdf()
    rez = []
    for b in pg.get_text("rawdict", flags=pymupdf.TEXTFLAGS_RAWDICT | _cid())["blocks"]:
        for ln in b.get("lines", []):
            car = [(c["c"], pymupdf.Rect(c["bbox"])) for s in ln["spans"] for c in s["chars"]]
            if any(not c.isspace() for c, _ in car):
                rez.append({"dir": ln["dir"], "bbox": pymupdf.Rect(ln["bbox"]), "car": car})
    return rez


def _comparabil(car):
    """Textul rândului simplificat și fără spații, plus indicele caracterului original al fiecărei litere."""
    s, idx = [], []
    for i, (c, _) in enumerate(car):
        for x in simplu(c):
            if not x.isspace():
                s.append(x)
                idx.append(i)
    return "".join(s), idx


def _cadru(rand):
    """Limitele rândului în sistemul lui: u de-a lungul textului, v spre rândul următor."""
    dx, dy = rand["dir"]
    r = rand["bbox"]
    u = [x * dx + y * dy for x in (r.x0, r.x1) for y in (r.y0, r.y1)]
    v = [-x * dy + y * dx for x in (r.x0, r.x1) for y in (r.y0, r.y1)]
    return min(u), max(u), min(v), max(v)


def _dedesubt(randuri, cadre, i):
    """Rândurile care pot continua rândul i: aceeași direcție, imediat dedesubt, suprapuse pe lungime."""
    a, (au0, au1, av0, av1) = randuri[i], cadre[i]
    rez = []
    for j, (b, (bu0, bu1, bv0, bv1)) in enumerate(zip(randuri, cadre)):
        h = max(av1 - av0, bv1 - bv0)
        if (j != i and math.dist(a["dir"], b["dir"]) < 0.01 and bv0 >= (av0 + av1) / 2 and bv0 - av1 <= h
                and min(au1, bu1) - max(au0, bu0) > -h):
            rez.append(j)
    return sorted(rez, key=lambda j: cadre[j][2])


def _uneste_dreptunghiuri(rects):
    return _pymupdf().Rect(min(r.x0 for r in rects), min(r.y0 for r in rects),
                           max(r.x1 for r in rects), max(r.y1 for r in rects))


def gaseste(pg, cautat, cuvinte_intregi=False, max_randuri=3):
    """Aparițiile unui text pe pagină, și pe mai multe rânduri (până la max_randuri): [{text, bbox, randuri}].

    Nu contează majusculele, diacriticele și spațiile: „Dormitor2” găsește și „DORMITOR 2”. Cu cuvinte_intregi,
    potrivirea începe și se termină la margine de cuvânt („BAIE 1” nu găsește „BAIE 10”).
    """
    q = "".join(c for c in simplu(cautat) if not c.isspace())
    if not q:
        return []
    randuri = _randuri_text(pg)
    sir = [_comparabil(r["car"]) for r in randuri]
    cadre = [_cadru(r) for r in randuri]
    gasite = {}

    def margine(r, i, pas):
        car = randuri[r]["car"]
        j = i + pas
        return not 0 <= j < len(car) or not car[j][0].isalnum()

    def adauga(bucati):
        (r0, i0, _), (r1, _, i1) = bucati[0], bucati[-1]
        if cuvinte_intregi and not (margine(r0, i0, -1) and margine(r1, i1, 1)):
            return
        dreptunghiuri, texte = [], []
        for r, a, b in bucati:
            parte = randuri[r]["car"][a:b + 1]
            dreptunghiuri += [cb for c, cb in parte if not c.isspace()]
            texte.append("".join(c for c, _ in parte).strip())
        bbox = _uneste_dreptunghiuri(dreptunghiuri)
        text = " / ".join(texte)
        gasite.setdefault((text, tuple(round(v, 1) for v in bbox)), {"text": text, "bbox": bbox,
                                                                      "randuri": len(bucati)})

    def continua(r, gasit, bucati):
        if len(bucati) >= max_randuri:
            return
        rest = q[gasit:]
        for r2 in _dedesubt(randuri, cadre, r):
            s2, idx2 = sir[r2]
            if not s2:
                continue
            if s2.startswith(rest):
                adauga(bucati + [(r2, idx2[0], idx2[len(rest) - 1])])
            elif rest.startswith(s2):
                continua(r2, gasit + len(s2), bucati + [(r2, idx2[0], idx2[-1])])

    for r, (s, idx) in enumerate(sir):
        p = s.find(q)
        while p >= 0:
            adauga([(r, idx[p], idx[p + len(q) - 1])])
            p = s.find(q, p + 1)
        # rândul se termină cu începutul textului căutat: restul poate fi pe rândul de dedesubt
        for p in range(max(0, len(s) - len(q) + 1), len(s)):
            if q.startswith(s[p:]):
                continua(r, len(s) - p, [(r, idx[p], idx[-1])])
    return sorted(gasite.values(), key=lambda g: (round(g["bbox"].y0), g["bbox"].x0))


def cuvinte(pg, zona=None):
    """Cuvintele dintr-o zonă: [(x0, y0, x1, y1, text)], de sus în jos și de la stânga la dreapta."""
    pymupdf = _pymupdf()
    z = zona if zona is not None else intreaga(pg)
    cuv = pg.get_text("words", flags=pymupdf.TEXTFLAGS_WORDS | _cid(), clip=z)
    return sorted(((round(w[0], 2), round(w[1], 2), round(w[2], 2), round(w[3], 2), w[4]) for w in cuv),
                  key=lambda w: (round(w[1]), w[0]))


# ------------------------------------------------------------------ liniile

def _este_alb(culoare):
    return culoare is not None and min(culoare[:3]) > 0.97


def _hexa(culoare):
    return "#" + "".join(f"{round(v * 255):02x}" for v in culoare[:3])


@dataclass
class Segment:
    """Un segment orizontal („H”, la y = c) sau vertical („V”, la x = c), de la a la b pe cealaltă axă, în pt."""
    o: str
    c: float
    a: float
    b: float
    umplere: tuple      # culoarea umplerii desenului din care vine sau None
    contur: tuple       # culoarea conturului sau None
    intrerupt: bool     # linie întreruptă: axe, linii ascunse
    stil: str
    bucati: int = 1     # din câte segmente a fost unit

    @property
    def lungime(self):
        return self.b - self.a

    def din_umplutura(self, cu_albe):
        return self.umplere is not None and (cu_albe or not _este_alb(self.umplere))

    def din_linie(self, cu_albe, cu_intrerupte):
        return (self.contur is not None and (cu_albe or not _este_alb(self.contur))
                and (cu_intrerupte or not self.intrerupt))

    def ca_dict(self):
        return {"orientare": self.o, "c": round(self.c, 2), "de_la": round(self.a, 2), "pana_la": round(self.b, 2),
                "lungime": round(self.lungime, 2), "stil": self.stil, "bucati": self.bucati}

    def descriere(self):
        axa, alta = ("y", "x") if self.o == "H" else ("x", "y")
        unit = f", din {self.bucati} bucăți" if self.bucati > 1 else ""
        return (f"{axa} {_fmt(self.c):>8}   {alta} {_fmt(self.a):>8} … {_fmt(self.b):<8}  {_fmt(self.lungime):>8} pt"
                f"   {self.stil}{unit}")


def segmente(pg, tol=0.05):
    """Segmentele orizontale și verticale din desenele paginii: linii, laturi de dreptunghiuri și patrulatere."""
    pymupdf = _pymupdf()
    rez = []
    for d in pg.get_drawings():
        tip = d.get("type") or ""
        umplere = d.get("fill") if "f" in tip else None
        contur = d.get("color") if "s" in tip else None
        intrerupt = contur is not None and not str(d.get("dashes") or "[]").replace(" ", "").startswith("[]")
        stil = ", ".join(filter(None, [
            f"umplut {_hexa(umplere)}" if umplere is not None else "",
            f"linie {_hexa(contur)} de {_fmt(d.get('width') or 0)} pt" if contur is not None else "",
            "întreruptă" if intrerupt else ""]))
        for it in d["items"]:
            if it[0] == "l":
                perechi = [(it[1], it[2])]
            elif it[0] == "re":
                r = pymupdf.Rect(it[1])
                perechi = [(r.tl, r.tr), (r.tr, r.br), (r.br, r.bl), (r.bl, r.tl)]
            elif it[0] == "qu":
                qd = it[1]
                perechi = [(qd.ul, qd.ur), (qd.ur, qd.lr), (qd.lr, qd.ll), (qd.ll, qd.ul)]
            else:
                continue            # curbele: arcele ușilor, simbolurile
            for p, q in perechi:
                if abs(p.y - q.y) <= tol < abs(p.x - q.x):
                    rez.append(Segment("H", (p.y + q.y) / 2, min(p.x, q.x), max(p.x, q.x), umplere, contur,
                                       intrerupt, stil))
                elif abs(p.x - q.x) <= tol < abs(p.y - q.y):
                    rez.append(Segment("V", (p.x + q.x) / 2, min(p.y, q.y), max(p.y, q.y), umplere, contur,
                                       intrerupt, stil))
    return rez


def alege(segs, din="toate", cu_albe=False, cu_intrerupte=False):
    """Segmentele din umpluturi, din linii trase sau toate. Albele și întreruptele rămân doar la cerere."""
    u, ln = din in ("umpluturi", "toate"), din in ("linii", "toate")
    return [s for s in segs if (u and s.din_umplutura(cu_albe)) or (ln and s.din_linie(cu_albe, cu_intrerupte))]


def fara_dubluri(segs):
    """Același segment desenat de mai multe ori (umplere și contur, straturi suprapuse) rămâne o dată."""
    vazute = {}
    for s in segs:
        vazute.setdefault((s.o, round(s.c, 2), round(s.a, 2), round(s.b, 2)), s)
    return list(vazute.values())


def uneste(segs, tol=0.05):
    """Unește segmentele de pe aceeași dreaptă care se ating sau se suprapun, de exemplu un perete din bucăți."""
    grupe = {}
    for s in segs:
        grupe.setdefault((s.o, round(s.c, 2)), []).append(s)
    rez = []
    for lst in grupe.values():
        lst.sort(key=lambda s: s.a)
        cur = replace(lst[0])
        for s in lst[1:]:
            if s.a <= cur.b + tol:
                cur.b = max(cur.b, s.b)
                cur.bucati += s.bucati
            else:
                rez.append(cur)
                cur = replace(s)
        rez.append(cur)
    return rez


def in_zona(s, z):
    if s.o == "H":
        return z.y0 <= s.c <= z.y1 and s.b >= z.x0 and s.a <= z.x1
    return z.x0 <= s.c <= z.x1 and s.b >= z.y0 and s.a <= z.y1


def linii(pg, zona=None, din="toate", lungime_min=10.0, cu_albe=False, cu_intrerupte=False, unite=False,
          tol=0.05):
    """(orizontale, verticale) dintr-o zonă, fără dubluri: fețele pereților, golurile, liniile de cotă.

    unite=True unește segmentele de pe aceeași dreaptă care se ating (un perete desenat din bucăți).
    """
    z = zona if zona is not None else intreaga(pg)
    segs = fara_dubluri(alege(segmente(pg, tol), din, cu_albe, cu_intrerupte))
    if unite:
        segs = uneste(segs, tol)
    segs = [s for s in segs if s.lungime >= lungime_min and in_zona(s, z)]
    return (sorted((s for s in segs if s.o == "H"), key=lambda s: (s.c, s.a)),
            sorted((s for s in segs if s.o == "V"), key=lambda s: (s.c, s.a)))


# ------------------------------------------------------------------ camera

def _candidati(segs, latura, et, interval, lungime_min):
    """Segmentele lungi de pe o latură a etichetei care se suprapun cu intervalul, de la cel mai apropiat."""
    o = "V" if latura in ("stânga", "dreapta") else "H"
    lim = {"stânga": et.x0, "dreapta": et.x1, "sus": et.y0, "jos": et.y1}[latura]
    semn = -1 if latura in ("stânga", "sus") else 1
    rez = [s for s in segs
           if s.o == o and (s.c - lim) * semn > 0 and s.lungime >= lungime_min
           and min(s.b, interval[1]) - max(s.a, interval[0]) > 1.0]
    return sorted(rez, key=lambda s: (round((s.c - lim) * semn, 2), -s.lungime))


def fete_camera(segs, et, banda=50.0, lungime_min=20.0, iteratii=8):
    """Fețele interioare ale pereților din jurul etichetei: pe fiecare latură, cea mai apropiată linie lungă.

    Prima căutare se face într-o bandă în jurul etichetei. Apoi banda devine camera găsită, ca un gol de ușă sau
    de fereastră din dreptul etichetei să nu trimită căutarea în camera vecină. Întoarce (fețele, candidații).
    """
    bx, by = (et.x0 - banda, et.x1 + banda), (et.y0 - banda, et.y1 + banda)
    for _ in range(iteratii):
        cand = {lat: _candidati(segs, lat, et, by if lat in ("stânga", "dreapta") else bx, lungime_min)
                for lat in LATURI}
        fete = {lat: (c[0] if c else None) for lat, c in cand.items()}
        nbx = (fete["stânga"].c, fete["dreapta"].c) if fete["stânga"] and fete["dreapta"] else bx
        nby = (fete["sus"].c, fete["jos"].c) if fete["sus"] and fete["jos"] else by
        if (nbx, nby) == (bx, by):
            break
        bx, by = nbx, nby
    return fete, cand


def masoara_camera(doc, eticheta, cota_cm=None, cota_pe="x", verifica_cm=None, scara=None, pagina_nr=None, nr=1,
                   din="umpluturi", lungime_min=20.0, banda=50.0, cu_albe=False, tol=0.05):
    """Dimensiunile interioare ale camerei cu eticheta dată, cu scara calibrată pe o cotă scrisă pe plan.

    cota_cm: o cotă scrisă, în cm, pe axa cota_pe („x” orizontal pe foaie, „y” vertical); din ea iese scara reală.
    verifica_cm: a doua cotă scrisă, pe cealaltă axă: cu ea se verifică scara. scara: 1:N din cartuș; fără
    cota_cm o folosești doar provizoriu, iar cu cota_cm afli abaterea față de ea.
    Întoarce un dict: pagina, eticheta, eticheta_bbox (pt), etichete_gasite, fete ({latură: Segment sau None}),
    candidati, gata (toate fețele găsite) și, când sunt: interior_pt, interior_mm_pe_hartie, cm_pe_pt,
    scara_echivalenta (N din 1:N), interior_cm, abatere_fata_de_cartus_pct și verificare (calculat_cm, scris_cm,
    diferenta_cm, diferenta_pct). None dacă nu găsește eticheta.
    """
    pagini = [pagina_nr] if pagina_nr else range(1, doc.page_count + 1)
    etichete = [(n, g) for n in pagini for g in gaseste(pagina(doc, n), eticheta, cuvinte_intregi=True)]
    if not etichete:
        return None
    if not 1 <= nr <= len(etichete):
        raise ValueError(f"am găsit {len(etichete)} etichete „{eticheta}”; nr e între 1 și {len(etichete)}")
    n, et = etichete[nr - 1]
    pg = pagina(doc, n)
    eb = et["bbox"]
    segs = uneste(fara_dubluri(alege(segmente(pg, tol), din, cu_albe)), tol)
    fete, cand = fete_camera(segs, eb, banda, lungime_min)
    rez = {"pagina": n, "eticheta": et["text"], "eticheta_bbox": eb, "etichete_gasite": len(etichete),
           "fete": fete, "candidati": cand, "gata": all(fete.values())}
    if not rez["gata"]:
        return rez
    dx = fete["dreapta"].c - fete["stânga"].c
    dy = fete["jos"].c - fete["sus"].c
    rez["interior_pt"] = (round(dx, 2), round(dy, 2))
    rez["interior_mm_pe_hartie"] = (round(dx * MM_PE_PT, 2), round(dy * MM_PE_PT, 2))
    cm_pe_pt = None
    if cota_cm:
        cm_pe_pt = cota_cm / (dx if cota_pe == "x" else dy)
        rez["scara_din"] = f"cota de {_fmt(cota_cm, 1)} cm pe {cota_pe}"
    elif scara:
        cm_pe_pt = scara * CM_PE_PT
        rez["scara_din"] = f"scara 1:{_fmt(scara, 0)} din cartuș, nesigură"
    if cm_pe_pt:
        rez["cm_pe_pt"] = round(cm_pe_pt, 5)
        rez["scara_echivalenta"] = round(cm_pe_pt / CM_PE_PT, 2)
        rez["interior_cm"] = (round(dx * cm_pe_pt, 1), round(dy * cm_pe_pt, 1))
        if cota_cm and scara:
            rez["abatere_fata_de_cartus_pct"] = round((cm_pe_pt / (scara * CM_PE_PT) - 1) * 100, 2)
        if cota_cm and verifica_cm:
            cealalta = dy * cm_pe_pt if cota_pe == "x" else dx * cm_pe_pt
            rez["verificare"] = {"pe": "y" if cota_pe == "x" else "x", "calculat_cm": round(cealalta, 1),
                                 "scris_cm": verifica_cm, "diferenta_cm": round(cealalta - verifica_cm, 1),
                                 "diferenta_pct": round((cealalta / verifica_cm - 1) * 100, 2)}
    return rez


def imagine_camera(doc, rez, dest, dpi=200):
    """Imaginea de verificare: zona camerei, cu camera găsită în roșu și eticheta în albastru."""
    from PIL import ImageDraw
    pymupdf = _pymupdf()
    pg = pagina(doc, rez["pagina"])
    f = rez["fete"]
    cam = pymupdf.Rect(f["stânga"].c, f["sus"].c, f["dreapta"].c, f["jos"].c)
    eb = rez["eticheta_bbox"]
    img, ox, oy, k = randeaza(pg, _uneste_dreptunghiuri([cam, eb]) + (-25, -25, 25, 25), dpi)
    d = ImageDraw.Draw(img)

    def P(x, y):
        return x * k - ox, y * k - oy

    d.rectangle([P(cam.x0, cam.y0), P(cam.x1, cam.y1)], outline=(230, 0, 0), width=3)
    d.rectangle([P(eb.x0, eb.y0), P(eb.x1, eb.y1)], outline=(0, 90, 230), width=2)
    fnt = _font(16)
    cm = rez.get("interior_cm")
    tx = f"{_fmt(cam.width)} pt" + (f" = {_fmt(cm[0], 1)} cm" if cm else "")
    ty = f"{_fmt(cam.height)} pt" + (f" = {_fmt(cm[1], 1)} cm" if cm else "")
    _scrie(d, *P((cam.x0 + cam.x1) / 2, cam.y0), tx, (200, 0, 0), fnt, "centru")
    _scrie(d, P(cam.x0, 0)[0] + 6, P(0, (cam.y0 + cam.y1) / 2)[1], ty, (200, 0, 0), fnt)
    _salveaza(img, dest)
    return img.size


def _salveaza(img, dest):
    folder = os.path.dirname(os.path.abspath(dest))
    os.makedirs(folder, exist_ok=True)
    img.save(dest)                  # PIL nu scrie metadate dacă nu i le dai
    avertizeaza_daca_nu_e_ignorat(dest)


# ------------------------------------------------------------------ linia de comandă

OPTIUNI = {"--pagina": 1, "--zona": 4, "--px": 1, "--json": 0, "--dpi": 1, "--grila": 1, "--cuvinte-intregi": 0,
           "--din": 1, "--lungime-min": 1, "--cu-albe": 0, "--cu-intrerupte": 0, "--uneste": 0, "--toleranta": 1,
           "--cota-cm": 1, "--cota-pe": 1, "--verifica-cm": 1, "--scara": 1, "--banda": 1, "--nr": 1,
           "--imagine": 1}
COMENZI = {"info": ("PDF-ul",), "randeaza": ("PDF-ul", "imaginea"), "cauta": ("PDF-ul", "textul"),
           "cuvinte": ("PDF-ul",), "linii": ("PDF-ul",), "camera": ("PDF-ul", "eticheta camerei")}


def _argumente(argv):
    """(argumentele poziționale, {opțiune: valoare}); ValueError cu mesaj în română."""
    poz, opt, i = [], {}, 0
    while i < len(argv):
        a = argv[i]
        if not a.startswith("--"):
            poz.append(a)
            i += 1
            continue
        if a not in OPTIUNI:
            raise ValueError(f"opțiune necunoscută: {a}")
        n = OPTIUNI[a]
        vals = argv[i + 1:i + 1 + n]
        if len(vals) < n or any(v.startswith("--") for v in vals):
            raise ValueError(f"{a} cere {n} {'valoare' if n == 1 else 'valori'}")
        opt[a] = True if n == 0 else (vals[0] if n == 1 else vals)
        i += 1 + n
    return poz, opt


def _numar(text, nume):
    try:
        return float(str(text).replace(",", "."))
    except ValueError:
        raise ValueError(f"{nume}: „{text}” nu e un număr") from None


def _json(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=1))


def _lista(r):
    return [round(v, 2) for v in (r.x0, r.y0, r.x1, r.y1)]


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    try:
        cmd, (poz, o) = argv[0], _argumente(argv[1:])
        if cmd not in COMENZI:
            raise ValueError(f"comandă necunoscută: {cmd}; comenzile sunt {', '.join(COMENZI)}")
        if len(poz) != len(COMENZI[cmd]):
            raise ValueError(f"`{cmd}` primește: {' și '.join(COMENZI[cmd])}")
        for k in ("--pagina", "--dpi", "--nr"):
            if k in o:
                if not str(o[k]).isdigit() or int(o[k]) < 1:
                    raise ValueError(f"{k}: „{o[k]}” nu e un număr întreg pozitiv")
                o[k] = int(o[k])
        px = _numar(o["--px"], "--px") if "--px" in o else None
        zona = [_numar(v, "--zona") for v in o["--zona"]] if "--zona" in o else None
        tol = _numar(o.get("--toleranta", 0.05), "--toleranta")
        din = o.get("--din", "umpluturi" if cmd == "camera" else "toate")
        if din not in ("umpluturi", "linii", "toate"):
            raise ValueError("--din e „umpluturi”, „linii” sau „toate”")
        if o.get("--cota-pe", "x") not in ("x", "y"):
            raise ValueError("--cota-pe e „x” sau „y”")
        pg_nr = o.get("--pagina") or (None if cmd in ("cauta", "camera") else 1)
        doc = deschide(poz[0])
        try:
            return _COMENZI[cmd](doc, poz, o, pg_nr, zona, px, tol, din)
        finally:
            doc.close()
    except (ValueError, FileNotFoundError, RuntimeError) as e:
        print(f"eroare: {e}. Vezi: python plan_pdf.py --help", file=sys.stderr)
        return 2


def _cmd_info(doc, poz, o, pg_nr, zona, px, tol, din):
    rez = info(doc)
    if "--json" in o:
        _json(rez)
        return 0
    print(f"Pagini: {rez['pagini']}" + (f" · creat cu: {' / '.join(rez['program'])}" if rez["program"] else ""))
    for p in rez["detalii"]:
        print(f"Pagina {p['pagina']}: {_fmt(p['latime_pt'])} × {_fmt(p['inaltime_pt'])} pt = "
              f"{_fmt(p['latime_mm'], 1)} × {_fmt(p['inaltime_mm'], 1)} mm, {p['format']}, rotație {p['rotatie']}°")
        text = f"  text: {_cate(p['cuvinte'], 'cuvânt', 'cuvinte')}"
        if p["caractere_fara_unicode"]:
            text += (f"; {_cate(p['caractere_fara_unicode'], 'caracter', 'caractere')} din fonturi fără Unicode "
                     "(fără tabel ToUnicode), citite cu TEXT_CID_FOR_UNKNOWN_UNICODE")
        print(text)
        print(f"  desene: {p['desene']} (cu umplere {p['cu_umplere']}, cu contur {p['cu_contur']})")
        if p["rotatie"]:
            print("  Atenție: pagina e rotită. Toate comenzile folosesc coordonatele paginii nerotite.")
    return 0


def _cmd_randeaza(doc, poz, o, pg_nr, zona, px, tol, din):
    pg = pagina(doc, pg_nr)
    z = dreptunghi(zona, px, pg)
    dpi = int(o.get("--dpi", 150))
    img, ox, oy, k = randeaza(pg, z, dpi)
    if "--grila" in o:
        grila(img, ox, oy, k, z, _numar(o["--grila"], "--grila"))
    _salveaza(img, poz[1])
    print(f"salvat {os.path.basename(poz[1])}: {img.width} × {img.height} px, zona {_fmt(z.x0)} {_fmt(z.y0)} "
          f"{_fmt(z.x1)} {_fmt(z.y1)} pt, la {dpi} dpi")
    print(f"Pixelul (px, py) e în pt la x = (px + {ox}) × 72/{dpi}, y = (py + {oy}) × 72/{dpi}.")
    return 0


def _cmd_cauta(doc, poz, o, pg_nr, zona, px, tol, din):
    rez = []
    for n in [pg_nr] if pg_nr else range(1, doc.page_count + 1):
        pg = pagina(doc, n)
        z = dreptunghi(zona, px, pg) if zona else None
        rez += [{"pagina": n, **g} for g in gaseste(pg, poz[1], "--cuvinte-intregi" in o)
                if z is None or z.intersects(g["bbox"])]
    if "--json" in o:
        _json([{"pagina": g["pagina"], "text": g["text"], "bbox": _lista(g["bbox"]), "randuri": g["randuri"]}
               for g in rez])
        return 0 if rez else 1
    if not rez:
        print(f"Nu am găsit „{poz[1]}”.")
        return 1
    print(f"„{poz[1]}”: {_cate(len(rez), 'apariție', 'apariții')} (dreptunghiul în pt)")
    for g in rez:
        b = g["bbox"]
        print(f"  pagina {g['pagina']}: x {_fmt(b.x0)} … {_fmt(b.x1)}, y {_fmt(b.y0)} … {_fmt(b.y1)}, "
              f"centrul {_fmt((b.x0 + b.x1) / 2)} {_fmt((b.y0 + b.y1) / 2)}  „{g['text']}”")
    return 0


def _cmd_cuvinte(doc, poz, o, pg_nr, zona, px, tol, din):
    pg = pagina(doc, pg_nr)
    z = dreptunghi(zona, px, pg)
    cuv = cuvinte(pg, z)
    if "--json" in o:
        _json([{"text": w[4], "bbox": list(w[:4])} for w in cuv])
        return 0
    print(f"{_cate(len(cuv), 'cuvânt', 'cuvinte')} în zona {_fmt(z.x0)} {_fmt(z.y0)} {_fmt(z.x1)} {_fmt(z.y1)} pt")
    print(f"{'x0':>7} {'y0':>7} {'x1':>7} {'y1':>7}  text")
    for w in cuv:
        print(f"{_fmt(w[0], 1):>7} {_fmt(w[1], 1):>7} {_fmt(w[2], 1):>7} {_fmt(w[3], 1):>7}  {w[4]}")
    return 0


def _cmd_linii(doc, poz, o, pg_nr, zona, px, tol, din):
    pg = pagina(doc, pg_nr)
    oriz, vert = linii(pg, dreptunghi(zona, px, pg), din, _numar(o.get("--lungime-min", 10.0), "--lungime-min"),
                       "--cu-albe" in o, "--cu-intrerupte" in o, "--uneste" in o, tol)
    if "--json" in o:
        _json({"orizontale": [s.ca_dict() for s in oriz], "verticale": [s.ca_dict() for s in vert]})
        return 0
    print(f"Orizontale: {len(oriz)} (y; capetele pe x; lungimea; stilul)")
    for s in oriz:
        print("  " + s.descriere())
    print(f"Verticale: {len(vert)} (x; capetele pe y; lungimea; stilul)")
    for s in vert:
        print("  " + s.descriere())
    return 0


def _cmd_camera(doc, poz, o, pg_nr, zona, px, tol, din):
    def nr(k):
        return _numar(o[k], k) if k in o else None

    rez = masoara_camera(doc, poz[1], nr("--cota-cm"), o.get("--cota-pe", "x"), nr("--verifica-cm"), nr("--scara"),
                         pg_nr, int(o.get("--nr", 1)), din, nr("--lungime-min") or 20.0, nr("--banda") or 50.0,
                         "--cu-albe" in o, tol)
    if rez is None:
        print(f"Nu găsesc eticheta „{poz[1]}”. Caută o parte din ea cu `cauta`.")
        return 1
    if rez["gata"] and "--imagine" in o:
        imagine_camera(doc, rez, o["--imagine"], int(o.get("--dpi", 200)))
        rez["imagine"] = os.path.basename(o["--imagine"])
    if "--json" in o:
        iesire = dict(rez, eticheta_bbox=_lista(rez["eticheta_bbox"]),
                      fete={k: (s.ca_dict() if s else None) for k, s in rez["fete"].items()},
                      candidati={k: [s.ca_dict() for s in c[:4]] for k, c in rez["candidati"].items()})
        _json(iesire)
        return 0 if rez["gata"] else 1
    eb, fete = rez["eticheta_bbox"], rez["fete"]
    if rez["etichete_gasite"] > 1:
        print(f"Am găsit {rez['etichete_gasite']} etichete „{poz[1]}”; folosesc a {o.get('--nr', 1)}-a (alta: --nr).")
    print(f"Eticheta „{rez['eticheta']}”, pagina {rez['pagina']}: x {_fmt(eb.x0)} … {_fmt(eb.x1)}, "
          f"y {_fmt(eb.y0)} … {_fmt(eb.y1)} pt")
    print(f"Fețele interioare ale pereților (din segmentele: {din}):")
    for lat in LATURI:
        print(f"  {lat:<8} " + (fete[lat].descriere() if fete[lat] else "negăsită"))
    if not rez["gata"]:
        print("Nu am găsit toate fețele. Încearcă `--din toate`, o `--banda` mai mare sau o `--lungime-min` mai mică "
              "și verifică zona cu `linii`.")
        return 1
    dx, dy = rez["interior_pt"]
    print(f"Interior: {_fmt(dx)} pt pe x × {_fmt(dy)} pt pe y "
          f"({_fmt(rez['interior_mm_pe_hartie'][0])} × {_fmt(rez['interior_mm_pe_hartie'][1])} mm pe hârtie)")
    if "cm_pe_pt" in rez:
        print(f"Scara: {rez['scara_din']} → 1 pt = {_fmt(rez['cm_pe_pt'], 4)} cm, adică "
              f"1:{_fmt(rez['scara_echivalenta'], 1)} pe hârtie")
        if "abatere_fata_de_cartus_pct" in rez:
            print(f"  Față de scara din cartuș (1:{_fmt(nr('--scara'), 0)}): "
                  f"{rez['abatere_fata_de_cartus_pct']:+.2f} %".replace(".", ","))
        print(f"Camera: {_fmt(rez['interior_cm'][0], 1)} cm pe x × {_fmt(rez['interior_cm'][1], 1)} cm pe y")
        v = rez.get("verificare")
        if v:
            print(f"Verificare pe {v['pe']}: ies {_fmt(v['calculat_cm'], 1)} cm, cota scrisă e "
                  f"{_fmt(v['scris_cm'], 1)} cm → diferență {v['diferenta_cm'] + 0.0:+.1f} cm "
                  f"({v['diferenta_pct'] + 0.0:+.2f} %)".replace(".", ","))
    else:
        print("Pentru cote în cm dai --cota-cm (o cotă scrisă pe plan); scara din cartuș (--scara) nu e sigură.")
    print("Următorii candidați, de la cel mai apropiat (verifică să fie pereți, nu mobilier sau linii de cotă):")
    for lat in LATURI:
        vazute, rest = {round(fete[lat].c, 2)}, []
        for s in rez["candidati"][lat]:
            if round(s.c, 2) not in vazute and len(rest) < 2:
                vazute.add(round(s.c, 2))
                rest.append(s)
        if rest:
            print(f"  {lat:<8} " + " · ".join(f"{_fmt(s.c)} ({_fmt(s.lungime)} pt, {s.stil})" for s in rest))
    if "imagine" in rez:
        print(f"Imaginea de verificare: {rez['imagine']} (camera în roșu, eticheta în albastru)")
    return 0


_COMENZI = {"info": _cmd_info, "randeaza": _cmd_randeaza, "cauta": _cmd_cauta, "cuvinte": _cmd_cuvinte,
            "linii": _cmd_linii, "camera": _cmd_camera}


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
