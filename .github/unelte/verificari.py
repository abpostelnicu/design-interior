"""Verificările unui proiect înainte de commit: livrabilele, metadatele, linkurile, textele și calculele.

    python .github/unelte/verificari.py "Cuier hol"              # un proiect (folderul lui din rădăcină)
    python .github/unelte/verificari.py --toate                  # toate proiectele
    python .github/unelte/verificari.py --strict "Cuier hol"     # și avertismentele dau codul 1

Iese cu codul 1 la PROBLEME. AVERTISMENTELE doar le afișează: te uiți la fiecare și decizi.

Variantele în plus pentru același proiect (C și D după A și B) stau în folderul lui, cu fișiere noi, cu sufix:
`propunere_C_beton_gri.jpg`, `comparatie_acum_vs_propuneri_beton.jpg`, `lista_materiale_beton.md`,
`plan_tehnic_polite_viniluri_beton.pdf`. Verificarea le ia și pe ele. Sursele lor stau într-un subfolder al surselor
proiectului (`.github/surse/polite-viniluri/beton/`) și se verifică odată cu restul surselor.

PROBLEME:
- lipsește un livrabil: README.md, lista_materiale.md, comparatie_acum_vs_propuneri.jpg, propunere_A_*.jpg,
  varianta_B_*.jpg, plan_tehnic_*.pdf și plan_tehnic_*.png, sau un plan are doar PDF ori doar PNG;
- o imagine din proiect sau din surse are metadate (EXIF, mai ales GPS), ori un plan PDF nu e A3;
- un link relativ din Markdown duce la un fișier sau la o ancoră (#titlu) care nu există;
- litere cu sedilă (ş, ţ) în loc de virgulă (ș, ț);
- căi absolute de pe calculator (/Users/…, /home/…, C:\\Users\\…) sau coordonate GPS, în texte și în surse;
- în fiecare listă de materiale (`lista_materiale*.md`): Cant. × Preț ≠ Subtotal, un total care nu se adună,
  lipsa datei verificării;
- README-ul din rădăcină nu are link spre proiect.

AVERTISMENTE: pașii de montaj nenumerotați la rând („### 1.”, „### 2.”…), punct zecimal înaintea unei unități
(„2.5 cm”), adrese de email care nu sunt „noreply”, numere de telefon sau de înmatriculare, secțiuni lipsă din
README, un fișier din folderul proiectului fără link în README, valori din tabelul final care nu apar ca total,
lipsa surselor din `.github/surse/<proiect>/`.
"""
import os
import re
import sys
import unicodedata
from urllib.parse import unquote

from PIL import Image

RADACINA = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IMAGINI = (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".heic")
TEXTE = (".md", ".py", ".json", ".txt", ".yml", ".yaml", ".html", ".csv")
SECTIUNI = ("Conținutul folderului", "Cote măsurate", "Montaj pas cu pas", "Întreținere")
SP = "[ \u00a0\u202f\u2009]"
SUMA = re.compile(rf"(?<![\d,.])(\d{{1,3}}(?:{SP}\d{{3}})+|\d+)(?:,(\d+))?(?={SP}*lei)")
NUMERE = re.compile(rf"\d{{1,3}}(?:{SP}\d{{3}})+(?:,\d+)?|\d+(?:[.,]\d+)?")
PROZA = (".md", ".txt", ".html", ".yml", ".yaml")
JUDETE = ("AB|AG|AR|BC|BH|BN|BR|BT|BV|BZ|CJ|CL|CS|CT|CV|DB|DJ|GJ|GL|GR|HD|HR|IF|IL|IS|MH|MM|MS|NT|OT|PH|SB|SJ|SM|"
          "SV|TL|TM|TR|VL|VN|VS|B")
