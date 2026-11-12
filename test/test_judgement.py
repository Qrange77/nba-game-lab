"""Judgements must address tradeoffs without inventing ties or advantages."""
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from backend.research.judgement import Judgement, JudgementReview, validate, decide, comparisons
from test.test_impact_review import evidence
from test.test_scoring_review import contract


def proposal(**changes):
    values=dict(position='left',criterion='Prioritize observed creation with ball security as counterevidence.',reason='The selected player creates more recorded assists per minute.',support=['creation'],counterevidence=['security'],counterargument='The other player has stronger recorded ball security.',tradeoff='Creation is more relevant to the requested passing contribution; the security disadvantage limits confidence.',sensitivity='Prioritizing ball security would reverse this preference.')
    return Judgement(**(values|changes))
ROWS=[dict(id='creation',complete=True,direction='left'),dict(id='security',complete=True,direction='right')]
class JudgementTests(unittest.TestCase):
    def test_split_evidence_allows_qualified_preference(self):self.assertEqual(validate(proposal(),ROWS),[])
    def test_wrong_direction_cannot_support_preference(self):self.assertTrue(validate(proposal(position='right',support=['creation'],counterevidence=['creation']),ROWS))
    def test_opposing_advantage_must_be_addressed(self):self.assertTrue(validate(proposal(counterevidence=[]),ROWS))
    def test_missing_evidence_cannot_support_a_winner(self):self.assertTrue(validate(proposal(),[r|{'complete':False,'direction':'missing'} for r in ROWS]))
    def test_missing_data_is_not_a_tie(self):self.assertTrue(validate(proposal(position='close',support=[],counterevidence=[]),[]))
    def test_new_numbers_cannot_escape_numeric_renderer(self):self.assertTrue(validate(proposal(reason='His value is 99.7 so he leads the comparison.'),ROWS))
    def test_per_minute_must_not_be_described_as_per_possession(self):
        self.assertTrue(validate(proposal(reason='His assist production rate per possession is higher.'),ROWS))
    def test_defense_proxies_do_not_force_a_complete_defensive_winner(self):
        rows=[r|{'dimension':'defense'} for r in ROWS]
        self.assertTrue(validate(proposal(),rows))
        self.assertEqual(validate(proposal(position='insufficient'),rows),[])
    def test_unmeasured_spacing_cannot_be_asserted_as_a_reason(self):
        self.assertTrue(validate(proposal(reason='His superior spacing value makes the offense more valuable.'),ROWS))
    def test_fallback_respects_the_primary_phase(self):
        from backend.research.judgement import bounded_fallback
        investigation=SimpleNamespace(c=contract(),priority_phase='Playoffs',p=SimpleNamespace(research=SimpleNamespace(names={'1':'Alpha','2':'Beta'})))
        rows=[dict(id=phase,dimension='offense',metric='TS_PCT',phase=phase,complete=True,direction=side) for phase,side in [('Regular Season','left'),('Playoffs','right')]]
        result=bounded_fallback(investigation,rows)
        self.assertEqual(result.position,'right');self.assertIn('playoffs',result.criterion)
    def test_fallback_honors_explicit_ball_security_priority(self):
        from backend.research.judgement import bounded_fallback
        parent=SimpleNamespace(messages=[{'role':'user','content':'Prioritize ball security.'}],research=SimpleNamespace(names={'1':'Alpha','2':'Beta'}))
        investigation=SimpleNamespace(c=contract(),priority_phase='Regular Season',p=parent)
        rows=[dict(id=m,dimension='playmaking',metric=m,phase='Regular Season',complete=True,direction=side) for m,side in [('AST36','left'),('AST_TO','right')]]
        self.assertEqual(bounded_fallback(investigation,rows).position,'right')
    def test_multiple_team_stints_cannot_be_cherry_picked(self):
        c=contract(research_domain='on_court',impact_dimensions=['team'])
        records=evidence().team()['records']
        self.assertTrue(all(not r['complete'] for r in comparisons(records,c)))
    def test_failed_reasoning_review_revises_once_then_falls_back(self):
        parent=SimpleNamespace(messages=[{'role':'user','content':'Who helped more?'}],deadline=999999999)
        investigation=SimpleNamespace(p=parent,c=contract(research_domain='on_court'),records=lambda:[],results={})
        rejected=proposal(position='insufficient',support=[],counterevidence=[])
        parent.structured=lambda prompt,schema,**kw:rejected if schema is Judgement else JudgementReview(valid=False,issues=['The conclusion does not address the question.'])
        verdict,rows,attempts=decide(investigation)
        self.assertEqual(verdict.position,'insufficient');self.assertEqual(len(attempts),3)
        self.assertTrue(all(not a['accepted'] for a in attempts[:2]))
