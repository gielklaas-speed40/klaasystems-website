import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import parse  # noqa: E402
import verrijk  # noqa: E402

XML = b"""<?xml version="1.0"?><gemeenteblad><kop><titel>Besluit omgevingsvergunning reguliere procedure verleend Overtoom 53-2 1054HB Amsterdam</titel></kop>
<al>Het college van burgemeester en wethouders heeft een omgevingsvergunning verleend voor het plaatsen van een dakkapel op het achterdakvlak van de woning Overtoom 53-2, 1054HB Amsterdam.</al>
<al>Bezwaar maken kan binnen zes weken.</al></gemeenteblad>"""


class VerrijkTests(unittest.TestCase):
    def test_tekst_en_kern(self):
        tekst = verrijk.tekst_uit_xml(XML)
        self.assertIn("dakkapel", tekst)
        self.assertEqual(verrijk.kern_uit_tekst(tekst), "plaatsen van een dakkapel op het achterdakvlak van de woning Overtoom 53-2, 1054HB Amsterdam"[:140].split(", 1054")[0])

    def test_pas_tekst_toe(self):
        v = parse.verwerk({"id": "gmb-2026-1", "titel": "Besluit omgevingsvergunning reguliere procedure verleend Overtoom 53-2 1054HB Amsterdam", "gemeente": "Amsterdam", "activiteit": "bouwen"})
        self.assertEqual(v["werksoort"], "overig")
        self.assertEqual(v["omschrijving"], "")
        verrijk.pas_tekst_toe(v, verrijk.tekst_uit_xml(XML))
        self.assertEqual(v["werksoort"], "dakkapel")
        self.assertTrue(v["omschrijving"].startswith("plaatsen van een dakkapel"))
        self.assertTrue(v["verrijkt"])

    def test_kern_stopt_bij_zaakadres(self):
        t = "GEMEENTEBLAD Aanvraag omgevingsvergunning Bestevaerstraat 199-H 1055TL Amsterdam Omschrijving: vergroten van de kelder en het realiseren van een aanbouw Zaakadres: Bestevaerstraat 199-H Besluit: verleend"
        self.assertEqual(verrijk.kern_uit_tekst(t), "vergroten van de kelder en het realiseren van een aanbouw")

    def test_xml_url(self):
        self.assertEqual(verrijk.xml_url_voor({"id": "gmb-2026-426434"}),
                         "https://repository.overheid.nl/frbr/officielepublicaties/gmb/2026/gmb-2026-426434/1/xml/gmb-2026-426434.xml")
        self.assertEqual(verrijk.xml_url_voor({"id": "x", "xml_url": "https://a/b.xml"}), "https://a/b.xml")


if __name__ == "__main__":
    unittest.main()
