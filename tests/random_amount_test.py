import unittest

from amlsim.random_amount import RandomAmount

class RoundedAmountTests(unittest.TestCase):

    def test_get_0_10_amount(self):
        amount = RandomAmount(0.0, 10.0).getAmount()
        self.assertLessEqual(amount, 10.0)
        self.assertGreaterEqual(amount, 0.0)

    def test_get_2_35_amount(self):
        amount = RandomAmount(2.0, 31.0).getAmount()
        self.assertGreaterEqual(amount, 2.0)
        self.assertLessEqual(amount, 31.0)

        


if __name__ == ' main ':
    unittest.main()