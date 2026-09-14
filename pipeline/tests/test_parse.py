import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fetch  # noqa: E402
import parse  # noqa: E402

FIXTURE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures", "sru_sample.xml")


class ParseTests(unittest.TestCase):
    def test_status(self):
        self.assertEqual(parse.bepaal_status("Verleende omgevingsvergunning dakkapel"), "verleend")
        self.assertEqual(parse.bepaal_status("Aanvraag omgevingsvergunning, bouwen"), "aangevraagd")
        self.assertEqual(parse.bepaal_status("Verlengen beslistermijn omgevingsvergunning"), "verlengd")
        self.assertEqual(parse.bepaal_status("Geweigerde omgevingsvergunning"), "geweigerd")

    def test_status_toestemming_en_voornemen(self):
        self.assertEqual(parse.bepaal_status("Toestemming voor het plaatsen van een woonwagen, Molenheg 31"), "verleend")
        self.assertEqual(parse.bepaal_status("Voornemen om een vergunning te verlenen voor het aanpassen"), "ontwerp")
        self.assertEqual(parse.bepaal_status("Kennisgeving besluit op aanvraag omgevingsvergunning Kerkvaart"), "verleend")

    def test_geen_valse_straat(self):
        a = parse.vind_adres("Toestemming voor het bouwen van een woning aan Lobelia ong, kavel 59 De Moer, Verzoeklocatie 2026063002080")
        self.assertNotEqual(a["straat"], "Verzoeklocatie")
        self.assertNotIn("2026063002080", a["huisnummer"])

    def test_omschrijving_schoon(self):
        self.assertEqual(parse.omschrijving_uit_titel("Ingediende aanvraag omgevingsvergunning: plaatsen van 2 airco units, Remuslaan 2 5631JP Eindhoven"), "plaatsen van 2 airco units, Remuslaan 2")
        self.assertEqual(parse.omschrijving_uit_titel("Kennisgeving verlenging beslistermijn"), "")
        self.assertEqual(parse.omschrijving_uit_titel("Kennisgeving termijnverlenging Z2026-00000352, Kruinweg 1b-105, 6369TZ Simpelveld"), "Kruinweg 1b-105")

    def test_postcode_zonder_spatie(self):
        v = parse.verwerk({"id": "y", "titel": "Aanvraag, plaatsen overkapping, Industrieweg 6, 4153BW Beesd", "gemeente": "West Betuwe"})
        self.assertEqual(v["adres"]["postcode"], "4153 BW")
        self.assertEqual(v["omschrijving"], "plaatsen overkapping")

    def test_omschrijving_na_adres(self):
        v = parse.verwerk({"id": "z", "titel": "Verleend, reguliere procedure, Wethouder Rebellaan 104 Barneveld, het verbouwen en uitbreiden van de woning", "gemeente": "Barneveld"})
        self.assertEqual(v["adres"]["straat"], "Wethouder Rebellaan")
        self.assertEqual(v["omschrijving"], "verbouwen en uitbreiden van de woning")
        self.assertEqual(v["status"], "verleend")

    def test_werksoort(self):
        self.assertEqual(parse.bepaal_werksoort("plaatsen van een dakkapel")[0], "dakkapel")
        self.assertEqual(parse.bepaal_werksoort("kappen van een boom")[0], "kappen")
        self.assertEqual(parse.bepaal_werksoort("het bouwen van een woning")[0], "nieuwbouw")
        self.assertEqual(parse.bepaal_werksoort("vervangen kozijnen voorgevel")[0], "gevel")
        self.assertEqual(parse.bepaal_werksoort("iets onduidelijks")[0], "overig")

    def test_adres_met_postcode(self):
        a = parse.vind_adres("dakkapel, Dorpsstraat 12, 5611 AB Eindhoven")
        self.assertEqual(a, {"straat": "Dorpsstraat", "huisnummer": "12", "postcode": "5611 AB", "plaats": "Eindhoven"})

    def test_adres_zonder_postcode(self):
        a = parse.vind_adres("aanbouw, Van der Heijdenlaan 3a te Tilburg")
        self.assertEqual(a["straat"], "Van der Heijdenlaan")
        self.assertEqual(a["huisnummer"], "3a")

    def test_adres_plaats_met_lidwoord(self):
        a = parse.vind_adres("Kerkstraat 7, 5251 AB Vlijmen")
        self.assertEqual(a["plaats"], "Vlijmen")
        a = parse.vind_adres("Markt 1, 5211 JX 's-Hertogenbosch")
        self.assertEqual(a["postcode"], "5211 JX")

    def test_verwerk_uit_fixture(self):
        with open(FIXTURE, "rb") as f:
            records, totaal, diagnose = fetch.records_uit_xml(f.read())
        self.assertEqual(totaal, 6)
        self.assertEqual(diagnose, "")
        verwerkt = [parse.verwerk(r) for r in records]
        ids = {v["id"] for v in verwerkt}
        self.assertIn("gmb-2026-400001", ids)
        eerste = next(v for v in verwerkt if v["id"] == "gmb-2026-400001")
        self.assertEqual(eerste["gemeente"], "Eindhoven")
        self.assertEqual(eerste["werksoort"], "dakkapel")
        self.assertEqual(eerste["status"], "verleend")
        self.assertEqual(eerste["url"], "https://zoek.officielebekendmakingen.nl/gmb-2026-400001.html")
        self.assertEqual(eerste["activiteit"], "bouwen")
        self.assertEqual(eerste["coord"], "51.43810,5.47520")
        self.assertNotIn("Dorpsstraat", eerste["omschrijving"])
        groningen = next(v for v in verwerkt if v["id"] == "gmb-2026-400006")
        self.assertEqual(groningen["gemeente"], "Groningen")
        kap = next(v for v in verwerkt if v["id"] == "gmb-2026-400003")
        self.assertFalse(kap["is_bouw"])

    def test_activiteit_bouwen_zonder_herkende_werksoort(self):
        v = parse.verwerk({"id": "x", "titel": "Verleende omgevingsvergunning, Kerkstraat 7, 5251 AB Vlijmen", "gemeente": "Heusden", "activiteit": "bouwen"})
        self.assertEqual(v["werksoort"], "overig")
        self.assertTrue(v["is_bouw"])
        self.assertEqual(v["vakgroepen"], ["aannemer"])

    def test_queries(self):
        q = fetch.bouw_queries("2026-09-01")
        self.assertIn('w.publicatienaam=="Gemeenteblad"', q[0])
        self.assertIn('dt.type=="omgevingsvergunning"', q[0])
        self.assertIn('dt.title any "omgevingsvergunning"', q[1])


if __name__ == "__main__":
    unittest.main()
