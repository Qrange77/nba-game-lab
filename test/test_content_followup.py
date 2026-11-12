"""Content-driven follow-up: completed tools can still leave evidence gaps."""
import copy
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from backend.data.nba import aggregate, provenance, DataUnavailable, season_label
from backend.debate.schemas import Scope
from backend.assistant.research_tools import AssistantResearchTools
from backend.research.scoring import ScoringRun
from backend.research.scoring_evidence import ScoringEvidence
from backend.research.support_review import supporting_cast_gaps, assess_support_gaps, complete_sample
from test.test_scoring_review import Data, contract
from test.test_debate import row, entry, response, tool_call


def support_contract(**changes):
    return contract(**dict({'phases':['Regular Season','Playoffs'],'include_context':True},**changes))


def make_sample(tool,pid,year=1995,phase='Playoffs',sparse=False):
    records=[]
    for index,(ppg,gp) in enumerate(((30,2 if sparse else 10),(20,10),(5,10)),1):
        values=aggregate([row(season_label(year),GP=gp,PTS=ppg*gp,MIN=30*gp,FGA=20*gp,FTA=5*gp)])
        ident=pid*100+index
        r=tool.add({'kind':'supporting_cast','player_id':ident,'player_name':f'Helper {ident}',
            'scope':Scope(start=year,end=year,phase=phase).model_dump(),
            'context':{'focal_player_id':pid,'team_id':pid,'team_name':f'Team {pid}'},
            'values':values,'sources':[provenance(entry({}))],'limitations':[]})
        records.append(r)
    return {'player_id':pid,'season':year,'phase':phase,'core':[r['id'] for r in records[:2]],
        'rotation':[r['id'] for r in records],'selection':'Controlled source fixture: core by PPG, rotation by minutes.'},records


def fixtures(**changes):
    t=ScoringEvidence(support_contract(**changes),data=Data(),players=[{'id':1,'name':'Alpha'},{'id':2,'name':'Beta'}])
    a,_=make_sample(t,1,sparse=True);b,_=make_sample(t,2)
    return t,[a,b]


