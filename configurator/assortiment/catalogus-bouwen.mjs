#!/usr/bin/env node
/*
  Bouwt catalogus.json uit de assortimentslijsten in deze map.

  Gebruik:
    node configurator/assortiment/catalogus-bouwen.mjs
    node configurator/assortiment/catalogus-bouwen.mjs --map ./export --uit ./catalogus.json

  De lijsten zijn CSV met een puntkomma ertussen, zoals Excel ze in het
  Nederlands opslaat. Een komma als decimaalteken mag, 6,5 en 6.5 zijn hetzelfde.
  Het script controleert de vulling en noemt bij een fout het bestand en de
  regel. Zie README.md voor de betekenis van elke kolom.
*/

import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const args = process.argv.slice(2);
function arg(naam, standaard) {
  const i = args.indexOf(naam);
  return i === -1 || !args[i + 1] ? standaard : args[i + 1];
}
const MAP = resolve(arg("--map", dirname(fileURLToPath(import.meta.url))));
const UIT = resolve(arg("--uit", join(MAP, "catalogus.json")));

const fouten = [];
const waarschuwingen = [];
function fout(bestand, regel, tekst) { fouten.push(bestand + " regel " + regel + ": " + tekst); }

/* CSV lezen. Scheidingsteken komt uit de kopregel, puntkomma of komma of tab. */
function leesCsv(bestand, verplicht) {
  const pad = join(MAP, bestand);
  if (!existsSync(pad)) {
    if (verplicht) fouten.push(bestand + " ontbreekt in " + MAP);
    return [];
  }
  const tekst = readFileSync(pad, "utf8").replace(/^﻿/, "");
  const scheider = [";", "\t", ","].map((s) => [s, (tekst.split("\n")[0].match(new RegExp("\\" + s, "g")) || []).length])
    .sort((a, b) => b[1] - a[1])[0][0];

  const velden = [];
  let huidig = "", rij = [], inAanhaling = false;
  for (let i = 0; i < tekst.length; i++) {
    const c = tekst[i];
    if (inAanhaling) {
      if (c === '"' && tekst[i + 1] === '"') { huidig += '"'; i++; }
      else if (c === '"') inAanhaling = false;
      else huidig += c;
    } else if (c === '"') inAanhaling = true;
    else if (c === scheider) { rij.push(huidig); huidig = ""; }
    else if (c === "\n") { rij.push(huidig.replace(/\r$/, "")); velden.push(rij); rij = []; huidig = ""; }
    else huidig += c;
  }
  if (huidig !== "" || rij.length) { rij.push(huidig.replace(/\r$/, "")); velden.push(rij); }

  const kop = (velden.shift() || []).map((k) => k.trim().toLowerCase());
  return velden
    .map((r, i) => ({ regel: i + 2, waarden: r }))
    .filter((r) => r.waarden.some((v) => String(v).trim() !== ""))
    .map((r) => {
      const o = { _bestand: bestand, _regel: r.regel };
      kop.forEach((k, i) => { o[k] = (r.waarden[i] === undefined ? "" : String(r.waarden[i])).trim(); });
      return o;
    });
}

function nummer(rij, kolom) {
  const rauw = rij[kolom];
  if (rauw === undefined || rauw === "") return undefined;
  const n = Number(String(rauw).replace(/\s/g, "").replace(",", "."));
  if (isNaN(n)) { fout(rij._bestand, rij._regel, "kolom " + kolom + " is geen getal: " + rauw); return undefined; }
  return n;
}
function jaNee(rij, kolom) {
  const v = String(rij[kolom] || "").toLowerCase();
  if (v === "") return false;
  if (["ja", "j", "waar", "true", "1", "x"].includes(v)) return true;
  if (["nee", "n", "onwaar", "false", "0"].includes(v)) return false;
  fout(rij._bestand, rij._regel, "kolom " + kolom + " verwacht ja of nee, staat er: " + rij[kolom]);
  return false;
}

/* Inlezen */
const instellingen = {};
leesCsv("instellingen.csv", false).forEach((r) => { instellingen[String(r.sleutel || "").toLowerCase()] = r.waarde; });

const rijenGroepen = leesCsv("productgroepen.csv", true);
const rijenModellen = leesCsv("modellen.csv", true);
const rijenOpties = leesCsv("opties.csv", true);
const rijenWaarden = leesCsv("optiewaarden.csv", true);
const rijenBereik = leesCsv("maatbereik.csv", false);

const SOORTEN = ["maat", "keuze", "kleur", "schakelaar", "aantal"];
const TEKENINGEN = ["bank", "tafel", "kast", "raam"];

