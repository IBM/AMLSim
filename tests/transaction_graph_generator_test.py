import unittest

from scripts.transaction_graph_generator import directed_configuration_model, get_degrees, get_in_and_out_degrees

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
        with self.assertRaises(ValueError) as context:
            get_in_and_out_degrees([
                ['1', '2', '4'],
                ['2', '4', '2'],
                ['1', '2', '4']
            ], 7)
        self.assertEqual('The number of total accounts (7) must be a multiple of the degree sequence length (4).',
            str(context.exception))

    
    def test_get_in_and_out_degrees_unequal_degrees_throws(self):
        with self.assertRaises(ValueError) as context:
            get_in_and_out_degrees([
                ['1', '2', '4'],
                ['2', '4', '2'],
                ['1', '2', '3']
            ], 8)
        self.assertEqual('The sum of in-degree (12) and out-degree (11) must be same.', 
            str(context.exception))


    def test_directed_configuration_model(self):
        G = directed_configuration_model(
            [2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1], # in
            [0, 0, 2, 1, 1, 0, 0, 0, 1, 1, 0, 0],
            0
        )
        # no self-loops were removed.
        self.assertEqual(G.degree(0), 2)
        self.assertEqual(G.degree(1), 2)
        self.assertEqual(G.degree(2), 2)
        self.assertEqual(G.degree(3), 1)
        self.assertEqual(G.degree(4), 1)
        self.assertEqual(G.degree(5), 0)
        self.assertEqual(G.degree(6), 0)
        self.assertEqual(G.degree(7), 0)
        self.assertEqual(G.degree(8), 1)
        self.assertEqual(G.degree(9), 1)
        self.assertEqual(G.degree(10), 1)
        self.assertEqual(G.degree(11), 1)


    def test_directed_configuration_model_no_self_loops(self):
        G = directed_configuration_model(
            [2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1], # in
            [0, 0, 2, 1, 1, 0, 0, 0, 1, 1, 0, 0],
            0
        )
        self.assertEqual(G.selfloop_edges(), [])

    
    def test_directed_configuration_model_self_loops(self):
        G = directed_configuration_model(
            [10, 1, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0], # in
            [2, 10, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            0
        )
        self.assertEqual(G.degree(0), 12)
        self.assertEqual(G.degree(1), 11)
        self.assertEqual(G.degree(2), 5)
        self.assertEqual(G.degree(3), 0)
        self.assertEqual(G.degree(4), 0)
        self.assertEqual(G.degree(5), 0)
        self.assertEqual(G.degree(6), 0)
        self.assertEqual(G.degree(7), 0)
        self.assertEqual(G.degree(8), 0)
        self.assertEqual(G.degree(9), 0)
        self.assertEqual(G.degree(10), 0)
        self.assertEqual(G.degree(11), 0)
        self.assertEqual(G.selfloop_edges(), [])
        


if __name__ == ' main ':
    unittest.main()