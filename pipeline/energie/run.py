"""Energie per wijk: CBS-cijfers ophalen en pagina's bouwen.

  python pipeline/energie/run.py                  echte run
  python pipeline/energie/run.py --fixture pipeline/energie/fixtures/kwb_sample.json
  python pipeline/energie/run.py --rebuild        alleen pagina's bouwen uit energie/data/cbs.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import energiesite as build  # noqa: E402
import cbs  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture")
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.dirname(HIER)), "energie"))
    ap.add_argument("--vandaag")
    args = ap.parse_args()
    vandaag = dt.date.fromisoformat(args.vandaag) if args.vandaag else dt.date.today()
    opslag = os.path.join(args.out, "data", "cbs.json")

    if args.fixture:
        with open(args.fixture, encoding="utf-8") as f:
            d = json.load(f)
        rijen = [cbs.normaliseer(r) for r in d["rijen"]]
        namen = d["namen"]
        bronnen = d.get("bronnen") or {"kerncijfers": {"id": "fixture", "jaar": 2025}, "energie": None, "aanvulling": None}
    elif args.rebuild:
        with open(opslag, encoding="utf-8") as f:
            d = json.load(f)
        rijen, namen, bronnen = d["rijen"], d["namen"], d.get("bronnen") or {}
    else:
        rijen, bronnen = cbs.haal_op()
        namen = cbs.wijknamen(bronnen["kerncijfers"]["id"])
        os.makedirs(os.path.dirname(opslag), exist_ok=True)
        with open(opslag, "w", encoding="utf-8") as f:
            json.dump({"bijgewerkt": vandaag.isoformat(), "bronnen": bronnen, "rijen": rijen, "namen": namen}, f, ensure_ascii=False, separators=(",", ":"))
    print(f"rijen: {len(rijen)}, namen: {len(namen)}, bronnen: {bronnen}")
    for veld in ("gas_m3", "zonnestroom_pct", "aardgasvrij_pct"):
        print(f"  {veld}: {cbs.gevuld(rijen, veld)} wijken gevuld")
    print("gebouwd:", build.bouw_site(rijen, namen, args.out, vandaag, bronnen))
    return 0


if __name__ == "__main__":
    sys.exit(main())
