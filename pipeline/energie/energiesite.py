"""Pagina's per gemeente en wijk over energieverbruik, woningvoorraad en subsidie."""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import sys
from collections import defaultdict

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))
from build import CSS, CONFIG, e, datum_nl  # noqa: E402
from parse import slugify  # noqa: E402

with open(os.path.join(HIER, "subsidies.json"), encoding="utf-8") as f:
    SUBSIDIES = json.load(f)

MAATREGELEN = {
    "isolatie": "Isolatie", "warmtepomp": "Warmtepomp", "zonnepanelen": "Zonnepanelen", "thuisbatterij": "Thuisbatterij",
}

EXTRA_CSS = """
.cijfers td.num{width:110px}
.advies p{margin:0 0 10px}
.knoppen{display:flex;flex-wrap:wrap;gap:10px;margin:8px 0 4px}
.knoppen a{display:inline-block;background:var(--acc);color:#fff;text-decoration:none;padding:9px 16px;border-radius:6px;font-weight:600}
"""


def getal(w, eenheid: str = "", decimalen: int = 0) -> str:
    if w is None or w == "":
        return "onbekend"
    try:
        w = float(w)
    except (TypeError, ValueError):
        return e(w)
    s = f"{w:,.{decimalen}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s}{eenheid}"


def pagina(titel: str, body: str, diepte: int, omschrijving: str, canonical: str) -> str:
    root = "../" * diepte
    adsense = ""
    if CONFIG.get("adsense_client"):
        adsense = f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={e(CONFIG["adsense_client"])}" crossorigin="anonymous"></script>'
    return f"""<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(titel)}</title>
<meta name="description" content="{e(omschrijving)}">
<link rel="canonical" href="https://klaasystems.nl/energie/{canonical}">
{adsense}
<style>{CSS}{EXTRA_CSS}</style>
</head>
<body>
<header><div class="wrap">
<a class="brand" href="{root}">Energie<span>perwijk</span></a>
<nav><a href="{root}">Gemeenten</a><a href="{root}subsidie.html">Subsidie {SUBSIDIES['jaar']}</a><a href="{root}over.html">Over de data</a><a href="{root}../vergunningen/">Vergunningen</a></nav>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">Bron: CBS Kerncijfers wijken en buurten 2025, aardgas- en stroomcijfers over 2024. Subsidiebedragen van RVO, controleer altijd de actuele regeling. Een dienst van <a href="https://klaasystems.nl/">Klaasystems</a>.</div></footer>
</body>
</html>
"""


def vergelijk(w: dict, g: dict, nl: dict, veld: str, eenheid: str = "") -> str:
    return f"<tr><td>{{label}}</td><td class=\"num\">{getal(w.get(veld), eenheid)}</td><td class=\"num\">{getal(g.get(veld), eenheid)}</td><td class=\"num\">{getal(nl.get(veld), eenheid)}</td></tr>"


def cijfertabel(w: dict, g: dict, nl: dict, wijknaam: str, gemeentenaam: str) -> str:
    rijen = [
        ("Woningen", "woningen", ""),
        ("Koopwoningen", "koop_pct", "%"),
        ("In bezit woningcorporatie", "corporatie_pct", "%"),
        ("Eengezinswoningen", "eengezins_pct", "%"),
        ("Gebouwd meer dan tien jaar geleden", "ouder_dan_tien_jaar_pct", "%"),
        ("Gemiddeld gasverbruik per woning", "gas_m3", " m³"),
        ("Gemiddelde stroomlevering per woning", "stroom_kwh", " kWh"),
        ("Woningen met zonnepanelen", "zonnestroom_pct", "%"),
        ("Aardgasvrije woningen", "aardgasvrij_pct", "%"),
        ("Stadsverwarming", "stadsverwarming_pct", "%"),
        ("Hoofdzakelijk elektrisch verwarmd", "elektrisch_verwarmd_pct", "%"),
        ("Gemiddelde WOZ-waarde", "woz", " duizend euro"),
    ]
    kop = f"<tr><th></th><th>{e(wijknaam)}</th><th>{e(gemeentenaam)}</th><th>Nederland</th></tr>"
    body = "".join(vergelijk(w, g, nl, veld, eenheid).format(label=e(label)) for label, veld, eenheid in rijen)
    return f'<div class="tbl"><table class="cijfers">{kop}{body}</table></div>'