class ContentGapTests(unittest.TestCase):
    def test_completed_collection_exposes_sparse_helper_and_symmetric_targets(self):
        t,samples=fixtures();gaps=supporting_cast_gaps(t.contract,samples,t.evidence)
        self.assertEqual(len(gaps),1);self.assertEqual(gaps[0]['kind'],'sparse_helper_sample')
        self.assertEqual([(v['player_id'],v['season'],v['phase']) for v in gaps[0]['targets']],
            [(1,1995,'Regular Season'),(2,1995,'Regular Season')])
        self.assertTrue(all(complete_sample(s,t.evidence) for s in samples))
        self.assertEqual(len(gaps[0]['evidence_ids']),2)

    def test_supported_appearance_samples_do_not_create_an_extra_round(self):
        t,_=fixtures();a,_=make_sample(t,1);b,_=make_sample(t,2)
        self.assertEqual(supporting_cast_gaps(t.contract,[a,b],t.evidence),[])

    def test_existing_matched_evidence_is_reused_without_new_dispatch(self):
        t,samples=fixtures();a,_=make_sample(t,1,phase='Regular Season');b,_=make_sample(t,2,phase='Regular Season')
        checks=assess_support_gaps(supporting_cast_gaps(t.contract,samples,t.evidence),t.evidence,samples+[a,b],{},{} )
        self.assertEqual(checks[0]['status'],'completed');self.assertTrue(checks[0]['reused'])

    def test_incomplete_later_sample_does_not_hide_valid_existing_evidence(self):
        t,samples=fixtures();a,_=make_sample(t,1,phase='Regular Season');b,_=make_sample(t,2,phase='Regular Season')
        incomplete=dict(b,core=['ev_'+'0'*20])
        checks=assess_support_gaps(supporting_cast_gaps(t.contract,samples,t.evidence),t.evidence,samples+[a,b,incomplete],{},{} )
        self.assertEqual(checks[0]['status'],'completed');self.assertTrue(checks[0]['reused'])

    def test_narrow_playoff_scope_is_not_expanded_to_regular_season(self):
        t,samples=fixtures(phases=['Playoffs'])
        gaps=supporting_cast_gaps(t.contract,samples,t.evidence)
        self.assertEqual(gaps[0]['targets'],[]);self.assertEqual(gaps[0]['status'],'unavailable')

    def test_helper_phase_restriction_survives_broader_scoring_scope(self):
        t,samples=fixtures(support_phases=['Playoffs'])
        self.assertIn('Regular Season',t.contract.phases)
        gaps=supporting_cast_gaps(t.contract,samples,t.evidence)
        self.assertEqual(gaps[0]['targets'],[])
        t.support_targets=[{'player_id':1,'season':1995,'phase':'Regular Season'}]
        with patch.object(t,'query_supporting_cast') as fetch:result=json.loads(t.dispatch('inspect_supporting_cast',{}))
        fetch.assert_not_called();self.assertIn('error',result)

    def test_initial_helper_collection_honors_regular_season_restriction(self):
        t,_=fixtures(support_phases=['Regular Season']);calls=[]
        def support(p,prefer_roster=False):
            calls.append(p.phase);sample,records=make_sample(t,p.player_id,p.season,p.phase)
            return {'core_candidates':records[:2],'rotation':records,'gaps':[]}
        with patch.object(t,'selected_finals',return_value=([],[])),patch.object(t,'query_supporting_cast',side_effect=support):
            result=t.collect_scoring_support()
        self.assertTrue(calls);self.assertEqual(set(calls),{'Regular Season'})
        self.assertTrue(all(s['phase']=='Regular Season' for s in result['samples']))

    def test_missing_metrics_choose_an_alternate_source_once(self):
        t,samples=fixtures();sample=samples[1]
        t.evidence[sample['core'][0]]['values']['TS_PCT'].update(value=None,complete=False)
        gaps=[g for g in supporting_cast_gaps(t.contract,samples,t.evidence) if g['kind']=='missing_helper_metrics']
        self.assertTrue(all(v['source']=='roster' for v in gaps[0]['targets']))
        checked=assess_support_gaps(gaps,t.evidence,samples,{gaps[0]['id']:{'gaps':[{'reason':'Source unavailable'}]}},{gaps[0]['id']:1})
        self.assertEqual(checked[0]['status'],'unavailable')

    def test_record_scope_cannot_be_hidden_by_sample_metadata(self):
        t,samples=fixtures()
        t.evidence[samples[1]['core'][0]]['scope']['phase']='Regular Season'
        self.assertFalse(complete_sample(samples[1],t.evidence))
        self.assertTrue(any(g['kind']=='missing_helper_metrics' for g in supporting_cast_gaps(t.contract,samples,t.evidence)))

    def test_disagreeing_alternate_source_is_not_silently_accepted(self):
        t,samples=fixtures();sample=samples[1]
        t.evidence[sample['core'][0]]['values']['TS_PCT'].update(value=None,complete=False)
        gaps=[g for g in supporting_cast_gaps(t.contract,samples,t.evidence) if g['kind']=='missing_helper_metrics']
        alternate=[]
        for pid in (1,2):
            s,records=make_sample(t,pid)
            if pid==2:t.evidence[s['core'][0]]['values']['GP']['value']=11
            alternate.append(s)
        # Preserve the original source object rather than mutating its ID.
        old=copy.deepcopy(t.evidence[alternate[1]['core'][0]])
        old['id']='ev_'+'f'*20;old['values']['GP']['value']=10;old['values']['TS_PCT'].update(value=None,complete=False)
        t.evidence[old['id']]=old;gaps[0]['evidence_ids']=[old['id']]
        checked=assess_support_gaps(gaps,t.evidence,samples+alternate,{gaps[0]['id']:{'samples':alternate}},{gaps[0]['id']:1})
        self.assertEqual(checked[0]['status'],'unavailable')
        self.assertTrue(any(c['metric']=='GP' for c in checked[0]['conflicts']))

    def test_unsupported_investigation_target_cannot_escape_locked_scope(self):
        t,_=fixtures();t.support_targets=[{'player_id':1,'season':1994,'phase':'Regular Season'}]
        with patch.object(t,'query_supporting_cast') as fetch:
            result=json.loads(t.dispatch('inspect_supporting_cast',{}))
        fetch.assert_not_called();self.assertIn('error',result)


