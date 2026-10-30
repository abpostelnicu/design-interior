# Sursele imaginilor din „Polițe viniluri”

Scripturile din acest folder generează randările, imaginea de comparație și planul tehnic din [`Polite viniluri/`](../../../Polite%20viniluri/). Rulate fără modificări, produc exact fișierele publicate, octet cu octet. Singura excepție e data creării din PDF. Folderele care încep cu punct nu apar pe site.

Tiparul general al proiectelor e în memoria comună: [`.github/memorie/memorie.md`](../../memorie/memorie.md). Aici sunt doar uneltele. Scripturile pornesc de la cele din [`cuier-hol/`](../cuier-hol/README.md), cu trei diferențe: camera e calibrată pe obiecte cu dimensiuni cunoscute (nu pe tavan), randarea folosește un buffer de adâncime și texturile vin din fotografie.

Sursele variantelor C și D, cu polițele din beton decorativ și stejar, sunt în subfolderul [`beton/`](beton/README.md). Au același tipar și scriu în `Polite viniluri/` fișiere cu nume noi, fără să le atingă pe cele de aici.

## Fișiere

| Fișier | Rol |
|---|---|
| `curata_foto.py` | Face `original.jpg` din fotografia primită: fără EXIF, cu televizorul stins (pe ecran se vedeau numele rețelelor Wi-Fi din jur) și fără persoana din ușa din dreapta. Se rulează o singură dată |
| `original.jpg` | Fotografia peretelui, 1024 × 768, deja curățată, fără metadate |
| `segments.json` | Segmentele de dreaptă din fotografie, grupate pe muchii: tavanul, colțul din stânga, capătul peretelui din dreapta, pardoseala, plinta, marginile televizorului și ale comodei |
| `camera.py` | Calibrează aparatul foto din aceste segmente și salvează `camera.json` |
| `design.py` | Sursa unică pentru cote: `SITE` (peretele; estimările sunt marcate `# est.`), produsele existente (`TV`, `CABINET`, `CENTER`, `TOWER`, `LP`), `D` (polițele, opritoarele și tijele), `ROWS` (cât din fiecare poliță ocupă discurile în randări) și `rod_check()` (verificarea tijelor) |
| `core.py` | Baza randării: camera la rezoluția de lucru, `Canvas.face` (fețe plane texturate, cu buffer de adâncime; cu `color=None` doar ascunde, de exemplu boxele din poză), `Canvas.multiply_wall` (umbre pe perete) și `wall_light_map` (lumina peretelui din poză) |
| `materials.py` | Texturile: stejarul (fibra luată din parchetul din poză, adus la tonul ramei comodei, lipit din lamele) și culorile cotoarelor de discuri |
| `render.py` | Randează în fotografie propunerea A (opritoare îmbrăcate în stejar) și varianta B (opritoare negre), plus `out/acum.jpg` |
| `compare.py` | Face imaginea cu trei panouri: Acum, A, B (după `render.py`) |
| `drawing.py` | Desenează planul tehnic A3 la 1:15: vedere frontală, secțiune laterală și plan, plus detaliul A (prinderea ascunsă) la 1:3, detaliul B (opritorul) la 1:5 și notele |

## Cum regenerezi imaginile

```sh
cd ".github/surse/polite-viniluri"
python3 -m venv .venv
.venv/bin/pip install pillow numpy matplotlib opencv-python-headless scipy
.venv/bin/python render.py     # out/propunere_A_stejar.jpg, out/varianta_B_opritoare_negre.jpg și out/acum.jpg
.venv/bin/python compare.py    # out/comparatie_acum_vs_propuneri.jpg (după render.py)
.venv/bin/python drawing.py    # out/plan_tehnic_polite_viniluri.pdf și .png
cp out/propunere_A_stejar.jpg out/varianta_B_opritoare_negre.jpg out/comparatie_acum_vs_propuneri.jpg \
   out/plan_tehnic_polite_viniluri.pdf out/plan_tehnic_polite_viniluri.png "../../../Polite viniluri/"
```

`.venv/bin/python design.py` afișează cotele derivate: pozițiile polițelor și ale tijelor, distanțele până la boxă și până la dispozitivul alb, numărul de discuri, greutățile și efortul din tije.

## Calibrarea

Peretele a fost dat doar ca lățime (419 cm) și înălțime (250 cm), fără alte repere măsurate. De aceea camera se calibrează pe obiectele cu dimensiuni cunoscute din fișele producătorilor: televizorul (216,6 × 123,6 cm), comoda (242 × 48 × 67 cm) și lățimea peretelui.

```sh
.venv/bin/python camera.py        # tavanul rămâne necunoscut: ~261,9 cm, eroare medie 0,6 px (camera.json)
.venv/bin/python camera.py 250    # tavanul fixat la 250 cm: eroare medie 4,6 px, deci 250 nu se potrivește cu poza
```

Polițele se așază față de televizor (discurile de sus se termină la marginea de sus a televizorului; lateral, 10 cm), așa că tavanul nu le schimbă poziția. Dacă se remăsoară poziția televizorului, se schimbă `TV` în `design.py` și se regenerează tot.

## Coordonatele

Toate cotele sunt în cm:
- **X** e de-a lungul peretelui cu televizorul. X = 0 e în colțul din stânga, iar valorile cresc spre dreapta, până la 419.
- **Y** e înălțimea; Y = 0 e pardoseala.
- **Z** iese din perete spre aparatul foto; Z = 0 e fața peretelui.

`Camera.backproject(uv, "Z", 0)` transformă un pixel de pe perete în coordonate reale. Așa s-au estimat pozițiile boxelor, ale dispozitivului alb și înălțimea televizorului.

## Ce e diferit față de cuier

- **Bufferul de adâncime.** `Canvas.face` calculează fiecare față pixel cu pixel, cu raza din aparat. Polițele, discurile și opritoarele se acoperă unele pe altele, așa că ordinea de desenare nu mai contează. Boxele din fotografie se desenează doar în bufferul de adâncime (`Scene.occluders`), ca tot ce e în spatele lor să rămână ascuns.
- **Rândurile de discuri** sunt generate cu un generator aleator fix (`seed`), separat de cel al texturilor de stejar: discurile sunt aceleași în A și în B, iar rezultatul e reproductibil. Copertele de la capetele rândurilor au doar culori care nu se confundă cu stejarul (fără maro și galben); altfel, o copertă maro lângă opritorul de stejar pare o bucată de lemn.
- **Lumina.** Polițele urmează lumina peretelui din poză doar în parte (`Scene.M`), pentru că ies 33 cm din perete. Umbrele de pe perete se sting înainte de capacul boxelor de podea, care stau în fața peretelui. În dreptul grosimii poliței, dincolo de capete, peretele primește și umbra de sub poliță, și pe cea de deasupra; altfel rămâne acolo o bandă luminoasă.
- **Planul la 1:15.** Peretele de 419 cm încape pe A3 la 1:15 (320 mm cu cotele), cu planul dedesubt; secțiunea, detaliile și notele stau într-o coloană de 88 mm în dreapta.
- **Confidențialitatea.** `curata_foto.py` șterge din fotografie ecranul aprins și persoana din ușă. Verifică orice fotografie nouă: ecrane, documente, numere de înmatriculare, persoane.
