"""Titel en metadata van een bekendmaking omzetten naar een gestructureerde vergunning.

Alles hier is regelgebaseerd en zonder externe afhankelijkheden, zodat het
dagelijks in een GitHub Actions runner kan draaien.
"""
from __future__ import annotations

import re
import unicodedata

POSTCODE_RE = re.compile(r"\b([1-9][0-9]{3})\s?([A-Z]{2})\b")
# Straat + huisnummer: "Dorpsstraat 12", "Van der Heijdenlaan 3a", "1e Kruisweg 4-6"
STRAAT_RE = re.compile(
    r"\b((?:[A-Z][\w'.-]*|\d+e)(?:\s(?:[a-z]{1,4}|[A-Z][\w'.-]*)){0,5}?)\s(\d{1,5}(?:\s?[a-zA-Z]|-\d{1,5}| ?[A-Z]?\d*)?)\b(?=[\s,]|$)"
)

STATUSSEN = [
    ("geweigerd", ["geweigerd", "weigering", "weigeren"]),
    ("ingetrokken", ["ingetrokken", "intrekking", "buiten behandeling"]),
    ("verlengd", ["verlengen", "verlenging", "beslistermijn"]),
    ("verleend", ["verleend", "verleende", "verlening", "besluit omgevingsvergunning", "toegekend"]),
    ("ontwerp", ["ontwerp", "voornemen", "ter inzage"]),
    ("aangevraagd", ["aangevraagd", "aanvraag", "ontvangen", "ingediend", "kennisgeving"]),
]

# Werksoort, zoektermen, vakgroepen die hier normaal werk uit halen.
WERKSOORTEN = [
    ("dakkapel", ["dakkapel"], ["dakdekker", "timmerman", "kozijnen"]),
    ("dakopbouw", ["dakopbouw", "nokverhoging", "opbouw op", "verhogen van het dak", "verhogen van de nok"], ["aannemer", "dakdekker"]),
    ("dak", ["dakbedekking", "vervangen van het dak", "dakisolatie", "dakrenovatie", "dakpannen", "nieuw dak"], ["dakdekker"]),
    ("zonnepanelen", ["zonnepanelen", "zonnepaneel", "pv-panelen", "zonnecollector"], ["installateur"]),
    ("aanbouw", ["aanbouw", "uitbouw", "uitbreiden van de woning", "uitbreiding van de woning", "uitbreiding woning", "serre", "veranda", "overkapping", "erker"], ["aannemer", "timmerman", "kozijnen"]),
    ("bijgebouw", ["bijgebouw", "garage", "schuur", "berging", "tuinhuis", "carport", "blokhut"], ["aannemer", "timmerman"]),
    ("nieuwbouw", ["nieuwbouw", "bouwen van een woning", "bouwen van woningen", "oprichten van", "realiseren van woningen", "bouw van een woning", "bouwen van een vrijstaande", "bouwen van twee", "bouwen van appartementen", "nieuw te bouwen"], ["aannemer", "installateur", "schilder", "stukadoor"]),
    ("gevel", ["kozijn", "kozijnen", "gevelwijziging", "wijzigen van de gevel", "wijzigen van de voorgevel", "wijzigen van de achtergevel", "gevel", "raam", "ramen", "voordeur", "dakraam", "isoleren van de gevel", "gevelisolatie"], ["kozijnen", "schilder"]),
    ("verbouwing", ["verbouwen", "verbouwing", "renovatie", "renoveren", "interne verbouwing", "intern verbouwen", "wijzigen van de indeling", "verbouw", "moderniseren"], ["aannemer", "schilder", "stukadoor", "installateur"]),
    ("splitsing", ["splitsen", "splitsing", "kamerverhuur", "kamergewijze", "omzetten naar", "transformatie", "transformeren", "wijzigen van het gebruik", "gebruikswijziging"], ["aannemer", "installateur"]),
    ("bedrijfspand", ["bedrijfshal", "bedrijfspand", "loods", "bedrijfsgebouw", "kantoor", "winkel", "horeca"], ["aannemer", "installateur"]),
    ("sloop", ["slopen", "sloop", "sloopmelding"], ["sloopbedrijf"]),
    ("terras_en_erf", ["terras", "erfafscheiding", "schutting", "hekwerk", "inrit", "uitrit", "uitweg", "oprit"], ["hovenier", "bestrating"]),
    ("kappen", ["kappen", "boom", "bomen", "vellen"], []),
    ("evenement", ["evenement", "festival", "standplaats", "terrasvergunning", "drank- en horeca", "alcoholwet", "exploitatievergunning"], []),
]

BOUW_WERKSOORTEN = {w for w, _, vak in WERKSOORTEN if vak}


def slugify(tekst: str) -> str:
    tekst = unicodedata.normalize("NFKD", tekst or "").encode("ascii", "ignore").decode()
    tekst = re.sub(r"[^a-zA-Z0-9]+", "-", tekst).strip("-").lower()
    return tekst or "onbekend"