class ContentResearchIntegrationTests(unittest.TestCase):
    def run_case(self,sparse=True,source_failure=False):
        data=Data();research=AssistantResearchTools(data=data,players=[{'id':1,'name':'Alpha'},{'id':2,'name':'Beta'}],question='Compare career scoring and supporting casts')
        source_calls=[]
        def initial(tool):
            a,ar=make_sample(tool,1,sparse=sparse);b,br=make_sample(tool,2)
            return {'records':ar+br,'samples':[a,b],'gaps':[],'status':'completed'}
        def targeted(tool,p,prefer_roster=False):
            source_calls.append((p.player_id,p.season,p.phase,prefer_roster))
            if source_failure:raise DataUnavailable('The targeted source is unavailable.')
            sample,records=make_sample(tool,p.player_id,p.season,p.phase)
            return {'core_candidates':records[:2],'rotation':records,'gaps':[],'status':'completed'}
        def model(**kwargs):
            messages=kwargs['messages'];system=messages[0]['content']
            if 'Resolve a user' in system:obj=support_contract().model_dump()
            elif 'You lead a cross-era' in system:
                obj={'action':'finish'} if 'COVERAGE:' in system else {'action':'research','scope':'Approved scoring and supporting casts','criteria':'Observed scoring and support',
                    'tasks':[{'dimension':d,'question':'Investigate verified '+d+' evidence for both subjects'} for d in ('personal','era','teammates','opponents')]}
            elif 'independent NBA scoring researcher' in system:
                task=json.loads(messages[1]['content'])
                if len(messages)==2:return SimpleNamespace(choices=[SimpleNamespace(message=tool_call(task['required_collector'],{}))],usage=None)
                return SimpleNamespace(choices=[SimpleNamespace(message=response(content='Scoped collection completed; inspect the returned source rows.'))],usage=None)
            elif 'You are the Writer' in system:obj={'emphasis':'scope_first','highlight_rows':[0,1]}
            else:raise AssertionError(system[:80])
            return SimpleNamespace(choices=[SimpleNamespace(message=response(content=json.dumps(obj)))],usage=None)
        with patch('backend.research.scoring.ResearchData',return_value=data),patch.object(ScoringEvidence,'collect_scoring_support',initial),\
             patch.object(ScoringEvidence,'query_supporting_cast',targeted),patch.object(ScoringEvidence,'collect_scoring_finals',return_value={'records':[],'gaps':[],'status':'completed'}):
            run=ScoringRun([{'role':'user','content':research.question}],research,complete=model)
            answer,calls=run.run()
        return run,research,answer,calls,source_calls

    def test_real_evidence_gap_triggers_round_two_after_every_initial_collector_completed(self):
        run,research,answer,calls,source_calls=self.run_case()
        self.assertTrue(all(t['status']=='completed' for t in run.tasks if t['round']==1))
        followups=[t for t in run.tasks if t['round']>1]
        self.assertEqual(len(followups),1);self.assertEqual(followups[0]['dimension'],'teammates')
        self.assertTrue(followups[0]['gap_id']);self.assertEqual(followups[0]['round'],2)
        self.assertEqual({(c[0],c[2]) for c in source_calls},{(1,'Regular Season'),(2,'Regular Season')})
        self.assertEqual(run.content_checks[0]['status'],'completed')
        self.assertIn('Evidence-driven supporting-cast checks',answer)
        self.assertLess(answer.index('## Key evidence'),answer.index('## Why we investigated further'))
        self.assertLess(answer.index('## Why we investigated further'),answer.index('## Comparable evidence'))
        self.assertIn('Finding checked',answer)
        self.assertIn('do not change the focal-player scoring totals',answer)
        self.assertEqual(len(research.summary()['scoring']['support_samples']),4)
        self.assertEqual(research.summary()['verification']['status'],'checked')
        original=run.results['collect_scoring_support']['samples'][0]
        self.assertEqual(research.evidence[original['core'][0]]['values']['GP']['value'],2)
        nodes={n['id']:n for n in run.flow.snapshot()['nodes']}
        self.assertEqual(nodes['researcher-5']['depends_on'],['review-1'])
        self.assertEqual(nodes['researcher-5']['label'],'Helper follow-up')
        self.assertTrue(any(c['name']=='finish_blocked' for c in calls))

    def test_complete_findings_finish_in_one_round(self):
        run,_,_,calls,source_calls=self.run_case(sparse=False)
        self.assertEqual({t['round'] for t in run.tasks},{1});self.assertFalse(source_calls)
        self.assertFalse(any(c['name']=='inspect_supporting_cast' for c in calls))

    def test_exhausted_targeted_source_is_disclosed_without_repeating_completed_collection(self):
        run,research,answer,calls,source_calls=self.run_case(source_failure=True)
        self.assertEqual({t['round'] for t in run.tasks},{1,2})
        self.assertEqual(run.content_checks[0]['status'],'unavailable')
        self.assertEqual(len(source_calls),2)
        self.assertEqual(len([c for c in calls if c['name']=='collect_scoring_support']),1)
        self.assertIn('Limited by scope or source coverage',answer)
        self.assertIn('**Evidence remains limited:**',answer)
        self.assertNotIn('**Finding checked:**',answer)
        self.assertEqual(research.summary()['research']['coverage'],'partial')
