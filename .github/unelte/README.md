# Uneltele agenților

Aici sunt uneltele comune ale agenților care lucrează în depozit, mai ales ale agentului [Designer interior](../agents/designer-interior.agent.md). Sunt scripturile Python pe care fiecare proiect de până acum și le-a scris singur, adunate, curățate și testate, plus felul în care agenții lucrează cu ele. Un proiect nou nu mai pornește de la zero și nu mai copiază fișiere din alt proiect. Își scrie doar ce e al lui: cotele, dreptele pentru calibrare, scena randată și planul. Restul îl ia de aici.

Uneltele vin din sursele celor două proiecte, [`cuier-hol/`](../surse/cuier-hol/README.md) și [`polite-viniluri/`](../surse/polite-viniluri/README.md), inclusiv din subfolderul variantelor C și D ale polițelor, din beton decorativ, [`polite-viniluri/beton/`](../surse/polite-viniluri/beton/README.md). Scripturile acelor proiecte rămân neschimbate, pentru că reproduc imaginile publicate. Testele de aici verifică faptul că uneltele dau aceleași rezultate ca ele.

Planul de arhitect în PDF (`plan_pdf.py`), ușile de mobilier (`usi.py`) și câteva funcții din modulele de mai jos vin din proiectul „Comodă birou”, din [`comoda-birou/`](../surse/comoda-birou/README.md) și din uneltele scrise atunci pentru el.

Folderul începe cu punct, deci nu apare pe site, dar depozitul e public: fără căi absolute sau date personale în fișiere.

## Pregătirea

Din rădăcina depozitului:

```sh
python3 -m venv .venv
.venv/bin/pip install numpy scipy opencv-python-headless matplotlib pillow
.venv/bin/pip install pillow-heif            # doar pentru fotografiile HEIC de pe iPhone
.venv/bin/pip install pymupdf                # opțional, doar pentru planul de arhitect în PDF (plan_pdf.py)
```

Uneltele sunt testate cu Python 3.12, numpy 2.5, scipy 1.18, opencv-python-headless 5.0, matplotlib 3.11 și Pillow 13, iar `plan_pdf.py`, cu PyMuPDF 1.28. Rulezi cu `python -B`, ca să nu apară `__pycache__` în depozit. Oricum, `.gitignore` din rădăcină ignoră `__pycache__/`, `.venv/` și `out/`.

## Importul

Scripturile unui proiect stau, ca până acum, în `.github/surse/<proiect>/`, cu README propriu, și iau uneltele așa:

```python
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))          # .github
from unelte import camera, comparatie, foto, materiale, plan, randare, rezistenta
```

Le imporți ca `unelte.<modul>` și nu pui `.github/unelte` direct în `sys.path`. Proiectele au fișiere proprii cu aceleași nume ca modulele (`camera.py`, `core.py`, `design.py`), iar prefixul `unelte.` evită confuzia. Modulele nu se importă între ele: câteva funcții mici sunt copiate intenționat, ca fiecare modul să poată fi folosit singur.

Opt module se rulează și din linia de comandă: `foto.py`, `segmente.py`, `comparatie.py`, `plan.py`, `plan_pdf.py`, `usi.py`, `preturi.py` și `verificari.py`. Fără argumente, toate în afară de `verificari.py` își afișează modul de folosire, iar `verificari.py` verifică toate proiectele.

## Convențiile

- **Lumea**, în cm: X merge de-a lungul peretelui din fața aparatului, spre dreapta. Y merge în sus, cu Y = 0 pe pardoseală. Z iese din perete spre aparat, cu Z = 0 pe fața peretelui. Originea lui X o alegi la un colț: la polițe e colțul din stânga, la cuier e colțul din dreapta, deci acolo X e negativ.
- **Pixelii** au originea în colțul din stânga sus al fotografiei de lucru, care are 1024 px pe latura mare. Unghiurile din `camera.json` sunt în radiani; `camera.rezumat` le arată în grade.
- **Imaginile** se țin în memorie ca la OpenCV: BGR, float32, cu valori între 0 și 1 (`foto.citeste`). Pe disc ajung ca JPG fără metadate (`foto.scrie`, `randare.save_jpg`).
- **Texturile** au 10 px pe cm (`materiale.R`); rândurile lor merg de-a lungul lungimii piesei.
- **Aleatorul** vine doar din parametrul `rng`, de exemplu `np.random.RandomState(7)`, cu sămânță fixă, ca imaginile să iasă la fel la fiecare rulare.
- **Numele.** Funcțiile preluate din proiecte își păstrează numele în engleză (`face`, `glued_panel`, `rod_check`), ca să le recunoști în sursele vechi. Cele noi au nume în română (`calibreaza`, `pregateste`, `compune`). Docstringurile, comentariile și mesajele sunt în română.

## Catalogul

