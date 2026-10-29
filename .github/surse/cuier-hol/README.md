# Sursele imaginilor din „Cuier hol”

Scripturile din acest folder generează randările, imaginea de comparație și planul tehnic din [`Cuier hol/`](../../../Cuier%20hol/). Rulate fără modificări, produc exact fișierele publicate, octet cu octet. Singura excepție e data creării din PDF. Folderele care încep cu punct nu apar pe site.

Tiparul general al proiectelor (ce se livrează, convențiile depozitului, coordonarea între agenți) e în memoria comună: [`.github/memorie/memorie.md`](../../memorie/memorie.md). Aici sunt doar uneltele.

## Fișiere

| Fișier | Rol |
|---|---|
| `original.jpg` | Fotografia holului, 768 × 1024, fără metadate |
| `segments.json` | Segmentele de dreaptă din fotografie, grupate după muchia camerei căreia îi aparțin (colțuri, tavan, pardoseală, fereastră, ușă) |
| `camera.py` | Calibrează aparatul foto din aceste segmente. Rezultatul e salvat în `camera_H270.json` (270 = înălțimea tavanului în cm, care dă scara) |
| `design.py` | Sursa unică pentru cote: `SITE` conține cotele măsurate (cele estimate sunt marcate `# est.`), `D` parametrii designului, iar `Layout` poziționează panoul |
| `render.py` | Randează cele două variante în fotografie |
| `compare.py` | Face imaginea cu trei panouri: Acum, A, B |
| `drawing.py` | Desenează planul tehnic A3, la scara 1:15 |

## Cum regenerezi imaginile

```sh
cd ".github/surse/cuier-hol"
python3 -m venv .venv
.venv/bin/pip install pillow numpy matplotlib opencv-python-headless scipy
.venv/bin/python render.py     # out/propunere_stejar.jpg și out/propunere_antracit.jpg
.venv/bin/python compare.py    # out/comparatie_acum_vs_propuneri.jpg (după render.py)
.venv/bin/python drawing.py    # out/plan_tehnic_cuier.pdf și .png
```

Apoi copiezi rezultatele în proiect. Randările se redenumesc la copiere:

```sh
cp out/propunere_stejar.jpg "../../../Cuier hol/propunere_A_stejar.jpg"
cp out/propunere_antracit.jpg "../../../Cuier hol/varianta_B_antracit.jpg"
cp out/comparatie_acum_vs_propuneri.jpg out/plan_tehnic_cuier.pdf out/plan_tehnic_cuier.png "../../../Cuier hol/"
```

Calibrarea o refaci doar dacă se schimbă `segments.json` sau înălțimea tavanului: `.venv/bin/python camera.py 270`. Eroarea medie de acum e de 0,6 px; o valoare sub 1 px e bună.

## Coordonatele

Toate cotele sunt în cm:
- **X** e de-a lungul peretelui cu fereastra. X = 0 e în colțul cu peretele din dreapta; valorile negative merg spre stânga, adică spre fereastră și spre peretele cu ușa de intrare.
- **Y** e înălțimea; Y = 0 e pardoseala.
- **Z** iese din perete spre aparatul foto; Z = 0 e fața peretelui.

`Camera.backproject(uv, "Z", 0)` transformă un pixel de pe perete în coordonate reale. Așa s-au estimat din poză prizele, golul ușii și fereastra, înainte de măsurători.

## Cum le adaptezi pentru un proiect nou

1. Copiezi folderul în `.github/surse/<proiect>/`. Numele folderului e fără diacritice, cu cratimă între cuvinte.
2. Pui fotografia nouă ca `original.jpg`, salvată cu PIL ca să nu păstreze metadatele:
   ```python
   from PIL import Image, ImageOps
   ImageOps.exif_transpose(Image.open(sursa)).convert("RGB").resize((768, 1024)).save("original.jpg", quality=95)
   ```
   - `exif_transpose` rotește poza după orientarea din telefon, înainte să se piardă metadatele.
   - `camera.py` presupune o imagine de 768 × 1024 (`PP` e centrul ei). Dacă fotografia are alt raport, ajustezi `PP`.
   - Nu folosi `sips`: păstrează coordonatele GPS din pozele de pe telefon.
3. Detectezi segmentele cu `cv2.createLineSegmentDetector(cv2.LSD_REFINE_ADV)` pe imaginea alb-negru. Desenezi segmentele numerotate peste poză și le alegi pe indici. Le scrii în `segments.json`, grupate pe muchii: colțurile camerei, tavanul, pardoseala, ramele ferestrelor și ale ușilor.
4. Rescrii în `camera.py` funcția `_line3d`, adică dreptele 3D ale fiecărui grup. Ajustezi și `NAMES` și valorile de pornire din `calibrate` pentru dimensiunile necunoscute ale camerei. Calibrezi cu înălțimea tavanului măsurată și verifici eroarea medie.
5. În `design.py` treci cotele: în `SITE` cele măsurate și cele estimate, marcate `# est.`, iar în `D` parametrii obiectului.
6. În `render.py` schimbi variantele (`VARIANTS`) și funcțiile de desenare (`draw_*`).
   - Așezi obiectele după geometria din poză (`cam1.q`), nu după cotele măsurate, ca să se alinieze vizual. De exemplu, aici plinta apare în poză la 7,26 cm, deși măsurată are 8 cm.
   - Planul tehnic folosește cotele măsurate.
7. În `drawing.py` schimbi vederile, notele și numele fișierului de ieșire.
8. În `compare.py` schimbi titlurile și subtitlurile.