/* Productgroepen */
const groepen = [];
const perGroep = {};
rijenGroepen
  .sort((a, b) => (Number(a.volgorde || 0) || 0) - (Number(b.volgorde || 0) || 0))
  .forEach((r) => {
    if (!r.groep_id) return fout(r._bestand, r._regel, "groep_id is leeg");
    if (perGroep[r.groep_id]) return fout(r._bestand, r._regel, "groep_id " + r.groep_id + " staat er al");
    const grondslag = (r.grondslag || "breedte").toLowerCase();
    if (!["breedte", "m2"].includes(grondslag)) fout(r._bestand, r._regel, "grondslag moet breedte of m2 zijn, staat er: " + r.grondslag);
    if (r.tekening && !TEKENINGEN.includes(r.tekening)) {
      waarschuwingen.push(r._bestand + " regel " + r._regel + ": tekening " + r.tekening + " bestaat niet in de pagina, de configurator valt terug op de kasttekening. Beschikbaar: " + TEKENINGEN.join(", "));
    }
    const g = {
      id: r.groep_id,
      naam: r.naam || r.groep_id,
      enkelvoud: r.enkelvoud || undefined,
      tekening: r.tekening || "kast",
      grondslag: grondslag,
      minimumEenheid: nummer(r, "minimum_eenheid"),
      modellen: [],
      opties: []
    };
    perGroep[g.id] = g;
    groepen.push(g);
  });

/* Modellen */
const perModel = {};
rijenModellen
  .sort((a, b) => (Number(a.volgorde || 0) || 0) - (Number(b.volgorde || 0) || 0))
  .forEach((r) => {
    const g = perGroep[r.groep_id];
    if (!g) return fout(r._bestand, r._regel, "onbekende groep_id " + r.groep_id);
    if (!r.artikelcode) return fout(r._bestand, r._regel, "artikelcode is leeg");
    if (perModel[r.artikelcode]) return fout(r._bestand, r._regel, "artikelcode " + r.artikelcode + " staat er al");
    const basis = nummer(r, "basisprijs");
    if (basis === undefined) fout(r._bestand, r._regel, "basisprijs is leeg");
    const m = {
      code: r.artikelcode,
      naam: r.naam || r.artikelcode,
      basis: basis || 0,
      perEenheid: nummer(r, "prijs_per_eenheid") || 0,
      omschrijving: r.omschrijving || undefined
    };
    perModel[r.artikelcode] = { model: m, groep: g.id };
    g.modellen.push(m);
  });

/* Opties */
const perOptie = {};
rijenOpties
  .sort((a, b) => (Number(a.volgorde || 0) || 0) - (Number(b.volgorde || 0) || 0))
  .forEach((r) => {
    const g = perGroep[r.groep_id];
    if (!g) return fout(r._bestand, r._regel, "onbekende groep_id " + r.groep_id);
    if (!r.optie_id) return fout(r._bestand, r._regel, "optie_id is leeg");
    const sleutel = r.groep_id + "." + r.optie_id;
    if (perOptie[sleutel]) return fout(r._bestand, r._regel, "optie_id " + r.optie_id + " staat al in groep " + r.groep_id);
    const soort = (r.soort || "").toLowerCase();
    if (!SOORTEN.includes(soort)) return fout(r._bestand, r._regel, "soort moet een van deze zijn: " + SOORTEN.join(", "));

    const o = { id: r.optie_id, naam: r.naam || r.optie_id, groep: r.blok || "Opties", type: soort };
    if (soort === "maat" || soort === "aantal") {
      o.min = nummer(r, "min");
      o.max = nummer(r, "max");
      o.stap = nummer(r, "stap") || 1;
      o.standaard = nummer(r, "standaard");
      if (o.min === undefined || o.max === undefined) fout(r._bestand, r._regel, "min en max zijn nodig bij soort " + soort);
      else if (o.min > o.max) fout(r._bestand, r._regel, "min is groter dan max");
      if (o.standaard === undefined) o.standaard = o.min;
      else if (o.min !== undefined && o.max !== undefined && (o.standaard < o.min || o.standaard > o.max)) {
        fout(r._bestand, r._regel, "standaard " + o.standaard + " valt buiten " + o.min + " tot " + o.max);
      }
      if (soort === "maat") o.eenheid = r.eenheid || "cm";
      if (soort === "aantal") {
        o.prijs = nummer(r, "prijs") || 0;
        const gratis = nummer(r, "gratis_tot");
        if (gratis !== undefined) o.gratisTot = gratis;
      }
    } else if (soort === "schakelaar") {
      const prijs = nummer(r, "prijs");
      const perEenheid = nummer(r, "prijs_per_eenheid");
      if (prijs !== undefined) o.prijs = prijs;
      if (perEenheid !== undefined) o.prijsPerEenheid = perEenheid;
      if (prijs === undefined && perEenheid === undefined) {
        waarschuwingen.push(r._bestand + " regel " + r._regel + ": schakelaar " + r.optie_id + " heeft geen prijs, hij komt zonder meerprijs in het formulier");
      }
      o.standaard = jaNee(r, "standaard");
    } else {
      o.standaard = r.standaard || undefined;
    }

    if (r.alleen_bij_model) {
      o.alleenBijModel = r.alleen_bij_model.split("|").map((c) => c.trim()).filter(Boolean);
      o.alleenBijModel.forEach((code) => {
        if (!perModel[code]) fout(r._bestand, r._regel, "alleen_bij_model verwijst naar onbekende artikelcode " + code);
        else if (perModel[code].groep !== g.id) fout(r._bestand, r._regel, "artikelcode " + code + " hoort bij groep " + perModel[code].groep);
      });
    }
    if (r.alleen_bij) {
      o.alleenBij = {};
      r.alleen_bij.split(",").forEach((deel) => {
        const [sleutelNaam, waardeLijst] = deel.split("=");
        if (!sleutelNaam || !waardeLijst) return fout(r._bestand, r._regel, "alleen_bij verwacht optie_id=waarde of optie_id=waarde|waarde");
        o.alleenBij[sleutelNaam.trim()] = waardeLijst.split("|").map((w) => w.trim()).filter(Boolean);
      });
    }

    perOptie[sleutel] = { optie: o, rij: r };
    g.opties.push(o);
  });

