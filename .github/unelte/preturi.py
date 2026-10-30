"""Prețurile din magazinele online: citește pagina produsului și scoate prețul, moneda, titlul și ambalajul.

    python preturi.py <url> [<url> ...]          # câte un rând pe link, cu data verificării
    python preturi.py --json <url> [...]         # același lucru, ca JSON
    python preturi.py --lista "<Proiect>/lista_materiale.md"   # toate linkurile din listă, cu prețul din ea

Prețul se caută, în ordine, în: microdata (`itemprop="price"`), Open Graph (`product:price:amount`) și JSON-LD
(`"price"`). La Dedeman, prețul afișat poate fi pe cutie: caută „Se livrează la: cutie (N buc)” și calculezi
cantitatea pe cutii.

Stările unui link:
- ok: prețul a fost găsit;
- fara_pret: pagina s-a încărcat, dar nu are prețul în cod; îl verifici în browser;
- blocat: magazinul refuză cererile automate (Hornbach, MatHaus și Leroy Merlin fac asta mereu). Atunci deschizi
  pagina cu unealta playwright sau ceri prețul utilizatorului; nu-l ghicești și nu-l copiezi din altă parte;
- eroare: rețeaua sau adresa (DNS, timp depășit, 404). Nu înseamnă că magazinul blochează.

Înainte să trimiți subagenți de cercetare, rulezi scriptul o dată, pe un link: afli din prima ce merge din mediul
de lucru. În lista de materiale treci prețul cu virgulă zecimală („19,49 lei/buc”), linkul și data verificării.
"""
import html as _html
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
BLOCHEAZA = ("hornbach.", "mathaus.", "leroymerlin.")      # magazine care au blocat mereu cererile automate
SEMNE_BLOCARE = ("Client Challenge", "Just a moment", "challenge-platform", "captcha", "Access Denied",
                 "cf-chl", "Request unsuccessful")
CODURI_BLOCARE = (401, 403, 429, 503)


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
    """Prețul, moneda, titlul și ambalajul dintr-o pagină HTML (fără rețea; așa se și testează)."""
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
    return {"url": url, "stare": "ok" if pret is not None else ("blocat" if blocat else "fara_pret"),
            "pret": pret, "moneda": moneda, "sursa": sursa, "titlu": titlu, "cutie": cutie}


def citeste(url, timeout=20):
    """Descarcă pagina și o analizează; întoarce dicționarul din analizeaza, cu cod_http, mesaj și data."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ro-RO,ro;q=0.9,en;q=0.5",
                                               "Accept": "text/html,application/xhtml+xml"})
    rez = {"url": url, "stare": "eroare", "pret": None, "moneda": None, "sursa": None, "titlu": None,
           "cutie": None, "cod_http": None, "mesaj": None, "data": azi()}
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            page = r.read().decode(r.headers.get_content_charset() or "utf-8", "replace")
            rez.update(analizeaza(page, url))
            rez["cod_http"] = r.status
    except urllib.error.HTTPError as e:
        rez["cod_http"] = e.code
        rez["stare"] = "blocat" if e.code in CODURI_BLOCARE else "eroare"
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
    if rez["stare"] == "ok":
        s = f"ok         {_lei(rez['pret'])} {rez['moneda'] or ''}".rstrip()
        if rez.get("cutie"):
            c = rez["cutie"]
            s += f" ({c['ambalaj']} de {c['bucati']} buc: {_lei(rez['pret'] / c['bucati'])} pe bucată)"
    else:
        s = f"{rez['stare']:10s} {rez.get('mesaj') or ''}".rstrip()
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


def main(argv):
    if not argv:
        print(__doc__)
        return 2
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
