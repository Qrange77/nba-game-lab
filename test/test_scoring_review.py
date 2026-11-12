"""Acceptance rules for scoped scoring evidence and enforced research follow-up."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4
from fastapi.testclient import TestClient
import app
from backend.assistant.research_tools import AssistantResearchTools
from backend.research.contract import ScoringContract
from backend.research.scoring import ScoringRun
from backend.research.scoring_evidence import ScoringEvidence, scoring_matrix, adjudicate
from backend.research.tools import ResearchTools, Season
from test.test_debate import FakeData, row, entry, response, tool_call


class Data(FakeData):
    requests=0
    def __init__(self):
        super().__init__()
        self.career={1:[row('1995-96',PTS=200),row('1996-97',PTS=300)],
                     2:[row('1995-96',PTS=160),row('1996-97',PTS=220)]}
    def fetch(self,kind,**params):
        if kind=='league_games':
            return entry({'LeagueGameLog':[dict(GAME_ID='g',TEAM_ID=i,PTS=100,FGA=80,FTA=20,
                FGM=40,FG3M=10,FG3A=25,FTM=10,OREB=None,TOV=None,MIN=240) for i in (10,11)]})
        return super().fetch(kind,**params)


def contract(**overrides):
    return ScoringContract(**dict({'action':'review','claim':'Alpha had stronger scoring than Beta.',
        'left_player':1,'right_player':2,'period':'windows','left_start':1995,'left_end':1996,
        'right_start':1995,'right_end':1996,'cutoff':1996,'phases':['Regular Season'],
        'include_context':False},**overrides))


def tools(data=None,**overrides):
    return ScoringEvidence(contract(**overrides),data=data or Data(),players=[{'id':1,'name':'Alpha'},{'id':2,'name':'Beta'}])


class ContractTests(unittest.TestCase):
    def test_explicit_mixed_lenses_cannot_be_silently_narrowed_to_volume(self):
        for question,expected in [('Compare scoring volume, raw shooting efficiency and league-relative efficiency.','overall_scoring'),
                                  ('Compare scoring volume only, not shooting efficiency.','volume')]:
            run=ScoringRun([{'role':'user','content':question}],AssistantResearchTools(data=Data(),players=[{'id':1,'name':'Alpha'},{'id':2,'name':'Beta'}]))
            with patch.object(run,'structured',return_value=contract(lens='volume')):resolved=run.resolve_contract()
            self.assertEqual(resolved.lens,expected)

    def test_windows_must_have_same_length_and_completed_cutoff(self):
        for change in ({'right_end':1995},{'left_start':1983},{'cutoff':2100},{'left_player':2}):
            with self.subTest(change=change),self.assertRaises(ValueError):contract(**change)

    def test_unsupported_argument_cannot_change_collector_scope(self):
        t=tools()
        with patch.object(t.data,'fetch') as fetch:
            result=json.loads(t.dispatch('collect_scoring_profile',{'player_id':999}))
        fetch.assert_not_called();self.assertIn('error',result)

    def test_non_scoring_and_early_era_requests_do_not_query_statistics(self):
        questions=['Who was the better defender?','Compare scoring in 1961-62 and 2022-23.',
                   'Prove more championships if their teammates were swapped.','Jordan or LeBron: who is better?']
        for q in questions:
            r=AssistantResearchTools(data=Data(),players=[{'id':1,'name':'Alpha'},{'id':2,'name':'Beta'}],question=q)
            run=ScoringRun([{'role':'user','content':q}],r)
            with patch.object(run.data,'fetch') as fetch:
                c=run.resolve_contract()
            fetch.assert_not_called();self.assertNotEqual(c.action,'review')


class ComputationTests(unittest.TestCase):
    def test_percentages_recomputed_from_totals_not_average_of_season_percentages(self):
        data=Data()
        data.career[1]=[row('1995-96',PTS=100,FGA=50,FTA=0),row('1996-97',PTS=100,FGA=150,FTA=0)]
        t=tools(data);r=t.scoring_record(1,'Regular Season','per_game')
        self.assertEqual(r['values']['PTS']['value'],10)
        self.assertEqual(r['values']['TS_PCT']['value'],50)
        self.assertNotAlmostEqual(r['values']['TS_PCT']['value'],(100+100/3)/2)

    def test_future_or_ongoing_season_rows_are_excluded(self):
        data=Data();data.career[1].append(row('2026-27',PTS=99999))
        t=tools(data,period='career');r=t.scoring_record(1,'Regular Season','totals')
        self.assertEqual(r['values']['PTS']['value'],500)
        self.assertNotIn('2026-27',r['seasons'])

    def test_total_team_rows_do_not_double_count_traded_season(self):
        data=Data();data.career[1]=[row('1995-96',team=10,PTS=100),row('1995-96',team=20,PTS=200),row('1995-96',team=0,PTS=300)]
        t=tools(data,left_end=1995,right_end=1995);r=t.scoring_record(1,'Regular Season','totals')
        self.assertEqual(r['values']['PTS']['value'],300)

    def test_missing_pace_inputs_preserve_shooting_baseline(self):
        t=ResearchTools(data=Data(),players=[{'id':1,'name':'Alpha'}])
        result=t.query_era_environment(Season(player_id=1,season=1995))
        self.assertIsNone(result['environment']['values']['EST_PACE']['value'])
        self.assertAlmostEqual(result['environment']['values']['LEAGUE_TS_PCT']['value'],10000/(2*(80+.44*20)))

    def test_weighted_relative_ts_uses_shooting_opportunity_weights(self):
        data=Data();data.career[1]=[row('1995-96',PTS=100,FGA=50,FTA=0),row('1996-97',PTS=100,FGA=150,FTA=0)]
        t=tools(data);result=t.collect_scoring_environment()
        r=next(r for r in result['records'] if r['player_id']==1)
        league_ts=10000/(2*(80+.44*20))
        expected=((100-league_ts)*50+(100/3-league_ts)*150)/200
        self.assertAlmostEqual(r['values']['WEIGHTED_RTS']['value'],expected)
        self.assertEqual(r['values']['ERA_COVERAGE']['value'],100)
        self.assertTrue(r['values']['WEIGHTED_RTS']['complete'])

    def test_missing_baseline_blocks_full_relative_efficiency_verdict(self):
        data=Data();original=data.fetch
        def fetch(kind,**params):
            if kind=='league_games' and params.get('season')=='1995-96':
                return entry({'LeagueGameLog':[]})
            return original(kind,**params)
        data.fetch=fetch;t=tools(data)
        t._remember(t.collect_scoring_profile());t._remember(t.collect_scoring_environment())
        rows=scoring_matrix(t.evidence,t.contract)
        self.assertFalse(next(r for r in rows if r['metric']=='WEIGHTED_RTS')['complete'])
        self.assertEqual(adjudicate(rows,t.contract),'insufficient_data')

    def test_missing_participation_row_is_not_silently_dropped(self):
        data=Data();data.career[1]=data.career[1][:1];t=tools(data)
        r=t.scoring_record(1,'Regular Season','per_game')
        self.assertFalse(r['values']['PTS']['complete'])
        self.assertEqual(r['missing_seasons'],[1996])

    def test_missing_shooting_inputs_are_visible_in_collection_coverage(self):
        data=Data();data.career[1][0]['FGA']=None
        result=tools(data).collect_scoring_profile()
        self.assertEqual(result['status'],'partial')
        self.assertTrue(any('TS_PCT' in g['reason'] for g in result['gaps']))

    def test_rate_accumulation_reversal_produces_conditional_verdict(self):
        t=tools();t._remember(t.collect_scoring_profile());t._remember(t.collect_scoring_environment())
        matrix=scoring_matrix(t.evidence,t.contract)
        for r in matrix:r.update(complete=True,direction='left')
        matrix[0]['direction']='right'
        self.assertEqual(adjudicate(matrix,t.contract),'conditional')

    def test_verdict_can_support_or_contradict_a_directional_volume_claim(self):
        t=tools(lens='volume');t._remember(t.collect_scoring_profile());t._remember(t.collect_scoring_environment())
        self.assertEqual(adjudicate(scoring_matrix(t.evidence,t.contract),t.contract),'supported')
        reverse=contract(left_player=2,right_player=1,lens='volume',claim='Beta had stronger scoring volume than Alpha.')
        self.assertEqual(adjudicate(scoring_matrix(t.evidence,reverse),reverse),'contradicted')


class FollowupTests(unittest.TestCase):
    def test_plan_wording_cannot_promise_out_of_scope_phases_or_metrics(self):
        from backend.research.schemas import Decision, Task
        run=ScoringRun([],AssistantResearchTools(data=Data()));run.contract=contract()
        proposed=Decision(action='research',scope='scoring',criteria='scoring',tasks=[
            Task(dimension='personal',question='Investigate regular season and postseason scoring changes'),
            Task(dimension='era',question='Compare pace and offensive ratings for these eras')])
        with patch.object(run,'structured',return_value=proposed):decision=run.decision()
        self.assertNotIn('postseason',decision.tasks[0].question)
        self.assertNotIn('pace',decision.tasks[1].question)
        self.assertTrue(any(c['name']=='repair_research_plan' for c in run.log))

    def test_completed_dimension_is_not_researched_again(self):
        from backend.research.schemas import Decision, Task
        run=ScoringRun([],AssistantResearchTools(data=Data()))
        run.contract=contract();run.results={'collect_scoring_profile':{'gaps':[]},'collect_scoring_environment':{'gaps':[]}}
        proposed=Decision(action='research',scope='scoring',criteria='scoring',
            tasks=[Task(dimension='era',question='Repeat league benchmark collection')])
        with patch.object(run,'structured',return_value=proposed):decision=run.decision(review=True)
        self.assertEqual(decision.action,'finish');self.assertFalse(decision.tasks)

    def test_invalid_lead_plan_is_repaired_without_broadening_scope(self):
        research=AssistantResearchTools(data=Data(),players=[{'id':1,'name':'Alpha'},{'id':2,'name':'Beta'}])
        run=ScoringRun([],research);run.contract=contract()
        from backend.research.schemas import Decision, Task
        invalid=Decision(action='research',scope='scoring',criteria='scoring',
            tasks=[Task(dimension='honors',question='Compare career achievements')])
        for response in (invalid,ValueError('Invalid model JSON')):
            with self.subTest(response=str(response)):
                kwargs={'side_effect':response} if isinstance(response,Exception) else {'return_value':response}
                with patch.object(run,'structured',**kwargs):plan=run.decision()
                self.assertEqual([t.dimension for t in plan.tasks],['personal','era'])
                self.assertTrue(any(c['name']=='repair_research_plan' for c in run.log))

    def test_lead_finish_is_blocked_until_omitted_collector_is_researched(self):
        data=Data();research=AssistantResearchTools(data=data,players=[{'id':1,'name':'Alpha'},{'id':2,'name':'Beta'}],question='Compare career scoring')
        starts={'personal':0,'era':0}
        def model(**kwargs):
            messages=kwargs['messages'];system=messages[0]['content']
            if 'Resolve a user' in system:
                obj=contract(period='career').model_dump()
            elif 'You lead a cross-era' in system:
                obj={'action':'finish'} if 'COVERAGE:' in system else {'action':'research','scope':'career scoring','criteria':'scoring',
                    'tasks':[{'dimension':'personal','question':'Investigate scoring volume and raw efficiency'}, {'dimension':'era','question':'Investigate contemporaneous efficiency baselines'}]}
            elif 'independent NBA scoring researcher' in system:
                task=json.loads(messages[1]['content']);dimension=task['task']['dimension']
                if len(messages)==2:
                    starts[dimension]+=1
                    if dimension=='personal' and starts[dimension]==1:
                        return SimpleNamespace(choices=[SimpleNamespace(message=response(content='Collection was omitted.'))],usage=None)
                    return SimpleNamespace(choices=[SimpleNamespace(message=tool_call(task['required_collector'],{}))],usage=None)
                return SimpleNamespace(choices=[SimpleNamespace(message=response(content='Verified scoped evidence collected.'))],usage=None)
            elif 'You are the Writer' in system:obj={'emphasis':'tradeoff_first','highlight_rows':[0,1]}
            else:raise AssertionError(system[:90])
            return SimpleNamespace(choices=[SimpleNamespace(message=response(content=json.dumps(obj)))],usage=None)
        with patch('backend.research.scoring.ResearchData',return_value=data):
            run=ScoringRun([{'role':'user','content':'Compare career scoring'}],research,complete=model)
            answer,calls=run.run()
        self.assertEqual(starts,{'personal':2,'era':1})
        self.assertIn('finish_blocked',[c['name'] for c in calls])
        self.assertEqual({t['round'] for t in run.tasks},{1,2})
        self.assertTrue(all(c['status']=='completed' for c in run.coverage()))
        self.assertEqual(research.summary()['verification']['status'],'checked')
        self.assertIn('Scoring Claim Review',answer)
        self.assertTrue(all(c.get('agent') for c in calls))
        flow=run.flow.snapshot();nodes={n['id']:n for n in flow['nodes']}
        self.assertEqual(flow['status'],'completed')
        self.assertEqual(nodes['researcher-3']['depends_on'],['review-1'])
        self.assertEqual(nodes['review-1']['depends_on'],['researcher-1','researcher-2'])
        self.assertEqual(nodes['writer']['depends_on'],['review-2'])
        self.assertEqual(nodes['researcher-1']['status'],'partial')
        self.assertEqual(nodes['researcher-3']['status'],'completed')
        self.assertTrue(all(c.get('node_id') in nodes for c in calls))


class EvidenceEndpointTests(unittest.TestCase):
    def test_exact_record_is_available_only_to_its_session_owner(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(app,'HISTORY_DIR',Path(folder)):
            client=TestClient(app.app);client.get('/sessions')
            owner=client.cookies['nba_browser'];sid=str(uuid4());eid='ev_'+'a'*20
            app.save_history(owner,{'session_id':sid,'evidence':{eid:{'id':eid,'values':{'PTS':{'value':20}}}}})
            url=f'/sessions/{sid}/evidence/{eid}'
            self.assertEqual(client.get(url).json()['values']['PTS']['value'],20)
            self.assertEqual(TestClient(app.app).get(url).status_code,404)
            self.assertEqual(client.get(f'/sessions/{sid}/evidence/bad').status_code,400)
