"""Completed cutoff notation is resolved internally without bypassing real ambiguity."""
import unittest
from unittest.mock import patch

from backend.assistant.research_tools import AssistantResearchTools
from backend.research.contract import ScoringContract
from backend.research.scoring import ScoringRun
from backend.research.scope_review import completed_cutoff_fact
from test.test_scoring_review import Data, contract


QUESTION = ('Compare Alpha and Beta over their entire scoring careers, including regular-season '
            'and playoff scoring volume and efficiency. Use completed seasons through 1996-97.')


class CompletedCutoffTests(unittest.TestCase):
    def run_for(self, question=QUESTION):
        research = AssistantResearchTools(data=Data(), players=[{'id': 1, 'name': 'Alpha'}, {'id': 2, 'name': 'Beta'}])
        run = ScoringRun([{'role': 'user', 'content': question}], research)
        run.data = Data()
        return run

    def test_valid_notation_has_one_unambiguous_start_year(self):
        with patch('backend.research.scope_review.current_season', return_value=2026):
            fact = completed_cutoff_fact([{'role': 'user', 'content': QUESTION.replace('1996-97', '2025-26')}])
        self.assertEqual(fact, {'season': '2025-26', 'start_year': 2025, 'completed': True})

    def test_future_invalid_and_multiple_cutoffs_are_not_validated(self):
        with patch('backend.research.scope_review.current_season', return_value=2026):
            for text in ('2026-27', '2025-27', '1983-84', '1996-97 and completed seasons through 1995-96'):
                with self.subTest(text=text):
                    self.assertIsNone(completed_cutoff_fact([{'role': 'user', 'content': 'Use completed seasons through '+text}]))

    def test_assistant_dates_and_stale_user_scope_are_not_treated_as_a_new_cutoff(self):
        messages = [{'role': 'user', 'content': QUESTION}, {'role': 'assistant', 'content': QUESTION},
                    {'role': 'user', 'content': 'Actually use their three-season peaks.'}]
        self.assertIsNone(completed_cutoff_fact(messages))

    def test_invalid_or_ongoing_cutoff_requires_clarification_before_model_or_data_calls(self):
        for suffix in ('2026-27', '2025-27', '1996-97 and completed seasons through 1995-96'):
            with self.subTest(suffix=suffix):
                run = self.run_for(QUESTION.replace('1996-97', suffix))
                with patch('backend.research.scope_review.current_season', return_value=2026), \
                     patch.object(run, 'structured') as model, patch.object(run.data, 'fetch') as fetch:
                    self.assertEqual(run.resolve_contract().action, 'clarify')
                model.assert_not_called()
                fetch.assert_not_called()

    def test_missing_contract_fields_are_resolved_internally_once(self):
        run = self.run_for()
        confused = ScoringContract(action='clarify', question='Is completed 1996-97 cutoff 1996?')
        accepted = contract(period='career', include_context=True)
        with patch.object(run, 'structured', side_effect=[confused, accepted]) as resolve:
            result = run.resolve_contract()
        self.assertEqual(result.action, 'review')
        self.assertEqual(result.cutoff, 1996)
        self.assertEqual(resolve.call_count, 2)
        self.assertEqual(len([m for m in run.messages if m['role'] == 'user']), 1)
        self.assertEqual(run.log[0]['name'], 'recheck_scoring_scope')

    def test_retry_preserves_a_genuine_remaining_scope_question(self):
        run = self.run_for()
        confused = ScoringContract(action='clarify', question='Confirm the completed cutoff?')
        real = ScoringContract(action='clarify', question='Which two players should be compared?')
        with patch.object(run, 'structured', side_effect=[confused, real]) as resolve:
            result = run.resolve_contract()
        self.assertIs(result, real)
        self.assertEqual(resolve.call_count, 2)

    def test_other_clarifications_are_never_bypassed_or_retried(self):
        run = self.run_for()
        real = ScoringContract(action='clarify', question='Choose career scoring or explicit equal-length windows.')
        with patch.object(run, 'structured', return_value=real) as resolve:
            self.assertIs(run.resolve_contract(), real)
        resolve.assert_called_once()

    def test_explicit_earlier_cutoff_overrides_wrong_model_default(self):
        run = self.run_for()
        with patch.object(run, 'structured', return_value=contract(period='career', cutoff=2000)) as resolve:
            result = run.resolve_contract()
        self.assertEqual(result.cutoff, 1996)
        resolve.assert_called_once()

    def test_a_window_beyond_the_user_cutoff_is_not_silently_accepted(self):
        run = self.run_for()
        with patch.object(run, 'structured', return_value=contract(cutoff=2000, left_end=1998, right_end=1998)):
            self.assertEqual(run.resolve_contract().action, 'clarify')


if __name__ == '__main__':
    unittest.main()