CAI_ABSOLUTE = re.compile(r"(?<![\w.])(/Users/|/home/|/workspaces/|/root/|/private/var/|[A-Za-z]:\\\\?Users|file://)")
GPS = re.compile(r"(?<![\d.])-?\d{1,2}\.\d{4,}\s*[,;]\s*-?\d{1,3}\.\d{4,}(?![\d.])|\d{1,2}°\s?\d{1,2}['′]\s?\d")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
TELEFON = re.compile(r"(?<![\d.,])(?:\+40|0040|0)\s?7\d{2}[\s.-]?\d{3}[\s.-]?\d{3}(?!\d)")
NUMAR_AUTO = re.compile(rf"\b(?:{JUDETE})[ -]?\d{{2,3}}[ -]?[A-Z]{{3}}\b")
PUNCT_ZECIMAL = re.compile(r"(?<![\w.,])\d+\.\d+\s?(?:cm|mm|m|kg|lei|kN|MPa|ml|l)\b")
URL = re.compile(r"https?://[^\s)>\]\"']+")


class Raport:
    def __init__(self):
        self.probleme, self.avertismente, self.ok = [], [], []

    def problema(self, loc, mesaj):
        self.probleme.append(f"{loc}: {mesaj}" if loc else mesaj)

    def avertisment(self, loc, mesaj):
        self.avertismente.append(f"{loc}: {mesaj}" if loc else mesaj)


def rel(path):
    return os.path.relpath(path, RADACINA)


def numar_de(n, unu, mai_multe):
    """Numărul cu substantivul acordat: „1 rând”, „2 rânduri”, „21 de rânduri”, „101 rânduri”."""
    if n == 1:
        return f"1 {unu}"
    return f"{n} {'de ' if n and (n % 100 == 0 or n % 100 >= 20) else ''}{mai_multe}"


def slug(nume):
    """„Polite viniluri” -> „polite-viniluri”: numele folderului de surse."""
    s = unicodedata.normalize("NFKD", nume).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def proiecte():
    """Folderele din rădăcină care au README.md și lista_materiale.md."""
    out = []
    for d in sorted(os.listdir(RADACINA)):
        p = os.path.join(RADACINA, d)
        if d[0] in "._" or not os.path.isdir(p):
            continue
        if os.path.isfile(os.path.join(p, "README.md")) and os.path.isfile(os.path.join(p, "lista_materiale.md")):
            out.append(d)
    return out


def fisiere(folder, ext):
    out = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in ("out", ".venv", "__pycache__", ".git")]
        out += [os.path.join(root, f) for f in sorted(files) if f.lower().endswith(ext)]
    return out


# ------------------------------------------------------------------ fișiere

def verifica_livrabile(folder, rap):
    nume = os.listdir(folder)
    cerute = [("README.md", lambda n: n == "README.md"),
              ("lista_materiale.md", lambda n: n == "lista_materiale.md"),
              ("comparatie_acum_vs_propuneri.jpg", lambda n: n == "comparatie_acum_vs_propuneri.jpg"),
              ("propunere_A_<material>.jpg", lambda n: re.fullmatch(r"propunere_A_\w+\.jpg", n)),
              ("varianta_B_<material>.jpg", lambda n: re.fullmatch(r"varianta_B_\w+\.jpg", n)),
              ("plan_tehnic_<proiect>.pdf", lambda n: re.fullmatch(r"plan_tehnic_\w+\.pdf", n)),
              ("plan_tehnic_<proiect>.png", lambda n: re.fullmatch(r"plan_tehnic_\w+\.png", n))]
    gasite = 0
    for eticheta, test in cerute:
        if any(test(n) for n in nume):
            gasite += 1
        else:
            rap.problema(rel(folder), f"lipsește {eticheta}")
    rap.ok.append(f"{gasite} din {len(cerute)} livrabile")
    planuri = sorted({n[:-4] for n in nume if re.fullmatch(r"plan_tehnic_\w+\.(?:pdf|png)", n)})
    for plan in planuri:
        for ext in (".pdf", ".png"):
            if plan + ext not in nume:
                rap.problema(rel(folder), f"lipsește {plan}{ext}: fiecare plan se publică în PDF și în PNG")


def metadate(path):
    """(câmpuri EXIF, are GPS, alte blocuri de metadate)."""
    with Image.open(path) as im:
        ex = im.getexif()
        gps = bool(ex) and (0x8825 in ex or bool(ex.get_ifd(0x8825)))
        altele = sorted(k for k in im.info if k.lower() in ("exif", "xmp", "xml:com.adobe.xmp", "comment", "iptc",
                                                             "photoshop"))
    return len(ex), gps, altele


