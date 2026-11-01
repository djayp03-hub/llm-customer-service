import unittest
from evaluation.score import score


class EvaluationTests(unittest.TestCase):
    def test_top_three_is_not_top_one(self):
        result = score([{'id': 'a', 'expected_flow': 'cancel_order',
                         'candidates': ['query_order_detail', 'cancel_order'],
                         'expected_slots': {'order_id': '123'},
                         'predicted_slots': {'order_id': 'wrong'}}])
        self.assertEqual(result['top1'], 0)
        self.assertEqual(result['top3'], 1)
        self.assertEqual(result['slot_exact_match'], 0)
        self.assertIsNone(result['task_success_rate'])

    def test_duplicate_cases_rejected(self):
        with self.assertRaises(ValueError):
            score([{'id': 'a', 'expected_flow': 'x', 'candidates': []}] * 2)
