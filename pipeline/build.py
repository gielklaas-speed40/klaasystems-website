"""Statische pagina's genereren uit de verzamelde vergunningen."""
from __future__ import annotations

import datetime as dt
import html
import json
import os
from collections import Counter, defaultdict

from parse import slugify

WERKSOORT_LABEL = {
    "dakkapel": "Dakkapellen", "dakopbouw": "Dakopbouwen", "dak": "Dakwerk",
    "zonnepanelen": "Zonnepanelen", "installatie": "Warmtepompen, airco's en laadpalen", "aanbouw": "Aanbouwen en uitbouwen", "bijgebouw": "Bijgebouwen",
    "nieuwbouw": "Nieuwbouw", "gevel": "Gevels en kozijnen", "verbouwing": "Verbouwingen",
    "splitsing": "Splitsing en gebruikswijziging", "bedrijfspand": "Bedrijfspanden", "sloop": "Sloop",
    "terras_en_erf": "Terrassen, erf en inritten", "kappen": "Kapvergunningen", "evenement": "Evenementen",
    "overig": "Overig",
}
VAKGROEP_LABEL = {
    "aannemer": "aannemers", "dakdekker": "dakdekkers", "timmerman": "timmerlieden", "kozijnen": "kozijnbedrijven",
    "installateur": "installateurs", "schilder": "schilders", "stukadoor": "stukadoors", "sloopbedrijf": "sloopbedrijven",
    "hovenier": "hoveniers", "bestrating": "bestraters",
}
STATUS_LABEL = {
    "verleend": "verleend", "aangevraagd": "aangevraagd", "ontwerp": "ontwerpbesluit", "verlengd": "beslistermijn verlengd",
    "geweigerd": "geweigerd", "ingetrokken": "ingetrokken", "melding": "melding", "onbekend": "status onbekend",
}
FORMSPREE = "https://formspree.io/f/mwlewqjg"

CSS = """
:root{--bg:#f5f6f8;--panel:#fff;--ink:#15202b;--mut:#61707f;--line:#dde3ea;--acc:#0f6b5c;--acc-soft:#e3f2ee;--warn:#b3541e}
*{box-sizing:border-box}
body{margin:0;font:15px/1.5 -apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink);background:var(--bg)}
a{color:var(--acc)}
header{background:var(--panel);border-bottom:1px solid var(--line)}
.wrap{max-width:1040px;margin:0 auto;padding:0 20px}
header .wrap{display:flex;justify-content:space-between;align-items:baseline;padding-top:14px;padding-bottom:12px;gap:16px;flex-wrap:wrap}
header .brand{font-weight:700;font-size:17px;text-decoration:none;color:var(--ink)}
header .brand span{color:var(--acc)}
header nav a{margin-left:16px;font-size:14px}
main{padding:28px 0 48px}
h1{font-size:26px;margin:0 0 6px;line-height:1.2}
h2{font-size:18px;margin:32px 0 10px}
.lead{color:var(--mut);margin:0 0 20px;max-width:680px}
table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);font-size:14px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-weight:600;color:var(--mut);font-size:12.5px;background:#fafbfc}
tr:last-child td{border-bottom:none}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.tbl{overflow-x:auto}
.tag{display:inline-block;padding:1px 7px;border-radius:4px;background:var(--acc-soft);color:var(--acc);font-size:12px;white-space:nowrap}
.tag.grijs{background:#eef1f4;color:var(--mut)}
.klein{color:var(--mut);font-size:13px}
.kolommen{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:4px 20px;font-size:14px}
.kolommen a{text-decoration:none}
.kolommen .n{color:var(--mut);font-variant-numeric:tabular-nums}
form.mail{background:var(--panel);border:1px solid var(--line);padding:16px 18px;max-width:560px}
form.mail label{display:block;font-size:13px;color:var(--mut);margin:10px 0 4px}
form.mail input,form.mail select{width:100%;font:inherit;font-size:16px;padding:8px;border:1px solid var(--line);border-radius:6px;background:#fff}
form.mail button{margin-top:14px;font:inherit;padding:9px 16px;background:var(--acc);color:#fff;border:none;border-radius:6px;cursor:pointer}
footer{border-top:1px solid var(--line);padding:18px 0;color:var(--mut);font-size:13px}
@media (max-width:600px){header nav a{margin-left:10px}h1{font-size:22px}}
"""