def advies(w: dict, g: dict, nl: dict, naam: str) -> list[str]:
    """Regelgebaseerde duiding. Geeft alinea's terug, alleen waar de cijfers iets zeggen."""
    uit: list[str] = []
    gas, gas_nl = w.get("gas_m3"), nl.get("gas_m3")
    zon, zon_nl = w.get("zonnestroom_pct"), nl.get("zonnestroom_pct")
    oud = w.get("ouder_dan_tien_jaar_pct")
    koop = w.get("koop_pct")
    eengezins = w.get("eengezins_pct")
    stads = w.get("stadsverwarming_pct") or 0
    corporatie = w.get("corporatie_pct")

    if gas and gas_nl:
        verschil = (gas - gas_nl) / gas_nl * 100
        if verschil > 25:
            uit.append(f"Een woning in {naam} verbruikt gemiddeld {getal(gas)} m³ gas per jaar, {getal(abs(verschil))} procent meer dan het Nederlandse gemiddelde van {getal(gas_nl)} m³. Bij de huidige gasprijs is dat een verschil van enkele honderden euro's per jaar. Isolatie van dak, vloer en spouw haalt daar het meeste vanaf, en dat is ook de maatregel met de hoogste subsidie per euro.")
        elif verschil < -25:
            uit.append(f"Het gasverbruik in {naam} ligt met {getal(gas)} m³ per woning ruim onder het landelijke gemiddelde van {getal(gas_nl)} m³. Dat wijst op kleinere of nieuwere woningen, of op woningen die al van het gas af zijn. Voor wie nog wel gas stookt, is een hybride warmtepomp meestal de logische volgende stap.")
        else:
            uit.append(f"Het gasverbruik in {naam} zit met {getal(gas)} m³ per woning dicht bij het landelijke gemiddelde van {getal(gas_nl)} m³. De grootste besparing zit dan in de combinatie van isolatie en een hybride warmtepomp, waarbij de isolatiesubsidie verdubbelt.")
    if oud is not None and oud >= 90 and eengezins and eengezins >= 60:
        uit.append(f"Ruim {getal(oud)} procent van de woningen is ouder dan tien jaar en {getal(eengezins)} procent is een eengezinswoning. Precies het type huis waar spouwmuur- en dakisolatie het snelst terugverdienen, vaak binnen vijf jaar.")
    if zon is not None and zon_nl is not None:
        if zon < zon_nl - 8 and koop and koop >= 50:
            uit.append(f"Slechts {getal(zon)} procent van de woningen heeft zonnepanelen, tegen {getal(zon_nl)} procent landelijk, terwijl {getal(koop)} procent koopwoning is. Er ligt hier dus veel dak ongebruikt. De btw op zonnepanelen voor woningen is nul procent, en salderen loopt nog tot en met 2026.")
        elif zon > zon_nl + 8:
            uit.append(f"Met {getal(zon)} procent woningen met zonnepanelen loopt {naam} voor op Nederland ({getal(zon_nl)} procent). Na het einde van salderen wordt een thuisbatterij hier eerder interessant, omdat overdag veel stroom wordt teruggeleverd.")
    if stads and stads >= 25:
        uit.append(f"{getal(stads)} procent van de woningen zit op stadsverwarming. Voor die huizen is een warmtepomp niet aan de orde; isolatie en zonnepanelen wel.")
    if corporatie is not None and corporatie >= 50:
        uit.append(f"{getal(corporatie)} procent van de woningen is van een woningcorporatie. Huurders vragen isolatie en zonnepanelen aan via de corporatie, niet via de ISDE. De cijfers hieronder gaan vooral op voor de koopwoningen in de wijk.")
    return uit


