"""Voor bekendmakingen zonder omschrijving in de titel: de tekst van de publicatie ophalen
en daaruit de werksoort en een korte omschrijving halen."""
from __future__ import annotations

import re
import time
import xml.etree.ElementTree as ET

import fetch
import parse

KERN_RE = re.compile(
    r"(?i)(?:omschrijving|betreft|betreffende|werkzaamheden|inhoud)\s*:\s*([^.;\n]{6,140})"
    r"|(?:voor|betreft|betreffende|activiteit|omschrijving|inhoud|werkzaamheden)\s*:?\s*"
    r"((?:het|een|de)\s+[\w-]+(?:en|eren)\b[^.;\n]{3,140})"
)
WERKWOORD_RE = re.compile(r"(?i)\b((?:het\s+)?(?:plaatsen|bouwen|realiseren|vergroten|verbouwen|veranderen|wijzigen|"
                          r"vervangen|uitbreiden|oprichten|slopen|kappen|renoveren|aanleggen|splitsen|verhogen|"
                          r"maken|vernieuwen|isoleren|herstellen|legaliseren)\s+(?:van\s+)?[^.;\n]{3,140})")


def xml_url_voor(v: dict) -> str:
    if v.get("xml_url"):
        return v["xml_url"]
    ident = v.get("id", "")
    m = re.match(r"(gmb)-(\d{4})-(\d+)$", ident)
    if not m:
        return ""
    return f"https://repository.overheid.nl/frbr/officielepublicaties/{m.group(1)}/{m.group(2)}/{ident}/1/xml/{ident}.xml"


def tekst_uit_xml(xml_bytes: bytes) -> str:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return ""
    delen = []
    for node in root.iter():
        naam = node.tag.rsplit("}", 1)[-1].lower()
        if naam in {"al", "p", "li", "kop", "titel", "title", "dcterms:title"} and node.text:
            delen.append(" ".join(t.strip() for t in node.itertext() if t.strip()))
    tekst = " ".join(delen) if delen else " ".join(t.strip() for t in root.itertext() if t.strip())
    return re.sub(r"\s+", " ", tekst)[:6000]


STOP_RE = re.compile(r"\s*(?:Zaakadres|Zaaknummer|Besluit|Datum|Locatie|Adres|Kenmerk|Verzenddatum|Dossier|Ontvangstdatum|"
                     r"Rechtsmiddel|Bezwaar|Inzage|Procedure|Status|Activiteit|Aanvrager|Publicatiedatum|Toelichting|Ter inzage)\b\s*:?.*$")


def kern_uit_tekst(tekst: str) -> str:
    for rx in (KERN_RE, WERKWOORD_RE):
        m = rx.search(tekst)
        if m:
            k = re.sub(r"(?i)^(?:het|een|de)\s+", "", (m.group(1) or m.group(2) or "").strip(" ,:-"))
            k = re.sub(r"\b[1-9][0-9]{3}\s?[A-Z]{2}\b.*$", "", k)
            k = STOP_RE.sub("", k).strip(" ,:-")
            return k[:140]
    return ""


def pas_tekst_toe(v: dict, tekst: str) -> None:
    """Werksoort, vakgroepen en omschrijving bijwerken op basis van de publicatietekst."""
    v["tekst"] = tekst[:300]
    v["verrijkt"] = True
    kern = kern_uit_tekst(tekst)
    werksoort, vakgroepen = parse.bepaal_werksoort(v["titel"], kern or tekst[:1500])
    if werksoort != "overig":
        v["werksoort"] = werksoort
        v["vakgroepen"] = vakgroepen
        v["is_bouw"] = werksoort in parse.BOUW_WERKSOORTEN
    if not v.get("omschrijving") and kern:
        v["omschrijving"] = kern


def verrijk(vergunningen: list[dict], max_n: int = 800, pauze: float = 0.05, log=print, budget_s: float = 720) -> int:
    kandidaten = [v for v in vergunningen if v.get("werksoort") == "overig" and not v.get("verrijkt")
                  and "bouw" in (v.get("activiteit") or "")]
    kandidaten.sort(key=lambda v: v.get("datum", ""), reverse=True)
    n = 0
    start = time.monotonic()
    for v in kandidaten[:max_n]:
        if time.monotonic() - start > budget_s:
            log(f"verrijken gestopt na {budget_s:.0f} s, de rest volgt morgen")
            break
        url = xml_url_voor(v)
        if not url:
            v["verrijkt"] = True
            continue
        try:
            data = fetch._get(url, timeout=30)
        except Exception as e:  # noqa: BLE001
            log(f"verrijken mislukt {v['id']}: {e}")
            v["verrijkt"] = True
            continue
        pas_tekst_toe(v, tekst_uit_xml(data))
        n += 1
        time.sleep(pauze)
    log(f"verrijkt: {n} van {len(kandidaten)} kandidaten")
    return n
