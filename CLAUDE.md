# Klaasystems website

Statische site voor Klaasystems (klaasystems.nl), gehost via GitHub Pages vanaf `main`. Zie README.md voor hosting en het contactformulier.

- `index.html`: de hoofdsite, één zelfstandig bestand zonder dependencies (lettertype Archivo en logo zitten erin).
- `urenbriefje/`: demo urenregistratie.
- `vlakmaat/`: tool voor het opmeten van vlakken uit rastertekeningen.
- `configurator/`: demo productconfigurator die orders als JSON naar Speed40 stuurt, met een lokale bridge in `bridge.mjs`. Zie `configurator/README.md`.

Schrijf teksten in het Nederlands. Loop bij elke tekst- of ontwerpwijziging de checklist hieronder na voordat je klaar bent.

# AI-tell check (versie 1.1)

Nederlandse eindcontrole voor tekst en visuele output. Controleer punt voor punt. Komt een patroon terug zonder duidelijke reden, herschrijf of verwijder het. Eén patroon zegt weinig, het wordt vooral herkenbaar wanneer meerdere defaults zich opstapelen.

Dit is geen AI-detector. Behoud bewust gekozen stijl, citaten en merkregels. De voorbeelden onder "Afkeur" bevatten de genoemde patronen bewust.

## Tekstueel

Controleer taal, ritme, opbouw en formatting. De voorbeelden zijn patroonherkenning, geen letterlijke blacklist.

