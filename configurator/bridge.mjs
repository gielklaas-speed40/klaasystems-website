#!/usr/bin/env node
/*
  Bridge tussen de configurator in de browser en de API van Speed40.

  Start:   node configurator/bridge.mjs
  Daarna:  http://localhost:4040

  De bridge doet drie dingen. Hij serveert de pagina, hij zet de API-sleutel op
  het verzoek zodat die niet in de browser hoeft te staan, en hij stuurt het
  door naar Speed40 met de juiste CORS-antwoorden.

  Zonder SPEED40_BASIS draait hij in spiegelmodus. Dan gaat er niets naar
  buiten en antwoordt de bridge zelf met een ordernummer, zodat je de hele flow
  kunt laten zien voordat de echte koppeling klaar is.

  Instellingen via omgevingsvariabelen:
    SPEED40_BASIS    basis-URL van de API, bijvoorbeeld https://api.speed40.nl
    SPEED40_SLEUTEL  de API-sleutel
    SPEED40_HEADER   naam van de header voor de sleutel, standaard X-Api-Key
    PORT             poort van de bridge, standaard 4040
    CATALOGUS        pad naar een catalogus-JSON die op /speed40/v1/catalogus
                     wordt geserveerd in spiegelmodus
*/

import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";

const MAP = fileURLToPath(new URL(".", import.meta.url));
const POORT = Number(process.env.PORT || 4040);
const BASIS = (process.env.SPEED40_BASIS || "").replace(/\/$/, "");
const SLEUTEL = process.env.SPEED40_SLEUTEL || "";
const HEADER = process.env.SPEED40_HEADER || "X-Api-Key";
const CATALOGUS = process.env.CATALOGUS || "";

const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".svg": "image/svg+xml"
};

function cors(res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, " + HEADER);
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
}

function json(res, status, data) {
  cors(res);
  res.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(data, null, 2));
}

async function lichaam(req) {
  const delen = [];
  for await (const deel of req) delen.push(deel);
  return Buffer.concat(delen).toString("utf8");
}

function tijd() {
  return new Date().toLocaleTimeString("nl-NL");
}

async function spiegel(req, res, pad, rauw) {
  if (req.method === "GET" && pad.endsWith("/catalogus")) {
    if (!CATALOGUS) {
      return json(res, 404, {
        fout: "geen catalogus ingesteld",
        uitleg: "Start de bridge met CATALOGUS=/pad/naar/catalogus.json om hier een catalogus te serveren."
      });
    }
    try {
      const inhoud = await readFile(CATALOGUS, "utf8");
      cors(res);
      res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
      return res.end(inhoud);
    } catch (e) {
      return json(res, 500, { fout: "catalogus niet te lezen", melding: e.message });
    }
  }

  let order = null;
  try { order = JSON.parse(rauw || "{}"); } catch (e) {
    return json(res, 400, { fout: "ongeldige JSON", melding: e.message });
  }
  const regels = Array.isArray(order.regels) ? order.regels.length : 0;
  const nummer = "SO" + String(100000 + Math.floor(Math.random() * 899999));
  console.log(tijd() + "  spiegel " + req.method + " " + pad + ", " + regels + (regels === 1 ? " regel" : " regels") + ", ordernummer " + nummer);
  if (regels) {
    order.regels.forEach((r) => {
      console.log("          " + r.artikelcode + "  " + (r.omschrijving || "") + "  " + r.aantal + " x " + r.eenheidsprijs_excl);
    });
  }
  return json(res, 201, {
    status: "ontvangen",
    ordernummer: nummer,
    referentie: order.referentie || null,
    regels: regels,
    totaal_excl: order.totalen ? order.totalen.excl_btw : null,
    opmerking: "Spiegelmodus, er is niets naar Speed40 gestuurd."
  });
}

async function doorsturen(req, res, pad, rauw) {
  const doel = BASIS + pad + (req.url.includes("?") ? req.url.slice(req.url.indexOf("?")) : "");
  const headers = { "Content-Type": "application/json" };
  if (SLEUTEL) headers[HEADER] = SLEUTEL;
  const begin = Date.now();
  try {
    const antwoord = await fetch(doel, {
      method: req.method,
      headers: headers,
      body: req.method === "GET" ? undefined : rauw
    });
    const tekst = await antwoord.text();
    console.log(tijd() + "  " + req.method + " " + doel + " -> " + antwoord.status + " (" + (Date.now() - begin) + " ms)");
    cors(res);
    res.writeHead(antwoord.status, { "Content-Type": antwoord.headers.get("content-type") || "application/json; charset=utf-8" });
    res.end(tekst);
  } catch (e) {
    console.log(tijd() + "  " + req.method + " " + doel + " mislukt: " + e.message);
    json(res, 502, { fout: "speed40 niet bereikbaar", melding: e.message, doel: doel });
  }
}

async function bestand(res, pad) {
  const schoon = normalize(pad).replace(/^(\.\.[/\\])+/, "");
  const doel = join(MAP, schoon === "/" || schoon === "" ? "index.html" : schoon);
  try {
    const info = await stat(doel);
    const bron = info.isDirectory() ? join(doel, "index.html") : doel;
    const inhoud = await readFile(bron);
    res.writeHead(200, { "Content-Type": TYPES[extname(bron)] || "application/octet-stream" });
    res.end(inhoud);
  } catch (e) {
    res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("Niet gevonden");
  }
}

const server = createServer(async (req, res) => {
  const pad = decodeURIComponent(new URL(req.url, "http://localhost").pathname);

  if (req.method === "OPTIONS") {
    cors(res);
    res.writeHead(204);
    return res.end();
  }

  if (pad.startsWith("/speed40/")) {
    const rest = pad.slice("/speed40".length);
    const rauw = req.method === "GET" ? "" : await lichaam(req);
    if (!BASIS) return spiegel(req, res, rest, rauw);
    return doorsturen(req, res, rest, rauw);
  }

  return bestand(res, pad);
});

server.listen(POORT, () => {
  console.log("Configurator staat op http://localhost:" + POORT);
  console.log(BASIS
    ? "Verzoeken op /speed40/... gaan naar " + BASIS + (SLEUTEL ? " met header " + HEADER : " zonder sleutel")
    : "Spiegelmodus, er gaat niets naar buiten. Zet SPEED40_BASIS om echt door te sturen.");
});
