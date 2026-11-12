"""Meaningful orchestration checks: parallelism, isolation, gaps, citation safety."""
import json
import tempfile
import time
import unittest
from threading import Barrier, Lock
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from backend.assistant.research_tools import AssistantResearchTools
from backend.research.engine import ResearchRun, run_deep_research
from backend.research.schemas import Decision, Report
from backend.research.data import ResearchData
from backend.research.tools import ResearchTools, Season
from backend.data.nba import DataUnavailable
from test.test_debate import FakeData, response, tool_call, row, entry


def result(message):
    return SimpleNamespace(choices=[SimpleNamespace(message=message)],usage=None)


class OrchestrationTests(unittest.TestCase):
    def tools(self):
        return AssistantResearchTools(data=FakeData(),players=[{'id':1,'name':'Alpha'},{'id':2,'name':'Beta'}],question='Compare careers')

    def test_clarification_starts_no_research_or_data_queries(self):
        research=self.tools()
        def model(**kwargs):
            return result(response(content=json.dumps({'action':'clarify','question':'Career, peak, or Finals?'})))
        with patch.object(research.data,'fetch') as fetch:
            answer,calls=run_deep_research([{'role':'user','content':'Who is better?'}],research,lambda **k:None,complete=model)
        fetch.assert_not_called()
        self.assertIn('career',answer.lower())
        self.assertEqual([c['agent'] for c in calls],['Lead'])

    def test_parallel_fresh_contexts_gap_followup_and_checked_writer(self):
        research=self.tools()
        barrier=Barrier(2)
        guard=Lock()
        starts=[]
        reviews=[]
        emitted=[]
        def model(**kwargs):
            messages=kwargs['messages']
            system=messages[0]['content']
            if 'You are Lead' in system:
                review='REVIEW FINDINGS' in system
                if review:
                    reviews.append(True)
                    if len(reviews)==1:
                        obj={'action':'research','scope':'career','criteria':'PTS with counterevidence','tasks':[{'dimension':'personal','question':'Check Alpha evidence gap after first investigation'}]}
                    else:obj={'action':'finish'}
                else:obj={'action':'research','scope':'career','criteria':'PTS with counterevidence','tasks':[
                    {'dimension':'personal','question':'Investigate Alpha career performance'},
                    {'dimension':'playoffs','question':'Investigate Beta career performance'}]}
                return result(response(content=json.dumps(obj)))
            if 'independent NBA Researcher' in system:
                task=json.loads(messages[1]['content'])['task']['question']
                pid=2 if 'Beta' in task else 1
                if len(messages)==2:
                    with guard:starts.append(task)
                    if 'gap' not in task:barrier.wait(timeout=3)
                    self.assertNotIn('findings from another researcher',messages[1]['content'])
                    return result(tool_call('query_evidence',{'player_id':pid}))
                return result(response(content='Verified notes; task coverage stated.'))
            if 'NBA Game Lab Writer' in system:
                ledger=json.loads(system.split('SERVER EVIDENCE LEDGER:\n')[1].split('\nREPAIR')[0].split('\nJSON SCHEMA:')[0])
                records=[r for r in ledger if r.get('kind')=='stats']
                claims=[{'evidence_id':r['id'],'player_id':r['player_id'],'scope':r['scope'],'metric':'PTS','value':r['values']['PTS']['value']} for r in records]
                answer='\n\n'.join(f"{r['player_name']} averaged {r['values']['PTS']['value']} points. [{r['id']}]" for r in records)
                return result(response(content=json.dumps({'answer':answer,'claims':claims})))
            raise AssertionError('Unexpected model context')
        with patch('backend.research.engine.ResearchData',return_value=FakeData()):
            run=ResearchRun([{'role':'user','content':'Compare careers by scoring'}],research,emitted.append,complete=model)
            run.data.requests=0
            answer,calls=run.run(lambda **k:None)
        self.assertEqual(len(starts),3)
        self.assertEqual(len(reviews),2)
        self.assertIn('Data source 1]',answer)
        self.assertEqual(research.summary()['verification']['status'],'checked')
        self.assertEqual(research.summary()['verification']['checked_claims'],2)
        self.assertTrue(all(c.get('agent') for c in calls))
        self.assertEqual(len({c['id'] for c in calls}),len(calls))
        self.assertEqual({t['round'] for t in run.tasks},{1,2})
        self.assertEqual(len([e for e in emitted if e['type']=='research_task']),3)

    def test_unknown_citations_wrong_numbers_and_wrong_scopes_fail(self):
        research=self.tools()
        record=research.run('query_evidence',{'player_id':1})
        run=ResearchRun([],research)
        claim={'evidence_id':record['id'],'player_id':1,'scope':record['scope'],'metric':'PTS','value':999}
        report=Report(answer=f"Wrong 999 [{record['id']}] [ev_deadbeef]",claims=[claim])
        errors,_=run.validate_report(report)
        self.assertTrue(any('Unknown' in e for e in errors))
        self.assertTrue(any('Incorrect' in e for e in errors))
        claim.update(value=20,scope=dict(record['scope'],start=2000,end=2000))
        errors,_=run.validate_report(Report(answer=f"A season [{record['id']}]",claims=[claim]))
        self.assertTrue(any('scope' in e for e in errors))

    def test_grouped_citations_are_rendered_and_facts_use_server_values(self):
        research=self.tools()
        a=research.run('query_evidence',{'player_id':1})
        b=research.run('query_evidence',{'player_id':2})
        run=ResearchRun([],research)
        report=Report(answer=f"Alpha has the scoring edge [{a['id']}, {b['id']}].",facts=[{'evidence_id':a['id'],'metric':'PTS'}])
        run.resolve_facts(report)
        errors,cards=run.validate_report(report)
        self.assertFalse(errors)
        self.assertEqual(report.claims[0].value,20)
        rendered=run.render(report.answer+run.fact_table(cards))
        self.assertNotIn('[ev_',rendered)
        self.assertIn('20',rendered)

    def test_unsubmitted_numeric_prose_cannot_hide_behind_valid_claims(self):
        research=self.tools();r=research.run('query_evidence',{'player_id':1});run=ResearchRun([],research)
        report=Report(answer=f"Alpha scored 999 points [{r['id']}].",facts=[{'evidence_id':r['id'],'metric':'PTS'}])
        run.resolve_facts(report)
        errors,_=run.validate_report(report)
        self.assertTrue(any('999' in e for e in errors))

    def test_missing_report_is_partial_with_verified_fallback(self):
        research=self.tools()
        research.run('query_evidence',{'player_id':1})
        run=ResearchRun([],research,complete=lambda **kwargs:(_ for _ in ()).throw(TimeoutError()))
        run.data.requests=0
        run.tasks=[{'dimension':'personal','question':'Investigate Alpha','status':'partial'}]
        answer=run.write(Decision(action='finish',scope='career'))
        self.assertIn('could not be verified',answer)
        self.assertIn('20.00',answer)
        self.assertEqual(research.summary()['verification']['status'],'partial')