def knoppen(context: str) -> str:
    partners = CONFIG.get("partners", {})
    links = []
    for key, label in MAATREGELEN.items():
        p = partners.get(key) or {}
        if p.get("url"):
            links.append(f'<a href="{e(p["url"])}" rel="sponsored nofollow noopener" target="_blank">Offertes {e(label.lower())}</a>')
    if not links:
        return ""
    namen = sorted({(partners.get(k) or {}).get("naam") for k in MAATREGELEN if (partners.get(k) or {}).get("url")} - {None, ""})
    return f"""<h2>Offertes vergelijken</h2>
<div class="blok"><p style="margin:0 0 10px">Drie prijzen naast elkaar leggen scheelt in de praktijk het meest. Via {e(" en ".join(namen) or "onze partner")} vraag je ze in één keer aan bij bedrijven die in de buurt werken.</p>
<div class="knoppen">{"".join(links)}</div>
<p class="klein" style="margin:10px 0 0">Wij ontvangen een vergoeding als je via deze knoppen offertes aanvraagt. Dat verandert niets aan de prijs die je betaalt.</p></div>"""


def subsidietabel(kort: bool = False) -> str:
    s = SUBSIDIES
    wp = s["warmtepomp"]
    rijen = "".join(
        f'<tr><td>{e(m["naam"])}</td><td class="num">{getal(m["per_m2_enkel"], " euro")}</td><td class="num">{getal(m["per_m2_dubbel"], " euro")}</td><td class="num">{getal(m["minimum_m2"], " m²")}</td></tr>'
        for m in s["isolatie"]["maatregelen"]
    )
    return f"""<p>Warmtepomp: {getal(wp['basis'])} euro plus {getal(wp['per_kw'])} euro per kW vermogen, met {getal(wp['bonus_a_plus_plus_plus'])} euro extra bij energielabel A+++. Een toestel van 6 kW komt zo op {getal(wp['voorbeeld_6kw'])} euro, een van 10 kW op {getal(wp['voorbeeld_10kw'])} euro.</p>
<div class="tbl"><table><tr><th>Isolatie</th><th>Per m², één maatregel</th><th>Per m², twee of meer</th><th>Minimum</th></tr>{rijen}</table></div>
<p class="klein">{e(s['isolatie']['toelichting'])} Zonnepanelen: {e(s['zonnepanelen']['toelichting'])} Thuisbatterij: {e(s['thuisbatterij']['toelichting'])} Bron en actuele voorwaarden: <a href="{e(s['bron'])}" rel="noopener" target="_blank">rvo.nl</a>.</p>"""


