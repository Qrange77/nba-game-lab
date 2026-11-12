"""Clarification must retain the requested research, not maximize agent count."""
import unittest
from unittest.mock import patch

from backend.assistant.research_tools import AssistantResearchTools
from backend.research.scoring import ScoringRun
from backend.research.scope_review import current_question_users, requested_context
from backend.research.schemas import Decision, Task
from test.test_scoring_review import Data, contract


class ClarificationScopeTests(unittest.TestCase):
    def resolve(self, users, **changes):
        messages = []
        for text in users:
            if messages:
                messages.append({'role': 'assistant', 'content': 'Which equal season windows should I use?'})
            messages.append({'role': 'user', 'content': text})
        research = AssistantResearchTools(data=Data(), players=[{'id': 1, 'name': 'Alpha'}, {'id': 2, 'name': 'Beta'}])
        run = ScoringRun(messages, research)
        run.data = Data()
        with patch.object(run, 'structured', return_value=contract(**changes)):
            run.contract = run.resolve_contract()
        return run

    def test_short_date_reply_preserves_requested_teammate_research(self):
        run = self.resolve(['Compare Alpha and Beta scoring with teammate and Finals-opponent context.', '1995-96 through 1996-97 for both.'])
        self.assertEqual(run.required_dimensions(), ['personal', 'era', 'teammates', 'opponents'])

    def test_scoring_ability_in_windows_gets_bounded_context_without_agent_names(self):
        run = self.resolve(['Compare Alpha and Beta scoring ability.', '1995-96 through 1996-97 for both.'])
        self.assertTrue(run.contract.include_context)

    def test_clear_narrow_windows_do_not_force_all_researchers(self):
        for lens in ('volume', 'efficiency'):
            run = self.resolve([f'Compare {lens} only for Alpha and Beta in 1995-96 through 1996-97.'], lens=lens, include_context=True)
            self.assertEqual(run.required_dimensions(), ['personal', 'era'])

    def test_user_can_narrow_prior_broad_request(self):
        for reply in ('Volume only.', 'No context.', 'Skip teammates and opponents.'):
            run = self.resolve(['Compare scoring ability, teammates and opponents.', reply], include_context=True)
            self.assertFalse(run.contract.include_context)

    def test_explicit_context_can_accompany_a_narrow_metric(self):
        run = self.resolve(['Compare efficiency and teammates.', '1995-96 through 1996-97 for both.'], lens='efficiency')
        self.assertTrue(run.contract.include_context)

    def test_completed_report_stops_scope_inheritance(self):
        messages = [{'role': 'user', 'content': 'Compare scoring ability with teammates.'},
                    {'role': 'assistant', 'content': '# Scoring Claim Review\n\n## Answer\nA completed review.'},
                    {'role': 'user', 'content': 'Compare Alpha and Beta PPG in 1995-96.'}]
        users = current_question_users(messages)
        self.assertEqual(len(users), 1)
        self.assertFalse(requested_context(users, contract()))

    def test_incomplete_initial_plan_after_clarification_is_repaired_to_four_tasks(self):
        run = self.resolve(['Compare their scoring ability.', '1995-96 through 1996-97 for both.'])
        partial = Decision(action='research', scope='Approved windows', criteria='Scoring',
                           tasks=[Task(dimension='personal', question='Compare scoring')])
        with patch.object(run, 'structured', return_value=partial):
            plan = run.decision()
        self.assertEqual({t.dimension for t in plan.tasks}, {'personal', 'era', 'teammates', 'opponents'})
        self.assertEqual(len(plan.tasks), 4)


if __name__ == '__main__':
    unittest.main()