def e(t) -> str:
    return html.escape(str(t or ""))


def datum_nl(iso: str) -> str:
    try:
        d = dt.date.fromisoformat(iso)
    except ValueError:
        return iso
    maanden = ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
    return f"{d.day} {maanden[d.month - 1]} {d.year}"


def pagina(titel: str, body: str, diepte: int, omschrijving: str, canonical: str) -> str:
    root = "../" * diepte
    return f"""<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(titel)}</title>
<meta name="description" content="{e(omschrijving)}">
<link rel="canonical" href="https://klaasystems.nl/vergunningen/{canonical}">
<style>{CSS}</style>
</head>
<body>
<header><div class="wrap">
<a class="brand" href="{root}">Vergunningen<span>radar</span></a>
<nav><a href="{root}">Gemeenten</a><a href="{root}werk/">Werksoorten</a><a href="{root}over.html">Over de data</a><a href="https://klaasystems.nl/">Klaasystems</a></nav>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">Bron: gemeentebladen via officielebekendmakingen.nl, dagelijks bijgewerkt. Adressen komen uit de openbare bekendmaking, er staan geen namen van aanvragers op deze site. Een dienst van <a href="https://klaasystems.nl/">Klaasystems</a>.</div></footer>
</body>
</html>
"""


def rij(v: dict, met_gemeente: bool) -> str:
    a = v["adres"]
    adres = " ".join(x for x in [a.get("straat"), a.get("huisnummer")] if x)
    plaats = " ".join(x for x in [a.get("postcode"), a.get("plaats")] if x)
    status = v["status"]
    tagklasse = "tag" if status == "verleend" else "tag grijs"
    cellen = [
        f'<td class="num">{e(datum_nl(v["datum"]))}</td>',
        f'<td><a href="{e(v["url"])}" rel="nofollow noopener" target="_blank">{e(v["omschrijving"] or ("omgevingsvergunning" if v["werksoort"] == "overig" else WERKSOORT_LABEL.get(v["werksoort"], "").lower()))}</a>'
        f'{"" if v["omschrijving"] else "<div class=klein>" + e(v["titel"][:120]) + "</div>"}</td>',
        f'<td>{e(adres)}<div class="klein">{e(plaats)}</div></td>',
    ]
    if met_gemeente:
        cellen.append(f'<td><a href="../{v["gemeente_slug"]}/">{e(v["gemeente"])}</a></td>')
    cellen.append(f'<td><span class="{tagklasse}">{e(STATUS_LABEL.get(status, status))}</span></td>')
    return "<tr>" + "".join(cellen) + "</tr>"


def tabel(items: list[dict], met_gemeente: bool) -> str:
    if not items:
        return '<p class="klein">Nog geen bekendmakingen in deze periode.</p>'
    kop = "<tr><th>Datum</th><th>Wat</th><th>Adres</th>" + ("<th>Gemeente</th>" if met_gemeente else "") + "<th>Status</th></tr>"
    return '<div class="tbl"><table>' + kop + "".join(rij(v, met_gemeente) for v in items) + "</table></div>"


def mailformulier(context: str) -> str:
    opties = "".join(f'<option value="{k}">{e(lbl)}</option>' for k, lbl in VAKGROEP_LABEL.items())
    return f"""<h2>Wekelijks per mail</h2>
<form class="mail" action="{FORMSPREE}" method="POST">
<input type="hidden" name="_subject" value="Vergunningenradar aanmelding">
<input type="hidden" name="context" value="{e(context)}">
<p class="klein" style="margin:0">Elke maandag de nieuwe verleende vergunningen voor jouw vak in jouw regio. Gratis zolang de dienst in opbouw is.</p>
<label for="vak">Jouw vak</label>
<select id="vak" name="vakgroep">{opties}</select>
<label for="regio">Regio of gemeenten</label>
<input id="regio" name="regio" placeholder="Bijvoorbeeld Eindhoven, Helmond en Veldhoven">
<label for="email">E-mailadres</label>
<input id="email" name="email" type="email" required placeholder="jij@bedrijf.nl">
<button type="submit">Aanmelden</button>
</form>"""