| Modulul | La ce folosește | Funcțiile principale | Preluat din |
|---|---|---|---|
| [`plan_pdf.py`](plan_pdf.py) | Planul de arhitect în PDF: paginile, randările cu grilă, textele (și din fonturi fără Unicode), liniile și dimensiunile unei camere, cu scara calibrată pe o cotă scrisă și verificată pe a doua. Are nevoie de PyMuPDF | `deschide`, `info`, `randeaza`, `grila`, `gaseste`, `cuvinte`, `linii`, `masoara_camera`, `imagine_camera` | trusa proiectului „Comodă birou” |
| [`foto.py`](foto.py) | Fotografia de lucru: fără metadate, cu 1024 px pe latura mare, în sRGB. Face zoom-uri cu grilă de coordonate și curăță ecranele, persoanele și textele | `pregateste`, `metadate`, `citeste`, `scrie`, `grila`, `stinge_ecran`, `umple_de_sus`, `sterge`, `estompeaza` | `polite-viniluri/curata_foto.py` |
| [`segmente.py`](segmente.py) | Segmentele de dreaptă din fotografie (LSD), numerotate, ca să le alegi pe grupuri; LSD pe poza mărită, la pozele mici, și muchiile slabe, din gradient, pe care LSD nu le prinde | `detecteaza` (cu `marire`), `deseneaza`, `alege`, `muchie_slaba`, `abateri_segment`, `deseneaza_muchie` | metoda din [README-ul cuierului](../surse/cuier-hol/README.md); mărirea și muchia slabă, din trusa „Comodă birou” |
| [`camera.py`](camera.py) | Aparatul foto: proiecții, raze, trecerea din pixeli în cm și calibrarea, cu profilul erorii pentru parametrii liberi | `Camera` (`project`, `backproject`, `scaled`, `fara_distorsiune`), `calibreaza`, `profil`, `rezumat_profil`, `incarca`, `salveaza`, `citeste_segmente`, `puncte`, `rezumat` | `camera.py` din ambele proiecte; profilul, din `comoda-birou/camera.py` |
| [`usi.py`](usi.py) | Ușile de mobilier: unghiul la care o ușă atinge peretele sau blatul de lângă ea, cât rămâne liber la 90° și cât ar intra în obstacol la unghiul maxim al balamalelor; desenul ușii în vederea în plan | `analizeaza`, `deseneaza`, `imagine`, `colturi_usa`, `ocupat` | `door_check` din `comoda-birou/render_galla.py`, generalizat |
| [`randare.py`](randare.py) | Piesele noi, desenate în fotografie cu buffer de adâncime, în lumina peretelui și cu umbre | `Canvas` (`din_foto`, `face`, `multiply_wall`, `multiply_floor`), `box`, `solid`, `wall_light_map`, `finish`, `current_photo`, `save_jpg` | `polite-viniluri/core.py` și `render.py` |
| [`materiale.py`](materiale.py) | Texturile: stejar luat din parchetul din poză sau procedural, microciment, furnir și riflaj. Măsoară culorile din poză și diferența dintre ele (Lab, ΔE00) | `oak_source`, `glued_panel`, `end_grain`, `oak_procedural`, `veneer`, `reeding`, `concrete_panel`, `concrete_edge`, `concrete_end`, `sample`, `masoara`, `diferenta` | `polite-viniluri/materials.py`, `polite-viniluri/beton/beton.py` și `comoda-birou/materials.py` |
| [`comparatie.py`](comparatie.py) | Imaginea de comparație: Acum și propunerile (A și B sau, la variantele în plus, C și D), cu titluri și subtitluri | `compune` | `compare.py` din ambele proiecte |
| [`plan.py`](plan.py) | Planul tehnic A3 la 1:15: pagina, cotele, notele și trimiterile la detalii, plus verificarea automată a textelor și a formatului PDF | `pagina`, `make_axes`, `rect`, `dim_h`, `dim_v`, `label`, `callout`, `text_block`, `legend`, `scara`, `save`, `verifica_figura`, `e_a3` | `drawing.py` și `verifica_plan.py` din `polite-viniluri/beton/`, `polite-viniluri/drawing.py`; `callout`, din `comoda-birou/drawing.py` |
| [`rezistenta.py`](rezistenta.py) | Verificări de ordinul de mărime: tije în consolă, smulgerea din ancoră, greutăți | `rod_check`, `rod_pull`, `kg_placa`, `greutate`, `RHO`, `FY` | `design.py` din `polite-viniluri/` și `polite-viniluri/beton/` |
| [`preturi.py`](preturi.py) | Prețul, titlul și ambalajul din pagina produsului, pentru un link sau pentru toate linkurile unei liste de materiale. Recunoaște paginile care cer browserul și prețul recomandat de producător (PRP). Face foaia de produse: pozele, una lângă alta | `citeste`, `analizeaza`, `linkuri_din_lista`, `foaie`, `surse_din_fisier` | nou, după lecțiile din memorie; browserul, PRP-ul și foaia, din trusa „Comodă birou” |
| [`verificari.py`](verificari.py) | Verificarea unui proiect înainte de commit, cu variantele lui în plus: livrabile, metadate, linkuri, diacritice, date personale, calculele din listele de materiale | `verifica`, `verifica_texte`, `verifica_linkuri` | nou, după regulile din memorie |
| [`teste/test_unelte.py`](teste/test_unelte.py) | Testele tuturor uneltelor, inclusiv paritatea cu scripturile proiectelor | – | – |
| [`teste/test_unelte_noi.py`](teste/test_unelte_noi.py) | Testele uneltelor aduse din „Comodă birou”: planul PDF, pe planuri sintetice, ușile, funcțiile noi și paritatea cu `comoda-birou/` | – | – |

## Un proiect nou, pas cu pas

Pașii urmează „Pașii de lucru” din [memorie](../memorie/memorie.md); aici sunt doar comenzile. Exemplele pornesc din rădăcina depozitului, cu mediul `.venv` de la „Pregătirea”, iar `S` e folderul cu sursele proiectului.

