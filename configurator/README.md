# Productconfigurator, demo voor Speed40

Demo voor de beurs. Bezoekers configureren een bank, een eettafel, een kast of
raamdecoratie, zien de tekening en de prijs meelopen, en de order gaat als JSON
naar Speed40. De pagina is één HTML-bestand zonder dependencies, net als de
andere demo's in deze repo.

## Starten

```
node configurator/bridge.mjs
```

Open daarna http://localhost:4040. Zonder verdere instellingen draait de bridge
in spiegelmodus. Er gaat dan niets naar buiten en de bridge antwoordt zelf met
een ordernummer, zodat je de hele flow kunt laten zien voordat de koppeling
klaar is.

Echt doorsturen naar Speed40:

```
SPEED40_BASIS=https://api.speed40.nl \
SPEED40_SLEUTEL=xxxxxxxx \
SPEED40_HEADER=X-Api-Key \
node configurator/bridge.mjs
```

Een verzoek op `/speed40/v1/orders` gaat dan naar
`https://api.speed40.nl/v1/orders`, met de sleutel in de header. De bridge logt
elke aanroep met status en tijd.

De pagina kan ook rechtstreeks naar Speed40 posten. Vul dan het endpoint en de
sleutel in op het tabblad Speed40. Dat werkt alleen als de API CORS toestaat, en
de sleutel staat dan in de browser. Voor een demo op een beurslaptop is de
bridge de rustigere route.

Instellingen van de bridge:

| Variabele | Betekenis |
| --- | --- |
| `SPEED40_BASIS` | basis-URL van de API. Leeg laten voor spiegelmodus. |
| `SPEED40_SLEUTEL` | de API-sleutel |
| `SPEED40_HEADER` | naam van de header voor de sleutel, standaard `X-Api-Key` |
| `PORT` | poort van de bridge, standaard 4040 |
| `CATALOGUS` | pad naar een catalogus-JSON die in spiegelmodus op `/speed40/v1/catalogus` komt te staan |

## Wat er naar Speed40 gaat

POST met `Content-Type: application/json`. Voorbeeld met één regel:

```json
{
  "bron": "configurator-demo",
  "catalogus_versie": "demo-2026-09",
  "referentie": "CFG-20260918-417",
  "aangemaakt_op": "2026-09-18T08:12:44.201Z",
  "valuta": "EUR",
  "relatie": {
    "naam": "Woonwinkel De Hoek",
    "klantnummer": "10245",
    "email": "inkoop@dehoek.nl",
    "telefoon": "040 123 45 67",
    "referentie_klant": "Offerte 2026-118"
  },
  "levering": { "gewenste_week": "2026-W41", "opmerking": "" },
  "regels": [
    {
      "regelnummer": 1,
      "artikelcode": "BNK-LNG",
      "productgroep": "bank",
      "omschrijving": "Bank, Lounge, 220 cm",
      "aantal": 1,
      "eenheidsprijs_excl": 3046.4,
      "kortingspercentage": 0,
      "regeltotaal_excl": 3046.4,
      "btw_percentage": 21,
      "configuratie_id": "rm4k2p1x9a",
      "kenmerken": [
        { "code": "breedte", "naam": "Breedte", "waarde_code": "220", "waarde": "220 cm", "eenheid": "cm" },
        { "code": "stofgroep", "naam": "Stofgroep", "waarde_code": "B", "waarde": "Groep B" }
      ]
    }
  ],
  "totalen": { "excl_btw": 3046.4, "btw": 639.74, "incl_btw": 3686.14 }
}
```

Elk kenmerk heeft een code en een waardecode voor de verwerking, en een naam en
waarde voor op papier. Speed40 kan op die codes matchen voor stuklijst, inkoop
en werkbon, terwijl dezelfde regel op een orderbevestiging leesbaar blijft.

Het antwoord mag alles zijn wat de API teruggeeft. De demo toont status, tijd en
de eerste 600 tekens van het antwoord in het verkeerslogboek. De spiegelmodus
antwoordt met `201` en een verzonnen ordernummer.

## De catalogus

Alles wat je in het formulier ziet komt uit de catalogus. In de demo staat die
bovenaan `index.html` onder `DEMO_CATALOGUS`. Op het tabblad Speed40 laad je een
catalogus van een URL, of exporteer je de huidige als JSON om er in het ERP mee
te beginnen.

```json
{
  "versie": "2026-09-18",
  "btw": 21,
  "valuta": "EUR",
  "groepen": [
    {
      "id": "bank",
      "naam": "Banken",
      "enkelvoud": "Bank",
      "tekening": "bank",
      "grondslag": "breedte",
      "modellen": [
        { "code": "BNK-LNG", "naam": "Lounge", "basis": 1290, "perEenheid": 6.5, "omschrijving": "Losse kussens, lage rug" }
      ],
      "opties": []
    }
  ]
}
```

### Assortiment vullen

De map `assortiment/` bevat vijf platte lijsten waarin je vastlegt welke
productgroepen, modellen, opties en varianten er zijn, plus een script dat er
`catalogus.json` van maakt.

```
node configurator/assortiment/catalogus-bouwen.mjs
CATALOGUS=$PWD/configurator/assortiment/catalogus.json node configurator/bridge.mjs
```

