"""Behavioral acceptance for focused reports and explicit counterevidence."""
import unittest
from unittest.mock import patch

from backend.research.contract import ScoringPresentation
from backend.research.scoring import ScoringRun
from backend.research.scoring_evidence import scoring_matrix, adjudicate
from backend.research.scope_review import repair_equal_windows
from test.test_scoring_review import contract
from test.test_scoring_review import Data, tools
from test.test_debate import row, entry


class PhaseData(Data):
    def fetch(self, kind, **params):
        if kind == 'career':
            pid = params['player_id']
            return entry({
                'SeasonTotalsRegularSeason': [row('1995-96', PTS=200 if pid == 1 else 300, FGA=250, FTA=0)],
                'SeasonTotalsPostSeason': [row('1995-96', PTS=300 if pid == 1 else 350, FGA=250, FTA=0)],
            })
        return super().fetch(kind, **params)


def prepared(lens, phases=None, data=None):
    research = tools(data or Data(), lens=lens, phases=phases or ['Regular Season'],
                     left_end=1995, right_end=1995)
    results = {}
    for name in ('collect_scoring_profile', 'collect_scoring_environment'):
        results[name] = getattr(research, name)()
        research._remember(results[name])
    run = ScoringRun([], research)
    run.contract = research.contract
    run.results = results
    return run


def render(run, highlights=None):
    matrix = scoring_matrix(run.current_evidence(), run.contract)
    return run.render_report(matrix, adjudicate(matrix, run.contract),
                             ScoringPresentation(highlight_rows=highlights or []), run.coverage())