def bouw_site(vergunningen: list[dict], uit: str, vandaag: dt.date, dagen_lijst: int = 60) -> dict:
    grens = (vandaag - dt.timedelta(days=dagen_lijst)).isoformat()
    grens30 = (vandaag - dt.timedelta(days=30)).isoformat()
    recent = sorted([v for v in vergunningen if v["datum"] >= grens], key=lambda v: (v["datum"], v["id"]), reverse=True)
    bouw = [v for v in recent if v["is_bouw"]]
    per_gemeente: dict[str, list[dict]] = defaultdict(list)
    for v in bouw:
        per_gemeente[v["gemeente_slug"]].append(v)
    per_werk: dict[str, list[dict]] = defaultdict(list)
    for v in bouw:
        per_werk[v["werksoort"]].append(v)

    os.makedirs(os.path.join(uit, "data"), exist_ok=True)
    os.makedirs(os.path.join(uit, "werk"), exist_ok=True)

    # Overzicht
    tel30 = Counter(v["gemeente_slug"] for v in bouw if v["datum"] >= grens30)
    naam = {v["gemeente_slug"]: v["gemeente"] for v in bouw}
    gem_links = "".join(
        f'<div><a href="{slug}/">{e(naam[slug])}</a> <span class="n">{tel30.get(slug, 0)}</span></div>'
        for slug in sorted(per_gemeente, key=lambda s: naam[s])
    )
    werk_tel = Counter(v["werksoort"] for v in bouw if v["datum"] >= grens30)
    werk_rijen = "".join(
        f'<tr><td><a href="werk/{w}/">{e(WERKSOORT_LABEL.get(w, w))}</a></td><td class="num">{n}</td>'
        f'<td class="klein">{e(", ".join(VAKGROEP_LABEL.get(x, x) for x in next((v["vakgroepen"] for v in bouw if v["werksoort"] == w), [])))}</td></tr>'
        for w, n in werk_tel.most_common()
    )
    n_verleend30 = sum(1 for v in bouw if v["datum"] >= grens30 and v["status"] == "verleend")
    body = f"""<h1>Verleende bouwvergunningen per gemeente</h1>
<p class="lead">Elke dag halen we de omgevingsvergunningen uit de gemeentebladen en sorteren we ze op werksoort. Zo zie je in welke straat binnenkort een dakkapel, aanbouw of nieuwbouw komt. Een aanvraag is het vroegste openbare signaal, vaak maanden voordat de schilder, stukadoor of installateur wordt gekozen.</p>
<p class="klein">Laatste 30 dagen: {n_verleend30} verleende bouwvergunningen in {len(tel30)} gemeenten. Bijgewerkt op {e(datum_nl(vandaag.isoformat()))}.</p>
<h2>Per werksoort</h2>
<div class="tbl"><table><tr><th>Werksoort</th><th>Laatste 30 dagen</th><th>Interessant voor</th></tr>{werk_rijen}</table></div>
<h2>Per gemeente</h2>
<div class="kolommen">{gem_links}</div>
<h2>Nieuwste bekendmakingen</h2>
{tabel(bouw[:40], True)}
{mailformulier("overzicht")}"""
    with open(os.path.join(uit, "index.html"), "w", encoding="utf-8") as f:
        f.write(pagina("Vergunningenradar, verleende bouwvergunningen per gemeente", body, 0,
                       "Dagelijks overzicht van verleende omgevingsvergunningen voor dakkapellen, aanbouwen, nieuwbouw en verbouwingen per gemeente.", ""))

    # Per gemeente
    for slug, items in per_gemeente.items():
        g = naam[slug]
        os.makedirs(os.path.join(uit, slug), exist_ok=True)
        soorten = Counter(v["werksoort"] for v in items if v["datum"] >= grens30)
        samenvatting = ", ".join(f"{WERKSOORT_LABEL.get(w, w).lower()} {n}" for w, n in soorten.most_common(5))
        verleend = [v for v in items if v["status"] == "verleend"]
        rest = [v for v in items if v["status"] != "verleend"]
        body = f"""<h1>Bouwvergunningen in {e(g)}</h1>
<p class="lead">Omgevingsvergunningen voor bouwwerk die de gemeente {e(g)} de afgelopen {dagen_lijst} dagen heeft gepubliceerd. Laatste 30 dagen: {samenvatting or 'geen bouwvergunningen'}.</p>
<h2>Verleend</h2>
<p class="klein">De vergunning is rond, het werk kan beginnen. Meestal is de hoofdaannemer al gekozen, het afbouwwerk en de leveringen vaak nog niet.</p>
{tabel(verleend, False)}
<h2>Aangevraagd en overige berichten</h2>
<p class="klein">Aanvragen lopen acht weken of langer voor op het besluit. Dit is het vroegste openbare signaal dat er gebouwd gaat worden.</p>
{tabel(rest, False)}
{mailformulier(f"gemeente:{g}")}"""
        with open(os.path.join(uit, slug, "index.html"), "w", encoding="utf-8") as f:
            f.write(pagina(f"Bouwvergunningen {g}, verleende omgevingsvergunningen", body, 1,
                           f"Verleende omgevingsvergunningen in {g}: dakkapellen, aanbouwen, nieuwbouw en verbouwingen met adres en datum.", f"{slug}/"))
        with open(os.path.join(uit, "data", f"{slug}.json"), "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, separators=(",", ":"))

    # Per werksoort
    werk_index = "".join(
        f'<tr><td><a href="{w}/">{e(WERKSOORT_LABEL.get(w, w))}</a></td><td class="num">{len(items)}</td></tr>'
        for w, items in sorted(per_werk.items(), key=lambda kv: -len(kv[1]))
    )
    with open(os.path.join(uit, "werk", "index.html"), "w", encoding="utf-8") as f:
        f.write(pagina("Bouwvergunningen per werksoort", f"<h1>Per werksoort</h1><p class=\"lead\">Alle verleende en aangevraagde vergunningen van de afgelopen {dagen_lijst} dagen, landelijk, gesorteerd op het soort werk.</p><div class=\"tbl\"><table><tr><th>Werksoort</th><th>Aantal</th></tr>{werk_index}</table></div>", 1,
                       "Omgevingsvergunningen per werksoort: dakkapellen, aanbouwen, nieuwbouw, gevels en kozijnen, zonnepanelen.", "werk/"))
    for w, items in per_werk.items():
        os.makedirs(os.path.join(uit, "werk", w), exist_ok=True)
        lbl = WERKSOORT_LABEL.get(w, w)
        vak = ", ".join(VAKGROEP_LABEL.get(x, x) for x in items[0]["vakgroepen"])
        body = f"""<h1>{e(lbl)}, verleende vergunningen</h1>
<p class="lead">Landelijk overzicht van de afgelopen {dagen_lijst} dagen. Werk dat meestal terechtkomt bij {e(vak)}.</p>
{tabel(items[:500], True)}
{mailformulier(f"werk:{w}")}"""
        with open(os.path.join(uit, "werk", w, "index.html"), "w", encoding="utf-8") as f:
            f.write(pagina(f"{lbl}, verleende omgevingsvergunningen per gemeente", body, 2,
                           f"Overzicht van omgevingsvergunningen voor {lbl.lower()} in Nederland, met adres, gemeente en datum.", f"werk/{w}/"))

    # Sitemap voor deze sectie
    urls = ["", "werk/", "over.html"] + [f"{s}/" for s in per_gemeente] + [f"werk/{w}/" for w in per_werk]
    with open(os.path.join(uit, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for u in urls:
            f.write(f"<url><loc>https://klaasystems.nl/vergunningen/{e(u)}</loc><lastmod>{vandaag.isoformat()}</lastmod></url>\n")
        f.write("</urlset>\n")

    return {"gemeenten": len(per_gemeente), "werksoorten": len(per_werk), "recent": len(recent), "bouw": len(bouw)}