def bepaal_status(titel: str) -> str:
    t = titel.lower()
    for status, termen in STATUSSEN:
        if any(term in t for term in termen):
            return status
    return "onbekend"


def bepaal_werksoort(titel: str, omschrijving: str = "") -> tuple[str, list[str]]:
    t = f"{titel} {omschrijving}".lower()
    for werksoort, termen, vakgroepen in WERKSOORTEN:
        if any(term in t for term in termen):
            return werksoort, list(vakgroepen)
    return "overig", []


def vind_adres(tekst: str) -> dict:
    """Postcode, plaats en straat uit vrije tekst. Geeft lege strings als niets gevonden."""
    adres = {"straat": "", "huisnummer": "", "postcode": "", "plaats": ""}
    if not tekst:
        return adres
    pc = POSTCODE_RE.search(tekst)
    if pc:
        adres["postcode"] = f"{pc.group(1)} {pc.group(2)}"
        # Plaatsnaam staat meestal direct na de postcode: "5611 AB Eindhoven"
        na = tekst[pc.end():]
        m = re.match(r"\s*(?:te\s+)?([A-Z][\w'.-]*(?:\s(?:aan|op|de|den|der|het|'t|bij|en|van|ter|ten)\s[A-Z]?[\w'.-]*|\s[A-Z][\w'.-]*){0,3})", na)
        if m:
            adres["plaats"] = m.group(1).strip(" ,.")
    # Straat + huisnummer zoeken in het stuk voor de postcode, anders in de hele tekst.
    zoekruimte = tekst[: pc.start()] if pc else tekst
    kandidaten = [m for m in STRAAT_RE.finditer(zoekruimte)]
    for m in reversed(kandidaten):
        straat = m.group(1).strip()
        if straat.lower() in {"gemeente", "besluit", "omgevingsvergunning", "aanvraag", "verleend", "week", "zaaknummer", "nummer", "zaak"}:
            continue
        if re.fullmatch(r"\d{4}", m.group(2)) and not pc:
            continue
        if straat[0].isdigit() and not re.match(r"\d+e\s", straat):
            continue
        adres["straat"] = straat
        adres["huisnummer"] = m.group(2).strip()
        break
    return adres


def omschrijving_uit_titel(titel: str) -> str:
    """Het deel van de titel dat het werk beschrijft, zonder gemeente, status en adres."""
    t = titel
    t = re.sub(r"^(gemeente\s+)?[A-Z][\w' .-]*?\s[-:|]\s", "", t)  # "Gemeente X - " voorvoegsel
    t = re.sub(r"(?i)\b(verleende|verleend|aangevraagde|aanvraag|ontvangen|besluit|kennisgeving|ontwerp|geweigerde|ingetrokken|verlengen beslistermijn|verlenging beslistermijn|reguliere procedure|uitgebreide procedure)\b", "", t)
    t = re.sub(r"(?i)\bomgevingsvergunning(en)?\b", "", t)
    t = re.sub(r"\b[1-9][0-9]{3}\s?[A-Z]{2}\b.*$", "", t)
    t = re.sub(r"\s+", " ", t).strip(" ,:-|.")
    return t


def verwerk(record: dict) -> dict:
    """Ruwe metadata (uit SRU of fixture) omzetten naar één vergunning-dict."""
    titel = (record.get("titel") or "").strip()
    gemeente = (record.get("gemeente") or "").strip()
    gemeente = re.sub(r"^(gemeente|gemeenteraad)\s+", "", gemeente, flags=re.I)
    tekst_voor_adres = titel
    if record.get("omschrijving"):
        tekst_voor_adres = f"{titel} {record['omschrijving']}"
    adres = vind_adres(tekst_voor_adres)
    for veld in ("straat", "huisnummer", "postcode", "plaats"):
        if record.get(veld):
            adres[veld] = str(record[veld]).strip()
    if not adres["plaats"] and gemeente:
        adres["plaats"] = gemeente
    omschrijving = record.get("omschrijving") or omschrijving_uit_titel(titel)
    if adres["straat"] and adres["straat"] in omschrijving:
        omschrijving = omschrijving.split(adres["straat"], 1)[0].strip(" ,:-|.")
    omschrijving = re.sub(r"(?i)^(voor|van|betreft|t\.b\.v\.|tbv)\s+", "", omschrijving).strip(" ,:-|.")
    werksoort, vakgroepen = bepaal_werksoort(titel, record.get("omschrijving", ""))
    return {
        "id": record.get("id", ""),
        "titel": titel,
        "omschrijving": omschrijving,
        "gemeente": gemeente,
        "gemeente_slug": slugify(gemeente),
        "datum": (record.get("datum") or "")[:10],
        "status": record.get("status") or bepaal_status(titel),
        "werksoort": werksoort,
        "vakgroepen": vakgroepen,
        "is_bouw": werksoort in BOUW_WERKSOORTEN,
        "adres": adres,
        "url": record.get("url", ""),
    }
