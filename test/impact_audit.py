"""Independently recompute contribution values from archived original NBA tables."""
import json
import argparse
from pathlib import Path
from test.context_audit import Sources, raw_table, require, check_values, ENDPOINTS, helper_rows, metrics, audit_final
ENDPOINTS['on_off']='teamplayeronoffsummary'

def audit_record(r,sources):
    scope=r['scope'];phase=scope['phase'];pid=r['player_id']
    if r['kind']=='impact_team':
        entry=sources.cited(r,'on_off',team_id=r['context']['team_id'],season_type_all_star=phase)
        expected={}
        for state in ('On','Off'):
            rows=[x for x in raw_table(entry,'Players'+state+'CourtTeamPlayerOnOffSummary') if x['VS_PLAYER_ID']==pid]
            require(len(rows)==1,'Nonunique on/off subject')
            for k in ('MIN','OFF_RATING','DEF_RATING','NET_RATING'):expected[state.upper()+'_'+k]=rows[0][k]
        expected['NET_DIFF']=expected['ON_NET_RATING']-expected['OFF_NET_RATING'] if expected['ON_MIN']>0 and expected['OFF_MIN']>0 else None
        return check_values(r,expected)
    entry=sources.cited(r,'career',player_id=pid)
    raw=raw_table(entry,'SeasonTotalsRegularSeason' if phase=='Regular Season' else 'SeasonTotalsPostSeason')
    years=range(scope['start'],scope['end']+1);rows=[]
    for year in years:
        candidates=[x for x in raw if int(x['SEASON_ID'][:4])==year and x.get('GP',0)>0 and x.get('LEAGUE_ID','00')=='00']
        totals=[x for x in candidates if x['TEAM_ID']==0]
        require(len(totals)<=1,'Duplicate season totals')
        rows+=totals or candidates
    expected={};keys=('GP','MIN','PTS','FGA','FTA','AST','TOV','STL','BLK','DREB')
    totals={k:sum(x[k] for x in rows) if all(x.get(k) is not None for x in rows) else None for k in keys}
    for k in r['values']:
        if k in ('PTS36','AST36','STL36','BLK36','DREB36'):
            n=totals[k[:-2]];d=totals['MIN'];v=36*n/d if n is not None and d else None
        elif k=='AST_TO':v=totals['AST']/totals['TOV'] if totals['AST'] is not None and totals['TOV'] else None
        elif k=='TS_PCT':v=100*totals['PTS']/(2*(totals['FGA']+.44*totals['FTA'])) if all(totals[x] is not None for x in ('PTS','FGA','FTA')) and totals['FGA']+.44*totals['FTA'] else None
        elif k=='GP':v=totals['GP']
        else:v=totals[k]/totals['GP'] if totals[k] is not None and totals['GP'] else None
        expected[k]=v
    return check_values(r,expected)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--folder',default='docs/impact-review');parser.add_argument('--offline',action='store_true');args=parser.parse_args()
    folder=Path(args.folder);sources=Sources(folder,None if args.offline else Path('data_cache/nba.sqlite3').resolve());checks=[]
    for path in sorted(folder.glob('*.json')):
        if path.name in ('sources.json','audit.json'):continue
        case=json.loads(path.read_text())
        if 'case' not in case:continue
        count=0;records=0;context_count=0
        for r in case.get('evidence',{}).values():
            if r['kind'].startswith('impact_'):count+=audit_record(r,sources);records+=1
            elif r['kind']=='supporting_cast':
                rows=[x for x in helper_rows(r,sources) if x['PLAYER_ID']==r['player_id']]
                require(len(rows)==1,'Wrong helper identity')
                context_count+=check_values(r,metrics(rows))
            elif r['kind']=='finals_series':context_count+=audit_final(r,sources)
        require(records>0,'No impact evidence in '+path.name)
        calls=case['raw']['model_calls'];require(len(calls)==1,'Raw did not run exactly once')
        require(calls[0]['message_roles']==['user'] and calls[0]['tool_names']==[],'Raw had tools/history')
        require(all(c['parameters']['model']==case['model'] for c in calls+case['model_calls']),'Model differs')
        require(not any(c.get('truncated') for c in calls),'Raw output truncated')
        checks.append({'case':case['case']['id'],'checked_records':records,'checked_values':count,'context_values':context_count,'truncated_agent_calls':[c['index'] for c in case['model_calls'] if c.get('truncated')],'raw_calls':len(calls)})
    (folder/'sources.json').write_text(json.dumps(sources.index,indent=2)+'\n')
    (folder/'audit.json').write_text(json.dumps({'checks':checks,'method':'Direct arithmetic from original NBA resultSets, independent of production aggregation. Covers all returned impact records; not unmeasured defense, causality or general agent superiority.'},indent=2)+'\n')
    print(json.dumps(checks))
if __name__=='__main__':main()
