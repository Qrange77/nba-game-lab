"""Offline acceptance against original NBA response tables, not scoring helpers.

Run after the opt-in live cases. Reads the local response cache without network
access or mutation. It intentionally does not import production aggregation code.
"""
import json
import math
import sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    db=sqlite3.connect(f'file:{ROOT / "data_cache/nba.sqlite3"}?mode=ro',uri=True)
    entries={key:json.loads(body) for key,body in db.execute('SELECT key,body FROM responses')}
    db.close()

    def raw(kind,**params):
        entry=entries[json.dumps([kind,params],sort_keys=True)]
        sets=entry['raw']['resultSets']
        return {s['name']:[dict(zip(s['headers'],row)) for row in s['rowSet']] for s in sets}

    def player_rows(pid,phase,lo,hi):
        table='SeasonTotalsRegularSeason' if phase=='Regular Season' else 'SeasonTotalsPostSeason'
        rows=raw('career',player_id=pid,per_mode36='Totals',league_id_nullable='00')[table]
        selected={}
        for row in rows:
            year=int(row['SEASON_ID'][:4])
            if lo<=year<=hi and row.get('LEAGUE_ID','00')=='00' and row['GP']:
                selected.setdefault(year,[]).append(row)
        result=[]
        for year,stints in sorted(selected.items()):
            total=[r for r in stints if r['TEAM_ID']==0 or r.get('TEAM_ABBREVIATION')=='TOT']
            if total:result.append(total[0])
            elif len(stints)==1:result.append(stints[0])
            else:
                combined=dict(stints[0])
                for key in ('GP','PTS','FGA','FTA'):
                    combined[key]=sum(r[key] for r in stints)
                result.append(combined)
        assert result,'No independent player rows'
        return result

    def expected(pid,phase,lo,hi):
        rows=player_rows(pid,phase,lo,hi)
        pts,gp,fga,fta=(sum(r[k] for r in rows) for k in ('PTS','GP','FGA','FTA'))
        weighted=0;weight_sum=0
        for row in rows:
            league=raw('league_games',season=row['SEASON_ID'],season_type_all_star=phase,
                player_or_team_abbreviation='T')['LeagueGameLog']
            assert league and len(league)==len({(r['GAME_ID'],r['TEAM_ID']) for r in league})
            points,shots,free=(sum(r[k] for r in league) for k in ('PTS','FGA','FTA'))
            league_ts=100*points/(2*(shots+.44*free))
            weight=row['FGA']+.44*row['FTA']
            weighted+=(100*row['PTS']/(2*weight)-league_ts)*weight
            weight_sum+=weight
        return {('PTS','totals'):pts,('PTS','per_game'):pts/gp,
            ('TS_PCT','per_game'):100*pts/(2*(fga+.44*fta)),
            ('WEIGHTED_RTS','per_game'):weighted/weight_sum}

    rows=[];numeric_checks=0
    for name in ('career','windows','postseason'):
        new=json.loads((ROOT/f'output/scoring-review/{name}.json').read_text())
        old=json.loads((ROOT/f'output/scoring-baseline-20261110/results/{name}.json').read_text())
        scoring=new['evidence_result']['scoring'];contract=scoring['contract'];matrix=scoring['matrix']
        values={}
        for side in ('left','right'):
            pid=contract[side+'_player']
            lo=1984 if contract['period']=='career' else contract[side+'_start']
            hi=contract['cutoff'] if contract['period']=='career' else contract[side+'_end']
            for phase in contract['phases']:values[(side,phase)]=expected(pid,phase,lo,hi)
        matched_old=0
        for row in matrix:
            assert row['complete'],(name,row)
            for side in ('left','right'):
                wanted=values[(side,row['phase'])][(row['metric'],row['basis'])]
                assert math.isclose(row[side],wanted,rel_tol=1e-10,abs_tol=1e-9),(name,row,side,wanted)
                numeric_checks+=1
            direction='tie' if math.isclose(row['left'],row['right'],abs_tol=1e-9) else 'left' if row['left']>row['right'] else 'right'
            assert direction==row['direction']
            # Compare published, checked values on the same axes, not general
            # answer quality. A whole-career number including 2026-27 fails.
            cards=(old.get('evidence_result') or {}).get('cards',[])
            both=True
            for side in ('left','right'):
                scope=row[side+'_scope'];pid=contract[side+'_player']
                candidates=[c for c in cards if c.get('player_id')==pid and c.get('title')==row['metric']
                    and row['phase'] in c.get('scope','')
                    and ('totals' if row['basis']=='totals' else 'per game') in c.get('scope','')
                    and c.get('value') is not None and math.isclose(c['value'],row[side],rel_tol=1e-10,abs_tol=1e-9)]
                if contract['period']=='windows':
                    candidates=[c for c in candidates if f"{scope['start']}-{str(scope['start']+1)[-2:]}" in c['scope'] and f"{scope['end']}-{str(scope['end']+1)[-2:]}" in c['scope']]
                both=both and bool(candidates)
            matched_old+=int(both)
        assert all(c.get('agent') for c in new['tool_calls'])
        assert new['evidence_result']['verification']['status']=='checked'
        rows.append({'case':name,'comparable_axes':len(matrix),'old_published_axes_matching_scoped_values':matched_old,
            'new_independently_verified_axes':len(matrix),'old_seconds':old['seconds'],'new_seconds':new['seconds'],
            'verdict':scoring['verdict']})

    boundary=[]
    for name,action in [('vague','clarify'),('outside_scope','outside_scope'),('early_era','unsupported_era'),('causal','causal_limit')]:
        result=json.loads((ROOT/f'output/scoring-review/{name}.json').read_text())
        call=next(c for c in result['tool_calls'] if c['name']=='confirm_scoring_contract')
        assert json.loads(call['result'])['action']==action
        assert not result['evidence']
        boundary.append({'case':name,'action':action,'statistical_collection_calls':0})

    fault=json.loads((ROOT/'output/scoring-review/windows-gap.json').read_text())
    assert fault['controlled_gap_injected']
    tasks=fault['evidence_result']['research']['tasks']
    assert {t['round'] for t in tasks}=={1,2}
    assert len([t for t in tasks if t['dimension']=='personal'])==2
    assert len([t for t in tasks if t['dimension']=='era'])==1
    assert fault['evidence_result']['research']['coverage']=='completed'
    output={'cases':rows,'independent_numeric_checks':numeric_checks,'boundaries':boundary,
        'controlled_fault':{'case':'windows-gap','rounds':2,'coverage':'completed','repeated_completed_dimensions':0},
        'method':'Independent arithmetic from cached original NBA resultSets; no production scoring/aggregation imports. Paired baseline uses identical questions and model. Published-axis coverage measures this product contract, not universal answer quality. Cached API timing is not a cold-start benchmark.'}
    (ROOT/'docs/acceptance-results.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))


if __name__=='__main__':main()