O variantă în plus pentru un proiect existent nu e un proiect nou: intră în folderul lui, după regula „Variantele noi se adaugă, nu înlocuiesc” din memorie. Literele continuă (C și D după A și B), fișierele au nume noi, cu sufix (`propunere_C_<material>.jpg`, `varianta_D_<material>.jpg`, `comparatie_acum_vs_propuneri_<sufix>.jpg`, `lista_materiale_<sufix>.md`, `plan_tehnic_<proiect>_<sufix>.pdf` și `.png`), iar fișierele existente rămân neschimbate. Sursele ei stau într-un subfolder, de exemplu `S=".github/surse/polite-viniluri/beton"`; pașii sunt aceiași.

### 0. Planul de arhitect, dacă îl ai

```sh
S=".github/surse/<proiect>"
mkdir -p "$S/out"
P="<cale>/plan_etaj.pdf"                     # calea rămâne în terminal; PDF-ul nu intră în depozit
.venv/bin/python -B .github/unelte/plan_pdf.py info "$P"
.venv/bin/python -B .github/unelte/plan_pdf.py randeaza "$P" "$S/out/plan_p1.png" --dpi 100 --grila 50
.venv/bin/python -B .github/unelte/plan_pdf.py cauta "$P" "DORMITOR 2"
.venv/bin/python -B .github/unelte/plan_pdf.py cuvinte "$P" --zona 560 330 780 570       # cotele, ușile, ferestrele
.venv/bin/python -B .github/unelte/plan_pdf.py camera "$P" "DORMITOR 2" --cota-cm 327 --verifica-cm 366 --scara 50 \
  --imagine "$S/out/camera.png"
```

Planul dă cotele camerei înainte de fotografie: lățimea și adâncimea, golurile ușilor și ale ferestrelor, parapetele. Te uiți pe randarea cu grilă (coordonatele sunt în puncte tipografice, pe pagina nerotită), găsești eticheta camerei și citești cotele scrise din zona ei. `camera` găsește fețele interioare ale pereților din jurul etichetei și calibrează scara pe o cotă scrisă (`--cota-cm`), apoi o verifică pe a doua (`--verifica-cm`): diferența trebuie să fie de câțiva milimetri. Pe imaginea de verificare, camera e în roșu și eticheta în albastru. Randările planului rămân în `out/`, pentru că arată cartușul (vezi „Capcane”).

### 1. Fotografia

```sh
S=".github/surse/<proiect>"
mkdir -p "$S/out"
.venv/bin/python -B .github/unelte/foto.py pregateste "<fotografia primită>" "$S/out/fotografie.jpg"
.venv/bin/python -B .github/unelte/foto.py exif "$S/out/fotografie.jpg"      # trebuie să scrie „ok”
.venv/bin/python -B .github/unelte/foto.py grila "$S/out/fotografie.jpg" "$S/out/zoom.png" 600 0 1024 400
```

`pregateste` rotește fotografia după EXIF și o trece în sRGB, pentru că telefoanele fotografiază în Display P3. O micșorează la 1024 px pe latura mare și o salvează fără metadate: fără EXIF, GPS, XMP sau comentariu JPEG. Merge și cu HEIC, dacă ai instalat `pillow-heif`.

Te uiți pe fotografie și pe zoom-uri cu unealta `view`, după ecrane aprinse, documente, numere de înmatriculare și persoane. Le cureți într-un `curata_foto.py` al proiectului, rulat o singură dată, care scrie `original.jpg`:

```python
from unelte import foto

img = foto.citeste(os.path.join(HERE, "out", "fotografie.jpg"))
img = foto.stinge_ecran(img, [(312, 140), (705, 150), (700, 372), (316, 366)])   # colțurile ecranului, în px
img = foto.sterge(img, [(900, 520), (960, 520), (960, 545), (900, 545)])          # un text mic
foto.scrie(os.path.join(HERE, "original.jpg"), img)
```

Dacă nu e nimic de curățat, `pregateste` scrie direct `original.jpg`.

### 2. Segmentele

```sh
.venv/bin/python -B .github/unelte/segmente.py "$S/original.jpg" "$S/out/"
.venv/bin/python -B .github/unelte/segmente.py "$S/original.jpg" "$S/out/" --zona 600 0 1024 400
```

Te uiți pe `out/segmente_numerotate.png` cu `view`; cu `--zona` o iei pe bucăți, ca indicii să se citească. Scrii în `grupuri.json` indicii segmentelor pentru fiecare muchie cu poziție cunoscută, de exemplu `{"ceil": [12, 40], "corner_left": [3]}`. Un grup e o singură dreaptă 3D: tavanul de pe peretele din față, un colț, plinta, marginea de sus a televizorului. Folosești același `--min` la toate zonele, pentru că fiecare rulare rescrie `segmente_toate.json`, iar indicii depind de el.

```sh
.venv/bin/python -B .github/unelte/segmente.py --alege "$S/out/segmente_toate.json" "$S/grupuri.json" "$S/segments.json"
```

La o fotografie mică, de ~300 px pe latura mare, adaugi `--marire 2` la prima comandă: LSD rulează pe poza mărită de 2 ori și prinde și muchiile fine, iar coordonatele rămân în pixelii pozei. O muchie slabă, pe care LSD n-o prinde, de exemplu tavanul alb pe peretele alb, o cauți din gradient, într-o bandă de rânduri:

```sh
.venv/bin/python -B .github/unelte/segmente.py --muchie "$S/original.jpg" --banda 55 110 --de-la 4 --pana-la 240 \
  --segment 238 93 302 98 --imagine "$S/out/muchie.png"
```

Comanda dă dreapta prin cele mai multe puncte, cu abaterea fiecăruia, și segmentul pe care îl adaugi de mână în grupul lui din `segments.json`. Cu `--segment` verifici că un segment LSD de pe aceeași muchie e în prelungirea ei, la sub 1 px; pe imaginea de control, punctele scoase din potrivire sunt portocalii. Pentru o muchie verticală adaugi `--verticala`, iar banda e atunci pe coloane.

### 3. Calibrarea

În `camera.py` al proiectului scrii, pentru fiecare grup, dreapta 3D pe care stau segmentele lui. Necunoscutele scenei, ca tavanul `H` sau pozițiile televizorului și ale comodei, intră în `p0`. Exemplul de mai jos e calibrarea polițelor, cu 12 din cele 15 grupuri ale lor:

```python
from unelte import camera

WALL_W = 419.0                                        # lățimea peretelui, măsurată


def dreapta(grup, q):
    H, x0, y0, z = q["H"], q["xtv"], q["ytv"], q["ztv"]
    x1, y1 = x0 + 216.6, y0 + 123.6                   # televizorul: 216,6 × 123,6 cm, din fișa lui
    c0, c1, cf, cs = q["xc"], q["xc"] + 242, q["zc"], q["zc"] - 48   # comoda: 242 × 48 × 67 cm
    return {
        "ceil": ([0, H, 0], [WALL_W, H, 0]),
        "corner_left": ([0, 0, 0], [0, H, 0]),
        "wall_right": ([WALL_W, 0, 0], [WALL_W, H, 0]),
        "floor": ([0, 0, 1.5], [WALL_W, 0, 1.5]),     # pardoseala, la fața plintei (1,5 cm de perete)
        "tv_top": ([x0, y1, z], [x1, y1, z]),
        "tv_bottom": ([x0, y0, z], [x1, y0, z]),
        "tv_left": ([x0, y0, z], [x0, y1, z]),
        "tv_right": ([x1, y0, z], [x1, y1, z]),
        "cab_top_front": ([c0, 67, cf], [c1, 67, cf]),
        "cab_top_back": ([c0, 67, cs], [c1, 67, cs]),
        "cab_top_left": ([c0, 67, cs], [c0, 67, cf]),     # muchiile care ies din perete fixează distanța
        "cab_top_right": ([c1, 67, cs], [c1, 67, cf]),
    }[grup]


segs = camera.citeste_segmente(os.path.join(HERE, "segments.json"))
p0 = dict(f=780, yaw=0, pitch=0, roll=0, cx=200, cy=140, cz=330, H=260, xtv=100, ytv=80, ztv=5, xc=80, zc=55)
q = camera.calibreaza(segs, dreapta, p0, size=(1024, 768))
print(camera.rezumat(q))                              # rms sub 1 px; rms_grupuri arată grupul greșit
camera.salveaza(q, os.path.join(HERE, "camera.json"))
```

Pe fotografia polițelor, exemplul dă rms 0,57 px și tavanul de 261,86 cm; calibrarea completă a proiectului dă 261,87 cm. Două reguli fac o calibrare bună:
- **Dreptele sunt infinite.** Contează doar dreapta pe care stau segmentele, nu capetele ei. O muchie orizontală nu spune nimic despre poziția pe lungimea ei, iar scara vine doar din distanțele dintre drepte paralele: între colțurile peretelui, între marginile televizorului, între fața și spatele comodei. Fiecare necunoscută are nevoie de o dreaptă care o fixează.
- **Ai nevoie de muchii care ies din perete**, pe Z: laturile comodei, colțul tavanului cu peretele lateral. Cu muchii doar în planul peretelui, distanța până la aparat și `f` se compensează una pe alta. În probă, fără comodă, `f` a ajuns la 7 px, cu aparatul la 3 cm de perete și rms 0,58 px, deci o eroare mică nu garantează o soluție bună. Te uiți și dacă `f` și poziția aparatului au sens. `f` e de obicei între 0,5 și 0,9 × lățimea fotografiei: 0,86 la polițe și 0,5 la cuier, fotografiat cu unghi larg. La cele două proiecte, aparatul a stat la 1–1,4 m înălțime și la 2–4 m de perete.

Scara vine din ce e cunoscut. Două rețete au mers:

| Proiectul | Scara | Apelul | Rezultatul |
|---|---|---|---|
| Polițe viniluri | televizorul (216,6 × 123,6 cm), comoda (242 × 48 × 67 cm) și lățimea peretelui (419 cm); tavanul rămâne necunoscut | `calibreaza(segs, dreapta, p0, (1024, 768))` | rms 0,60 px; tavanul calculat e de 261,9 cm |
| Cuier hol | tavanul măsurat, 270 cm | `calibreaza(segs, dreapta, p0, (768, 1024), fixe={"H": 270.0}, k1_liber=True, regularizare={"roll": 20}, max_nfev=20000)` | rms 0,60 px; k1 = −0,0038 |

Ceri întâi tavanul măsurat. La cuier, un tavan presupus de 280 cm în loc de 270 a umflat toate cotele cu circa 4 %. Dacă tavanul spus nu se potrivește cu poza, îl lași liber și îi spui utilizatorului: la polițe, cu tavanul fixat la 250 cm, eroarea medie urcă la 4,6 px.

