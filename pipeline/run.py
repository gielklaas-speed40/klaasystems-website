"""Dagelijkse run: ophalen, verwerken, opslaan en pagina's bouwen.

Gebruik:
  python pipeline/run.py --since 3                 echte run, laatste 3 dagen ophalen
  python pipeline/run.py --fixture pipeline/fixtures/sru_sample.xml   zonder netwerk
  python pipeline/run.py --since 3 --dry-run       ophalen en verwerken, niets wegschrijven
  python pipeline/run.py --debug --since 1         ruwe XML van het eerste record tonen
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import build  # noqa: E402
import fetch  # noqa: E402
import parse  # noqa: E402
import verrijk  # noqa: E402

BEWAAR_DAGEN = 75


def laad_opslag(pad: str) -> dict:
    if os.path.exists(pad):
        with open(pad, encoding="utf-8") as f:
            return json.load(f)
    return {"vergunningen": {}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", type=int, default=3, help="aantal dagen terug ophalen")
    ap.add_argument("--fixture", help="lokaal SRU-antwoord (xml) gebruiken in plaats van het netwerk")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vergunningen"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--term", default="omgevingsvergunning")
    ap.add_argument("--max", type=int, default=5000)
    ap.add_argument("--vandaag", help="JJJJ-MM-DD, voor reproduceerbare builds")
    ap.add_argument("--rebuild", action="store_true", help="niets ophalen, opslag opnieuw parsen en pagina's bouwen")
    ap.add_argument("--verrijk", type=int, default=1200, help="max. aantal publicaties waarvan de tekst wordt opgehaald (0 = uit)")
    args = ap.parse_args()

    vandaag = dt.date.fromisoformat(args.vandaag) if args.vandaag else dt.date.today()
    sinds = (vandaag - dt.timedelta(days=args.since)).isoformat()

    if args.debug and not args.fixture:
        print(fetch.eerste_record_ruw(sinds, args.term)[:8000])
        return 0

    opslag_pad = os.path.join(args.out, "data", "opslag.json")
    if args.rebuild:
        ruw = [{k: v.get(k, "") for k in ("id", "titel", "gemeente", "datum", "url", "xml_url", "activiteit", "coord")}
               for v in laad_opslag(opslag_pad)["vergunningen"].values()]
        print(f"rebuild: {len(ruw)} records uit opslag")
    elif args.fixture:
        with open(args.fixture, "rb") as f:
            ruw, totaal, diagnose = fetch.records_uit_xml(f.read())
        print(f"fixture: {len(ruw)} records (server meldt {totaal}) {diagnose}")
    else:
        ruw = fetch.haal_op(sinds, args.term, max_records=args.max)
        print(f"opgehaald: {len(ruw)} records sinds {sinds}")

    opslag = laad_opslag(opslag_pad)
    nieuw = 0
    for r in ruw:
        v = parse.verwerk(r)
        if not v["id"]:
            continue
        oud = opslag["vergunningen"].get(v["id"])
        if oud is None:
            nieuw += 1
        elif oud.get("verrijkt"):
            v["verrijkt"] = True
            if oud.get("tekst"):
                verrijk.pas_tekst_toe(v, oud["tekst"])
        opslag["vergunningen"][v["id"]] = v
    grens = (vandaag - dt.timedelta(days=BEWAAR_DAGEN)).isoformat()
    opslag["vergunningen"] = {k: v for k, v in opslag["vergunningen"].items() if v["datum"] >= grens}
    alle = list(opslag["vergunningen"].values())
    if args.verrijk and not args.fixture and not args.rebuild:
        verrijk.verrijk(alle, max_n=args.verrijk)
    werk = {}
    for v in alle:
        werk[v["werksoort"]] = werk.get(v["werksoort"], 0) + 1
    print(f"nieuw: {nieuw}, totaal in opslag: {len(alle)}")
    print("werksoorten: " + ", ".join(f"{k} {n}" for k, n in sorted(werk.items(), key=lambda kv: -kv[1])))
    zonder_adres = sum(1 for v in alle if not v["adres"]["straat"])
    print(f"zonder straat: {zonder_adres} van {len(alle)}")
    if args.debug:
        for v in alle[:15]:
            print(json.dumps(v, ensure_ascii=False))

    if args.dry_run:
        print("dry-run: niets weggeschreven")
        return 0

    os.makedirs(os.path.dirname(opslag_pad), exist_ok=True)
    opslag["bijgewerkt"] = vandaag.isoformat()
    with open(opslag_pad, "w", encoding="utf-8") as f:
        json.dump(opslag, f, ensure_ascii=False, separators=(",", ":"))
    stats = build.bouw_site(alle, args.out, vandaag)
    print(f"gebouwd: {stats}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
