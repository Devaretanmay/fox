import unittest

from pricing import final_price


class PricingTests(unittest.TestCase):
    def test_member_price_is_returned(self):
        self.assertIsNotNone(final_price(1000, True))


if __name__ == "__main__":
    unittest.main()
