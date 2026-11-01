import unittest
from valuation import estimate, buyer_offer


class ValuationTests(unittest.TestCase):
    def setUp(self):
        self.bike = dict(brand="B'Twin", model="My Bike", specs="Steel, single-speed, V-brakes",
                         size="M / 26", demand="standard", replacement=6999, age=2,
                         condition="good", repairs=300, overhead=200, quote=1800,
                         target=300, inspected=True, ownership=True, damage=False)

    def test_example_and_profit(self):
        r = estimate(self.bike)
        self.assertEqual((r["value"], r["buy_max"], r["sell"], r["profit"]), (3850, 2309, 3080, 780))
        self.assertTrue(r["eligible"])

    def test_strict_threshold_and_cost_guard(self):
        self.bike["quote"] = 2310
        self.assertFalse(estimate(self.bike)["eligible"])
        self.bike["quote"] = 2309
        self.bike["target"] = 1
        self.assertTrue(estimate(self.bike)["eligible"])
        self.bike["overhead"] = 2000
        self.assertFalse(estimate(self.bike)["eligible"])

    def test_inspection_ownership_and_damage(self):
        for field, value in (("inspected", False), ("ownership", False), ("damage", True), ("demand", "unknown")):
            with self.subTest(field=field):
                self.assertFalse(estimate({**self.bike, field: value})["eligible"])

    def test_repairs_can_wipe_out_value(self):
        self.bike["repairs"] = 10000
        r = estimate(self.bike)
        self.assertEqual(r["value"], 0)
        self.assertFalse(r["eligible"])
        self.assertIsNone(r["business_max"])

    def test_reject_invalid_numbers(self):
        for value in (float("nan"), float("inf"), -1, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                estimate({**self.bike, "quote": value})

    def test_buyer_floor_and_overbid(self):
        self.assertFalse(buyer_offer(3850, 3079)["price_ok"])
        self.assertTrue(buyer_offer(3850, 3080)["price_ok"])
        self.assertEqual(buyer_offer(3850, 4000)["price"], 3080)
        for offer in (-1, float("nan"), True, "oops"):
            with self.assertRaises(ValueError):
                buyer_offer(3850, offer)


if __name__ == "__main__":
    unittest.main()
