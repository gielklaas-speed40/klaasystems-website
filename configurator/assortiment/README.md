# Assortiment vastleggen voor de configurator

De configurator weet alleen wat er in deze lijsten staat. Vijf bestanden, elk
met één soort gegeven. Je vult ze in Excel of je exporteert ze uit Speed40, en
`catalogus-bouwen.mjs` maakt er `catalogus.json` van.

```
node configurator/assortiment/catalogus-bouwen.mjs
CATALOGUS=$PWD/configurator/assortiment/catalogus.json node configurator/bridge.mjs
```

Daarna staat de catalogus op http://localhost:4040/speed40/v1/catalogus en laad
je hem in de pagina onder het tabblad Speed40. Het script controleert de vulling
en noemt bij een fout het bestand en de regel. Zolang er een fout in zit schrijft
het niets weg.

Opslaan in Excel via Bestand, Opslaan als, CSV UTF-8. Een puntkomma tussen de
kolommen is goed, een komma of een tab leest het script ook. Voor decimalen mag
je 6,5 of 6.5 schrijven.

## Welke lijst bepaalt wat

| Vraag | Bestand |
| --- | --- |
| Welke productgroepen bestaan er en waarop rekenen ze | `productgroepen.csv` |
| Welke modellen kun je kiezen binnen een groep | `modellen.csv` |
| Welke keuzes horen bij een groep en hoe werken ze | `opties.csv` |
| Welke varianten heeft een keuze en wat kost elke variant | `optiewaarden.csv` |
| Welke maatgrenzen gelden per model | `maatbereik.csv` |

De varianten die een bezoeker ziet komen dus uit `modellen.csv` voor het model
zelf en uit `optiewaarden.csv` voor alles daaronder. Een nieuwe stofkleur is één
regel erbij, een nieuw model is één regel in `modellen.csv` plus de maatgrenzen
als die afwijken.

## instellingen.csv

Twee kolommen, `sleutel` en `waarde`. Dit hoort erin.

| Sleutel | Voorbeeld | Betekenis |
| --- | --- | --- |
| `versie` | `2026-09-18` | komt mee in elke order als `catalogus_versie`, zodat je terug kunt zien op welke prijslijst een order gemaakt is |
| `btw` | `21` | btw-percentage voor de hele catalogus |
| `valuta` | `EUR` | valuta voor de bedragen |
| `herkomst` | `Speed40 export` | vrije tekst, handig bij het testen |

## productgroepen.csv

Eén regel per groep, bijvoorbeeld banken of raamdecoratie.

| Kolom | Nodig | Betekenis |
| --- | --- | --- |
| `groep_id` | ja | korte code zonder spaties, bijvoorbeeld `bank`. Andere lijsten verwijzen hiernaar. |
| `naam` | ja | meervoud, zoals het op de knop komt te staan |
| `enkelvoud` | nee | gebruikt in de omschrijving van een orderregel |
| `tekening` | ja | `bank`, `tafel`, `kast` of `raam` |
| `grondslag` | ja | `breedte` rekent per centimeter breed, `m2` rekent met breedte maal hoogte |
| `minimum_eenheid` | nee | ondergrens voor de grondslag, bijvoorbeeld `0,6` m2 voor een klein rolgordijn |
| `volgorde` | nee | bepaalt de volgorde van de knoppen, laag getal komt eerst |

Een groep met `grondslag` op `breedte` heeft een optie `breedte` van soort `maat`
nodig. Een groep op `m2` heeft `breedte` en `hoogte` nodig. Het script zegt het
als dat ontbreekt.

## modellen.csv

Eén regel per model. Dit zijn de artikelen zoals ze in Speed40 staan.

| Kolom | Nodig | Betekenis |
| --- | --- | --- |
| `groep_id` | ja | verwijst naar `productgroepen.csv` |
| `artikelcode` | ja | gaat als `artikelcode` mee in de orderregel |
| `naam` | ja | naam op de knop |
| `omschrijving` | nee | regel eronder, bijvoorbeeld `Massief eiken, 6 cm dik` |
| `basisprijs` | ja | vast bedrag, exclusief btw |
| `prijs_per_eenheid` | nee | bedrag per centimeter of per m2, afhankelijk van de grondslag van de groep |
| `volgorde` | nee | volgorde van de modellen |

Een bank van 220 cm met basisprijs 1290 en 6,50 per centimeter komt uit op
1290 plus 220 maal 6,50 is 2720 euro materiaal, waar de opties nog bij komen.

## opties.csv

Eén regel per keuze binnen een groep. De kolom `soort` bepaalt hoe het veld
werkt en welke andere kolommen je invult.

