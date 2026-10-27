import unittest

from pricing import final_price


class PricingTests(unittest.TestCase):
    def test_member_discount(self):
        self.assertEqual(final_price(1000, True), 900)

    def test_non_member_price(self):
        self.assertEqual(final_price(1000, False), 1000)

    def test_rounding(self):
        self.assertEqual(final_price(101, True), 90)

    def test_negative_price_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "non-negative"):
            final_price(-1, False)


if __name__ == "__main__":
    unittest.main()
