# Klaasystems website

Statische website voor [Klaasystems](https://klaasystems.nl) — maatwerk automatisering.

Eén zelfstandig bestand (`index.html`) zonder dependencies: het lettertype (Archivo) en het logo (SVG) zitten in het bestand zelf.

## Contactformulier activeren (Formspree)

Het formulier staat klaar maar moet één keer gekoppeld worden:

1. Maak een gratis account op [formspree.io](https://formspree.io) met info@klaasystems.com.
2. Klik **New form**, geef hem een naam (bijv. "Website contact").
3. Kopieer het form-ID uit de endpoint-URL (`https://formspree.io/f/xxxxxxx`).
4. Vervang in `index.html` de tekst `JOUW_FORM_ID` door dat ID (één plek, in het `<form action="…">`-attribuut).
5. Commit en push — klaar. Inzendingen komen binnen op je e-mail.

Het gratis plan van Formspree is voldoende om te starten (50 inzendingen per maand).

## Hosting (GitHub Pages)

De site wordt gehost via GitHub Pages vanaf de `main`-branch. Elke push naar `main` is binnen ± een minuut live.

### Eigen domein koppelen (klaasystems.nl)

1. Ga in deze repo naar **Settings → Pages → Custom domain** en vul `klaasystems.nl` in.
2. Zet bij je domeinregistrar deze DNS-records:
   - `A`-records voor `klaasystems.nl` naar `185.199.108.153`, `185.199.109.153`, `185.199.110.153` en `185.199.111.153`
   - `CNAME`-record voor `www` naar `gielklaas-speed40.github.io`
3. Vink **Enforce HTTPS** aan zodra het certificaat is uitgegeven (kan een uur duren).