def verifica_imagini(foldere, rap):
    n = 0
    for folder in foldere:
        for p in fisiere(folder, IMAGINI):
            n += 1
            try:
                nex, gps, altele = metadate(p)
            except Exception as e:
                rap.problema(rel(p), f"nu se poate deschide ({type(e).__name__})")
                continue
            if gps:
                rap.problema(rel(p), "are coordonate GPS în EXIF: salveaz-o din nou cu `foto.py pregateste`")
            elif nex or altele:
                detalii = ", ".join([f"EXIF {nex} câmpuri"] * bool(nex) + altele)
                rap.problema(rel(p), f"are metadate ({detalii}): salveaz-o din nou cu `foto.py pregateste`")
    rap.ok.append(f"{numar_de(n, 'imagine', 'imagini')} fără metadate" if n else "nicio imagine")


def dimensiuni_pdf(path):
    with open(path, "rb") as f:
        data = f.read()
    m = re.search(rb"/MediaBox\s*\[\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\]", data)
    if not m:
        return None
    x0, y0, x1, y1 = (float(v) for v in m.groups())
    return (x1 - x0) * 25.4 / 72, (y1 - y0) * 25.4 / 72


def verifica_pdf(folder, rap):
    for p in fisiere(folder, (".pdf",)):
        d = dimensiuni_pdf(p)
        if d is None:
            rap.problema(rel(p), "nu găsesc mărimea paginii (/MediaBox)")
        elif not (abs(max(d) - 420) < 1 and abs(min(d) - 297) < 1):
            rap.problema(rel(p), f"pagina are {d[0]:.0f} × {d[1]:.0f} mm, nu A3 (420 × 297 mm)")
        else:
            rap.ok.append(f"{os.path.basename(p)} e A3")


# ------------------------------------------------------------------ Markdown

def linii_fara_cod(text):
    """Liniile textului, cu blocurile de cod și `codul` din rând golite (numerotarea liniilor rămâne)."""
    out, fence = [], None
    for line in text.split("\n"):
        m = re.match(r"\s*(```|~~~)", line)
        if m:
            fence = None if fence == m.group(1) else (fence or m.group(1))
            out.append("")
            continue
        out.append("" if fence else re.sub(r"`[^`]*`", "", line))
    return out


def ancora(titlu):
    """Ancora unui titlu, ca pe GitHub și pe site (kramdown GFM): litere mici, fără punctuație, spații -> „-”."""
    t = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", titlu)
    t = re.sub(r"<[^>]+>", "", t).replace("*", "").replace("`", "")
    t = re.sub(r"\s*\{#[^}]*\}\s*$", "", t)
    t = re.sub(r"[^\w\- \t]", "", t.strip().lower())
    return re.sub(r"[ \t]", "-", t)


def ancore(text):
    vazute, out = {}, set()
    for line in linii_fara_cod(text):
        m = re.match(r"\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$", line)
        if m:
            a = ancora(m.group(1))
            k = vazute.get(a, 0)
            vazute[a] = k + 1
            out.add(a if k == 0 else f"{a}-{k}")
            e = re.search(r"\{#([^}]+)\}\s*$", m.group(1))
            if e:
                out.add(e.group(1))
    out.update(re.findall(r"\b(?:id|name)\s*=\s*[\"']([^\"']+)[\"']", text))
    return out


def linkuri(text):
    """(linia, ținta) pentru linkurile și imaginile din Markdown și HTML, fără cele din blocurile de cod."""
    for i, line in enumerate(linii_fara_cod(text), 1):
        for m in re.finditer(r"!?\[[^\]]*\]\(\s*(<[^>]+>|[^)\s]+)(?:\s+\"[^\"]*\")?\s*\)", line):
            yield i, m.group(1).strip("<>")
        for m in re.finditer(r"\b(?:src|href)\s*=\s*[\"']([^\"']+)[\"']", line):
            yield i, m.group(1)
        m = re.match(r"\s{0,3}\[[^\]]+\]:\s*(\S+)", line)
        if m:
            yield i, m.group(1).strip("<>")


