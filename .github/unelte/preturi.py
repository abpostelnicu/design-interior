"""Prețurile din magazinele online: citește pagina produsului și scoate prețul, moneda, titlul și ambalajul.

    python preturi.py <url> [<url> ...]          # câte un rând pe link, cu data verificării
    python preturi.py --json <url> [...]         # același lucru, ca JSON
    python preturi.py --lista "<Proiect>/lista_materiale.md"   # toate linkurile din listă, cu prețul din ea
    python preturi.py --foaie out/foaie_comode.jpg <link sau cale> [...] [linkuri.txt]   # foaia de produse

Prețul se caută, în ordine, în: microdata (`itemprop="price"`), Open Graph (`product:price:amount`) și JSON-LD
(`"price"`). La Dedeman, prețul afișat poate fi pe cutie: caută „Se livrează la: cutie (N buc)” și calculezi
cantitatea pe cutii.

Stările unui link:
- ok: prețul a fost găsit;
- fara_pret: pagina s-a încărcat, dar nu are prețul în cod; îl verifici în browser;
- blocat: magazinul refuză cererile automate (Hornbach, MatHaus și Leroy Merlin fac asta mereu). Atunci deschizi
  pagina cu unealta playwright sau ceri prețul utilizatorului; nu-l ghicești și nu-l copiezi din altă parte;
- eroare: rețeaua sau adresa (DNS, timp depășit, 404). Nu înseamnă că magazinul blochează.

Rândul spune „folosește browserul” când pagina cere o verificare anti-robot (Cloudflare: „Just a moment...”, cod
403) sau se construiește din JavaScript, deci are prea puțin text fără preț: așa e BoConcept România. Câmpul
„prp” e prețul recomandat de producător, scris în pagină (la Cioata: „Pret recomandat producator (PRP): 4876”);
nu e neapărat prețul de vânzare.

Foaia de produse (`--foaie`, funcția `foaie`) pune pozele produselor una lângă alta, cu eticheta sub fiecare, ca
să compari modele, finisaje și desene cotate. Sursele sunt linkuri spre imagini, căi de pe disc sau un fișier
`.txt` cu câte o sursă pe rând, cu eticheta înainte: `NO Natural Oak https://...`. Imaginile descărcate rămân
lângă foaie, în folderul cu numele ei. Pozele produselor au drepturi de autor: foaia rămâne în `out/`.

Înainte să trimiți subagenți de cercetare, rulezi scriptul o dată, pe un link: afli din prima ce merge din mediul
de lucru. În lista de materiale treci prețul cu virgulă zecimală („19,49 lei/buc”), linkul și data verificării.
"""
import html as _html
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from urllib.parse import unquote, urlparse

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
BLOCHEAZA = ("hornbach.", "mathaus.", "leroymerlin.")      # magazine care au blocat mereu cererile automate
SEMNE_BLOCARE = ("Client Challenge", "Just a moment", "challenge-platform", "captcha", "Access Denied",
                 "cf-chl", "Request unsuccessful")
CODURI_BLOCARE = (401, 403, 429, 503)
DOAR_BROWSER = ("boconcept.",)                          # paginile se construiesc din JavaScript, după Cloudflare
SEMNE_JS = ("enable javascript", "activați javascript", "activati javascript", "activează javascript",
            "javascript is required", "javascript is disabled", "javascript must be enabled")
TEXT_MIN = 3000             # o pagină fără preț și cu mai puține caractere de text se construiește din JavaScript
FOLOSESTE_BROWSERUL = "folosește browserul (Playwright: page.goto(url), apoi page.locator('body').inner_text())"
_SUMA = (r"\d{1,3}(?:[.\u00a0\u202f ]\d{3})+(?:,\d{1,2})?|\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|\d+(?:[.,]\d{1,2})?")
PRP = re.compile(r"(?:pre[țţt]\w*\s+recomandat\w*(?:\s+(?:de\s+)?produc[ăa]tor\w*)?(?:\s*\(\s*PRP\s*\))?|\bPRP\b"
                 r"|rec(?:ommended|\.)\s*retail\s+price)\s*:?\s*(?:RON|lei)?\s*(" + _SUMA + r")(?!\d|[.,]\d)", re.I)


def azi():
    """Data de azi, la București: „30.10.2026”."""
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("Europe/Bucharest"))
    except Exception:
        now = datetime.now()
    return now.strftime("%d.%m.%Y")


def numar(s):
    """„1.065,50”, „1065.50”, „1 065,50”, „19.49” -> float; None dacă nu e un număr."""
    s = re.sub(r"[\s\u00a0\u202f\u2009]", "", str(s))
    if not re.fullmatch(r"\d[\d.,]*", s):
        return None
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _attr(tag, name):
    m = re.search(rf"\b{name}\s*=\s*([\"'])(.*?)\1", tag, re.I | re.S)
    return _html.unescape(m.group(2)).strip() if m else None


