"""Verify post-run anchoring repairs cannot invent a value or drop its sign."""
import unittest
from test.benchmark_review import anchor, repair_claim

class ReviewTests(unittest.TestCase):
    def test_markdown_repair_returns_literal_original_substring(self):
        text='**Postseason PPG:** **33.8**'
        actual=anchor('Postseason PPG: 33.8',text)
        self.assertEqual(actual,'Postseason PPG:** **33.8')
        self.assertIn(actual,text)
    def test_cannot_anchor_invented_text(self):
        self.assertIsNone(anchor('Average: 99.9','Average: 30.1'))
    def test_comma_repair_preserves_original_number(self):
        claim={'quote':'5,793','number':'5793','scope_quote':'Window','scope':'requested'}
        self.assertEqual(repair_claim(claim,'Window: 5,793')['number'],'5,793')
    def test_positive_sign_repaired_but_negative_sign_not_changed(self):
        base={'quote':'+9.71','number':'9.71','scope_quote':'Window','scope':'requested'}
        self.assertEqual(repair_claim(base,'Window: +9.71')['number'],'+9.71')
        negative={**base,'quote':'-9.71'}
        self.assertEqual(repair_claim(negative,'Window: -9.71')['number'],'9.71')
    def test_original_claim_not_mutated(self):
        claim={'quote':'5,793','number':'5793','scope_quote':'Window'}
        repair_claim(claim,'Window: 5,793')
        self.assertEqual(claim['number'],'5793')

if __name__=='__main__':unittest.main()
