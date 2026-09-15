"""Verkenning van de CBS OData-tabellen voor wijken en buurten: kolomnamen en voorbeeldrijen."""
import json
import sys
import urllib.parse
import urllib.request

TABELLEN = ["86165NED", "86333NED"]
BASIS = "https://opendata.cbs.nl/ODataApi/odata/{tabel}/{deel}"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "klaasystems-energie/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


for tabel in TABELLEN:
    print(f"\n=== {tabel} ===")
    try:
        info = get(BASIS.format(tabel=tabel, deel="TableInfos") + "?$format=json")
        for v in info.get("value", [])[:1]:
            print("titel:", v.get("Title"), "| periode:", v.get("Period"), "| records:", v.get("RecordCount"))
        props = get(BASIS.format(tabel=tabel, deel="DataProperties") + "?$format=json")
        for p in props.get("value", []):
            if p.get("Type") in ("Dimension", "GeoDimension", "GeoDetail", "TimeDimension", "Topic"):
                print(f"  {p.get('Type'):13} {p.get('Key'):45} {p.get('Title')}  [{p.get('Unit', '')}]")
        for dim in [p for p in props.get("value", []) if p.get("Type") in ("Dimension", "GeoDimension", "GeoDetail", "TimeDimension")]:
            try:
                rows = get(BASIS.format(tabel=tabel, deel=dim["Key"]) + "?$format=json&$top=5")
                print(f"  dimensie {dim['Key']}: " + "; ".join(f"{r.get('Key')}={r.get('Title')}" for r in rows.get("value", [])))
            except Exception as e:  # noqa: BLE001
                print(f"  dimensie {dim['Key']}: fout {e}")
        rows = get(BASIS.format(tabel=tabel, deel="TypedDataSet") + "?$format=json&$top=3")
        for r in rows.get("value", []):
            print("  rij:", json.dumps(r, ensure_ascii=False)[:1500])
        rows = get(BASIS.format(tabel=tabel, deel="TypedDataSet") + "?$format=json&$top=2&$filter=" + urllib.parse.quote("substringof('WK', WijkenEnBuurten)"))
        for r in rows.get("value", []):
            print("  wijkrij:", json.dumps(r, ensure_ascii=False)[:1500])
    except Exception as e:  # noqa: BLE001
        print("fout:", e)
        sys.exit(0)