def _meta(page, key, val):
    """Valoarea atributului content din tagurile cu key="val" (în orice ordine a atributelor)."""
    out = []
    for tag in re.findall(rf"<[^>]*\b{key}\s*=\s*[\"']{re.escape(val)}[\"'][^>]*>", page, re.I):
        c = _attr(tag, "content")
        if c:
            out.append(c)
    return out


def _jsonld(page):
    """Ofertele (price, priceCurrency) din blocurile JSON-LD ale paginii."""
    found = []

    def walk(o):
        if isinstance(o, dict):
            if "price" in o or "lowPrice" in o:
                found.append((o.get("price", o.get("lowPrice")), o.get("priceCurrency")))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    for block in re.findall(r"<script[^>]*application/ld\+json[^>]*>(.*?)</script>", page, re.I | re.S):
        try:
            walk(json.loads(block.strip()))
        except ValueError:
            continue
    return found


def text_vizibil(page):
    page = re.sub(r"<(script|style)\b.*?</\1>", " ", page, flags=re.I | re.S)
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", page))).strip()


def analizeaza(page, url=""):
    """Prețul, moneda, titlul și ambalajul dintr-o pagină HTML (fără rețea; așa se și testează).

    Plus „prp”, prețul recomandat de producător scris în pagină, și „browser”: True dacă pagina cere o verificare
    anti-robot sau, fără preț, se construiește din JavaScript, deci o deschizi în browser.
    """
    pret, moneda, sursa = None, None, None
    for tag in re.findall(r"<[^>]*\bitemprop\s*=\s*[\"']price[\"'][^>]*>", page, re.I):
        v = _attr(tag, "content")
        if v is None:
            m = re.match(r"\s*([^<]+)", page[page.find(tag) + len(tag):])
            v = m.group(1) if m else None
        if v and numar(v) is not None:
            pret, sursa = numar(v), "microdata"
            break
    if pret is None:
        for v in _meta(page, "property", "product:price:amount"):
            if numar(v) is not None:
                pret, sursa = numar(v), "open graph"
                break
    if pret is None:
        for v, cur in _jsonld(page):
            if v is not None and numar(v) is not None:
                pret, moneda, sursa = numar(v), cur, "json-ld"
                break
    if moneda is None:
        moneda = next(iter(_meta(page, "itemprop", "priceCurrency") + _meta(page, "property",
                                                                           "product:price:currency")), None)
    titlu = next(iter(_meta(page, "property", "og:title")), None)
    if not titlu:
        m = re.search(r"<title[^>]*>(.*?)</title>", page, re.I | re.S)
        titlu = re.sub(r"\s+", " ", _html.unescape(m.group(1))).strip() if m else None
    text = text_vizibil(page)
    cutie = None
    m = re.search(r"Se livreaz[ăa] la:?\s*([^\d(]{1,30}?)\s*\(\s*(\d+)\s*buc", text, re.I)
    if m:
        cutie = {"ambalaj": m.group(1).strip(), "bucati": int(m.group(2))}
    blocat = pret is None and any(s.lower() in page.lower() for s in SEMNE_BLOCARE)
    stare = "ok" if pret is not None else ("blocat" if blocat else "fara_pret")
    js = len(text) < TEXT_MIN or any(s in text.lower() for s in SEMNE_JS)
    m = PRP.search(text)
    return {"url": url, "stare": stare, "pret": pret, "moneda": moneda, "sursa": sursa, "titlu": titlu,
            "cutie": cutie, "prp": _numar_prp(m.group(1)) if m else None,
            "browser": stare == "blocat" or (stare == "fara_pret" and js) or (stare != "ok" and _doar_browser(url))}


def _numar_prp(s):
    """Ca `numar`, dar „12,345” cu virgulă la mii (prețurile în engleză) e 12345, nu 12,345."""
    s = re.sub(r"[\s\u00a0\u202f]", "", s)
    if re.fullmatch(r"\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?", s):
        s = s.replace(",", "")
    return numar(s)


def _doar_browser(url):
    return any(b in url for b in DOAR_BROWSER)


