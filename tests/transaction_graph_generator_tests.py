import unittest

from scripts.transaction_graph_generator import get_degrees, get_in_and_out_degrees

class TransactionGraphGeneratorTests(unittest.TestCase):

    
    def test_get_degrees(self):
        result = get_degrees('tests/csv/degree.csv', 12)
        self.assertEqual(result, (
           [2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1], # in
           [0, 0, 2, 1, 1, 0, 0, 0, 1, 1, 0, 0]  # out
        ))


    def test_get_in_and_out_degrees_no_padding(self):
        result = get_in_and_out_degrees([
            ['1', '2', '4'],
            ['2', '4', '2'],
            ['1', '2', '4']
        ], 4)
        self.assertEqual(result, (
            [2, 4, 4, 2],
            [4, 2, 2, 4]
        ))


    def test_get_in_and_out_degrees_padding(self):
        result = get_in_and_out_degrees([
            ['1', '2', '4'],
            ['2', '4', '2'],
            ['1', '2', '4']
        ], 8)
        self.assertEqual(result, (
            [2, 4, 4, 2, 2, 4, 4, 2],
            [4, 2, 2, 4, 4, 2, 2, 4]
        ))

    
    def test_get_in_and_out_degrees_bad_mod_throws(self):
        with self.assertRaises(ValueError):
            get_in_and_out_degrees([
                ['1', '2', '4'],
                ['2', '4', '2'],
                ['1', '2', '4']
            ], 7)
        


if __name__ == ' main ':
    unittest.main()