class SharedDataTests(unittest.TestCase):
    def test_duplicate_requests_run_only_once_across_workers(self):
        with tempfile.TemporaryDirectory() as folder:
            data=ResearchData(time.monotonic()+5,Path(folder)/'cache.sqlite3')
            calls=[]
            def live(*args):
                calls.append(1);time.sleep(.03)
                return {'resultSets':[1]},{'Rows':[{'value':1}]}
            with patch('backend.data.nba.NBAData._live',side_effect=live):
                with ThreadPoolExecutor(max_workers=4) as pool:
                    results=list(pool.map(lambda _:data.fetch('career',player_id=1),range(4)))
            self.assertEqual(len(calls),1)
            self.assertTrue(all(r==results[0] for r in results))

    def test_api_request_cap_and_deadline_are_bounded(self):
        data=ResearchData(time.monotonic()+5,max_requests=0)
        with self.assertRaises(DataUnavailable):data._live('career',{},1)
        data=ResearchData(time.monotonic()-1)
        with self.assertRaises(DataUnavailable):data._live('career',{},1)


class HistoricalContextTests(unittest.TestCase):
    def tools(self,data):
        return ResearchTools(data=data,players=[{'id':1,'name':'Alpha'}])

    def test_era_uses_paired_game_totals_and_labels_estimates(self):
        rows=[dict(GAME_ID='g1',TEAM_ID=i,PTS=100,FGA=80,FTA=20,FGM=40,FG3M=10,OREB=10,TOV=12,MIN=240) for i in (10,11)]
        fake=FakeData()
        original=fake.fetch
        def fetch(kind,**params):
            if kind=='league_games':return {'data':{'LeagueGameLog':rows},'parameters':params,'source_url':'https://stats.nba.com/stats/leaguegamelog','fetched_at':'2026-01-01','stale':False}
            return original(kind,**params)
        fake.fetch=fetch
        tools=self.tools(fake)
        r=tools.query_era_environment(Season(player_id=1,season=1995))
        env=tools.evidence[r['environment']['id']]
        self.assertEqual(env['values']['LEAGUE_TEAM_PPG']['value'],100)
        self.assertAlmostEqual(env['values']['LEAGUE_TS_PCT']['value'],10000/(2*(80+.44*20)))
        self.assertTrue(env['values']['EST_PACE']['estimated'])
        self.assertEqual(env['scope']['phase'],'Regular Season')
        rows.append(dict(rows[0]))
        self.assertIn('error',json.loads(tools.dispatch('query_era_environment',{'player_id':1,'season':1995})))

    def test_final_scope_and_future_seasons_are_validated(self):
        tools=self.tools(FakeData())
        self.assertIn('error',json.loads(tools.dispatch('query_finals_path',{'player_id':1,'season':2100})))
        self.assertIn('error',json.loads(tools.dispatch('query_supporting_cast',{'player_id':1,'season':2100})))
        self.assertIn('error',json.loads(tools.dispatch('query_era_environment',{'player_id':1,'season':2020,'phase':'Finals'})))

    def test_historical_roster_fallback_keeps_exact_team_stint_and_rotation(self):
        class Data(FakeData):
            def __init__(self):
                super().__init__()
                self.career={1:[dict(row(team=10),PLAYER_ID=1)],
                    2:[dict(row(team=10,PTS=100),PLAYER_ID=2),dict(row(team=20,PTS=900),PLAYER_ID=2)]}
            def fetch(self,kind,**params):
                if kind=='team_players':return entry({'PlayersSeasonTotals':[]})
                if kind=='roster':return entry({'CommonTeamRoster':[
                    {'TeamID':10,'PLAYER_ID':1,'PLAYER':'Alpha'},
                    {'TeamID':10,'PLAYER_ID':2,'PLAYER':'Helper'}]})
                return super().fetch(kind,**params)
        tools=self.tools(Data())
        r=json.loads(tools.dispatch('query_supporting_cast',{'player_id':1,'season':1995}))
        self.assertEqual(r['core_candidates'][0]['player_name'],'Helper')
        self.assertEqual(r['rotation'][0]['values']['PTS']['value'],10)
        self.assertEqual(r['rotation'][0]['context']['team_id'],10)
        self.assertIn('roster snapshot',r['rotation'][0]['limitations'][1])

    def test_espn_game_creates_two_citable_team_records(self):
        from test.test_tools import sample
        from backend.assistant import tools as game_tools
        data=sample()
        participants=data['header']['competitions'][0]['competitors']
        fields=['fieldGoalsMade-fieldGoalsAttempted','threePointFieldGoalsMade-threePointFieldGoalsAttempted',
                'freeThrowsMade-freeThrowsAttempted','offensiveRebounds','defensiveRebounds','totalTurnovers','totalRebounds']
        data['boxscore']['teams']=[{'team':p['team'],'statistics':[
            {'name':name,'displayValue':value} for name,value in zip(fields,['40-85','10-30','20-25','10','30','12','40'])]} for p in participants]
        tools=self.tools(FakeData())
        with patch.object(game_tools,'_fetch',return_value=data):
            result=json.loads(tools.dispatch('query_game_context',{'event_id':'100','date':'2026-01-15'}))
        self.assertEqual(len(result['teams']),2)
        first=result['teams'][0]
        self.assertLess(first['player_id'],0)
        self.assertEqual(first['values']['PTS']['value'],110)
        self.assertEqual(first['values']['REB']['value'],40)
        self.assertEqual(first['values']['POINT_MARGIN']['value'],5)
        self.assertEqual(result['comparison']['metrics']['PTS']['relation'],'higher')
        self.assertIn(first['id'],tools.used_evidence)
        self.assertEqual(first['sources'][0]['provider'],'ESPN')

    def test_citation_urls_use_actual_nba_http_parameter_names(self):
        from backend.data.nba import request_parameters
        p=request_parameters({'endpoint':'https://stats.nba.com/stats/playercareerstats',
                              'parameters':{'player_id':893,'per_mode36':'Totals','league_id_nullable':'00'}})
        self.assertEqual(p,{'PlayerID':893,'PerMode':'Totals','LeagueID':'00'})


if __name__=='__main__':unittest.main()