def citeste(url, timeout=20):
    """Descarcă pagina și o analizează; întoarce dicționarul din analizeaza, cu cod_http, mesaj și data."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ro-RO,ro;q=0.9,en;q=0.5",
                                               "Accept": "text/html,application/xhtml+xml"})
    rez = {"url": url, "stare": "eroare", "pret": None, "moneda": None, "sursa": None, "titlu": None,
           "cutie": None, "prp": None, "browser": False, "cod_http": None, "mesaj": None, "data": azi()}
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            page = r.read().decode(r.headers.get_content_charset() or "utf-8", "replace")
            rez.update(analizeaza(page, url))
            rez["cod_http"] = r.status
    except urllib.error.HTTPError as e:
        rez["cod_http"] = e.code
        rez["stare"] = "blocat" if e.code in CODURI_BLOCARE else "eroare"
        rez["browser"] = e.code in CODURI_BLOCARE or _doar_browser(url)
        rez["mesaj"] = f"HTTP {e.code}"
    except Exception as e:      # DNS, timp depășit, conexiune refuzată, certificat
        rez["mesaj"] = f"{type(e).__name__}: {getattr(e, 'reason', e)}"
    if rez["stare"] != "ok" and any(b in url for b in BLOCHEAZA):
        rez["mesaj"] = (rez["mesaj"] + "; " if rez["mesaj"] else "") + "magazinul blochează des cererile automate"
    return rez


def _lei(v):
    s = f"{v:,.2f}".replace(",", " ").replace(".", ",")
    return s[:-3] if s.endswith(",00") and v >= 1000 else s


def rand(rez):
    """Un rând de raport pentru un link."""
    prp = f"PRP {_lei(rez['prp'])} {rez.get('moneda') or 'lei'}" if rez.get("prp") is not None else None
    if rez["stare"] == "ok":
        s = f"ok         {_lei(rez['pret'])} {rez['moneda'] or ''}".rstrip()
        if rez.get("cutie"):
            c = rez["cutie"]
            s += f" ({c['ambalaj']} de {c['bucati']} buc: {_lei(rez['pret'] / c['bucati'])} pe bucată)"
        if prp and abs(rez["prp"] - rez["pret"]) > 0.005:
            s += f" · {prp}"
    else:
        parti = [p for p in (rez.get("mesaj"), prp, FOLOSESTE_BROWSERUL if rez.get("browser") else None) if p]
        s = f"{rez['stare']:10s} {'; '.join(parti)}".rstrip()
    titlu = (rez.get("titlu") or "")[:70]
    return f"{s}  ·  {titlu}  ·  {rez['url']}" if titlu else f"{s}  ·  {rez['url']}"


def linkuri_din_lista(path):
    """[(produsul din rând, prețul scris în listă, url)] pentru rândurile de tabel cu linkuri http din lista de
    materiale."""
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            for url in re.findall(r"\]\((https?://[^)\s]+)\)", line):
                pret = next((c for c in cells if re.search(r"\d\s*lei", c)), "")
                produs = max(cells, key=len) if cells else ""
                out.append((re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", produs)[:60], pret, url))
    return out


# ------------------------------------------------------------------ foaia de produse

EXTENSII = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp", "GIF": ".gif", "AVIF": ".avif", "BMP": ".bmp",
            "TIFF": ".tif", "MPO": ".jpg", "HEIF": ".heic"}


def surse_din_fisier(path):
    """[(eticheta sau None, link sau cale)] din fișierul cu câte o sursă pe rând; „#” începe un comentariu.

    Eticheta stă înaintea linkului sau a căii: „NO Natural Oak https://...”.
    """
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parti = line.rsplit(None, 1)
            if (len(parti) == 2 and (re.match(r"https?://", parti[1]) or os.path.isfile(parti[1]))
                    and not re.match(r"https?://", parti[0]) and not os.path.isfile(line)):
                out.append((parti[0].strip(), parti[1]))
            else:
                out.append((None, line))
    return out


def _eticheta(sursa):
    """Ultima parte din cale, fără extensie: eticheta implicită a unei imagini."""
    nume = unquote(urlparse(sursa).path.rstrip("/").rsplit("/", 1)[-1]) if re.match(r"https?://", sursa) \
        else os.path.basename(sursa)
    return os.path.splitext(nume)[0] or nume or "imagine"


def _descarca(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "image/avif,image/webp,image/*,*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _font(marime):
    """DejaVu Sans, din matplotlib: are diacriticele; fontul implicit din Pillow nu are „ă” și „ț”."""
    from PIL import ImageFont
    try:
        import matplotlib
        return ImageFont.truetype(os.path.join(matplotlib.get_data_path(), "fonts", "ttf", "DejaVuSans.ttf"), marime)
    except (ImportError, OSError):
        return ImageFont.load_default(size=marime)


def foaie(surse, dest, latura=300, coloane=None, fundal=(242, 242, 242), timeout=25):
    """Foaia de produse: pozele, în grilă, fiecare într-un chenar, cu eticheta dedesubt.

    surse: linkuri sau căi de pe disc, ori perechi (eticheta, link sau cale). Imaginile descărcate rămân în
    folderul `<dest fără extensie>/`, lângă foaie; cele cu transparență (WebP-urile BoConcept, PNG-urile) se
    lipesc pe `fundal` (RGB). Ce nu e imagine (o pagină de eroare sau de verificare anti-robot) se sare.
    coloane: câte miniaturi pe rând (implicit până la 4). Întoarce (mărimea foii, [(eticheta, motivul)] pentru
    sursele sărite); ValueError dacă nu intră nicio imagine.
    """
    from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError

    folder = os.path.splitext(dest)[0]
    elemente, sarite = [], []
    for k, s in enumerate(surse):
        eticheta, sursa = s if isinstance(s, (tuple, list)) else (None, s)
        eticheta = eticheta or _eticheta(sursa)
        try:
            if re.match(r"https?://", sursa):
                date = _descarca(sursa, timeout)
                with Image.open(io.BytesIO(date)) as im:
                    ext = EXTENSII.get(im.format, ".img")
                os.makedirs(folder, exist_ok=True)
                sursa = os.path.join(folder, f"{k + 1:02d}_{re.sub(r'[^0-9A-Za-z]+', '_', eticheta)[:40]}{ext}")
                with open(sursa, "wb") as f:
                    f.write(date)
            with Image.open(sursa) as im:
                im = ImageOps.exif_transpose(im)
                if im.mode in ("RGBA", "LA", "PA") or (im.mode == "P" and "transparency" in im.info):
                    im = im.convert("RGBA")
                    baza = Image.new("RGBA", im.size, tuple(fundal) + (255,))
                    baza.alpha_composite(im)
                    im = baza
                im = im.convert("RGB")
                im.thumbnail((latura, latura), Image.LANCZOS)
                elemente.append((eticheta, im.copy()))
        except urllib.error.HTTPError as e:
            e.close()
            sarite.append((eticheta, f"HTTP {e.code}"))
        except UnidentifiedImageError:
            sarite.append((eticheta, "nu e o imagine (poate o pagină de eroare sau de verificare anti-robot)"))
        except FileNotFoundError:
            sarite.append((eticheta, "fișierul nu există"))
        except (urllib.error.URLError, OSError) as e:       # DNS, timp depășit, imagine stricată
            sarite.append((eticheta, f"{type(e).__name__}: {getattr(e, 'reason', e)}"))
    if not elemente:
        raise ValueError("nicio imagine de pus pe foaie: " + "; ".join(f"{e}: {m}" for e, m in sarite))
    coloane = max(1, coloane or min(len(elemente), 4))
    spatiu, text_h = 10, 20
    randuri = -(-len(elemente) // coloane)
    img = Image.new("RGB", (coloane * latura + (coloane + 1) * spatiu,
                            randuri * (latura + text_h) + (randuri + 1) * spatiu), (255, 255, 255))
    d = ImageDraw.Draw(img)
    f = _font(13)
    for i, (eticheta, mini) in enumerate(elemente):
        r, c = divmod(i, coloane)
        x, y = spatiu + c * (latura + spatiu), spatiu + r * (latura + text_h + spatiu)
        d.rectangle((x - 1, y - 1, x + latura, y + latura), outline=(215, 215, 215))
        img.paste(mini, (x + (latura - mini.width) // 2, y + (latura - mini.height) // 2))
        text = eticheta
        while text and d.textlength(text + ("…" if text != eticheta else ""), font=f) > latura - 4:
            text = text[:-1]
        d.text((x + 2, y + latura + 3), text + ("…" if text != eticheta else ""), fill=(40, 40, 40), font=f)
    os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
    img.save(dest, quality=88)
    return img.size, sarite


def _main_foaie(argv):
    """`preturi.py --foaie <dest.jpg> <surse>`: un argument .txt e o listă de surse."""
    if len(argv) < 2:
        print(__doc__)
        return 2
    dest, surse = argv[0], []
    for a in argv[1:]:
        surse += surse_din_fisier(a) if a.lower().endswith(".txt") else [(None, a)]
    try:
        size, sarite = foaie(surse, dest)
    except ValueError as e:
        print(f"eroare: {e}", file=sys.stderr)
        return 1
    for eticheta, motiv in sarite:
        print(f"sărit: {eticheta}: {motiv}")
    print(f"salvat {dest} ({size[0]} × {size[1]}): {len(surse) - len(sarite)} din {len(surse)} imagini. Pozele "
          "produselor au drepturi de autor: foaia nu intră în depozit.")
    return 1 if sarite else 0


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    if argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "--foaie":
        return _main_foaie(argv[1:])
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    if argv[0] == "--lista":
        intrari = linkuri_din_lista(argv[1])
    else:
        intrari = [("", "", u) for u in argv]
    rezultate = []
    print(f"verificat pe {azi()}", file=sys.stderr)
    for produs, pret_lista, url in intrari:
        rez = citeste(url)
        rez["in_lista"] = pret_lista
        rezultate.append(rez)
        if not as_json:
            print(rand(rez) + (f"  ·  în listă: {pret_lista}" if pret_lista else ""))
    if as_json:
        print(json.dumps(rezultate, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
