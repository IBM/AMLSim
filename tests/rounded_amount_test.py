import unittest

from amlsim.rounded_amount import RoundedAmount

class RoundedAmountTests(unittest.TestCase):

    def test_get_0_10_amount(self):
        amount = RoundedAmount(0.0, 10.0).getAmount()
        self.assertLessEqual(amount, 10.0)
        self.assertGreaterEqual(amount, 0.0)

    def test_get_2_35_amount(self):
        amount = RoundedAmount(2.0, 31.0).getAmount()
        self.assertGreaterEqual(amount, 2.0)
        self.assertLessEqual(amount, 31.0)

    def test_get_2_100_amount(self):
        amount = RoundedAmount(2.0, 100.0).getAmount()
        self.assertGreaterEqual(amount, 2.0)
        self.assertLessEqual(amount, 100.0)
        self.assertEqual(amount % 10, 0.0)

    def test_get_42_1000_amount(self):
        amount = RoundedAmount(42.0, 999.0).getAmount()
        self.assertGreaterEqual(amount, 100.0)
        self.assertLessEqual(amount, 900.0)
        self.assertEqual(amount % 100, 0.0)

    def test_get_3000_3100_amount(self):
        amount = RoundedAmount(3000.0, 3100.0).getAmount()
        self.assertGreaterEqual(amount, 3000.0)
        self.assertLessEqual(amount, 3100.0)
        self.assertEqual(amount % 10, 0.0)

    def test_get_45_12000_amount(self):
        amount = RoundedAmount(45.0, 12000.0).getAmount()
        self.assertGreaterEqual(amount, 1000.0)
        self.assertLessEqual(amount, 12000.0)
        self.assertEqual(amount % 1000, 0.0)
        


if __name__ == ' main ':
    unittest.main()