class AnswerFocusTests(unittest.TestCase):
    def test_broad_scoring_verdict_can_choose_a_winner_despite_opposite_accumulation(self):
        run=prepared('overall_scoring')
        matrix=scoring_matrix(run.current_evidence(),run.contract)
        for row in matrix:
            row['direction']='right' if row['basis']=='totals' else 'left'
        text='\n'.join(run.scoring_position(matrix))
        self.assertIn('I favor Alpha in the selected sample',text)
        self.assertIn('Beta leads accumulated points',text)
        self.assertIn('prioritizes points per game and shooting efficiency',text)

    def test_position_does_not_force_a_winner_with_conflicting_or_missing_primary_evidence(self):
        run=prepared('overall_scoring')
        matrix=scoring_matrix(run.current_evidence(),run.contract)
        for row in matrix:row['direction']='left'
        matrix[-1]['direction']='right'
        self.assertIn('Split scoring verdict','\n'.join(run.scoring_position(matrix)))
        matrix[-1]['complete']=False
        self.assertIn('not enough comparable','\n'.join(run.scoring_position(matrix)))

    def test_scoring_verdict_respects_ties_and_narrow_metric_questions(self):
        run=prepared('overall_scoring')
        matrix=scoring_matrix(run.current_evidence(),run.contract)
        for row in matrix:row['direction']='tie'
        self.assertIn('no observed edge','\n'.join(run.scoring_position(matrix)))
        run.contract.lens='volume'
        self.assertEqual(run.scoring_position(matrix),[])

    def test_claim_conclusion_precedes_named_findings_and_key_evidence(self):
        answer, _ = render(prepared('volume'))
        self.assertLess(answer.index('Claim assessment:'), answer.index('Alpha leads'))
        self.assertLess(answer.index('Alpha leads'), answer.index('## Key evidence'))
        self.assertLess(answer.index('## Key evidence'), answer.index('## Comparable evidence'))

    def test_writer_cannot_omit_a_requested_metric_family_from_key_evidence(self):
        for lens, expected in (('volume', ('Accumulated points', 'Points per game')),
                               ('efficiency', ('Raw true shooting', 'Contemporaneous relative true shooting'))):
            with self.subTest(lens=lens):
                answer, _ = render(prepared(lens), [0])
                key = answer.split('## Key evidence', 1)[1].split('## Comparable evidence', 1)[0]
                for metric in expected:
                    self.assertIn(metric, key)

    def test_volume_report_has_no_efficiency_rows_or_efficiency_caveats(self):
        run = prepared('volume')
        answer, checks = render(run, [2, 3])
        self.assertIn('Accumulated points (total)', answer)
        self.assertIn('Points per game (per game)', answer)
        for unrelated in ('Raw true shooting', 'relative true shooting', 'TS%', 'league-baseline shooting',
                          'True shooting uses', 'Raw versus contemporaneous relative efficiency'):
            self.assertNotIn(unrelated, answer)
        self.assertEqual([c['test'] for c in checks], ['Accumulation versus scoring rate'])

    def test_efficiency_report_does_not_highlight_hidden_volume_counterevidence(self):
        run = prepared('efficiency')
        answer, checks = render(run, [0, 1])
        self.assertIn('Raw true shooting', answer)
        self.assertIn('Contemporaneous relative true shooting', answer)
        for unrelated in ('Accumulated points', 'Points per game', 'Accumulation versus scoring rate'):
            self.assertNotIn(unrelated, answer)
        self.assertEqual([c['test'] for c in checks], ['Raw versus contemporaneous relative efficiency'])

    def test_api_matrix_cards_and_writer_input_share_the_same_focus(self):
        run = prepared('efficiency')
        with patch.object(run, 'structured', return_value=ScoringPresentation()) as writer:
            run.publish()
        prompt = writer.call_args.args[0]
        self.assertNotIn('Accumulated points', prompt)
        self.assertNotIn('Points per game', prompt)
        summary = run.research.summary()
        self.assertEqual({r['metric'] for r in summary['scoring']['matrix']}, {'TS_PCT', 'WEIGHTED_RTS'})
        self.assertFalse(any(c['title'] == 'PTS' for c in summary['cards']))
        self.assertEqual(summary['verification']['status'], 'checked')
        # Full collection evidence remains available for provenance inspection.
        self.assertTrue(any('PTS' in r.get('values', {}) for r in run.research.evidence.values()))

    def test_writer_failure_keeps_the_focused_server_fallback(self):
        run = prepared('volume')
        with patch.object(run, 'structured', side_effect=ValueError('Invalid writer JSON')):
            answer = run.publish()
        self.assertIn('Accumulated points', answer)
        self.assertNotIn('Raw true shooting', answer)
        self.assertEqual({r['metric'] for r in run.research.summary()['scoring']['matrix']}, {'PTS'})

    def test_phase_changes_follow_the_requested_lens(self):
        for lens, present, absent in (
            ('volume', 'Points-per-game change', 'TS change (percentage points)'),
            ('efficiency', 'TS change (percentage points)', 'Points-per-game change'),
        ):
            with self.subTest(lens=lens):
                run = prepared(lens, ['Regular Season', 'Playoffs'], PhaseData())
                answer, _ = render(run)
                self.assertIn(present, answer)
                self.assertNotIn(absent, answer)
                change_records = [r for r in run.research.evidence.values() if r.get('kind') == 'scoring_change']
                expected = {'PTS_CHANGE'} if lens == 'volume' else {'TS_PCT_CHANGE'}
                self.assertTrue(change_records)
                self.assertTrue(all(set(r['values']) == expected for r in change_records))

    def test_counterevidence_names_winners_for_level_and_change(self):
        run = prepared('postseason', ['Regular Season', 'Playoffs'], PhaseData())
        answer, checks = render(run)
        self.assertIn('playoff raw true shooting comparison favors Beta; the playoff-minus-regular-season change favors Alpha', answer)
        self.assertIn('A higher playoff level is not the same as a larger change', answer)
        self.assertTrue(any(c['test'] == 'Raw true shooting level versus phase change' and c['result'] == 'changes' for c in checks))
        self.assertIn('prevent a causal interpretation', answer)

    def test_volume_rate_counterevidence_states_the_opposing_advantages(self):
        run = prepared('volume')
        matrix = scoring_matrix(run.current_evidence(), run.contract)
        matrix[0]['direction'] = 'left'
        matrix[1]['direction'] = 'right'
        answer, checks = run.render_report(matrix, 'conditional', ScoringPresentation(), run.coverage())
        self.assertIn('accumulated points comparison favors Alpha; the points per game comparison favors Beta', answer)
        self.assertEqual(checks[0]['result'], 'changes')

    def test_unavailable_phase_change_is_not_interpreted_as_zero_or_an_advantage(self):
        run = prepared('efficiency', ['Regular Season', 'Playoffs'], PhaseData())
        for record in run.current_evidence().values():
            if record.get('kind') == 'scoring_stats' and record['player_id'] == 1 and record['scope']['phase'] == 'Regular Season':
                record['values']['TS_PCT'].update(value=None, complete=False)
        answer, checks = render(run)
        self.assertIn('Unavailable', answer)
        self.assertFalse(any('level versus phase change' in c['test'] for c in checks))

    def test_broad_question_retains_both_metric_families(self):
        run = prepared('overall_scoring')
        answer, checks = render(run)
        for expected in ('Accumulated points', 'Points per game', 'Raw true shooting', 'Contemporaneous relative true shooting'):
            self.assertIn(expected, answer)
        self.assertEqual(len(checks), 2)

    def test_neutral_question_gets_named_advantages_without_a_claim_verdict(self):
        run = prepared('volume')
        run.contract.request_kind = 'comparison'
        run.contract.claim = 'Which player leads scoring volume in these windows?'
        answer, _ = render(run)
        self.assertIn('## Answer', answer)
        self.assertIn('Alpha leads total points, points per game', answer)
        self.assertNotIn('Claim assessment:', answer)
        self.assertNotIn('Supported under', answer)
        self.assertLess(answer.index('Alpha leads'), answer.index('## Scope and methods'))
        self.assertIn('Alpha **200**', answer)
        with patch.object(run,'structured',return_value=ScoringPresentation()):run.publish()
        self.assertEqual(run.research.summary()['scoring']['verdict'],'comparison')

    def test_asserted_claim_keeps_its_explicit_assessment(self):
        answer, _ = render(prepared('volume'))
        self.assertIn('Claim assessment: Supported', answer)

    def test_essential_postseason_highlights_cannot_be_replaced_by_regular_totals(self):
        run = prepared('postseason', ['Regular Season', 'Playoffs'], PhaseData())
        answer, _ = render(run, [0, 1, 2])
        key = answer.split('## Key evidence', 1)[1].split('## What changes', 1)[0]
        self.assertIn('Playoffs / Points per game', key)
        self.assertIn('Playoffs / Raw true shooting', key)
        self.assertNotIn('Regular Season / Accumulated points', key)
        self.assertLess(answer.index('## What changes'), answer.index('## Comparable evidence'))