def bouw_site(rijen: list[dict], namen: dict, uit: str, vandaag: dt.date) -> dict:
    nl = next((r for r in rijen if r["code"] == "NL00"), {})
    gemeenten = {r["code"]: r for r in rijen if r["soort"] == "gemeente"}
    wijken_per_gemeente: dict[str, list[dict]] = defaultdict(list)
    for r in rijen:
        if r["soort"] == "wijk" and r.get("woningen") and r["woningen"] >= 200:
            gm = next((c for c, g in gemeenten.items() if g["gemeente"] == r["gemeente"]), None)
            if gm:
                wijken_per_gemeente[gm].append(r)

    os.makedirs(uit, exist_ok=True)
    os.makedirs(os.path.join(uit, "data"), exist_ok=True)
    urls: list[str] = []

    # Wijknaam opschonen: "Wijk 00 Annen" -> "Annen"
    def wijknaam(code: str) -> str:
        n = namen.get(code, code)
        import re
        n = re.sub(r"^Wijk\s+\d+\s*", "", n).strip()
        return n or namen.get(code, code)

    # Gemeente- en wijkpagina's
    gem_slugs: dict[str, str] = {}
    for gm, g in sorted(gemeenten.items(), key=lambda kv: kv[1]["gemeente"]):
        gnaam = g["gemeente"]
        gslug = slugify(gnaam)
        gem_slugs[gm] = gslug
        wijken = sorted(wijken_per_gemeente.get(gm, []), key=lambda w: (w.get("gas_m3") is None, -(w.get("gas_m3") or 0)))
        os.makedirs(os.path.join(uit, gslug), exist_ok=True)
        wijkrijen = []
        wijkslugs = {}
        for w in wijken:
            wnaam = wijknaam(w["code"])
            wslug = slugify(wnaam)
            if wslug in wijkslugs:
                wslug = f"{wslug}-{w['code'].lower().strip()}"
            wijkslugs[wslug] = w
            wijkrijen.append(f'<tr><td><a href="{wslug}/">{e(wnaam)}</a></td><td class="num">{getal(w.get("woningen"))}</td><td class="num">{getal(w.get("gas_m3"), " m³")}</td><td class="num">{getal(w.get("zonnestroom_pct"), "%")}</td><td class="num">{getal(w.get("koop_pct"), "%")}</td><td class="num">{getal(w.get("ouder_dan_tien_jaar_pct"), "%")}</td></tr>')
            # Wijkpagina
            os.makedirs(os.path.join(uit, gslug, wslug), exist_ok=True)
            alineas = advies(w, g, nl, wnaam)
            body = f"""<h1>Energie in {e(wnaam)}, {e(gnaam)}</h1>
<p class="lead">{getal(w.get('woningen'))} woningen, {getal(w.get('koop_pct'), '%')} koop. Gemiddeld {getal(w.get('gas_m3'))} m³ gas en {getal(w.get('stroom_kwh'))} kWh stroom per woning per jaar, {getal(w.get('zonnestroom_pct'), '%')} van de woningen heeft zonnepanelen. Postcode {e(w.get('postcode') or '')}.</p>
<div class="advies">{"".join(f"<p>{e(a)}</p>" for a in alineas)}</div>
<h2>De cijfers naast elkaar</h2>
{cijfertabel(w, g, nl, wnaam, gnaam)}
<h2>Subsidie in {SUBSIDIES['jaar']}</h2>
{subsidietabel()}
{knoppen(f"wijk:{gnaam}/{wnaam}")}
<p class="klein">Verbouwen in {e(gnaam)}? Bekijk ook de <a href="../../../vergunningen/{gslug}/">recente bouwvergunningen in {e(gnaam)}</a>. Andere wijken: <a href="../">{e(gnaam)}</a>.</p>"""
            with open(os.path.join(uit, gslug, wslug, "index.html"), "w", encoding="utf-8") as f:
                f.write(pagina(f"Energie in {wnaam} ({gnaam}): gasverbruik, zonnepanelen en subsidie {SUBSIDIES['jaar']}", body, 2,
                               f"Gasverbruik, stroom, zonnepanelen en woningtype in {wnaam}, {gnaam}, vergeleken met de gemeente en Nederland. Met de ISDE-subsidie van {SUBSIDIES['jaar']}.", f"{gslug}/{wslug}/"))
            urls.append(f"{gslug}/{wslug}/")
        alineas_g = advies(g, g, nl, gnaam) if not wijken else []
        body = f"""<h1>Energie per wijk in {e(gnaam)}</h1>
<p class="lead">{getal(g.get('woningen'))} woningen in {len(wijken)} wijken. Gemiddeld {getal(g.get('gas_m3'))} m³ gas per woning (Nederland {getal(nl.get('gas_m3'))} m³), {getal(g.get('zonnestroom_pct'), '%')} van de woningen heeft zonnepanelen, {getal(g.get('aardgasvrij_pct'), '%')} is aardgasvrij.</p>
<div class="advies">{"".join(f"<p>{e(a)}</p>" for a in alineas_g)}</div>
<h2>Wijken, gesorteerd op gasverbruik</h2>
<div class="tbl"><table><tr><th>Wijk</th><th>Woningen</th><th>Gas per woning</th><th>Zonnepanelen</th><th>Koop</th><th>Ouder dan 10 jaar</th></tr>{"".join(wijkrijen)}</table></div>
{knoppen(f"gemeente:{gnaam}")}
<p class="klein">Bekijk ook de <a href="../../vergunningen/{gslug}/">recente bouwvergunningen in {e(gnaam)}</a>.</p>"""
        with open(os.path.join(uit, gslug, "index.html"), "w", encoding="utf-8") as f:
            f.write(pagina(f"Energie per wijk in {gnaam}: gasverbruik, zonnepanelen en subsidie", body, 1,
                           f"Gasverbruik, zonnepanelen en aardgasvrije woningen per wijk in {gnaam}, met de ISDE-subsidie van {SUBSIDIES['jaar']}.", f"{gslug}/"))
        urls.append(f"{gslug}/")
        with open(os.path.join(uit, "data", f"{gslug}.json"), "w", encoding="utf-8") as f:
            json.dump({"gemeente": g, "wijken": wijken}, f, ensure_ascii=False, separators=(",", ":"))

    # Overzicht
    links = "".join(f'<div><a href="{gem_slugs[gm]}/">{e(g["gemeente"])}</a> <span class="n">{getal(g.get("gas_m3"))} m³</span></div>'
                    for gm, g in sorted(gemeenten.items(), key=lambda kv: kv[1]["gemeente"]))
    body = f"""<h1>Gasverbruik, zonnepanelen en subsidie per wijk</h1>
<p class="lead">Voor elke wijk in Nederland: hoeveel gas en stroom een woning gemiddeld verbruikt, hoeveel huizen zonnepanelen hebben, hoe oud de woningen zijn en wat de ISDE-subsidie in {SUBSIDIES['jaar']} oplevert. Landelijk verbruikt een woning {getal(nl.get('gas_m3'))} m³ gas en {getal(nl.get('stroom_kwh'))} kWh stroom per jaar, {getal(nl.get('zonnestroom_pct'), '%')} van de woningen heeft zonnepanelen.</p>
<p class="klein">Cijfers van het CBS over 2024, gepubliceerd in 2025. Bijgewerkt op {e(datum_nl(vandaag.isoformat()))}.</p>
<h2>Kies je gemeente</h2>
<div class="kolommen">{links}</div>"""
    with open(os.path.join(uit, "index.html"), "w", encoding="utf-8") as f:
        f.write(pagina("Energie per wijk: gasverbruik, zonnepanelen en subsidie per gemeente", body, 0,
                       "Gasverbruik, stroom en zonnepanelen per wijk voor alle Nederlandse gemeenten, met de ISDE-subsidie.", ""))

    # Subsidiepagina
    with open(os.path.join(uit, "subsidie.html"), "w", encoding="utf-8") as f:
        f.write(pagina(f"ISDE-subsidie {SUBSIDIES['jaar']}: bedragen voor warmtepomp en isolatie", f"<h1>ISDE-subsidie {SUBSIDIES['jaar']}</h1><p class=\"lead\">De landelijke subsidie voor isolatie, warmtepompen en zonneboilers in bestaande woningen. Je vraagt hem aan bij RVO na de installatie, met factuur en betaalbewijs.</p>{subsidietabel()}{knoppen('subsidie')}", 0,
                       f"Alle ISDE-bedragen van {SUBSIDIES['jaar']} voor warmtepomp, isolatie en glas op een rij.", "subsidie.html"))

    with open(os.path.join(uit, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for u in ["", "subsidie.html", "over.html"] + urls:
            f.write(f"<url><loc>https://klaasystems.nl/energie/{e(u)}</loc><lastmod>{vandaag.isoformat()}</lastmod></url>\n")
        f.write("</urlset>\n")
    return {"gemeenten": len(gemeenten), "wijken": sum(len(v) for v in wijken_per_gemeente.values())}