De bridge serveert de catalogus dan op `/speed40/v1/catalogus` en je laadt hem in
de pagina onder het tabblad Speed40. Het script controleert de vulling en noemt
bij een fout het bestand en de regel. De kolommen staan in
`assortiment/README.md`, met de vertaling naar de velden in het ERP.

### Velden van de catalogus

Een groep kan op twee manieren in elkaar zitten. Of er staan modellen in
`modellen.csv` en bepalen de opties de uitvoering, of elke variant is een eigen
artikel en klik je er via een trap naartoe. In dat tweede geval staat de trap in
de kolom `trap` van `productgroepen.csv` en staan de artikelen in
`varianten.csv`, elk met zijn eigen pad. De fauteuils in de demo werken zo.

`grondslag` is `breedte` of `m2`. Bij `breedte` rekent de groep met de breedte in
centimeters, bij `m2` met breedte maal hoogte gedeeld door tienduizend. Met
`minimumEenheid` zet je een ondergrens, bijvoorbeeld 0,6 m2 voor een klein
rolgordijn. `tekening` verwijst naar een tekenfunctie in de pagina, nu `bank`,
`tafel`, `kast` of `raam`.

### Opties

| Soort | Velden | Prijsgedrag |
| --- | --- | --- |
| `maat` | `min`, `max`, `stap`, `standaard`, `eenheid` | bepaalt de grondslag, geen eigen toeslag |
| `keuze` | `keuzes` met `code` en `naam` | per keuze `prijs`, `prijsPerEenheid` of `factor` |
| `kleur` | `keuzes` met `code`, `naam`, `hex` | zelfde als `keuze`, de hexwaarde kleurt ook de tekening |
| `schakelaar` | `prijs` of `prijsPerEenheid`, `standaard` | telt mee als hij aan staat |
| `aantal` | `min`, `max`, `standaard`, `prijs`, `gratisTot` | prijs maal aantal boven `gratisTot` |

Drie velden regelen de afhankelijkheden.

- `alleenBijModel` toont de optie alleen bij bepaalde artikelcodes, bijvoorbeeld
  een hangroede die niet bij een dressoir hoort.
- `alleenBij` hangt de optie aan de waarde van een andere optie, bijvoorbeeld
  `{"bediening": ["motor", "motor-app"]}` voor een optie die alleen bij een motor
  bestaat.
- `bereikPerModel` geeft een maat per model andere grenzen, zodat een dressoir
  van 60 tot 120 cm hoog loopt terwijl een schuifdeurkast op 180 begint.

### Hoe de prijs opgebouwd wordt

1. De grondslag komt uit de maten, in centimeters of vierkante meters.
2. Het materiaalbedrag is `basis` van het model plus `perEenheid` maal de
   grondslag.
3. Keuzes met een `factor` werken op dat materiaalbedrag. Stofgroep C met factor
   1,28 maakt het materiaal 28 procent duurder, de toeslagen daarna niet.
4. De overige opties komen er als toeslag bij, vast of per eenheid.
5. Aantal en korting van de orderregel werken op het eindbedrag per stuk.

De hele berekening zit in de functie `bereken` en kent maar deze vijf stappen.
Alle getallen komen uit de catalogus, dus een prijsverhoging of een andere
staffel is een wijziging in de database en niet in de pagina.

## Opschalen naar de echte productdatabase

De demo werkt met vier productgroepen en een handvol modellen, maar de pagina
kent geen enkel product. Dat maakt de stap naar een echte catalogus klein.

- **Artikelen en opties horen in Speed40.** Artikelcodes, optiecodes, prijzen,
  staffels, levertijden en stuklijsten staan daar al. De configurator vraagt ze
  op en tekent het formulier dat erbij hoort. Een nieuwe stofcollectie is een
  aanvulling in het ERP, de volgende keer dat de pagina de catalogus ophaalt
  staat hij erin.
- **Klantprijzen komen mee met de catalogus.** Haal de catalogus op per debiteur
  en de prijzen die terugkomen zijn de prijzen van die klant. De pagina rekent
  alleen door wat hij binnenkrijgt, dus er staat geen prijslogica dubbel.
- **Meerdere merken of leveranciers** zijn extra productgroepen in dezelfde
  catalogus, of een eigen catalogus-URL per merk.
- **Meertaligheid** zit in de naamvelden. Wie Duits of Frans nodig heeft, levert
  de catalogus per taal en de codes blijven gelijk.
- **Een nieuwe productgroep** die lijkt op een bestaande gebruikt een bestaande
  tekening. Alleen een groep die er echt anders uitziet, zoals een keuken of een
  trapleuning, vraagt om een eigen tekenfunctie van ongeveer dertig regels.
- **Validatie** hoort aan beide kanten. De maten en afhankelijkheden in de
  catalogus vangen het meeste af, en Speed40 controleert bij ontvangst nog een
  keer voordat er een order van gemaakt wordt.

## Wat deze demo niet doet

Er zit geen inlog in en de demo kijkt niet naar voorraad, levertijden of
betaling. De prijzen in de ingebouwde catalogus zijn verzonnen en staan er om de
rekenregels te laten zien.
