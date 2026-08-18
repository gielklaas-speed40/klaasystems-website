# Klaasystems website

Statische website voor [Klaasystems](https://klaasystems.nl) — maatwerk automatisering.

Eén zelfstandig bestand (`index.html`) zonder dependencies: het lettertype (Archivo) en het logo (SVG) zitten in het bestand zelf.

## Contactformulier (Formspree)

Het formulier is gekoppeld aan Formspree-endpoint `https://formspree.io/f/mwlewqjg`; inzendingen komen binnen op het e-mailadres van het Formspree-account. Het gratis plan is voldoende om te starten (50 inzendingen per maand). Beheer en spamfilters: [formspree.io/forms](https://formspree.io/forms).

## Hosting (GitHub Pages)

De site wordt gehost via GitHub Pages vanaf de `main`-branch. Elke push naar `main` is binnen ± een minuut live.

### Eigen domein koppelen (klaasystems.nl)

1. Ga in deze repo naar **Settings → Pages → Custom domain** en vul `klaasystems.nl` in.
2. Zet bij je domeinregistrar deze DNS-records:
   - `A`-records voor `klaasystems.nl` naar `185.199.108.153`, `185.199.109.153`, `185.199.110.153` en `185.199.111.153`
   - `CNAME`-record voor `www` naar `gielklaas-speed40.github.io`
3. Vink **Enforce HTTPS** aan zodra het certificaat is uitgegeven (kan een uur duren).