Un parametru liber al scenei, ca tavanul sau poziția unui obiect, îl crezi doar după profilul erorii: îl fixezi pe rând la mai multe valori și compari eroarea.

```python
qs = camera.profil(segs, dreapta, p0, (1024, 768), "H", (230, 250, 270))
print(camera.rezumat_profil(qs, "H", arata=("cz", "xd")))   # rms-ul, aparatul și obiectul, la fiecare tavan
```

Dacă rms-ul rămâne același, fotografia nu determină parametrul: alții îl compensează, iar valoarea o ceri măsurată (vezi „Capcane”). Dacă rms-ul are un minim clar, acolo e valoarea din fotografie.

Camera calibrată face legătura dintre cm și pixeli:

```python
cam1 = camera.incarca(os.path.join(HERE, "camera.json"))
uv = cam1.project([[0, 250, 0], [419, 250, 0]])       # cm -> px
P = cam1.backproject([512, 300], "Z", 0)              # un pixel de pe perete -> cm
```

Randarea cere k1 = 0. Dacă ai calibrat cu `k1_liber=True`, randezi cu `cam1.fara_distorsiune()`. La cuier (k1 = −0,0038), pixelii se mută așa cu cel mult 2,5 px în toată fotografia și cu sub 0,5 px în zona cuierului. Dacă la tine diferența e mare în zona pieselor noi, calibrezi direct cu k1 = 0.

### 4. Propunerea: ușile de mobilier

```sh
.venv/bin/python -B .github/unelte/usi.py --latime 34 --grosime 2.5 --balama dreapta --distanta 3.6 --fata 51.5 \
  --obstacol-pana-la 70 --imagine "$S/out/usa_dreapta.png"
```

Un corp cu uși lângă un perete sau lângă alt obiect îl verifici înainte de randare: unghiul la care ușa atinge obstacolul, cât rămâne liber la 90° și cât ar intra în obstacol la unghiul maxim al balamalelor. Adâncimile sunt de la perete: `--fata` e fața corpului, iar un blat de birou de 70 cm e `--obstacol-pana-la 70`. Codul de ieșire 1 înseamnă că ușa atinge obstacolul înainte de unghiul maxim. Dulapul Cioata Galla 120, centrat între colț și birou, are 3,6 cm liberi de fiecare parte: ușa din dreapta, de 34 cm, are 1,1 cm liberi la 90° și ar intra ~5,8 cm în blat la 110°, iar cea din stânga, de 51 cm, are tot 1,1 cm până la perete. Ușile se deschid deci până la ~90°, nu până la cei 110° ai balamalelor; scrii asta în README și în plan. În planul tehnic, ușa o desenezi cu `usi.deseneaza` (pasul 8).

### 5. Materialele

```python
from unelte import materiale as mat

rng = np.random.RandomState(7)
src = mat.oak_source(photo, cam1, X=(40, 86), Z=(70, 116))    # o zonă de parchet liberă, în cm
panou = mat.glued_panel(src, length_cm=80, width_cm=33, rng=rng)
capat = mat.end_grain(33, 4, rng)
beton = mat.concrete_panel(80, 33, rng, "antracit")
perete, _ = mat.masoara(photo, cam1, X=(340, 400), Y=(140, 200))   # culoarea peretelui (mediana)
print(mat.diferenta(perete, mat.din_rgb(200, 196, 188)))           # ΔE00 față de o mostră
```

ΔE00 sub 2 abia se vede; peste 5 se vede clar. Dacă poza nu are parchet liber, iei `oak_procedural(rng)`. Un front din furnir de stejar are harta de detaliu `mat.veneer(lățime, înălțime, rng)`, iar unul riflat, umbrirea `mat.reeding(u_cm, pas)`; amândouă le înmulțești cu culoarea produsului și cu lumina peretelui, ca la „Comodă birou”.

### 6. Randarea

```python
from unelte import foto, randare as rd

photo = foto.citeste(os.path.join(HERE, "original.jpg"))
cv = rd.Canvas.din_foto(photo, cam1)                  # se calculează la 4x și iese la 2x
zid = [[0, 0, 0], [419, 0, 0], [419, 250, 0], [0, 250, 0]]
M, _ = rd.wall_light_map(photo, cam1, zid, size=(cv.W, cv.H))


def stejar(shade):                                    # funcția de culoare a unei fețe, ca rd.solid
    def color(s, t, X, yy, xx):                       # s, t: cm pe fața piesei (aici s pe lungime)
        return mat.sample(panou, t * mat.R, s * mat.R) * M[yy, xx][..., None] * shade
    return color


lemn = capat.reshape(-1, 3).mean(0)                   # culoarea medie a capătului, pentru canturi
rd.box(cv, (388, 415), (0, 110), (8, 55), lambda n: None)          # boxa din dreapta, din poză: doar în buffer
rd.box(cv, (329, 409), (128, 132), (0, 33),                        # o poliță de 80 × 33 × 4 cm
       lambda n: stejar(rd.SHADE[n]) if n[1] else rd.solid(lemn, M, rd.SHADE[n]))
cv.multiply_wall(lambda X, Y: 1 - 0.35 * np.exp(-((Y - 126) / 3) ** 2), 329, 409, 115, 128)   # umbra de sub ea
rd.save_jpg(os.path.join(HERE, "out", "propunere_A_stejar.jpg"), rd.finish(cv.img, cv.touch, cv.ss))
rd.save_jpg(os.path.join(HERE, "out", "acum.jpg"), rd.current_photo(photo))
```

