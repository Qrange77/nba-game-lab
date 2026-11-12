"""Verify the non-injected content-follow-up case against original NBA tables."""
import json
import math
import sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    folder=ROOT/'output/content-acceptance'
    case=json.loads((folder/'support_findings.json').read_text())
    sufficient=json.loads((folder/'career.json').read_text())
    research=case['evidence_result']['research'];checks=research['content_checks']
    assert not case['controlled_gap_injected']
    initial=[t for t in research['tasks'] if t['round']==1]
    additional=[t for t in research['tasks'] if t['round']>1]
    assert len(initial)==4 and all(t['status']=='completed' for t in initial)
    assert len(additional)==1 and additional[0]['round']==2 and additional[0]['dimension']=='teammates'
    assert len(checks)==1 and checks[0]['kind']=='sparse_helper_sample' and checks[0]['status']=='completed'
    assert additional[0]['gap_id']==checks[0]['id']
    reviews=[json.loads(c['result']) for c in case['tool_calls'] if c['name']=='review_content_evidence']
    assert reviews[0]['checks'][0]['status']=='retryable'
    assert reviews[-1]['checks'][0]['status']=='completed'
    assert len([c for c in case['tool_calls'] if c['name']=='collect_scoring_support'])==1
    assert len([c for c in case['tool_calls'] if c['name']=='inspect_supporting_cast'])==1
    assert all(t['round']==1 for t in sufficient['evidence_result']['research']['tasks'])
    assert not sufficient['evidence_result']['research']['content_checks']
    assert all(c['name']!='inspect_supporting_cast' for c in sufficient['tool_calls'])
    db=sqlite3.connect(f'file:{ROOT / "data_cache/nba.sqlite3"}?mode=ro',uri=True)
    entries={key:json.loads(body) for key,body in db.execute('SELECT key,body FROM responses')};db.close()

    def source_row(record):
        for source in record['sources']:
            params=source['parameters']
            if source.get('endpoint','').endswith('/teamplayerdashboard'):
                kind='team_players';table='PlayersSeasonTotals'
            elif source.get('endpoint','').endswith('/playercareerstats') and params.get('player_id')==record['player_id']:
                kind='career';table='SeasonTotalsRegularSeason' if record['scope']['phase']=='Regular Season' else 'SeasonTotalsPostSeason'
            else:continue
            entry=entries.get(json.dumps([kind,params],sort_keys=True))
            if not entry:continue
            result=next(r for r in entry['raw']['resultSets'] if r['name']==table)
            rows=[dict(zip(result['headers'],r)) for r in result['rowSet']]
            matches=[r for r in rows if (kind=='team_players' and r['PLAYER_ID']==record['player_id']) or
                (kind=='career' and int(r['SEASON_ID'][:4])==record['scope']['start'] and r['TEAM_ID']==record['context']['team_id'])]
            if len(matches)==1:return matches[0]
        raise AssertionError('No unique original API row for '+record['player_name'])

    metric_checks=0;samples=case['evidence_result']['scoring']['support_samples']
    original=[s for s in samples if not s.get('followup')];added=[s for s in samples if s.get('followup')]
    assert len(original)==2 and len(added)==2
    assert {s['phase'] for s in original}=={'Playoffs'}
    assert {(s['player_name'],s['season'],s['phase']) for s in added}=={
        ('Michael Jordan',1990,'Regular Season'),('LeBron James',2014,'Regular Season')}
    for sample in samples:
        for ident in sample['core']:
            record=case['evidence'][ident];raw=source_row(record)
            expected={'GP':raw['GP'],'PTS':raw['PTS']/raw['GP'],'MIN':raw['MIN']/raw['GP'],
                'TS_PCT':100*raw['PTS']/(2*(raw['FGA']+.44*raw['FTA']))}
            for key,value in expected.items():
                assert math.isclose(record['values'][key]['value'],value,rel_tol=1e-10,abs_tol=1e-9)
                metric_checks+=1
    proof=[case['evidence'][i] for i in checks[0]['evidence_ids']]
    for record in proof:assert source_row(record)['GP']==record['values']['GP']['value']
    love_post=next(r for r in proof if r['player_name']=='Kevin Love')
    love_regular=next(case['evidence'][i] for s in added for i in s['core'] if case['evidence'][i]['player_name']=='Kevin Love')
    assert love_post['values']['GP']['value']==4 and love_regular['values']['GP']['value']==75
    assert case['evidence_result']['verification']['status']=='checked'
    nodes={n['id']:n for n in case['research_flow']['nodes']}
    assert nodes['researcher-5']['depends_on']==['review-1'] and nodes['writer']['depends_on']==['review-2']
    output={'content_case':{'fault_injected':False,'first_round_completed_collectors':4,'additional_researchers':1,
        'rounds':2,'trigger':'Sparse helper appearances found in retrieved evidence','original_kevin_love_playoff_gp':4,
        'rotation_reference_gp':max(r['values']['GP']['value'] for r in proof),
        'added_kevin_love_regular_gp':75,'matched_baselines_for_both_subjects':True,'original_samples_preserved':True,
        'independent_helper_metric_checks':metric_checks,'content_gap_status':'completed',
        'published_numeric_claims_checked':case['evidence_result']['verification']['checked_claims']},
        'sufficient_case':{'rounds':1,'extra_researchers':0,'content_gaps':0},
        'method':'Original cached NBA resultSets checked independently of production scoring helpers. Sparse appearance screening is a declared adequacy heuristic, not an injury explanation or teammate-quality ranking.'}
    (ROOT/'docs/content-acceptance-results.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))


if __name__=='__main__':main()
