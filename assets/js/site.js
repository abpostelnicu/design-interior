// Îmbunătățiri mici pentru paginile site-ului; conținutul rămâne complet și fără JavaScript.
(function () {
  "use strict";

  var continut = document.getElementById("continut");
  if (!continut) {
    return;
  }

  // Celulele scurte din tabele (cantități, prețuri, magazine) rămân pe un singur rând; textele lungi se rup.
  continut.querySelectorAll("th, td").forEach(function (celula) {
    if (celula.textContent.trim().length <= 20) {
      celula.classList.add("scurt");
    }
  });

  // Linkurile către alte site-uri (magazine) se deschid într-o filă nouă.
  continut.querySelectorAll("a[href]").forEach(function (link) {
    if (!link.hostname || link.hostname === window.location.hostname) {
      return;
    }
    link.target = "_blank";
    link.rel = "noopener";
    var nota = document.createElement("span");
    nota.className = "ascuns";
    nota.textContent = " (se deschide într-o filă nouă)";
    link.appendChild(nota);
  });

  // Imaginile se pot deschide la dimensiunea completă (utile pentru planuri și randări).
  continut.querySelectorAll("img").forEach(function (imagine) {
    if (imagine.closest("a")) {
      return;
    }
    var link = document.createElement("a");
    link.href = imagine.getAttribute("src");
    link.className = "imagine-mare";
    link.setAttribute(
      "aria-label",
      "Deschide imaginea la dimensiunea completă" + (imagine.alt ? ": " + imagine.alt : "")
    );
    imagine.parentNode.insertBefore(link, imagine);
    link.appendChild(imagine);
  });

  // Titlurile primesc o legătură directă (la trecerea cu mouse-ul), ca să poți trimite cuiva o anumită secțiune sau un anumit pas.
  // Este ascunsă de cititoarele de ecran, ca să nu se repete în numele fiecărui titlu.
  continut.querySelectorAll("h2[id], h3[id], h4[id]").forEach(function (titlu) {
    var ancora = document.createElement("a");
    ancora.className = "ancora";
    ancora.href = "#" + encodeURIComponent(titlu.id);
    ancora.title = "Legătură directă către această secțiune";
    ancora.setAttribute("aria-hidden", "true");
    ancora.tabIndex = -1;
    ancora.textContent = "#";
    titlu.appendChild(ancora);
  });
})();
