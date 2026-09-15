import json
import os
import sys
import tempfile
import unittest
import datetime as dt

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HIER)

import energiesite as build  # noqa: E402
import cbs  # noqa: E402

FIXTURE = os.path.join(HIER, "fixtures", "kwb_sample.json")


class EnergieTests(unittest.TestCase):
    def setUp(self):
        with open(FIXTURE, encoding="utf-8") as f:
            self.d = json.load(f)
        self.rijen = [cbs.normaliseer(r) for r in self.d["rijen"]]

    def test_normaliseer(self):
        nl = self.rijen[0]
        self.assertEqual(nl["code"], "NL00")
        self.assertEqual(nl["soort"], "land")
        self.assertEqual(nl["gas_m3"], 790)
        self.assertEqual(self.rijen[2]["soort"], "wijk")

    def test_advies_hoog_gas(self):
        nl, g, w = self.rijen[0], self.rijen[1], self.rijen[3]
        alineas = build.advies(w, g, nl, "Eext")
        self.assertTrue(any("meer dan het Nederlandse gemiddelde" in a for a in alineas))
        self.assertTrue(any("zonnepanelen" in a.lower() for a in alineas))

    def test_advies_stadsverwarming_en_corporatie(self):
        nl, g, w = self.rijen[0], self.rijen[4], self.rijen[5]
        alineas = build.advies(w, g, nl, "Woensel-Zuid")
        self.assertTrue(any("stadsverwarming" in a for a in alineas))
        self.assertFalse(any("hybride warmtepomp" in a for a in alineas))
        self.assertTrue(any("woningcorporatie" in a for a in alineas))

    def test_bouw_site(self):
        with tempfile.TemporaryDirectory() as tmp:
            stats = build.bouw_site(self.rijen, self.d["namen"], tmp, dt.date(2026, 9, 15))
            self.assertEqual(stats["gemeenten"], 2)
            self.assertEqual(stats["wijken"], 4)
            self.assertTrue(os.path.exists(os.path.join(tmp, "aa-en-hunze", "annen", "index.html")))
            self.assertTrue(os.path.exists(os.path.join(tmp, "eindhoven", "stratum", "index.html")))
            with open(os.path.join(tmp, "eindhoven", "stratum", "index.html"), encoding="utf-8") as f:
                html = f.read()
            self.assertIn("Energie in Stratum, Eindhoven", html)
            self.assertIn("1.010 m³", html)
            self.assertIn("ISDE", html)
            self.assertNotIn("Offertes vergelijken", html)  # geen partner geconfigureerd

    def test_getal(self):
        self.assertEqual(build.getal(1234), "1.234")
        self.assertEqual(build.getal(7.4, "%", 1), "7,4%")
        self.assertEqual(build.getal(None), "onbekend")


if __name__ == "__main__":
    unittest.main()