1. **De em-dash.** Het lange gedachtestreepje (—) midden in een zin, zeker als het meerdere keren voorkomt voor nadruk of een dramatische pauze. Afkeur: "De oplossing werkt direct — zonder ingewikkelde implementatie." Gebruik een punt, komma of schrijf de zin opnieuw.
2. **De dubbele punt als standaard truc.** Ieder mini-inzicht, voordeel of antwoord wordt aangekondigd met een dubbele punt. Afkeur: "Het resultaat: meer rust." "De reden: eenvoud." "Ons advies: begin klein." Gebruik een dubbele punt alleen wanneer de zin hem echt nodig heeft.
3. **"Niet X, maar Y".** Eerst iets afwijzen om daarna het echte punt te presenteren. Afkeur: "Het gaat niet om harder werken, maar om slimmer werken." Ook: "Geen X. Geen Y. Gewoon Z." Zeg direct wat je bedoelt.
4. **Automatische drieslagen.** Groepjes van drie zonder dat de inhoud daar reden voor geeft. Afkeur: "Sneller, slimmer en efficiënter." "Meer rust, overzicht en controle." Laat het aantal uit de inhoud ontstaan.
5. **Losse punchlines.** Korte losse regels die vooral gewicht of ritme moeten suggereren. Afkeur: "Dit werkt. Elke keer. Zonder gedoe." Maak er gewone lopende tekst van wanneer de losse regels geen functie hebben.
6. **Nep-spanning als overgang.** Het inzicht wordt eerst aangekondigd en daarna pas gegeven. Afkeur: "Hier wordt het interessant." "En precies daar zit het verschil." "Wat veel mensen vergeten…" Schrap de aankondiging en begin bij het inhoudelijke punt.
7. **Retorische microvragen.** Een vraag die onmiddellijk door dezelfde schrijver wordt beantwoord. Afkeur: "Het resultaat? Meer overzicht." "Waarom? Heel simpel." "Het probleem? Tijd." Maak er een normale zin van.
8. **Vet label + dubbele punt.** Een antwoord of blok opgeknipt in mini-labels met vetgedrukte woorden en een dubbele punt. Afkeur: "Snelheid: … Kosten: … Schaalbaarheid: …" Gebruik koppen of bullets alleen wanneer de structuur ze nodig heeft.
9. **Versleten Nederlandse AI-woorden.** Woorden die op zichzelf prima zijn maar in generieke copy zonder concrete betekenis terugkomen: naadloos, moeiteloos, krachtig, slim, innovatief, toekomstbestendig, schaalbaar, impact, efficiëntie, ontzorgen, waarde toevoegen, naar een hoger niveau tillen. Ook: seamless, unlock, AI-powered, all-in-one, next level. Beschrijf wat er feitelijk gebeurt.
10. **Generieke openingen.** Openingen die op vrijwel ieder bedrijf of onderwerp passen. Afkeur: "In een wereld waarin…" "Steeds meer bedrijven…" "In het huidige digitale landschap…" "Of je nu ondernemer, marketeer of professional bent…" Begin bij de daadwerkelijke situatie.
11. **Vage autoriteit.** Claims geloofwaardiger maken met een niet-gespecificeerde bron of groep experts. Afkeur: "Onderzoek toont aan…" "Experts zijn het erover eens…" "Steeds meer organisaties ontdekken…" Noem de bron of haal de claim weg.
12. **Overbodige uitleg.** Na een duidelijke zin volgt een zin die uitlegt wat de lezer al begreep. Afkeur: "Hierdoor ontstaat meer overzicht. Dat zorgt ervoor dat teams beter kunnen werken." Controleer of de volgende zin daadwerkelijk nieuwe informatie bevat.
13. **Te nette CTA.** Een generieke afsluiting die onder vrijwel iedere zakelijke tekst kan staan. Afkeur: "Klaar voor de volgende stap?" "Benieuwd wat we voor jou kunnen betekenen?" "Ontdek de mogelijkheden." Vraag om de concrete actie die in deze situatie logisch is.
14. **Vlak ritme.** Alinea's met dezelfde lengte, zinsbouw en cadans voelen gemaakt in plaats van geschreven. Laat de inhoud het ritme bepalen. Wissel zinslengte en alinea-opbouw alleen wanneer dat natuurlijk volgt.
15. **Te perfecte balanszinnen.** Nette tegenstellingen die slim klinken maar weinig concreets zeggen. Afkeur: "Professioneel zonder afstandelijk te worden." "Snel zonder kwaliteit te verliezen." Maak concreet welke keuze, handeling of uitkomst bedoeld wordt.
16. **Overbodige voorbehouden.** Caveats die de boodschap nauwelijks veranderen. Afkeur: "Hoewel dit per situatie kan verschillen…" "Het is belangrijk om te benadrukken dat…" Houd alleen nuances die inhoudelijk echt nodig zijn.
17. **Generieke tweede persoon.** Een vaag "jij" zonder echte situatie, rol of probleem. Afkeur: "Zodat jij kunt focussen op wat echt telt." "Jij verdient een oplossing die werkt." Schrijf voor de daadwerkelijke lezer en benoem diens concrete context.
18. **Abstracte resultaatwoorden.** Grote woorden zonder voorbeeld, handeling, getal of duidelijke situatie: impact, groei, vertrouwen, verbinding, focus, kwaliteit, duidelijkheid, waarde, efficiëntie, resultaatgericht. Maak het resultaat concreet of laat het woord weg.
19. **Template-zinnen over maatwerk.** Standaardformules die persoonlijkheid of maatwerk suggereren zonder iets specifieks te zeggen. Afkeur: "Elke organisatie is uniek." "Geen twee bedrijven zijn hetzelfde." "We geloven in oplossingen op maat." Laat maatwerk blijken uit concrete keuzes.
20. **Te gladde neutraliteit.** De tekst probeert alles af te dekken, niemand uit te sluiten en geen keuze te maken. Kies. Benoem wat wel past en wat niet.

## Visueel

Controleer de basisopmaak van websites, interfaces en andere gegenereerde layouts. Let vooral op defaults die losstaan van merk of inhoud.

