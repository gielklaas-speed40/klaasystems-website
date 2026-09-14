"""Verkenning van de SRU-indexen: welke query levert records op, en hoe ziet een record eruit."""
import sys
import urllib.parse
import xml.etree.ElementTree as ET

sys.path.insert(0, __import__("os").path.dirname(__file__))
import fetch  # noqa: E402

BASIS = 'c.product-area==officielepublicaties AND dt.type=="Gemeenteblad"'
QUERIES = [
    BASIS,
    BASIS + ' AND dt.modified>="2026-09-01"',
    BASIS + ' AND dt.available>="2026-09-01"',
    BASIS + ' AND dt.issued>="2026-09-01"',
    BASIS + ' AND dt.title any "omgevingsvergunning"',
    BASIS + ' AND dt.title="omgevingsvergunning"',
    BASIS + ' AND dt.title any omgevingsvergunning',
    BASIS + ' AND cql.textAndIndexes="omgevingsvergunning"',
    BASIS + ' AND dt.title any "omgevingsvergunning" AND dt.available>="2026-09-01"',
    'dt.type=="Gemeenteblad" AND dt.title any "omgevingsvergunning"',
    'w.publicatienaam=="Gemeenteblad" AND dt.modified>="2026-09-01"',
    'c.product-area==officielepublicaties AND dt.modified>="2026-09-10"',
    'c.product-area==officielepublicaties AND dt.title any "omgevingsvergunning" AND dt.modified>="2026-09-10"',
]


def aantal(query):
    params = {"operation": "searchRetrieve", "version": "2.0", "query": query, "startRecord": 1,
              "maximumRecords": 1, "httpAccept": "application/xml"}
    try:
        data = fetch._get(f"{fetch.SRU_URL}?{urllib.parse.urlencode(params)}")
    except Exception as e:  # noqa: BLE001
        return -1, f"fout {e}", b""
    root = ET.fromstring(data)
    n, diag = 0, ""
    for node in root.iter():
        lokaal = node.tag.rsplit("}", 1)[-1]
        if lokaal == "numberOfRecords" and node.text:
            n = int(node.text)
        if lokaal == "diagnostic":
            diag = " ".join(t.strip() for t in node.itertext() if t.strip())
    return n, diag, data


beste = None
for q in QUERIES:
    n, diag, data = aantal(q)
    print(f"{n:>9}  {q}  {diag}")
    if n > 0 and beste is None and "omgevingsvergunning" in q:
        beste = data
if beste is None:
    for q in QUERIES:
        n, diag, data = aantal(q)
        if n > 0:
            beste = data
            break
if beste:
    print("\n--- eerste record ---")
    print(beste.decode("utf-8", "replace")[:7000])
