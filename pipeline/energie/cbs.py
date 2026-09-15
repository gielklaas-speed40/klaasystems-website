"""Kerncijfers wijken en buurten van het CBS ophalen via OData v3 (tabel 86165NED)."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request

TABEL = "86165NED"
# ODataFeed ondersteunt paginering ($skip en odata.nextLink), ODataApi niet.
FEED = f"https://opendata.cbs.nl/ODataFeed/odata/{TABEL}"
BASIS = f"{FEED}/TypedDataSet"
USER_AGENT = "klaasystems-energie/1.0 (+https://klaasystems.nl/energie/)"

# CBS-kolom -> onze naam
KOLOMMEN = {
    "WijkenEnBuurten": "code",
    "Gemeentenaam_1": "gemeente",
    "SoortRegio_2": "soort",
    "AantalInwoners_5": "inwoners",
    "HuishoudensTotaal_29": "huishoudens",
    "Woningvoorraad_35": "woningen",
    "GemiddeldeWOZWaardeVanWoningen_39": "woz",
    "PercentageEengezinswoning_40": "eengezins_pct",
    "PercentageTussenwoningEengezins_41": "tussenwoning_pct",
    "PercentageHoekwoningEengezins_42": "hoekwoning_pct",
    "PercentageTweeOnderEenKapWoningEe_43": "twee_onder_een_kap_pct",
    "PercentageVrijstaandeWoningEengezins_44": "vrijstaand_pct",
    "PercentageMeergezinswoning_45": "meergezins_pct",
    "Koopwoningen_47": "koop_pct",
    "HuurwoningenTotaal_48": "huur_pct",
    "InBezitWoningcorporatie_49": "corporatie_pct",
    "BouwjaarMeerDanTienJaarGeleden_51": "ouder_dan_tien_jaar_pct",
    "BouwjaarAfgelopenTienJaar_52": "jonger_dan_tien_jaar_pct",
    "GemiddeldeElektriciteitsleveringTotaal_53": "stroom_kwh",
    "GemiddeldAardgasverbruikTotaal_55": "gas_m3",
    "PercentageWoningenMetStadsverwarming_56": "stadsverwarming_pct",
    "AardgasvrijeWoningen_57": "aardgasvrij_pct",
    "WoningenMetZonnestroom_59": "zonnestroom_pct",
    "WoningenHoofdzElektrischVerwarmd_60": "elektrisch_verwarmd_pct",
    "AantalPubliekeLaadpalen_61": "laadpalen",
    "GemiddeldInkomenPerInwoner_78": "inkomen_per_inwoner",
    "MeestVoorkomendePostcode_118": "postcode",
    "MateVanStedelijkheid_120": "stedelijkheid",
}


def _get(url: str, timeout: int = 120) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def wijknamen(log=print) -> dict:
    """Code -> naam van wijk of gemeente, uit de dimensie WijkenEnBuurten."""
    namen: dict = {}
    for r in _alles(f"{FEED}/WijkenEnBuurten?$format=json"):
        namen[(r.get("Key") or "").strip()] = (r.get("Title") or "").strip()
    log(f"CBS: {len(namen)} regionamen")
    return namen


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


def haal_op(log=print) -> list[dict]:
    """Alle gemeente- en wijkrijen (geen buurten) met de kolommen uit KOLOMMEN."""
    select = ",".join(KOLOMMEN)
    filt = "startswith(WijkenEnBuurten,'GM') or startswith(WijkenEnBuurten,'WK') or startswith(WijkenEnBuurten,'NL')"
    params = {"$format": "json", "$select": select, "$filter": filt}
    rijen = _alles(f"{BASIS}?{urllib.parse.urlencode(params)}")
    log(f"CBS: {len(rijen)} rijen opgehaald")
    return [normaliseer(r) for r in rijen]


def normaliseer(rij: dict) -> dict:
    uit = {}
    for cbs, naam in KOLOMMEN.items():
        w = rij.get(cbs)
        if isinstance(w, str):
            w = w.strip()
        uit[naam] = w
    uit["code"] = (uit.get("code") or "").strip()
    uit["soort"] = (uit.get("soort") or "").strip().lower()
    return uit