21. **De zwevende middot.** De · als decoratieve separator tussen woorden, labels of metadata. Afkeur: "AI · AUTOMATION · SOFTWARE" of "Strategy · Design · Development". Gebruik normale spacing, typografie of een separator uit de huisstijl.
22. **Paarse AI-look.** Paars, indigo, elektrisch blauw en lavendel, zeker in combinatie met donkere achtergronden en glow. Gebruik het bestaande merkpalet en voeg geen AI-kleur toe omdat het onderwerp AI is.
23. **Gradient tekst.** Eén woord of deel van een headline met een blauw-paarse gradient. Gebruik typografie, schaal of positie voor hiërarchie.
24. **Gekleurde linkerrand op cards.** Een dunne blauwe, paarse of gradient lijn aan de linkerkant van een kaart of tekstblok. Gebruik echte visuele hiërarchie via typografie, ruimte of achtergrond.
25. **Drie identieke cards.** Drie even grote blokken met icoon, kop en twee regels tekst, vaak direct onder de hero. Laat formaat en positie volgen uit het belang van de inhoud.
26. **De standaard AI-hero.** Kleine pill of badge bovenaan, grote gecentreerde headline, kort grijs tekstje, twee buttons en daaronder drie cards. Bouw de compositie rond inhoud en merk.
27. **Overal grote afgeronde hoeken.** Cards, buttons, afbeeldingen en formulieren met dezelfde ruime border-radius. Gebruik afronding alleen wanneer die bij het ontwerp hoort.
28. **Glassmorphism en glow.** Halftransparante kaarten, blur, lichtvlekken, zwevende gradients en gekleurde aura's om een interface "premium" te laten voelen. Verwijder decoratie die geen functie heeft.
29. **Default AI-fonts.** Inter, Geist, system UI en vergelijkbare defaults zonder bewuste typografische keuze. Gebruik de merktypografie (hier: Archivo) of kies het lettertype bewust.
30. **Willekeurig cursief serif-woord.** Een sans-serif headline met ineens één cursief serif-woord voor visueel effect. Voeg geen tweede typografische stijl toe zonder duidelijke reden.
31. **Kleine kapitalen boven ieder blok.** Sectielabels in hoofdletters met veel letterafstand boven vrijwel ieder onderdeel. Afkeur: "PRODUCT FEATURES", "ABOUT US", "HOW IT WORKS". Gebruik de typografische hiërarchie van het merk.
32. **Sparkles en AI-sterretjes.** Sterretjes, glimmers en sparkle-iconen bij alles wat met AI te maken heeft, ook als SVG. Gebruik een icoon alleen wanneer het iets verduidelijkt.
33. **Generieke lijniconen.** Bij ieder voordeel hetzelfde soort dunne outline-icon zonder inhoudelijke toevoeging. Laat iconen weg wanneer de informatie zonder icoon even duidelijk is.
34. **Overmatige animatie.** Alles fade-in, cards bewegen bij hover, achtergronden zweven mee zonder functionele reden. Animeer alleen gedrag dat door beweging duidelijker of bruikbaarder wordt.
35. **Component-library look.** De pagina voelt als een standaard componentenset die rechtstreeks is ingevuld: dezelfde card, button, border, radius en spacing overal. Doorbreek defaults en maak hiërarchie die bij de inhoud past.
36. **Perfecte symmetrie.** Alles exact gecentreerd, iedere sectie dezelfde breedte, hoogte en hoeveelheid content. Laat belangrijke informatie visueel meer ruimte innemen.
37. **Stock-achtige AI-decoratie.** Abstracte 3D-objecten, zwevende dashboards, bollen, rasters en vormen die niets concreets laten zien. Gebruik echte productbeelden, concrete UI of laat de visual weg.

## Eindcontrole

- Hoort deze tekst of interface zichtbaar bij deze afzender, doelgroep en situatie?
- Staat er iets in dat net zo goed op tien andere websites of posts kan staan?
- Is ieder visueel element nodig, of staat het er vooral omdat de pagina anders leeg voelt?
- Zijn claims concreet genoeg om geloofwaardig te zijn?
- Is de toon menselijk, direct en eigen?

Als een zin, blok of ontwerpkeuze generiek voelt, pas hem aan of verwijder hem.
