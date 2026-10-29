# Instrucțiuni pentru agenții din acest depozit

Depozitul conține proiectele de amenajare interioară ale casei. Fiecare proiect are un folder cu README propriu, iar documentația se publică automat pe un site GitHub Pages public.

- **Limba:** scrie totul în română, cu diacritice (ș și ț cu virgulă): documente, comentarii, mesaje de commit, răspunsuri și mesaje către alți agenți. Numele de fișiere sunt în română, fără diacritice.
- **Confidențialitate:** depozitul și site-ul sunt publice. Adresa casei, numerele de înmatriculare, coordonatele GPS sau metadatele EXIF și căile absolute de pe calculator nu apar în texte, fișiere, imagini sau commit-uri. Commit-urile se fac doar cu adresa de email „noreply” de la GitHub.
- **Proiecte de amenajare:** propunerile, randările, planurile tehnice, listele de materiale și montajul le face agentul „Designer interior” din `.github/agents/designer-interior.agent.md`. Dacă lucrezi fără el, urmezi tiparul de design din memorie.
- **Memoria comună** e în `.github/memorie/`. Înainte să lucrezi la un proiect, citești `memorie.md`. La final adaugi o intrare în `jurnal.md` și treci în `memorie.md` ce folosește și altor proiecte: cote noi, preferințe, corecturi ale utilizatorului, lecții. Așa învață și ceilalți agenți din ce ai făcut.
- **Mai mulți agenți lucrează deodată** în același folder. Nu modifici și nu pui în commit fișierele altui agent; folosești `git add -- <căi>` și `git commit -- <căi>`, niciodată `git add -A`. Înainte să modifici fișiere comune (`README.md` din rădăcină, `_config.yml`, `_layouts/`, `assets/`, `.github/`), anunți agenții activi, după protocolul din memorie.
- **Commit și push** doar la cererea sau cu acordul utilizatorului: fiecare push pe `master` republică site-ul. Commit-urile sunt nesemnate, cu `git -c commit.gpgsign=false commit`, cu acordul utilizatorului pentru acest depozit.
