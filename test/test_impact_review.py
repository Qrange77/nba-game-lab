"""Offline contribution calculations, coverage and evidence-driven follow-up."""
import unittest
from unittest.mock import patch
from backend.assistant.research_tools import AssistantResearchTools
from backend.research.impact_evidence import ImpactEvidence
from backend.research.impact import ImpactInvestigation, InvestigationPresentation, opportunity_gap
from backend.research.scoring import ScoringRun
from test.test_scoring_review import Data, contract
from test.test_debate import row, entry

class ImpactData(Data):
    def fetch(self,kind,**params):
        if kind=='on_off':
            return entry({'Players'+state+'CourtTeamPlayerOnOffSummary':[dict(VS_PLAYER_ID=pid,TEAM_NAME='Fixture',MIN=minutes,OFF_RATING=110,DEF_RATING=100,NET_RATING=net) for pid in (1,2)] for state,minutes,net in [('On',300,10),('Off',180,-2)]})
        return super().fetch(kind,**params)

def evidence(data=None,**kwargs):
    return ImpactEvidence(contract(research_domain='on_court',**kwargs),data=data or ImpactData(),players=[{'id':1,'name':'Alpha'},{'id':2,'name':'Beta'}])

class ImpactTests(unittest.TestCase):
    def test_rates_use_summed_inputs(self):
        data=ImpactData();data.career[1]=[row(AST=50,TOV=10,MIN=100),row('1996-97',AST=100,TOV=50,MIN=500)]
        r=evidence(data).profile('playmaking')['records'][0]['values']
        self.assertEqual(r['AST36']['value'],9);self.assertEqual(r['AST_TO']['value'],2.5)
    def test_zero_turnovers_are_undefined_not_infinite(self):
        data=ImpactData()
        for r in data.career[1]:r['TOV']=0
        result=evidence(data).profile('playmaking')
        self.assertFalse(result['records'][0]['values']['AST_TO']['complete']);self.assertTrue(result['gaps'])
    def test_missing_defensive_input_is_not_zero(self):
        data=ImpactData();data.career[1][0]['BLK']=None
        self.assertFalse(evidence(data).profile('defense')['records'][0]['values']['BLK36']['complete'])
    def test_missing_window_blocks_comparison(self):
        data=ImpactData();data.career[1]=data.career[1][:1]
        self.assertFalse(evidence(data).profile('playmaking')['records'][0]['values']['AST36']['complete'])
    def test_traded_total_does_not_double_count(self):
        data=ImpactData();data.career[1]=[row(team=1,AST=20),row(team=2,AST=30),row(team=0,AST=50)]
        r=evidence(data,left_end=1995,right_end=1995).profile('playmaking')['records'][0]
        self.assertEqual(r['values']['AST']['value'],5)
    def test_onoff_retains_stints_and_rating_difference(self):
        result=evidence().team();self.assertEqual(len(result['records']),4)
        self.assertEqual(result['records'][0]['values']['NET_DIFF']['value'],12)
        self.assertEqual(result['records'][0]['values']['OFF_MIN']['value'],180)
    def test_empty_historical_onoff_is_gap_not_zero(self):
        data=ImpactData();original=data.fetch
        data.fetch=lambda kind,**p:entry({}) if kind=='on_off' else original(kind,**p)
        result=evidence(data).team();self.assertFalse(result['records']);self.assertTrue(result['gaps'])
    def test_zero_off_minutes_blocks_difference(self):
        data=ImpactData();original=data.fetch
        def fetch(kind,**p):
            result=original(kind,**p)
            if kind=='on_off':
                for r in result['data']['PlayersOffCourtTeamPlayerOnOffSummary']:r['MIN']=0
            return result
        data.fetch=fetch
        self.assertFalse(evidence(data).team()['records'][0]['values']['NET_DIFF']['complete'])
    def test_round_two_requires_actual_disagreement(self):
        c=contract(phases=['Regular Season','Playoffs']);records=[]
        for phase,pts,ts in [('Regular Season',20,60),('Playoffs',25,50)]:
            records.append({'id':phase,'kind':'impact_offense','player_id':1,'player_name':'Alpha','scope':{'phase':phase},'values':{'PTS':{'complete':True,'value':pts},'TS_PCT':{'complete':True,'value':ts}}})
        self.assertEqual(opportunity_gap(records,c)['dimension'],'opportunity')
        records[1]['values']['TS_PCT']['value']=65
        self.assertIsNone(opportunity_gap(records,c))
    def test_defensive_activity_does_not_produce_overall_winner(self):
        parent=ScoringRun([],AssistantResearchTools(data=ImpactData(),players=[{'id':1,'name':'Alpha'},{'id':2,'name':'Beta'}]))
        parent.contract=contract(research_domain='on_court',impact_dimensions=['defense'],include_context=False)
        investigation=ImpactInvestigation(parent)
        answer,edges=investigation.render(InvestigationPresentation())
        self.assertFalse(edges);self.assertIn('does not establish one overall',answer)
    def test_missing_period_clarifies_without_statistics(self):
        parent=ScoringRun([{'role':'user','content':'Compare their on-court impact.'}],AssistantResearchTools(data=ImpactData()))
        with patch.object(parent,'structured') as model:
            c=parent.resolve_contract()
        model.assert_not_called();self.assertEqual(c.action,'clarify')
    def test_narrow_team_question_does_not_add_scoring_or_defensive_box_scores(self):
        parent=ScoringRun([{'role':'user','content':'Compare Alpha and Beta in 1995-96 on team on/off impact: offensive and defensive ratings and minutes.'}],AssistantResearchTools(data=ImpactData(),players=[{'id':1,'name':'Alpha'},{'id':2,'name':'Beta'}]))
        with patch.object(parent,'structured',return_value=contract(research_domain='on_court',impact_dimensions=['offense','defense','team'])):
            c=parent.resolve_contract()
        self.assertEqual(c.impact_dimensions,['team'])
        parent.contract=c
        self.assertEqual(ImpactInvestigation(parent).dimensions,['team'])
    def test_explicit_defense_and_team_request_keeps_both(self):
        parent=ScoringRun([{'role':'user','content':'Compare Alpha and Beta in 1995-96 on defensive contributions and team on/off.'}],AssistantResearchTools(data=ImpactData(),players=[{'id':1,'name':'Alpha'},{'id':2,'name':'Beta'}]))
        with patch.object(parent,'structured',return_value=contract(research_domain='on_court',impact_dimensions=['defense'])):
            c=parent.resolve_contract()
        self.assertEqual(c.impact_dimensions,['defense','team'])
    def test_highlights_pair_same_phase_even_if_writer_picks_mismatched_records(self):
        child=evidence(phases=['Regular Season','Playoffs']);result=child.collect('playmaking')
        parent=ScoringRun([],AssistantResearchTools(data=ImpactData(),players=[{'id':1,'name':'Alpha'},{'id':2,'name':'Beta'}]))
        parent.contract=contract(research_domain='on_court',impact_dimensions=['playmaking'],phases=['Regular Season','Playoffs'])
        parent.research.evidence.update(child.evidence);parent.research.used_evidence.update(child.used_evidence)
        investigation=ImpactInvestigation(parent)
        selection=[r['id'] for r in result['records'] if (r['player_id']==1 and r['scope']['phase']=='Regular Season') or (r['player_id']==2 and r['scope']['phase']=='Playoffs')]
        answer,_=investigation.render(InvestigationPresentation(evidence_ids=selection))
        highlights=answer.split('## Key evidence')[1].split('## Evidence by dimension')[0]
        self.assertIn('Alpha',highlights);self.assertIn('Beta',highlights)
        self.assertIn('/ Regular Season',highlights);self.assertNotIn('/ Playoffs',highlights)
    def test_graph_does_not_count_finished_workers_as_still_concurrent(self):
        from backend.research.impact import InvestigationTask
        from backend.activity import ActivityLog
        from types import SimpleNamespace
        import time
        parent=ScoringRun([],AssistantResearchTools(data=ImpactData(),players=[{'id':1,'name':'Alpha'},{'id':2,'name':'Beta'}]))
        parent.contract=contract(research_domain='on_court',include_context=True)
        parent.flow.add('lead','Lead','lead','Lead');parent.flow.finish('lead')
        investigation=ImpactInvestigation(parent)
        def worker(*args):
            time.sleep(.002)
            return SimpleNamespace(evidence={},used_evidence=set()),{'records':[],'gaps':[]},ActivityLog(),''
        with patch.object(investigation,'worker',side_effect=worker):
            investigation.dispatch([InvestigationTask(dimension=d,question='Collect the approved evidence.') for d in investigation.dimensions],1)
        graph=parent.flow.snapshot()
        self.assertLessEqual(graph['peak_parallel'],4)
        self.assertTrue(all(n['status']=='completed' for n in graph['nodes']))
    def test_long_onoff_is_bounded_and_disclosed(self):
        data=ImpactData();data.career={pid:[row(str(y)+'-'+str((y+1)%100),team=pid) for y in range(1990,1997)] for pid in (1,2)}
        result=evidence(data,left_start=1990,right_start=1990).team()
        self.assertEqual(len(result['records']),8)
        self.assertTrue(any('bounded' in g['reason'] for g in result['gaps']))
    def test_completed_impact_report_ends_previous_scope(self):
        from backend.research.scope_review import current_question_users
        self.assertEqual(current_question_users([{'role':'user','content':'old'}, {'role':'assistant','content':'# On-Court Impact Review\n'}, {'role':'user','content':'new'}]),['new'])

if __name__=='__main__':unittest.main()
