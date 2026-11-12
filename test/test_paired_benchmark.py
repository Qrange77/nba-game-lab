"""Protect comparison fairness and independent reference arithmetic offline."""
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from test.benchmark_audit import audit_payload, check_claim, score_extraction
from test.benchmark_reference import aggregate, select_rows
from test.paired_benchmark import Recorder, raw_request

class PairedBenchmarkTests(unittest.TestCase):
    def fact(self, **changes):
        return {'id':'x','value':30.12,'required':True,'metric':'PPG','unit':'points per game','tolerance':.2,'method_required':True,**changes}
    def claim(self, **changes):
        return {'id':'x','quote':'Jordan: 30.1 PPG.','number':'30.1','scope_quote':'Career regular season.','scope':'requested','method':'aggregate',**changes}
    def answer(self):
        return 'Career regular season. Jordan: 30.1 PPG.'
    def test_raw_only_identical_user_question(self):
        request=raw_request('An unchanged question?','model')
        self.assertEqual(request['messages'],[{'role':'user','content':'An unchanged question?'}])
        for name in ('tools','tool_choice','temperature'):self.assertNotIn(name,request)
        self.assertGreaterEqual(request['max_tokens'],8192)
    def test_rounding_tolerance(self):
        self.assertEqual(check_claim(self.fact(),self.claim(),self.answer())['status'],'correct')
        self.assertEqual(check_claim(self.fact(value=31),self.claim(),self.answer())['status'],'incorrect')
    def test_missing_is_coverage_gap(self):
        scored=score_extraction('',{'facts':[self.fact()]},{'claims':[]})
        self.assertEqual(scored['required_missing'],1)
        self.assertEqual(scored['required_comparable'],0)
    def test_quotes_and_scope(self):
        self.assertEqual(check_claim(self.fact(),self.claim(quote='Invented: 30.1'),self.answer())['status'],'unverifiable_extraction')
        self.assertEqual(check_claim(self.fact(),self.claim(scope='other'),self.answer())['status'],'scope_mismatch')
    def test_negative_sign_must_be_preserved(self):
        claim=self.claim(quote='Change: -1.0',number='1.0')
        answer='Career regular season. Change: -1.0'
        self.assertEqual(check_claim(self.fact(value=1),claim,answer)['status'],'unverifiable_extraction')
        self.assertEqual(check_claim(self.fact(value=-1),{**claim,'number':'-1.0'},answer)['status'],'correct')
    def test_unspecified_relative_method(self):
        self.assertEqual(check_claim(self.fact(metric='RTS',method_required=False),self.claim(method='season_mean'),self.answer())['status'],'method_not_comparable')
    def test_extractor_never_receives_gold_values(self):
        payload=audit_payload('Q','A',{'facts':[self.fact(value=987.1234)]})
        self.assertNotIn('987.1234',json.dumps(payload))
        self.assertNotIn('value',payload['targets'][0])
    def test_traded_total_and_window(self):
        def row(team,year,pts,gp):
            return {'SEASON_ID':year,'TEAM_ID':team,'LEAGUE_ID':'00','PTS':pts,'GP':gp,'FGA':pts,'FTA':0}
        rows=[row(1,'2000-01',100,10),row(2,'2000-01',200,20),row(0,'2000-01',300,30),row(1,'2001-02',999,1)]
        self.assertEqual(aggregate(select_rows(rows,2000,2000)),{'PTS':300,'PPG':10,'TS':50})
    def test_original_questions_preserved(self):
        root=Path(__file__).parent
        original=json.loads((root/'scoring_cases.json').read_text())[:3]
        frozen=json.loads((root/'benchmark_cases.json').read_text())
        self.assertEqual([c['question'] for c in original],[c['question'] for c in frozen[:3]])
        self.assertEqual(len(frozen),6)
    def test_recorder_keeps_truncation(self):
        reply=SimpleNamespace(model='resolved-model',id='id',usage=None,choices=[SimpleNamespace(finish_reason='length')])
        recorder=Recorder(complete=lambda **kwargs:reply)
        recorder(**raw_request('Q','model'))
        call=recorder.calls[0]
        self.assertTrue(call['truncated'])
        self.assertEqual(call['parameters']['max_tokens'],8192)
        self.assertEqual(call['response_model'],'resolved-model')
        self.assertEqual(call['message_roles'],['user'])

if __name__=='__main__':unittest.main()
