# Design Interior

Proiecte de amenajare interioară.

Fiecare proiect are un folder propriu, cu documentația și fișierele aferente. Acest README oferă o prezentare generală și legături către documentația fiecărui proiect.

## Proiecte

| Folder | Conținutul folderului | README specific |
|---|---|---|
| [Cuier hol](Cuier%20hol/) | Comparație între situația actuală și propuneri, randări, plan tehnic în PDF și PNG, listă de materiale cu prețuri și linkuri | [Prezentare, cote, montaj pas cu pas și întreținere](Cuier%20hol/README.md) |
| [Polite viniluri](Polite%20viniluri/) | Peretele cu televizorul: comparație între situația actuală și propuneri, randări, plan tehnic în PDF și PNG, listă de materiale cu prețuri și linkuri | [Prezentare, cote, cum e gândit, execuție, montaj pas cu pas și întreținere](Polite%20viniluri/README.md) |
| [Comoda birou](Comoda%20birou/) | Dormitor 2, lângă birou: comparație între situația actuală și propuneri, randări, alternativa Cioata Galla 120, plan tehnic în PDF și PNG, listă de materiale cu prețuri și linkuri | [Prezentare, cote, cum e gândit, alternative, montaj pas cu pas și întreținere](Comoda%20birou/README.md) |

## Organizarea documentației

- README-ul fiecărui folder descrie proiectul, explică fișierele disponibile și include detaliile specifice de execuție.
- Randările, planurile tehnice și listele de materiale se păstrează în folderul proiectului.
- La adăugarea unui proiect, creează un folder cu propriul README și adaugă legătura către acesta în tabelul de mai sus.
- Depozitul este public, așa că documentația, numele fișierelor, imaginile și mesajele commit-urilor nu trebuie să conțină date personale: adresa casei, numere de înmatriculare sau coordonatele GPS din metadatele fotografiilor. Commit-urile se fac cu adresa de email „noreply” de la GitHub.

## Site

Documentația se poate trimite oricui ca site: <https://abpostelnicu.github.io/design-interior/>.

- Site-ul se generează automat cu GitHub Pages din fișierele Markdown ale depozitului, la fiecare modificare pe ramura `master`, deci nu se editează separat. Un proiect nou (folder cu `README.md`) apare singur în meniul site-ului.
- Linkurile dintre fișiere rămân cele relative obișnuite (de exemplu `Cuier%20hol/README.md`); pe site duc automat la paginile corespunzătoare.
- Depozitul și site-ul sunt publice: le poate deschide oricine are linkul. Motoarele de căutare sunt rugate să nu afișeze site-ul în rezultate (`indexare: false` în `_config.yml`).
- Aspectul paginilor este în `_layouts/default.html` și `assets/`, iar publicarea se face prin `.github/workflows/publicare-site.yml`.