Ce acoperă ce se rezolvă cu bufferul de adâncime, nu cu ordinea de desenare. Obiectele din poză care stau în fața pieselor noi, de exemplu boxele, le desenezi fără culoare (`color=None`, iar la `box`, `lambda n: None`): intră doar în buffer și ascund ce e în spatele lor. Fețele mari ale poliței, sus și jos, au textura; canturile au culoarea medie a lemnului. Toate sunt umbrite după orientare (`SHADE`). Aparatul e aici la 1 m înălțime, deci se vede fața de jos. După fiecare randare te uiți pe imagine cu `view`, mărit pe îmbinări, umbre și margini.

### 7. Comparația

```sh
.venv/bin/python -B .github/unelte/comparatie.py "$S/out/comparatie_acum_vs_propuneri.jpg" \
  "$S/out/acum.jpg" "Acum" "fotografia de acum" \
  "$S/out/propunere_A_stejar.jpg" "Propunere A – stejar" "2 polițe flotante, prinse ascuns" \
  "$S/out/varianta_B_beton.jpg" "Varianta B – beton" "aceleași polițe, din microciment"
```

Un titlu prea lung se micșorează până încape. Dacă nici așa nu încape, primești o eroare și îl scurtezi.

### 8. Planul tehnic

Îl desenezi în `drawing.py`, cu o funcție `build()` care întoarce figura; tiparul e în docstringul din [`plan.py`](plan.py). Notele le dai ca paragrafe întregi, iar `text_block` le rupe singur pe rânduri. Cotele au virgulă zecimală (`plan.fmt`). Trimiterea la un detaliu o pui cu `plan.callout`, planul camerei îl desenezi la 1:50, cu `MM50` și `K50` (orice scară: `plan.scara(n)`), iar ușile de mobilier, în vederea în plan:

```python
from unelte import usi

ax = make_axes(fig, 4, 3, (-38, 334), (-14, 120), "PLAN – VEDERE DE SUS (1:15)", MM15, invert=True)
rez = usi.analizeaza(34, 2.5, 3.6, fata=51.5, obstacol_pana_la=70)
usi.deseneaza(ax, rez, "dreapta", x_balama=122.6, k=K15, legenda=(0.30, 0.01))   # două uși: legende în locuri diferite
```

După fiecare schimbare:

```sh
.venv/bin/python -B .github/unelte/plan.py verifica "$S/drawing.py"     # 0 probleme, apoi te uiți pe PNG
.venv/bin/python -B "$S/drawing.py"                                     # out/plan_tehnic_<proiect>.pdf și .png
.venv/bin/python -B .github/unelte/plan.py a3 "$S/out/plan_tehnic_<proiect>.pdf"
```

`verifica` caută textele care ies din pagină, se suprapun, intră peste un desen sau sunt tăiate de o linie de indicație. Restul îl vezi doar pe PNG, cu `view`, mărit pe detalii.

### 9. Rezistența

```python
from unelte import rezistenta as rz

kg = rz.kg_placa(80, 33, 4, "stejar") + 25           # polița plus discurile de pe ea, în kg
sigma, rezerva = rz.rod_check(kg, P=33, rods=4)      # tije M12 din oțel 4.8, ca o consolă
kn = rz.rod_pull(kg, P=33, T=4, rods=4)              # smulgerea din ancoră, pe fiecare tijă
```

Sunt verificări de ordinul de mărime, fără coeficienți de siguranță. În README și în plan le însoțești cu fișa ancorei chimice pentru peretele real și cu proba de încărcare: 1,5 × sarcina, timp de 24 de ore.

### 10. Prețurile

```sh
.venv/bin/python -B .github/unelte/preturi.py "<linkul produsului>"
.venv/bin/python -B .github/unelte/preturi.py --lista "<Proiect>/lista_materiale.md"
.venv/bin/python -B .github/unelte/preturi.py --foaie "$S/out/foaie_comode.jpg" "$S/out/linkuri.txt"
```

Rulezi întâi pe un singur link, ca să afli ce merge din mediul de lucru. Starea `blocat` înseamnă că magazinul refuză cererile automate, cum fac mereu Hornbach, MatHaus și Leroy Merlin. Atunci deschizi pagina cu Playwright (`browser_navigate`, apoi `browser_snapshot`) sau îi ceri prețul utilizatorului; nu-l ghicești. La Dedeman, prețul poate fi pe cutie: scriptul semnalează „Se livrează la: cutie (N buc)”, iar tu calculezi cantitatea pe cutii.

Când rândul spune „folosește browserul”, pagina cere o verificare anti-robot sau se construiește din JavaScript, ca la BoConcept: o deschizi cu Playwright. „PRP” e prețul recomandat de producător, scris în pagină, ca la Cioata; nu e neapărat prețul de vânzare. `--foaie` pune pozele produselor una lângă alta, cu eticheta sub fiecare, ca să compari modele, finisaje și desene cotate. Sursele sunt linkuri spre imagini, căi sau un fișier `.txt` cu câte o sursă pe rând, cu eticheta înainte (`NO Natural Oak https://...`); foaia și pozele rămân în `out/`, pentru că au drepturi de autor.

### 11. Verificarea, înainte de commit

