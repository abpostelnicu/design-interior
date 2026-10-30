# Sursele imaginilor din „Polițe viniluri beton”

Scripturile din acest folder generează randările, imaginea de comparație și planul tehnic din [`Polite viniluri beton/`](../../../Polite%20viniluri%20beton/): polițe din microciment (beton decorativ) pe miez de placaj, legate printr-o verticală din stejar. Generatoarele aleatoare au semințe fixe, așa că o rulare nouă dă aceleași imagini. Folderele care încep cu punct nu apar pe site.

Tiparul general al proiectelor e în memoria comună: [`.github/memorie/memorie.md`](../../memorie/memorie.md). Aici sunt doar uneltele. Scripturile pornesc de la cele din [`polite-viniluri/`](../polite-viniluri/README.md), proiectul cu polițe din stejar, care la rândul lor pornesc de la [`cuier-hol/`](../cuier-hol/README.md). Ce s-a schimbat e în secțiunea „Ce e nou față de polite-viniluri”, la final.

## Fișiere

| Fișier | Rol |
|---|---|
| `curata_foto.py` | Face `original.jpg` din fotografia primită: fără EXIF, cu televizorul stins (pe ecran se vedeau numele rețelelor Wi-Fi din jur) și fără persoana din ușa din dreapta. Se rulează o singură dată. Preluat neschimbat |
| `original.jpg` | Fotografia peretelui, 1024 × 768, deja curățată, fără metadate. Preluată neschimbată |
| `segments.json` | Segmentele de dreaptă din fotografie, grupate pe muchii: tavanul, colțul din stânga, capătul peretelui din dreapta, pardoseala, plinta, marginile televizorului și ale comodei. Preluat neschimbat |
| `camera.py` | Calibrează aparatul foto din aceste segmente și salvează `camera.json`. Preluat neschimbat, ca și `camera.json` |
| `design.py` | Sursa unică pentru cote: `SITE` (peretele; estimările sunt marcate `# est.`), produsele existente (`TV`, `CABINET`, `CENTER`, `TOWER`, `LP`), `D` (polițele, miezul și microcimentul, verticala, cepurile, tijele, canalele, șablonul, proba de încărcare și opritoarele), `VERTS` (pozițiile verticalelor), `ROWS` (unde stau discurile în randări), `capacity()`, `loads()`, `rod_check()` (îndoirea tijelor) și `rod_pull()` (smulgerea din perete) |
| `beton.py` | Tonurile microcimentului: gri natural pentru A și antracit pentru B, cu antracitul măsurat pe fronturile comodei din poză (`measure_fronts`). Rulat singur, scrie mostre în `out/` (`beton_gri.png`, `beton_antracit.png`, `beton_comparatie.png`) și afișează diferența de culoare față de fronturi și față de perete |
| `core.py` | Baza randării: camera la rezoluția de lucru, `Canvas.face` (fețe plane texturate, cu buffer de adâncime; cu `color=None` doar ascunde, de exemplu boxele din poză), `Canvas.multiply_wall` (umbre pe perete) și `wall_light_map` (lumina peretelui din poză). Preluat neschimbat |
| `materials.py` | Texturile: stejarul (fibra luată din parchetul din poză, adus la tonul ramei comodei, lipit din lamele) și culorile cotoarelor de discuri. Preluat neschimbat |
| `render.py` | Randează în fotografie propunerea A (beton gri și stejar) și varianta B (beton antracit și stejar), plus `out/acum.jpg`. Cu argumentul `A` sau `B`, randează doar varianta aceea |
| `compare.py` | Face imaginea cu trei panouri: Acum, A, B (după `render.py`) |
| `drawing.py` | Desenează planul tehnic A3 la 1:15, comun pentru A și B: vedere frontală, secțiune și plan, plus detaliile A (tija), B (opritorul) și C (îmbinarea verticalei), notele și cotele de măsurat. Calea de ieșire se poate da ca argument |
| `verifica_plan.py` | Verifică planul fără să scrie fișiere: texte ieșite din pagină, texte suprapuse, note sau legendă intrate în desene, indicații care trec prin texte. Iese cu codul 1 dacă găsește ceva |

## Cum regenerezi imaginile

```sh
cd ".github/surse/polite-viniluri-beton"
python3 -m venv .venv && .venv/bin/pip install pillow numpy matplotlib opencv-python-headless scipy
.venv/bin/python design.py     # cotele derivate, în terminal; nu scrie fișiere
.venv/bin/python beton.py      # opțional: mostrele de beton, în out/
.venv/bin/python render.py     # out/propunere_A_beton_gri.jpg, out/varianta_B_beton_antracit.jpg și out/acum.jpg
.venv/bin/python compare.py    # out/comparatie_acum_vs_propuneri.jpg (după render.py)
.venv/bin/python drawing.py    # out/plan_tehnic_polite_viniluri_beton.pdf și .png
.venv/bin/python verifica_plan.py   # textele planului: în pagină, fără suprapuneri
cp out/propunere_A_beton_gri.jpg out/varianta_B_beton_antracit.jpg out/comparatie_acum_vs_propuneri.jpg \
   out/plan_tehnic_polite_viniluri_beton.pdf out/plan_tehnic_polite_viniluri_beton.png "../../../Polite viniluri beton/"
```

`design.py` afișează cotele derivate: pozițiile polițelor, ale verticalei și ale tijelor, rândurile de discuri, distanțele până la boxă și până la dispozitivul alb, numărul de discuri, greutățile, efortul din tije și smulgerea.

Toate fișierele ies în `out/`, care nu se publică. În `Polite viniluri beton/` se copiază, cu aceleași nume:

| Din `out/` | Ce e |
|---|---|
| `propunere_A_beton_gri.jpg` | randarea propunerii A |
| `varianta_B_beton_antracit.jpg` | randarea variantei B |
| `comparatie_acum_vs_propuneri.jpg` | comparația Acum, A, B |
| `plan_tehnic_polite_viniluri_beton.pdf` și `.png` | planul tehnic |

`acum.jpg` și mostrele `beton_*.png` rămân în `out/`: sunt doar pentru verificare.

## Calibrarea

Peretele a fost dat doar ca lățime (419 cm) și înălțime (250 cm), fără alte repere măsurate. De aceea camera se calibrează pe obiectele cu dimensiuni cunoscute din fișele producătorilor: televizorul (216,6 × 123,6 cm), comoda (242 × 48 × 67 cm) și lățimea peretelui.

```sh
.venv/bin/python camera.py        # tavanul rămâne necunoscut: ~261,9 cm, eroare medie 0,6 px (camera.json)
.venv/bin/python camera.py 250    # tavanul fixat la 250 cm: eroare medie 4,6 px, deci 250 nu se potrivește cu poza
```

Polițele se așază față de televizor (discurile de sus se termină la marginea de sus a televizorului; lateral, 10 cm), iar verticala față de marginea din stânga a boxei de podea din dreapta, așa că tavanul nu le schimbă poziția. Dacă se remăsoară poziția televizorului sau a boxei, se schimbă `TV` sau `TOWER` în `design.py` și se regenerează tot.

## Coordonatele

Toate cotele sunt în cm:
- **X** e de-a lungul peretelui cu televizorul. X = 0 e în colțul din stânga, iar valorile cresc spre dreapta, până la 419.
- **Y** e înălțimea; Y = 0 e pardoseala.
- **Z** iese din perete spre aparatul foto; Z = 0 e fața peretelui.

`Camera.backproject(uv, "Z", 0)` transformă un pixel de pe perete în coordonate reale. Așa s-au estimat pozițiile boxelor, ale dispozitivului alb și înălțimea televizorului.

## Ce e diferit față de cuier

- **Bufferul de adâncime.** `Canvas.face` calculează fiecare față pixel cu pixel, cu raza din aparat. Polițele, verticala, discurile și opritoarele se acoperă unele pe altele, așa că ordinea de desenare nu mai contează. Boxele din fotografie se desenează doar în bufferul de adâncime (`Scene.occluders`), ca tot ce e în spatele lor să rămână ascuns.
- **Rândurile de discuri** sunt generate cu un generator aleator fix (`seed`), separat de cel al texturilor de stejar: discurile sunt aceleași în A și în B, iar rezultatul e reproductibil. Copertele de la capetele rândurilor au doar culori care nu se confundă cu stejarul (fără maro și galben); altfel, o copertă maro lângă opritorul de stejar pare o bucată de lemn.
- **Lumina.** Polițele urmează lumina peretelui din poză doar în parte (`Scene.M`), pentru că ies 33 cm din perete. Umbrele de pe perete se sting înainte de capacul boxelor de podea, care stau în fața peretelui. În dreptul grosimii poliței, dincolo de capete, peretele primește și umbra de sub poliță, și pe cea de deasupra; altfel rămâne acolo o bandă luminoasă.
- **Planul la 1:15.** Peretele de 419 cm încape pe A3 la 1:15, cu planul dedesubt; secțiunea, detaliile și notele stau în dreapta.
- **Confidențialitatea.** `curata_foto.py` șterge din fotografie ecranul aprins și persoana din ușă. Verifică orice fotografie nouă: ecrane, documente, numere de înmatriculare, persoane.

## Cum schimbi designul

- **Cotele** sunt toate în `D`, din `design.py`. După o schimbare, rulează `design.py` și verifică rezervele din tije (`rod_check()`) și smulgerea (`rod_pull()`), apoi regenerează imaginile și planul.
- **Încă o verticală** (de exemplu, pe polița de jos, în stânga): adaugi poziția ei, în cm de la capătul din stânga al poliței, în `VERTS`. Capacitatea și greutățile se recalculează singure, dar rândurile de discuri din randări sunt în `ROWS`, deci și ele trebuie împărțite în dreptul verticalei noi. Verticala stă între două tije, ca cepurile ei să nu întâlnească canalele.
- **Notele planului** sunt paragrafe în `notes()`, din `drawing.py`. `text_block()` le rupe singur pe lățimea `NOTE_W` și ține cifrele lipite de unități. Dacă adaugi text, rulează `verifica_plan.py` și privește PNG-ul.
- **Tonurile betonului** sunt în `TONES`, din `beton.py`, iar variantele randate (ton, nume de fișier) în `VARIANTS`, din `render.py`.

## Ce e nou față de polite-viniluri

- `design.py`: polițele au miez de placaj și microciment (greutatea ține cont de amândouă), plus verticala, cepurile, șablonul, proba de încărcare, `capacity()` cu golurile dintre verticală și opritoare, tijele de clasa 8.8 și `rod_pull()`.
- `beton.py` e nou: tonurile de beton și măsurarea fronturilor comodei.
- `render.py`: texturile de microciment, muchiile rotunjite, care prind mai multă lumină, verticala din lamele de stejar, cu fibra pe verticală, și cele două variante de ton. Opritoarele sunt în ambele variante cu placă de stejar.
- `drawing.py`: detaliul C, cu piciorul verticalei, lipit în locașul poliței de jos, și rostul de sub cea de sus. Notele sunt paragrafe: `wrap()` le rupe pe lățimea coloanei, măsurând textul cu fontul real.
- `verifica_plan.py` e nou: verifică automat textele planului.
- `camera.py`, `core.py`, `materials.py`, `curata_foto.py`, `original.jpg`, `segments.json` și `camera.json` sunt preluate neschimbate.
