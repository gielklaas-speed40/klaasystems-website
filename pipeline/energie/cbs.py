"""Kerncijfers wijken en buurten en energieverbruik per wijk ophalen bij het CBS (OData v3).

De tabel-id's komen uit de CBS-catalogus en de kolommen worden op titel gezocht,
zodat een nieuwe jaargang zonder codewijziging meegaat. Energiekolommen die in de
nieuwste kerncijfers nog leeg zijn, worden uit de aparte energietabel en uit de
vorige jaargang gehaald.
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

CATALOGUS = "https://opendata.cbs.nl/ODataCatalog/Tables"
FEED = "https://opendata.cbs.nl/ODataFeed/odata/{tabel}"
USER_AGENT = "klaasystems-energie/1.0 (+https://klaasystems.nl/energie/)"

# Onze naam -> kandidaat-titels (begin van de CBS-kolomtitel, kleine letters)
VELDEN = {
    "gemeente": ["gemeentenaam"],
    "soort": ["soort regio"],
    "inwoners": ["aantal inwoners"],
    "huishoudens": ["huishoudens totaal"],
    "woningen": ["woningvoorraad"],
    "woz": ["gemiddelde woz-waarde van woningen"],
    "eengezins_pct": ["percentage eengezinswoning"],
    "tussenwoning_pct": ["percentage tussenwoning"],
    "hoekwoning_pct": ["percentage hoekwoning"],
    "twee_onder_een_kap_pct": ["percentage twee-onder"],
    "vrijstaand_pct": ["percentage vrijstaande"],
    "meergezins_pct": ["percentage meergezinswoning"],
    "koop_pct": ["koopwoningen"],
    "huur_pct": ["huurwoningen totaal"],
    "corporatie_pct": ["in bezit woningcorporatie"],
    "ouder_dan_tien_jaar_pct": ["bouwjaar meer dan tien jaar geleden", "bouwjaar voor 2000"],
    "jonger_dan_tien_jaar_pct": ["bouwjaar afgelopen tien jaar", "bouwjaar vanaf 2000"],
    "stroom_kwh": ["gemiddelde elektriciteitslevering totaal", "gemiddeld elektriciteitsverbruik totaal", "gemiddelde elektriciteitslevering"],
    "gas_m3": ["gemiddeld aardgasverbruik totaal", "gemiddeld aardgasverbruik"],
    "stadsverwarming_pct": ["percentage woningen met stadsverwarming", "stadsverwarming"],
    "aardgasvrij_pct": ["aardgasvrije woningen"],
    "zonnestroom_pct": ["woningen met zonnestroom"],
    "elektrisch_verwarmd_pct": ["woningen hoofdz. elektrisch verwarmd", "woningen hoofdzakelijk elektrisch"],
    "laadpalen": ["aantal publieke laadpalen"],
    "postcode": ["meest voorkomende postcode"],
    "stedelijkheid": ["mate van stedelijkheid"],
}
ENERGIEVELDEN = ["stroom_kwh", "gas_m3", "stadsverwarming_pct", "aardgasvrij_pct", "zonnestroom_pct", "elektrisch_verwarmd_pct", "laadpalen"]

# Statische fallback voor de fixture en voor als de catalogus niet bereikbaar is.
KOLOMMEN = {
    "WijkenEnBuurten": "code", "Gemeentenaam_1": "gemeente", "SoortRegio_2": "soort", "AantalInwoners_5": "inwoners",
    "HuishoudensTotaal_29": "huishoudens", "Woningvoorraad_35": "woningen", "GemiddeldeWOZWaardeVanWoningen_39": "woz",
    "PercentageEengezinswoning_40": "eengezins_pct", "PercentageTussenwoningEengezins_41": "tussenwoning_pct",
    "PercentageHoekwoningEengezins_42": "hoekwoning_pct", "PercentageTweeOnderEenKapWoningEe_43": "twee_onder_een_kap_pct",
    "PercentageVrijstaandeWoningEengezins_44": "vrijstaand_pct", "PercentageMeergezinswoning_45": "meergezins_pct",
    "Koopwoningen_47": "koop_pct", "HuurwoningenTotaal_48": "huur_pct", "InBezitWoningcorporatie_49": "corporatie_pct",
    "BouwjaarMeerDanTienJaarGeleden_51": "ouder_dan_tien_jaar_pct", "BouwjaarAfgelopenTienJaar_52": "jonger_dan_tien_jaar_pct",
    "GemiddeldeElektriciteitsleveringTotaal_53": "stroom_kwh", "GemiddeldAardgasverbruikTotaal_55": "gas_m3",
    "PercentageWoningenMetStadsverwarming_56": "stadsverwarming_pct", "AardgasvrijeWoningen_57": "aardgasvrij_pct",
    "WoningenMetZonnestroom_59": "zonnestroom_pct", "WoningenHoofdzElektrischVerwarmd_60": "elektrisch_verwarmd_pct",
    "AantalPubliekeLaadpalen_61": "laadpalen", "MeestVoorkomendePostcode_118": "postcode", "MateVanStedelijkheid_120": "stedelijkheid",
}


def _get(url: str, timeout: int = 120, pogingen: int = 4) -> dict:
    fout = None
    for i in range(pogingen):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:  # noqa: PERF203
            fout = e
            time.sleep(3 * (i + 1))
    raise fout


def _alles(url: str) -> list[dict]:
    """Alle rijen van een feed-URL, met odata.nextLink of $skip als vervolg."""
    rijen: list[dict] = []
    skip = 0
    volgende = url
    while volgende:
        data = _get(volgende)
        deel = data.get("value", [])
        rijen.extend(deel)
        volgende = data.get("odata.nextLink") or data.get("@odata.nextLink")
        if not volgende and len(deel) >= 10000:
            skip += len(deel)
            volgende = f"{url}&$skip={skip}"
        if not deel:
            break
    return rijen


def tabellen(zoekterm: str, log=print) -> list[dict]:
    """Tabellen uit de catalogus waarvan de titel met de zoekterm begint, nieuwste jaargang eerst."""
    url = f"{CATALOGUS}?$format=json&$filter=" + urllib.parse.quote(f"substringof('{zoekterm}',Title)")
    uit = []
    for t in _get(url).get("value", []):
        titel = t.get("Title", "")
        if not titel.lower().startswith(zoekterm.lower()):
            continue
        m = re.search(r"(20\d\d)", titel)
        uit.append({"id": t.get("Identifier"), "titel": titel, "jaar": int(m.group(1)) if m else 0})
    uit.sort(key=lambda t: -t["jaar"])
    log(f"CBS catalogus '{zoekterm}': " + ", ".join(f"{t['id']} ({t['jaar']})" for t in uit[:4]))
    return uit


def kolommen_van(tabel: str, velden: dict | None = None) -> dict:
    """{CBS-kolom: onze naam} op basis van de kolomtitels van de tabel. Leeg als de tabel geen wijkdimensie heeft."""
    velden = dict(velden or VELDEN)
    velden.setdefault("gemeente", VELDEN["gemeente"])
    velden.setdefault("soort", VELDEN["soort"])
    props = _get(FEED.format(tabel=tabel) + "/DataProperties?$format=json").get("value", [])
    geo = next((p["Key"] for p in props if p.get("Type") in ("GeoDetail", "GeoDimension") or p.get("Key") == "WijkenEnBuurten"), None)
    if not geo:
        return {}
    uit = {geo: "code"}
    for p in props:
        if p.get("Type") == "Dimension" and p.get("Key") != geo:
            uit[p["Key"]] = "_dim_" + p["Key"]
    gebruikt = set()
    for naam, kandidaten in velden.items():
        for kandidaat in kandidaten:
            hit = next((p for p in props if p.get("Type") == "Topic" and (p.get("Title") or "").strip().lower().startswith(kandidaat) and p["Key"] not in gebruikt), None)
            if hit:
                uit[hit["Key"]] = naam
                gebruikt.add(hit["Key"])
                break
    return uit


def rijen_van(tabel: str, kolommen: dict, extra_filter: str = "") -> list[dict]:
    geo = next(k for k, v in kolommen.items() if v == "code")
    filt = f"(startswith({geo},'GM') or startswith({geo},'WK') or startswith({geo},'NL'))"
    if extra_filter:
        filt = f"{filt} and {extra_filter}"
    params = {"$format": "json", "$select": ",".join(kolommen), "$filter": filt}
    return [normaliseer(r, kolommen) for r in _alles(FEED.format(tabel=tabel) + "/TypedDataSet?" + urllib.parse.urlencode(params))]


def gevuld(rijen: list[dict], veld: str, soort: str = "wijk") -> int:
    return sum(1 for r in rijen if r.get("soort") == soort and r.get(veld) is not None)


def haal_op(log=print) -> tuple[list[dict], dict]:
    """Gemeente- en wijkrijen met alle velden, plus een dict met de gebruikte bronnen."""
    kwb = tabellen("Kerncijfers wijken en buurten", log)
    if not kwb:
        raise RuntimeError("geen kerncijfers-tabel gevonden in de catalogus")
    basis, kol, rijen = None, {}, []
    for t in kwb:
        try:
            kol = kolommen_van(t["id"])
            if "woningen" not in kol.values():
                continue
            rijen = rijen_van(t["id"], kol)
        except urllib.error.HTTPError as e:
            log(f"CBS {t['id']}: overgeslagen ({e})")
            continue
        if rijen:
            basis = t
            break
    if not basis:
        raise RuntimeError("geen bruikbare kerncijfers-tabel gevonden")
    kwb = [t for t in kwb if t["jaar"] < basis["jaar"] or t["id"] == basis["id"]]
    bronnen = {"kerncijfers": basis, "energie": None, "aanvulling": None}
    log(f"CBS {basis['id']}: {len(rijen)} rijen, {len(kol)} kolommen")
    per_code = {r["code"]: r for r in rijen}

    # 1. Energieverbruik uit de aparte tabel (nieuwste jaargang), alleen totaal woningen.
    for veld in ("gas_m3", "stroom_kwh", "stadsverwarming_pct"):
        if gevuld(rijen, veld) > 100:
            continue
        energie = tabellen("Energieverbruik particuliere woningen", log)
        for t in energie:
            try:
                ek = kolommen_van(t["id"], {"gas_m3": VELDEN["gas_m3"], "stroom_kwh": VELDEN["stroom_kwh"], "stadsverwarming_pct": VELDEN["stadsverwarming_pct"]})
                if "gas_m3" not in ek.values():
                    log(f"CBS {t['id']}: geen gaskolom gevonden")
                    continue
                dim = next((k for k, v in ek.items() if v == "_dim_Woningkenmerken"), None)
                try:
                    erijen = rijen_van(t["id"], ek, f"{dim} eq 'T001100'") if dim else rijen_van(t["id"], ek)
                except urllib.error.HTTPError:
                    erijen = rijen_van(t["id"], ek)
                if dim:
                    erijen = [r for r in erijen if (r.get("_dim_Woningkenmerken") or "T001100").strip() == "T001100"]
            except urllib.error.HTTPError as e:
                log(f"CBS {t['id']}: overgeslagen ({e})")
                continue
            log(f"CBS {t['id']}: {len(erijen)} energierijen, {gevuld(erijen, 'gas_m3')} wijken met gas")
            if gevuld(erijen, "gas_m3") > 100:
                for er in erijen:
                    doel = per_code.get(er["code"])
                    if doel:
                        for v in ("gas_m3", "stroom_kwh", "stadsverwarming_pct"):
                            if doel.get(v) is None and er.get(v) is not None:
                                doel[v] = er[v]
                bronnen["energie"] = t
                log(f"CBS {t['id']}: energie voor {gevuld(erijen, 'gas_m3')} wijken")
                break
        break

    # 2. Overige energievelden uit een oudere kerncijfers-jaargang waar ze wel gevuld zijn.
    leeg = [v for v in ENERGIEVELDEN if gevuld(rijen, v) <= 100]
    for t in [t for t in kwb if t["id"] != basis["id"]][:3]:
        if not leeg:
            break
        try:
            ok = kolommen_van(t["id"], {v: VELDEN[v] for v in leeg})
            if len(ok) < 2:
                continue
            orijen = rijen_van(t["id"], ok)
        except urllib.error.HTTPError as e:
            log(f"CBS {t['id']}: overgeslagen ({e})")
            continue
        gehaald = [v for v in leeg if gevuld(orijen, v) > 100]
        log(f"CBS {t['id']}: {len(orijen)} rijen, gevuld: " + ", ".join(f"{v} {gevuld(orijen, v)}" for v in leeg))
        if not gehaald:
            continue
        for orij in orijen:
            doel = per_code.get(orij["code"])
            if doel:
                for v in gehaald:
                    if doel.get(v) is None and orij.get(v) is not None:
                        doel[v] = orij[v]
        bronnen["aanvulling"] = {**t, "velden": gehaald}
        log(f"CBS {t['id']}: aanvulling {gehaald}")
        leeg = [v for v in leeg if v not in gehaald]
    return rijen, bronnen


def wijknamen(tabel: str | None = None, log=print) -> dict:
    """Code -> naam van wijk of gemeente, uit de dimensie WijkenEnBuurten."""
    if not tabel:
        tabel = tabellen("Kerncijfers wijken en buurten", log)[0]["id"]
    namen: dict = {}
    for r in _alles(FEED.format(tabel=tabel) + "/WijkenEnBuurten?$format=json"):
        namen[(r.get("Key") or "").strip()] = (r.get("Title") or "").strip()
    log(f"CBS: {len(namen)} regionamen")
    return namen


def normaliseer(rij: dict, kolommen: dict | None = None) -> dict:
    kolommen = kolommen or KOLOMMEN
    uit = {naam: None for naam in VELDEN}
    for cbs, naam in kolommen.items():
        if naam.startswith("_dim_"):
            uit[naam] = rij.get(cbs)
            continue
        w = rij.get(cbs)
        if isinstance(w, str):
            w = w.strip()
        uit[naam] = w
    uit["code"] = (uit.get("code") or "").strip()
    uit["soort"] = (uit.get("soort") or "").strip().lower()
    return uit