```sh
.venv/bin/python -B .github/unelte/verificari.py "<Proiect>"
.venv/bin/python -B .github/unelte/verificari.py --toate
```

Scriptul iese cu codul 1 la probleme: livrabile lipsă, un plan fără perechea lui PDF sau PNG, imagini cu metadate, un PDF care nu e A3, linkuri relative rupte, ș sau ț cu sedilă, căi absolute sau coordonate GPS, calcule greșite într-o listă de materiale. Variantele în plus se verifică odată cu proiectul: toate listele `lista_materiale*.md`, toate planurile și sursele din subfoldere. Avertismentele le citești și decizi; unul dintre ele apare pentru fiecare fișier din folder fără link în README. Abia apoi faci commit-ul, după regulile din [`copilot-instructions.md`](../copilot-instructions.md).

## Uneltele agentului

Uneltele lui Copilot pe care le-au folosit agenții și la ce:

| Unealta | La ce |
|---|---|
| `view` | Orice imagine: fotografia, zoom-urile cu grilă, segmentele numerotate, fiecare randare și PNG-ul planului, mărit pe detalii. Nu declari o imagine gata fără s-o fi văzut |
| `bash` | Scripturile de aici, cu `.venv/bin/python -B`, și git |
| `web_search`, `web_fetch` | Idei, fișe tehnice, prețuri |
| Playwright (`browser_navigate`, `browser_snapshot`, `browser_take_screenshot`) | Magazinele care blochează cererile automate |
| `task` | Subagenții: `explore` citește în depozit, `research` caută surse și prețuri, `general-purpose` face randări sau planul, `rubber-duck` revizuiește conceptul și planul, `code-review` verifică scripturile |
| `sql` | Lista de sarcini (`todos`), când lucrezi cu subagenți în paralel |
| `ask_user` | Cotele care lipsesc și alegerile de design, câte o întrebare pe rând |
| `store_memory`, `vote_memory` | Faptele durabile, pe lângă [memorie.md](../memorie/memorie.md) |

## Lucrul în paralel, cu subagenți

Variantele din beton ale polițelor (C și D) s-au lucrat cu 10 subagenți în paralel: idei, tehnică, prețurile vechi, prețurile noi, textura, testul mediului, revizuirea conceptului, randările, planul și documentația. Ce a mers:

- **Coordonatorul**, adică agentul principal, păstrează `design.py`, memoria și commit-ul. Subagenții scriu doar în fișierele primite. Dacă unul se oprește la jumătate, coordonatorul îi termină treaba.
- **Mediul îl testezi o singură dată**, înainte să trimiți cercetarea: `preturi.py` pe un link și o căutare. Dacă rețeaua e blocată, nu trimiți zece agenți să afle același lucru.
- **Cerințele sunt puține și precise**: ce citește subagentul, ce scrie, cum arată rezultatul și când se oprește. Îi dai tot contextul, pentru că nu vede conversația.
- **Revizuirea conceptului** (`rubber-duck`) vine înainte de randări: o greșeală găsită după randare costă încă o randare.
- **Cheile din `design.py`** nu le redenumești cât timp lucrează subagenții cu ele.
- **Notele planului** le scrii ca paragrafe și rulezi `plan.py verifica` după fiecare schimbare.
- **Textele subagenților** le rescrii în română, cu diacritice, înainte să intre în depozit.
- **Uneltele noi** le aduce în trusă un subagent separat, în paralel, ca să nu blocheze proiectul: așa a cerut utilizatorul. O unealtă generală scrisă într-un proiect intră aici cu test, după pașii de la „Testele”; subagentul compară întâi cu ce e deja în trusă și nu aduce dubluri.

Un tipar de cerere pentru un subagent:

```text
Lucrezi pentru proiectul „<Proiect>” din depozitul design-interior. Depozitul e public: fără date personale.
Scrii în română, cu diacritice.
Citește: .github/memorie/memorie.md (secțiunea „<…>”) și .github/surse/<proiect>/design.py.
Sarcina: <una singură, cu cotele și materialele necesare>.
Unelte: .github/unelte/ (vezi README.md de acolo); rulezi cu .venv/bin/python -B.
Scrii doar în: <fișierele tale>. Nu faci commit și nu modifici memoria.
Rezultatul: <forma exactă, de exemplu tabelul Produs | Preț | Link | Data verificării>.
Te oprești când: <criteriul>.
```

## Testele

```sh
.venv/bin/python -B -m unittest discover -s .github/unelte/teste
.venv/bin/python -B -m unittest discover -s .github/unelte/teste -v -k Camera       # doar o parte
```

Sunt 89 de teste: 57 în `test_unelte.py` și 32 în `test_unelte_noi.py`, pentru uneltele aduse din „Comodă birou”. Niciunul nu are nevoie de rețea. Ce verifică:
- paritatea cu scripturile proiectelor: aceleași proiecții ca `camera.py` de la cuier și de la polițe, aceeași calibrare (rms 0,5956 px la polițe și 0,5961 px la cuier) și aceleași calcule de rezistență;
- fotografiile: `pregateste` scoate EXIF-ul, GPS-ul și comentariul JPEG, rotește după EXIF și trece culorile în sRGB;
- randarea, texturile, culorile (ΔE00 pe perechile de referință publicate), comparația și planul A3;
- prețurile, pe un server local, și verificările, pe proiecte sintetice, inclusiv cu variante în plus în același folder;
- liniile de comandă ale modulelor;
- planul PDF, pe planuri sintetice făcute în test (o cameră de 327 × 366 cm la ~1:52,2, cu un gol de ușă în dreptul etichetei), fără planul real, care are date personale;
- ușile, pe cazul Cioata Galla 120, și desenul lor într-un plan care trece `verifica_figura`;
- mărirea pentru LSD, muchia slabă, profilul erorii pe o scenă sintetică, pagina care cere browserul, PRP-ul de la Cioata și foaia de produse.

