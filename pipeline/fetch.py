"""SRU-koppeling met repository.overheid.nl voor gemeentebladen over omgevingsvergunningen.

Documentatie: KOOP, "SRU handleiding officiële publicaties". De query gebruikt CQL.
Er zijn geen externe afhankelijkheden; alleen urllib en ElementTree.
"""
from __future__ import annotations

import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

SRU_URL = "https://repository.overheid.nl/sru"
USER_AGENT = "klaasystems-vergunningen/1.0 (+https://klaasystems.nl/vergunningen/)"

# Kandidaat-veldnamen (lokale naam, zonder namespace, kleine letters) per gewenst veld.
VELDEN = {
    "id": ["identifier"],
    "titel": ["title"],
    "gemeente": ["creator", "spatial", "authority"],
    "datum": ["available", "issued", "modified", "datumtijdstipwijzigingwork"],
    "straat": ["straatnaam", "straat"],
    "huisnummer": ["huisnummer"],
    "postcode": ["postcode"],
    "plaats": ["plaatsnaam", "woonplaats", "plaats"],
    "omschrijving": ["omschrijving", "description"],
    "bekendmakingtype": ["bekendmakingtype"],
    "url": ["preferredurl"],
    "xml_url": ["url"],
    "activiteit": ["activiteit"],
    "locatiepunt": ["locatiepunt"],
    "ligt_in_gemeente": ["ligtingemeente"],
}


def bouw_queries(sinds: str, term: str = "omgevingsvergunning") -> list[str]:
    """Eerste query op rubriek (dt.type), tweede op titel als de rubriek niets oplevert."""
    basis = f'c.product-area==officielepublicaties AND w.publicatienaam=="Gemeenteblad" AND dt.modified>="{sinds}"'
    return [
        f'{basis} AND dt.type=="{term}"',
        f'{basis} AND dt.title any "{term}"',
    ]


def bouw_query(sinds: str, term: str = "omgevingsvergunning") -> str:
    return bouw_queries(sinds, term)[0]


def _get(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/xml"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _lokaal(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _leaf_dict(el: ET.Element) -> dict:
    """Alle bladelementen onder el als {lokale naam: tekst}. Eerste waarde wint."""
    uit: dict = {}
    for node in el.iter():
        if len(node) == 0 and node.text and node.text.strip():
            naam = _lokaal(node.tag)
            uit.setdefault(naam, node.text.strip())
            # Sommige leveranciers zetten het veld in een name-attribuut: <meta name="OVERHEIDbm.postcode" content="..">
        if _lokaal(node.tag) == "meta" and node.get("name") and node.get("content"):
            naam = node.get("name").rsplit(".", 1)[-1].lower()
            uit.setdefault(naam, node.get("content").strip())
        # itemUrl met manifestatie html of xml
        if _lokaal(node.tag) == "itemurl" and node.text and node.get("manifestation") == "html":
            uit.setdefault("preferredurl", node.text.strip())
    return uit


def records_uit_xml(xml_bytes: bytes) -> tuple[list[dict], int, str]:
    """Geeft (records, totaal aantal volgens de server, diagnosemelding)."""
    root = ET.fromstring(xml_bytes)
    totaal = 0
    diagnose = ""
    records: list[dict] = []
    for node in root.iter():
        naam = _lokaal(node.tag)
        if naam == "numberofrecords" and node.text:
            totaal = int(node.text.strip() or 0)
        elif naam == "diagnostic":
            diagnose = " ".join(t.strip() for t in node.itertext() if t.strip())
        elif naam == "record":
            velden = _leaf_dict(node)
            rec = {}
            for doel, kandidaten in VELDEN.items():
                for k in kandidaten:
                    if velden.get(k):
                        rec[doel] = velden[k]
                        break
            if rec.get("id") and not rec.get("url"):
                rec["url"] = f"https://zoek.officielebekendmakingen.nl/{rec['id']}.html"
            if rec.get("xml_url") and not rec["xml_url"].endswith(".xml"):
                rec.pop("xml_url")
            if rec.get("titel"):
                rec["_ruw"] = velden
                records.append(rec)
    return records, totaal, diagnose


def haal_op(sinds: str, term: str = "omgevingsvergunning", per_pagina: int = 200,
            max_records: int = 5000, pauze: float = 0.3, log=print) -> list[dict]:
    """Alle records sinds datum (JJJJ-MM-DD) ophalen, gepagineerd."""
    alle: list[dict] = []
    for query in bouw_queries(sinds, term):
        alle = _haal_query(query, per_pagina, max_records, pauze, log)
        if alle:
            break
    return alle


def _haal_query(query: str, per_pagina: int, max_records: int, pauze: float, log) -> list[dict]:
    alle: list[dict] = []
    start = 1
    while start <= max_records:
        params = {
            "operation": "searchRetrieve",
            "version": "2.0",
            "query": query,
            "startRecord": start,
            "maximumRecords": per_pagina,
            "httpAccept": "application/xml",
        }
        url = f"{SRU_URL}?{urllib.parse.urlencode(params)}"
        data = _get(url)
        records, totaal, diagnose = records_uit_xml(data)
        if diagnose:
            log(f"SRU diagnose: {diagnose}")
        if start == 1:
            log(f"SRU: {totaal} records voor query {query}")
        if not records:
            break
        alle.extend(records)
        start += len(records)
        if start > totaal:
            break
        time.sleep(pauze)
    return alle


def eerste_record_ruw(sinds: str, term: str = "omgevingsvergunning") -> str:
    """Voor debug: de ruwe XML van het eerste record, om de veldnamen te bekijken."""
    params = {"operation": "searchRetrieve", "version": "2.0", "query": bouw_query(sinds, term),
              "startRecord": 1, "maximumRecords": 1, "httpAccept": "application/xml"}
    return _get(f"{SRU_URL}?{urllib.parse.urlencode(params)}").decode("utf-8", "replace")


if __name__ == "__main__":
    print(eerste_record_ruw(sys.argv[1] if len(sys.argv) > 1 else "2026-09-01")[:6000])