def verifica_linkuri(md, rap, cache):
    with open(md, encoding="utf-8") as f:
        text = f.read()
    n = 0
    for i, tinta in linkuri(text):
        if re.match(r"(https?:|mailto:|tel:|//|\{\{)", tinta):
            continue
        n += 1
        loc = f"{rel(md)}:{i}"
        cale, _, frag = tinta.partition("#")
        if cale.startswith("/"):
            rap.avertisment(loc, f"link absolut {tinta!r}: pe site, proiectul nu e la rădăcina domeniului; "
                                 "folosește un link relativ")
            continue
        dest = os.path.normpath(os.path.join(os.path.dirname(md), unquote(cale))) if cale else md
        if not os.path.exists(dest):
            rap.problema(loc, f"linkul {tinta!r} duce la un fișier care nu există")
            continue
        if frag and dest.endswith(".md"):
            if dest not in cache:
                with open(dest, encoding="utf-8") as f:
                    cache[dest] = ancore(f.read())
            if unquote(frag) not in cache[dest]:
                rap.problema(loc, f"ancora #{frag} nu există în {os.path.basename(dest)}")
    return n


def verifica_texte(paths, rap):
    for p in paths:
        try:
            with open(p, encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            rap.problema(rel(p), "nu e UTF-8")
            continue
        md = p.endswith(".md")
        linii = linii_fara_cod(text) if md else text.split("\n")
        brute = text.split("\n")
        for i, line in enumerate(brute, 1):
            loc = f"{rel(p)}:{i}"
            if re.search("[şţŞŢ]", line):
                rap.problema(loc, "litere cu sedilă (ş, ţ); se scriu cu virgulă: ș, ț")
            fara_url = URL.sub(" ", line)
            if CAI_ABSOLUTE.search(fara_url):
                rap.problema(loc, f"cale absolută de pe calculator: {CAI_ABSOLUTE.search(fara_url).group(0)}…")
            if p.endswith(PROZA) and GPS.search(fara_url):       # în .json/.py, perechile de numere sunt pixeli
                rap.problema(loc, f"pare o coordonată GPS: {GPS.search(fara_url).group(0)}")
            for e in EMAIL.findall(fara_url):
                if not e.lower().endswith("noreply.github.com"):
                    rap.avertisment(loc, f"adresă de email: {e}")
            if TELEFON.search(fara_url):
                rap.avertisment(loc, f"pare un număr de telefon: {TELEFON.search(fara_url).group(0)}")
            if NUMAR_AUTO.search(fara_url):
                rap.avertisment(loc, f"pare un număr de înmatriculare: {NUMAR_AUTO.search(fara_url).group(0)}")
            if md and PUNCT_ZECIMAL.search(URL.sub(" ", linii[i - 1])):
                rap.avertisment(loc, f"punct zecimal: {PUNCT_ZECIMAL.search(URL.sub(' ', linii[i - 1])).group(0)!r}; "
                                     "în română se scrie cu virgulă")


def verifica_readme(folder, proiect, rap):
    md = os.path.join(folder, "README.md")
    if not os.path.isfile(md):
        return
    with open(md, encoding="utf-8") as f:
        text = f.read()
    linii = linii_fara_cod(text)
    titluri = [re.sub(r"^#+\s*", "", ln).strip() for ln in linii if re.match(r"#{1,6}\s", ln)]
    for s in SECTIUNI:
        if not any(t.lower().startswith(s.lower()) for t in titluri):
            rap.avertisment(rel(md), f"lipsește secțiunea „{s}” (tiparul de README din memorie)")
    tinte = {unquote(t.partition("#")[0]) for _, t in linkuri(text)}
    for n in sorted(os.listdir(folder)):
        if n != "README.md" and n[0] not in "._" and os.path.isfile(os.path.join(folder, n)) and n not in tinte:
            rap.avertisment(rel(md), f"nu are link spre {n}: fiecare fișier din folder apare în README")
    prev = 0
    for i, ln in enumerate(linii, 1):
        m = re.match(r"###\s+(\d+)\.", ln)
        if m:
            k = int(m.group(1))
            if k != prev + 1 and k != 1:
                rap.avertisment(f"{rel(md)}:{i}", f"pasul {k} vine după pasul {prev}")
            prev = k


def verifica_radacina(proiect, rap):
    md = os.path.join(RADACINA, "README.md")
    with open(md, encoding="utf-8") as f:
        text = f.read()
    tinte = [unquote(t).rstrip("/") for _, t in linkuri(text)]
    if not any(t == proiect or t.startswith(proiect + "/") for t in tinte):
        rap.problema("README.md", f"nu are link spre proiectul „{proiect}” (tabelul de proiecte)")


# ------------------------------------------------------------------ lista de materiale

def suma(cell):
    """(valoarea în lei, aproximativă) dintr-o celulă: „19,49 lei/buc”, „**1 065 lei**”, „≈ 440 lei”; altfel None."""
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", cell.replace("**", ""))
    found = SUMA.findall(t)
    if len(found) != 1 or len(NUMERE.findall(t)) != 1:      # „145 sau 205 lei” e ambiguu
        return None
    intreg, zec = found[0]
    v = float(re.sub(SP, "", intreg) + ("." + zec if zec else ""))
    return v, bool(re.search(r"[≈~]|aprox|circa|\bcca\b", t, re.I))


def cantitate(cell):
    t = cell.replace("**", "").strip()
    m = re.fullmatch(r"(\d+(?:,\d+)?)(?:\s*(?:buc|bucăți|m|ml|mp|m²|set|seturi|kg|l|cutii|cutie|role|rolă))?\.?", t)
    return float(m.group(1).replace(",", ".")) if m else None


def tabele(text):
    """[(linia de început, cap de tabel, [(linia, celule)])] pentru tabelele Markdown."""
    out, cur = [], None
    for i, line in enumerate(linii_fara_cod(text), 1):
        if line.lstrip().startswith("|"):
            raw = line.strip().replace("\\|", "\x00")[1:]
            raw = raw[:-1] if raw.endswith("|") else raw
            cells = [c.strip().replace("\x00", "|") for c in raw.split("|")]
            if cur is None:
                cur = (i, [c.lower() for c in cells], [])
                out.append(cur)
            elif not all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                cur[2].append((i, cells))
        else:
            cur = None
    return out


def _lei(v):
    return f"{v:,.2f}".replace(",", " ").replace(".", ",")


def _col(cap, *prefixe, exact=False):
    def ok(c, p):
        c = c.replace("*", "").strip()
        return c == p if exact else c.startswith(p)
    return next((k for k, c in enumerate(cap) if any(ok(c, p) for p in prefixe)), None)


def liste_materiale(folder):
    """`lista_materiale.md` și listele variantelor în plus (`lista_materiale_<sufix>.md`) din folderul proiectului."""
    return sorted(n for n in os.listdir(folder) if re.fullmatch(r"lista_materiale(?:_\w+)?\.md", n))


def verifica_lista(folder, rap):
    for nume in liste_materiale(folder):
        verifica_o_lista(os.path.join(folder, nume), rap)


def verifica_o_lista(md, rap):
    with open(md, encoding="utf-8") as f:
        text = f.read()
    r = rel(md)
    eticheta = "lista de materiale" if os.path.basename(md) == "lista_materiale.md" else os.path.basename(md)
    if not re.search(r"verificat\w*[^\n]{0,80}?\d{1,2}(?:\s*[–-]\s*\d{1,2})?\.\d{1,2}\.\d{4}", text, re.I):
        rap.problema(r, "nu scrie când au fost verificate prețurile (de exemplu „verificate pe 30.10.2026”)")
    randuri = totaluri = 0
    valori_total = []
    finale = []
    for start, cap, rows in tabele(text):
        ic, ip, isub = _col(cap, "cant"), _col(cap, "preț", "pret"), _col(cap, "subtotal")
        ice, icat = _col(cap, "ce", exact=True), _col(cap, "cât", "cat", exact=True)
        if None not in (ic, ip, isub):
            acc, complet = 0.0, True
            for i, cells in rows:
                if len(cells) <= max(ic, ip, isub):
                    continue
                if any("total" in c.lower() for c in cells[:isub]):
                    s = suma(cells[isub])
                    if s is None:
                        continue
                    totaluri += 1
                    valori_total.append(s[0])
                    if not complet:
                        rap.avertisment(f"{r}:{i}", "totalul nu se poate verifica: un rând de deasupra n-are subtotal")
                        continue
                    tol = max(1.0, 0.01 * s[0]) if s[1] else 0.011
                    if abs(acc - s[0]) > tol:
                        rap.problema(f"{r}:{i}", f"totalul e {_lei(s[0])} lei, dar subtotalurile dau {_lei(acc)} lei")
                    continue
                q, p, s = cantitate(cells[ic]), suma(cells[ip]), suma(cells[isub])
                if s is None:
                    complet = False
                    continue
                acc += s[0]
                if q is not None and p is not None:
                    randuri += 1
                    tol = max(1.0, 0.01 * s[0]) if (s[1] or p[1]) else 0.011
                    if abs(q * p[0] - s[0]) > tol:
                        rap.problema(f"{r}:{i}", f"{q:g} × {_lei(p[0])} = {_lei(q * p[0])} lei, dar subtotalul e "
                                                 f"{_lei(s[0])} lei")
        elif ice is not None and icat is not None:
            finale.append((ice, icat, rows))
    for ice, icat, rows in finale:
        acc, complet = 0.0, True
        for i, cells in rows:
            if len(cells) <= max(ice, icat):
                continue
            s = suma(cells[icat])
            if "total" in cells[ice].lower():
                if s is None:
                    continue
                totaluri += 1
                if not complet:
                    rap.avertisment(f"{r}:{i}", "totalul nu se poate verifica: un rând de deasupra n-are o sumă clară")
                elif abs(acc - s[0]) > (max(1.0, 0.01 * s[0]) if s[1] else 0.011):
                    rap.problema(f"{r}:{i}", f"totalul e {_lei(s[0])} lei, dar rândurile de deasupra dau {_lei(acc)} lei")
                continue
            if s is None:
                complet = False
                continue
            acc += s[0]
            if valori_total and not any(abs(s[0] - v) < 0.011 for v in valori_total):
                rap.avertisment(f"{r}:{i}", f"{_lei(s[0])} lei nu apare ca total în tabelele de mai sus")
    rap.ok.append(f"{eticheta}: {numar_de(randuri, 'rând', 'rânduri')} și "
                  f"{numar_de(totaluri, 'total', 'totaluri')} verificate")


# ------------------------------------------------------------------ proiectul

def verifica(proiect):
    rap = Raport()
    folder = os.path.join(RADACINA, proiect)
    if not os.path.isdir(folder):
        rap.problema(proiect, "folderul nu există în rădăcina depozitului")
        return rap, None
    surse = os.path.join(RADACINA, ".github", "surse", slug(proiect))
    if not os.path.isdir(surse):
        rap.avertisment(rel(surse), "lipsesc sursele care generează imaginile (tiparul: .github/surse/<proiect>/)")
        surse = None
    elif not os.path.isfile(os.path.join(surse, "README.md")):
        rap.avertisment(rel(surse), "sursele nu au README.md")
    verifica_livrabile(folder, rap)
    verifica_imagini([folder] + ([surse] if surse else []), rap)
    verifica_pdf(folder, rap)
    cache, n = {}, 0
    for md in fisiere(folder, (".md",)) + (fisiere(surse, (".md",)) if surse else []):
        n += verifica_linkuri(md, rap, cache)
    rap.ok.append(numar_de(n, "link relativ", "linkuri relative"))
    verifica_texte(fisiere(folder, TEXTE) + (fisiere(surse, TEXTE) if surse else []), rap)
    verifica_readme(folder, proiect, rap)
    verifica_lista(folder, rap)
    verifica_radacina(proiect, rap)
    return rap, surse


def main(argv):
    strict = "--strict" in argv
    argv = [a for a in argv if a != "--strict"]
    if not argv or argv == ["--toate"]:
        lista = proiecte()
    elif argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    else:
        lista = [a.rstrip("/") for a in argv]
    total_p = total_a = 0
    for proiect in lista:
        rap, surse = verifica(proiect)
        print(f"Proiectul „{proiect}”" + (f" (sursele: {rel(surse)})" if surse else ""))
        for p in rap.probleme:
            print("  PROBLEMĂ    ", p)
        for a in rap.avertismente:
            print("  avertisment ", a)
        print("  ok:", "; ".join(rap.ok))
        total_p += len(rap.probleme)
        total_a += len(rap.avertismente)
    print(f"probleme: {total_p} · avertismente: {total_a}")
    return 1 if total_p or (strict and total_a) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