Trei teste compară uneltele cu sursele variantelor din beton (`beton.py`, `design.py` și `verifica_plan.py`). Ele rulează când există `.github/surse/polite-viniluri/beton/` sau când variabila `UNELTE_BETON` arată spre o copie a folderului. Pe o ramură fără acel folder, se sar. La fel, două teste compară `veneer`, `reeding` și `callout` cu sursele din `.github/surse/comoda-birou/`, iar testele planului PDF se sar dacă PyMuPDF nu e instalat.

O unealtă nouă intră aici când a folosit la un proiect și poate folosi și la altele:
1. O pui în modulul potrivit sau într-unul nou, cu nume în română, fără diacritice, și cu docstring în română.
2. Adaugi un test. Dacă vine dintr-un proiect, adaugi și un test de paritate cu scriptul de acolo.
3. O treci în catalogul de mai sus și, dacă schimbă pașii de lucru, în [memorie](../memorie/memorie.md).
4. Rulezi toate testele.

Scripturile proiectelor publicate nu le schimbi: ele trebuie să reproducă imaginile de pe site.

## Capcane

- **`materiale.sample` oglindea invers.** În scripturile polițelor, oglindirea texturii mapa coloana 0 pe ultima, așa că textura apărea întoarsă. Aici e corectat. Imaginile publicate rămân cum sunt, dar o randare nouă nu mai iese identică, pixel cu pixel, cu cea veche.
- **`scaled(k)`** e relativ la fotografie, nu la scara de acum: `cam1.scaled(4)` e camera pentru fotografia mărită de 4 ori, oricare ar fi scara lui `cam1`.
- **Funcțiile de culoare** ale fețelor înmulțesc cu `M[yy, xx][..., None]`, nu cu `M[yy, xx]`: harta de lumină are un singur canal.
- **Fotografiile.** Nu folosești `sips`, pentru că păstrează GPS-ul. Pillow, începând cu versiunea 9.4, copiază comentariul JPEG în fișierul nou, de aceea `pregateste` golește `info` înainte de salvare și verifică rezultatul. Fără conversia din Display P3 în sRGB, culorile ies spălăcite.
- **Scara planului PDF.** Scara din cartuș nu e sigură, pentru că PDF-ul poate fi scalat la tipărire. Planul etajului din „Comodă birou” scria 1:50, dar era la ~1:52,2: cu scara din cartuș, camera ar fi ieșit cu ~14 cm mai îngustă. Scara reală o iei dintr-o cotă scrisă pe plan (`plan_pdf.py camera --cota-cm`) și o verifici pe a doua (`--verifica-cm`).
- **Fonturile fără tabel Unicode.** Planurile exportate din Archicad au fonturi compuse (Type0) fără tabel Unicode: textul iese „�”, iar căutarea obișnuită din PyMuPDF nu găsește nimic. `plan_pdf.py` citește textul cu `TEXT_CID_FOR_UNKNOWN_UNICODE`, iar `info` arată câte caractere sunt așa.
- **Planurile PDF au date personale în cartuș**: nume, adresă, semnături, cod QR. PDF-ul, calea lui și randările paginii întregi nu intră în depozit; `plan_pdf.py` te avertizează când salvezi o randare într-un loc din depozit neignorat de git. În fișiere scrii doar cotele.
- **BoConcept România se citește doar din browser.** `curl`, `web_fetch` și `preturi.py` primesc doar verificarea Cloudflare („Just a moment...”, cod 403) sau subsolul paginii. Cu Playwright, prețul e după „Rec. retail price”, în RON, cu TVA, iar dimensiunile, după „Dimensions and weights”.
- **Instrucțiunile de montaj** în PDF ale producătorului dau cotele exacte. Comoda BoConcept Element are pe site 115 × 46½ × 91 cm, iar în instrucțiuni 115 × 46,2 × 90,8 cm, cu corpul de 77,8 cm. Le citești cu PyMuPDF, ca pe planuri.
- **Dedeman vinde unele șuruburi doar la cutie.** Șuruburile Spax de 4,5 × 60 mm se vând doar la cutia de 500, cu 225 lei, deși pagina arată „0,45 lei/bucată”. `preturi.py` semnalează „Se livrează la: cutie (500 buc)”, iar în listă treci cutia.
- **Profilul erorii la calibrare.** Într-o poză fără colțul camerei, cu obiectul cunoscut în poziție liberă, tavanul poate rămâne nedeterminat. La „Comodă birou”, cu tavanul fixat la 230, 250 sau 270 cm, eroarea a rămas aceeași, 0,5476 px, iar biroul s-a mutat: de la −38 la +33 cm față de perete. Limitele puse parametrilor nu rezolvă problema, doar o ascund. Faci profilul cu `camera.profil` și dai tavanul măsurat.
- **Tavanul presupus** strică toate cotele: ceri tavanul măsurat înainte de calibrare.
- **`out/`** și `__pycache__/` nu intră în commit. Imaginile finale le copiezi în folderul proiectului.
