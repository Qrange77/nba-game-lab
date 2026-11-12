"""Execution-graph truthfulness, concurrency and persistence checks."""
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from unittest.mock import patch
from fastapi.testclient import TestClient
import app
from backend.research.flow import ResearchFlow
from backend.research.scoring import ScoringRun
from backend.assistant.research_tools import AssistantResearchTools
from test.test_scoring_review import Data, contract


class FlowTests(unittest.TestCase):
    def test_only_dispatched_nodes_appear_and_snapshots_do_not_mutate(self):
        events=[];flow=ResearchFlow(events.append)
        flow.add('lead','Lead','lead','Lead')
        first=events[0]['flow']
        self.assertEqual([n['id'] for n in first['nodes']],['lead'])
        self.assertEqual(first['nodes'][0]['status'],'running')
        flow.finish('lead');flow.add('worker','Scoring','researcher','Researcher 1',['lead'],queued=True)
        self.assertEqual(len(first['nodes']),1)
        self.assertEqual(first['nodes'][0]['status'],'running')
        self.assertEqual(flow.snapshot()['nodes'][1]['status'],'queued')
        with self.assertRaises(ValueError):flow.add('bad','Bad','researcher','Researcher X',['future'])

    def test_parallel_intervals_and_public_versions_are_real(self):
        events=[];flow=ResearchFlow(events.append)
        flow.add('lead','Lead','lead','Lead');flow.finish('lead')
        for i in (1,2):flow.add(str(i),'Worker','researcher',f'Researcher {i}',['lead'],queued=True)
        barrier=Barrier(2)
        def worker(ident):
            flow.start(ident);barrier.wait(timeout=3);flow.finish(ident)
        with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(worker,['1','2']))
        flow.close();snapshot=flow.snapshot();workers=snapshot['nodes'][1:]
        self.assertEqual(snapshot['peak_parallel'],2)
        self.assertLessEqual(max(n['started_ms'] for n in workers),min(n['ended_ms'] for n in workers))
        self.assertEqual([e['flow']['version'] for e in events],list(range(1,len(events)+1)))

    def test_failure_preserves_finished_nodes_and_cancels_queued_work(self):
        flow=ResearchFlow(lambda event:None)
        flow.add('lead','Lead','lead','Lead');flow.finish('lead')
        flow.add('a','A','researcher','A',['lead']);flow.add('b','B','researcher','B',['lead'],queued=True)
        flow.close('failed')
        self.assertEqual([n['status'] for n in flow.snapshot()['nodes']],['completed','failed','cancelled'])

    def test_clarification_does_not_invent_researchers_or_writer(self):
        run=ScoringRun([{'role':'user','content':'Who is better?'}],AssistantResearchTools(data=Data()))
        run.run();flow=run.flow.snapshot()
        self.assertEqual(flow['status'],'clarification')
        self.assertEqual([n['id'] for n in flow['nodes']],['lead'])

    def test_actual_run_failure_closes_graph_before_propagating(self):
        run=ScoringRun([],AssistantResearchTools(data=Data()))
        with patch.object(run,'resolve_contract',return_value=contract()),patch.object(run,'decision',side_effect=TimeoutError()):
            with self.assertRaises(TimeoutError):run.run()
        self.assertEqual(run.flow.snapshot()['status'],'failed')
        self.assertTrue(all(n['status']!='running' for n in run.flow.snapshot()['nodes']))

    def test_stream_and_history_preserve_failed_graph(self):
        def runner(messages,on_event,**kwargs):
            flow=ResearchFlow(on_event);flow.add('lead','Lead','lead','Lead');flow.close('failed')
            raise TimeoutError('Controlled acceptance failure')
        with tempfile.TemporaryDirectory() as folder,patch.object(app,'HISTORY_DIR',Path(folder)),patch.object(app,'run_agent',side_effect=runner):
            client=TestClient(app.app)
            response=client.post('/chat/stream',json={'message':'Test flow persistence'})
            import json
            events=[json.loads(line[5:]) for line in response.text.splitlines() if line.startswith('data:')]
            final=events[-1]['data']
            self.assertTrue(final['failed']);self.assertEqual(final['research_flow']['status'],'failed')
            saved=client.get('/sessions/'+final['session_id']).json()['turns'][0]
            self.assertEqual(saved['research_flow'],final['research_flow'])
            self.assertEqual([e for e in events if e['type']=='research_flow'][0]['flow']['nodes'][0]['status'],'running')