class ScopeReviewTests(unittest.TestCase):
    def test_objectively_false_unequal_window_clarification_is_repaired(self):
        c = contract(action='clarify', question='The requested windows have unequal lengths.')
        messages = [{'role': 'user', 'content': 'Compare Alpha in 1995-96 through 1996-97 with Beta in 1995-96 through 1996-97 on scoring volume.'}]
        result = repair_equal_windows(c, messages, {'1': 'Alpha', '2': 'Beta'})
        self.assertEqual(result.action, 'review')
        self.assertEqual(result.bounds(1), (1995, 1996))

    def test_real_unequal_windows_ambiguous_scope_and_other_clarifications_are_preserved(self):
        examples = [
            (contract(action='clarify', question='Unequal windows.', right_end=1995), 'Compare Alpha in 1995-96 through 1996-97 with Beta in 1995-96 through 1995-96 on scoring volume.'),
            (contract(action='clarify', question='Unequal windows.'), 'Compare Alpha and Beta scoring peaks.'),
            (contract(action='clarify', question='Which scoring criterion should be used?'), 'Compare Alpha in 1995-96 through 1996-97 with Beta in 1995-96 through 1996-97 on scoring volume.'),
            (contract(action='clarify', question='Unequal windows.'), 'Compare Alpha in 1994-95 through 1995-96 with Beta in 1995-96 through 1996-97 on scoring volume.'),
        ]
        for c, question in examples:
            with self.subTest(question=question):
                self.assertIs(repair_equal_windows(c, [{'role': 'user', 'content': question}], {'1': 'Alpha', '2': 'Beta'}), c)

    def test_followup_reuses_user_windows_but_never_assistant_invented_dates(self):
        c=contract(action='clarify',question='Use identical season ranges instead?')
        messages=[{'role':'user','content':'Compare Alpha in 1995-96 through 1996-97 with Beta in 1995-96 through 1996-97 on scoring volume.'},
                  {'role':'assistant','content':'Use 1990-91 through 1999-00?'},
                  {'role':'user','content':'Both windows have two seasons. Use them as stated.'}]
        self.assertEqual(repair_equal_windows(c,messages,{'1':'Alpha','2':'Beta'}).action,'review')
        messages.append({'role':'user','content':'Actually use 1994-95.'})
        self.assertIs(repair_equal_windows(c,messages,{'1':'Alpha','2':'Beta'}),c)


if __name__ == '__main__':
    unittest.main()