/* Optiewaarden */
rijenWaarden
  .sort((a, b) => (Number(a.volgorde || 0) || 0) - (Number(b.volgorde || 0) || 0))
  .forEach((r) => {
    const sleutel = r.groep_id + "." + r.optie_id;
    const gevonden = perOptie[sleutel];
    if (!gevonden) return fout(r._bestand, r._regel, "onbekende combinatie " + sleutel);
    const o = gevonden.optie;
    if (o.type !== "keuze" && o.type !== "kleur") {
      return fout(r._bestand, r._regel, "optie " + r.optie_id + " is van soort " + o.type + " en heeft geen waarden nodig");
    }
    if (!r.waarde_code) return fout(r._bestand, r._regel, "waarde_code is leeg");
    o.keuzes = o.keuzes || [];
    if (o.keuzes.some((k) => k.code === r.waarde_code)) return fout(r._bestand, r._regel, "waarde_code " + r.waarde_code + " staat al bij " + sleutel);
    const k = { code: r.waarde_code, naam: r.naam || r.waarde_code };
    const prijs = nummer(r, "prijs");
    const perEenheid = nummer(r, "prijs_per_eenheid");
    const factor = nummer(r, "factor");
    if (factor !== undefined) k.factor = factor;
    if (perEenheid !== undefined) k.prijsPerEenheid = perEenheid;
    if (prijs !== undefined) k.prijs = prijs;
    if (factor !== undefined && (prijs || perEenheid)) {
      fout(r._bestand, r._regel, "kies per waarde een factor of een prijs, niet allebei");
    }
    if (o.type === "kleur") {
      if (!/^#[0-9a-fA-F]{3,8}$/.test(r.hex || "")) fout(r._bestand, r._regel, "hex is nodig bij een kleur, bijvoorbeeld #D9CCB8");
      else k.hex = r.hex;
    }
    o.keuzes.push(k);
  });

/* Maatbereik per model */
rijenBereik.forEach((r) => {
  const gevonden = perOptie[r.groep_id + "." + r.optie_id];
  if (!gevonden) return fout(r._bestand, r._regel, "onbekende combinatie " + r.groep_id + "." + r.optie_id);
  const o = gevonden.optie;
  if (o.type !== "maat" && o.type !== "aantal") return fout(r._bestand, r._regel, "maatbereik werkt alleen bij soort maat of aantal");
  if (!perModel[r.artikelcode]) return fout(r._bestand, r._regel, "onbekende artikelcode " + r.artikelcode);
  const b = {};
  ["min", "max", "stap", "standaard"].forEach((k) => { const n = nummer(r, k); if (n !== undefined) b[k] = n; });
  if (b.min !== undefined && b.max !== undefined && b.min > b.max) fout(r._bestand, r._regel, "min is groter dan max");
  if (b.standaard !== undefined) {
    const min = b.min !== undefined ? b.min : o.min;
    const max = b.max !== undefined ? b.max : o.max;
    if (b.standaard < min || b.standaard > max) fout(r._bestand, r._regel, "standaard " + b.standaard + " valt buiten " + min + " tot " + max);
  }
  o.bereikPerModel = o.bereikPerModel || {};
  o.bereikPerModel[r.artikelcode] = b;
});

/* Laatste controles */
groepen.forEach((g) => {
  if (!g.modellen.length) fouten.push("groep " + g.id + " heeft geen enkel model in modellen.csv");
  if (g.grondslag === "m2") {
    ["breedte", "hoogte"].forEach((nodig) => {
      if (!g.opties.some((o) => o.id === nodig && o.type === "maat")) {
        fouten.push("groep " + g.id + " rekent op m2 en heeft daarvoor een optie " + nodig + " van soort maat nodig");
      }
    });
  } else if (!g.opties.some((o) => o.id === "breedte" && o.type === "maat")) {
    fouten.push("groep " + g.id + " rekent op breedte en heeft daarvoor een optie breedte van soort maat nodig");
  }
  g.opties.forEach((o) => {
    const rij = perOptie[g.id + "." + o.id].rij;
    if (o.type === "keuze" || o.type === "kleur") {
      if (!o.keuzes || !o.keuzes.length) {
        fouten.push(rij._bestand + " regel " + rij._regel + ": optie " + o.id + " heeft geen waarden in optiewaarden.csv");
      } else if (!o.standaard) {
        o.standaard = o.keuzes[0].code;
        waarschuwingen.push(rij._bestand + " regel " + rij._regel + ": geen standaard ingevuld, de configurator kiest " + o.keuzes[0].code);
      } else if (!o.keuzes.some((k) => k.code === o.standaard)) {
        fout(rij._bestand, rij._regel, "standaard " + o.standaard + " komt niet voor in optiewaarden.csv");
      }
    }
    if (o.alleenBij) {
      Object.keys(o.alleenBij).forEach((ander) => {
        const doel = perOptie[g.id + "." + ander];
        if (!doel) return fout(rij._bestand, rij._regel, "alleen_bij verwijst naar onbekende optie " + ander);
        o.alleenBij[ander].forEach((w) => {
          const geldig = doel.optie.type === "schakelaar" ? ["ja", "nee"] : (doel.optie.keuzes || []).map((k) => k.code);
          if (!geldig.includes(w)) fout(rij._bestand, rij._regel, "alleen_bij waarde " + w + " bestaat niet bij optie " + ander);
        });
      });
    }
  });
});

const catalogus = {
  versie: instellingen.versie || new Date().toISOString().slice(0, 10),
  herkomst: instellingen.herkomst || "assortimentslijsten",
  btw: instellingen.btw ? Number(String(instellingen.btw).replace(",", ".")) : 21,
  valuta: instellingen.valuta || "EUR",
  groepen: groepen
};

/* Meldingen op volgorde van bestand en regel, dat leest prettiger terug in Excel. */
function opVolgorde(lijst) {
  return lijst.slice().sort((a, b) => {
    const pa = a.match(/^(\S+) regel (\d+)/), pb = b.match(/^(\S+) regel (\d+)/);
    if (!pa || !pb) return pa ? 1 : pb ? -1 : a.localeCompare(b);
    return pa[1] === pb[1] ? Number(pa[2]) - Number(pb[2]) : pa[1].localeCompare(pb[1]);
  });
}

if (waarschuwingen.length) {
  console.error("Let op");
  opVolgorde(waarschuwingen).forEach((w) => console.error("  " + w));
}
if (fouten.length) {
  console.error("Er is niets weggeschreven, eerst dit oplossen");
  opVolgorde(fouten).forEach((f) => console.error("  " + f));
  process.exit(1);
}

writeFileSync(UIT, JSON.stringify(catalogus, null, 2) + "\n");
const aantalOpties = groepen.reduce((n, g) => n + g.opties.length, 0);
const aantalWaarden = groepen.reduce((n, g) => n + g.opties.reduce((m, o) => m + (o.keuzes ? o.keuzes.length : 0), 0), 0);
console.log("Catalogus " + catalogus.versie + " geschreven naar " + UIT);
console.log(groepen.length + " productgroepen, " + Object.keys(perModel).length + " modellen, " + aantalOpties + " opties, " + aantalWaarden + " optiewaarden");
groepen.forEach((g) => {
  console.log("  " + g.id + ": " + g.modellen.length + " modellen, " + g.opties.length + " opties, rekent op " + (g.grondslag === "m2" ? "m2" : "breedte"));
});
