# Design Interior

Proiecte de amenajare interioară.

Fiecare proiect are un folder propriu, cu documentația și fișierele aferente. Acest README oferă o prezentare generală și legături către documentația fiecărui proiect.

## Proiecte

| Folder | Conținutul folderului | README specific |
|---|---|---|
| [Cuier hol](Cuier%20hol/) | Comparație între situația actuală și propuneri, randări, plan tehnic în PDF și PNG, listă de materiale cu prețuri și linkuri | [Prezentare, cote, montaj pas cu pas și întreținere](Cuier%20hol/README.md) |

## Organizarea documentației

- README-ul fiecărui folder descrie proiectul, explică fișierele disponibile și include detaliile specifice de execuție.
- Randările, planurile tehnice și listele de materiale se păstrează în folderul proiectului.
- La adăugarea unui proiect, creează un folder cu propriul README și adaugă legătura către acesta în tabelul de mai sus.

## Site

Documentația se poate trimite oricui ca site: <https://abpostelnicu.github.io/design-interior/>.

- Site-ul se generează automat cu GitHub Pages din fișierele Markdown ale depozitului, la fiecare modificare pe ramura `master`, deci nu se editează separat. Un proiect nou (folder cu `README.md`) apare singur în meniul site-ului.
- Linkurile dintre fișiere rămân cele relative obișnuite (de exemplu `Cuier%20hol/README.md`); pe site duc automat la paginile corespunzătoare.
- Site-ul este public, chiar dacă depozitul este privat: îl poate deschide oricine are linkul. Motoarele de căutare sunt rugate să nu-l afișeze în rezultate (`indexare: false` în `_config.yml`).
- Aspectul paginilor este în `_layouts/default.html` și `assets/`, iar publicarea se face prin `.github/workflows/publicare-site.yml`.