| Kolom | Nodig | Betekenis |
| --- | --- | --- |
| `groep_id` | ja | verwijst naar `productgroepen.csv` |
| `optie_id` | ja | korte code, uniek binnen de groep. Komt als `code` mee in het kenmerk op de orderregel. |
| `naam` | ja | label boven het veld |
| `blok` | nee | kopje waaronder de optie komt te staan, bijvoorbeeld `Maatvoering` of `Bekleding` |
| `soort` | ja | `maat`, `keuze`, `kleur`, `schakelaar` of `aantal` |
| `volgorde` | nee | volgorde binnen het blok |
| `eenheid` | bij `maat` | `cm` of `mm`, staat achter de waarde |
| `min` `max` `stap` | bij `maat` en `aantal` | grenzen van de schuifbalk |
| `standaard` | zie hieronder | waarde waarmee het formulier opent |
| `prijs` | bij `schakelaar` en `aantal` | vaste meerprijs, bij `aantal` is het de prijs per stuk |
| `prijs_per_eenheid` | nee | meerprijs per centimeter of per m2, alleen bij `schakelaar` |
| `gratis_tot` | nee | aantal stuks dat niets kost, bijvoorbeeld twee legplanken inbegrepen |
| `alleen_bij_model` | nee | artikelcodes met een `|` ertussen, de optie verschijnt alleen daarbij |
| `alleen_bij` | nee | `optie_id=waarde` of `optie_id=waarde|waarde`, de optie verschijnt alleen bij die keuze |

Wat er in `standaard` hoort:

- bij `maat` en `aantal` een getal binnen min en max
- bij `keuze` en `kleur` een `waarde_code` uit `optiewaarden.csv`
- bij `schakelaar` `ja` of `nee`

## optiewaarden.csv

Eén regel per variant van een optie van soort `keuze` of `kleur`. Hier staan de
stofgroepen, de kleuren, de onderstellen en de soorten bediening.

| Kolom | Nodig | Betekenis |
| --- | --- | --- |
| `groep_id` `optie_id` | ja | verwijzen naar de optie |
| `waarde_code` | ja | code die meegaat in de order als `waarde_code` |
| `naam` | ja | tekst op de knop |
| `prijs` | nee | vaste meerprijs voor deze variant |
| `prijs_per_eenheid` | nee | meerprijs per centimeter of per m2 |
| `factor` | nee | vermenigvuldigt de materiaalprijs, `1,28` is 28 procent duurder |
| `hex` | bij `kleur` | kleurcode zoals `#D9CCB8`, kleurt ook de tekening |
| `volgorde` | nee | volgorde van de knoppen |

Per variant kies je een factor of een prijs, niet allebei. Een factor gebruik je
voor iets dat over het hele product gaat, zoals een stofgroep of een doeksoort.
Een prijs gebruik je voor een toevoeging, zoals een motor of een cassette.

## maatbereik.csv

Alleen nodig als een maat per model andere grenzen heeft. Een dressoir is 60 tot
120 cm hoog, een schuifdeurkast 180 tot 280, met dezelfde optie `hoogte`.

| Kolom | Nodig | Betekenis |
| --- | --- | --- |
| `groep_id` `optie_id` | ja | verwijzen naar een optie van soort `maat` of `aantal` |
| `artikelcode` | ja | het model waarvoor dit bereik geldt |
| `min` `max` `stap` `standaard` | nee | wat je invult overschrijft de waarde uit `opties.csv` |

## Vanuit Speed40 in plaats van Excel

De vijf lijsten zijn bewust plat, zodat ze uit een query of een export kunnen
komen. Dit is de vertaling.

| Lijst | Waar het in het ERP vandaan komt |
| --- | --- |
| `modellen.csv` | artikelstam, met artikelnummer, omschrijving en verkoopprijs |
| `opties.csv` | de kenmerken of variantgroepen die aan een artikelgroep hangen |
| `optiewaarden.csv` | de toegestane waarden per kenmerk, met hun toeslag |
| `maatbereik.csv` | de maatgrenzen per artikel |
| `productgroepen.csv` | de artikelgroepen die je in de configurator wilt tonen |

Laat de API die lijsten samenvoegen tot dezelfde JSON en de configurator leest
hem rechtstreeks. Dan hoef je hier niets meer te draaien en is een prijswijziging
in Speed40 meteen zichtbaar in het formulier.

## Een variant toevoegen

Een kleur erbij is één regel in `optiewaarden.csv`.

```
bank;kleur;mosterd;Mosterd;;;;#C8922F;70
```

Een model erbij is één regel in `modellen.csv`, en een regel in `maatbereik.csv`
als de maten afwijken. Alle opties van de groep gelden meteen voor dat model,
behalve die met een `alleen_bij_model` waar de nieuwe code niet in staat.

## Minimaal per productgroep

- een regel in `productgroepen.csv` met een tekening en een grondslag
- minstens één model met een basisprijs
- een optie `breedte` van soort `maat`, en bij `m2` ook `hoogte`
- per optie van soort `keuze` of `kleur` minstens één waarde, met een standaard
  die daadwerkelijk bestaat
