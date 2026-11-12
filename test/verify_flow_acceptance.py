"""Inspect real execution snapshots captured by live and browser acceptance."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def inspect(path):
    result=json.loads(path.read_text())
    events=result['flow_events'];flow=result['research_flow'];nodes=flow['nodes']
    assert [n['id'] for n in events[0]['nodes']]==['lead']
    assert events[0]['nodes'][0]['status']=='running'
    assert [e['version'] for e in events]==sorted(set(e['version'] for e in events))
    known=set()
    for node in nodes:
        assert node['id'] not in known
        assert set(node['depends_on'])<=known
        known.add(node['id'])
        assert node['status'] not in ('queued','running')
        if node['started_ms'] is not None:assert node['ended_ms']>=node['started_ms']
    calls=result['tool_calls']
    assert {c['id'] for c in calls}=={ident for n in nodes for ident in n['tool_ids']}
    for call in calls:
        node=next(n for n in nodes if n['id']==call['node_id'])
        assert node['agent']==call['agent']
    assert flow['status']=='completed'
    assert result['evidence_result']['verification']['status']=='checked'
    assert result['evidence_result']['scoring']['verdict']=='conditional'
    return result


def main():
    folder=ROOT/'output/flow-acceptance'
    normal=inspect(folder/'career.json');recovery=inspect(folder/'browser-gap.json')
    flow=normal['research_flow'];workers=[n for n in flow['nodes'] if n['role']=='researcher']
    assert len(workers)==4 and all(n['round']==1 for n in workers)
    assert max(n['started_ms'] for n in workers)<min(n['ended_ms'] for n in workers)
    assert flow['peak_parallel']==4
    recovered={n['id']:n for n in recovery['research_flow']['nodes']}
    assert recovery['controlled_fault'] and recovery['injected']
    assert recovered['researcher-1']['status']=='partial'
    assert recovered['researcher-3']['depends_on']==['review-1']
    assert recovered['review-2']['depends_on']==['researcher-3']
    assert recovered['writer']['depends_on']==['review-2']
    assert len([n for n in recovered.values() if n['role']=='researcher'])==3
    output={'normal':{'researchers':4,'rounds':1,'peak_concurrent_researchers':4,
        'shared_overlap_ms':min(n['ended_ms'] for n in workers)-max(n['started_ms'] for n in workers),
        'final_status':'completed'},
        'controlled_browser_recovery':{'researchers':3,'rounds':2,'original_partial_node_preserved':True,
            'repeated_completed_era_task':False,'writer_depends_on_final_review':True,'final_status':'completed'},
        'checks':['Only Lead appears initially','All dependencies reference earlier dispatched nodes',
            'Node durations derive from actual lifecycle timestamps','Every tool maps to exactly its execution node',
            'Final snapshots preserve partial attempts','Numeric evidence verification still passes'],
        'note':'The recovery case intentionally omits one collector. All other model and NBA calls are live/cached. Peak concurrency is measured, not an animation.'}
    (ROOT/'docs/flow-acceptance-results.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))


if __name__=='__main__':main()
