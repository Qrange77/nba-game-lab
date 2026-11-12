"""Auditable on-court evidence; descriptive contributions, never causal estimates."""
from backend.data.nba import aggregate, number, provenance, season_label, DataUnavailable
from backend.research.scoring_evidence import ScoringEvidence, gap
from backend.research.tools import metric

LABELS = {'GP':'Recorded games','MIN':'Minutes per game','PTS':'Points per game','TS_PCT':'True shooting',
          'AST':'Assists per game','TOV':'Turnovers per game','AST_TO':'Assists per turnover',
          'PTS36':'Points per 36 minutes','AST36':'Assists per 36 minutes','STL36':'Steals per 36 minutes',
          'BLK36':'Blocks per 36 minutes','DREB36':'Defensive rebounds per 36 minutes',
          'FGA':'Field-goal attempts per game','FTA':'Free-throw attempts per game'}
KEYS = {'offense':('GP','MIN','PTS','TS_PCT','PTS36'),
        'playmaking':('GP','MIN','AST','TOV','AST_TO','AST36'),
        'defense':('GP','MIN','STL36','BLK36','DREB36'),
        'opportunity':('GP','MIN','PTS','FGA','FTA','TS_PCT','PTS36')}
DESCRIPTIONS = {
    'offense':'Collect matched scoring and contemporaneous league efficiency, not all-around impact.',
    'playmaking':'Collect observed assists, turnovers and per-minute production; no claims about unobserved potential assists.',
    'defense':'Collect steals, blocks and defensive rebounds per minute as activity indicators; these cannot rank complete individual defense.',
    'team':'Retrieve each scoped team stint and phase on/off ratings and minutes; preserve missing coverage and do not average ratings across stints.',
    'context':'Collect bounded core helpers, rotation and Finals opposition; detect inadequate helper samples.',
    'opportunity':'Investigate a discovered points/efficiency disagreement using matched minutes, attempts and per-minute scoring in both phases.',
    'support_followup':'Retrieve the approved matched helper samples after a recorded sample-adequacy finding.'}


class ImpactEvidence(ScoringEvidence):
    def profile(self, dimension):
        records=[];gaps=[]
        for pid in self.subjects:
            for phase in self.contract.phases:
                try:
                    entry,rows=self.rows(pid,phase)
                    if not rows:raise DataUnavailable('No recorded participation for this period and phase.')
                    totals=aggregate(rows,'totals');values=aggregate(rows)
                    for source,target in (('PTS','PTS36'),('AST','AST36'),('STL','STL36'),('BLK','BLK36'),('DREB','DREB36')):
                        a,b=totals[source]['value'],totals['MIN']['value']
                        valid=totals[source]['complete'] and totals['MIN']['complete'] and b and a is not None
                        values[target]=metric(36*a/b if valid else None,LABELS[target],'per 36 minutes','36 * sum('+source+') / sum(MIN)',{source:a,'MIN':b})
                    a,b=totals['AST']['value'],totals['TOV']['value']
                    values['AST_TO']=metric(a/b if a is not None and b and totals['AST']['complete'] and totals['TOV']['complete'] else None,LABELS['AST_TO'],'ratio','sum(AST) / sum(TOV)',{'AST':a,'TOV':b})
                    lo,hi=self.contract.bounds(pid)
                    missing=sorted(set(range(lo,hi+1))-{int(r['SEASON_ID'][:4]) for r in rows}) if self.contract.period=='windows' and phase=='Regular Season' else []
                    selected={k:{**values[k],'label':LABELS[k]} for k in KEYS[dimension]}
                    if missing:
                        for value in selected.values():value['complete']=False
                        gaps.append(gap(dimension,self.names[str(pid)],'Missing regular-season participation: '+str(missing)))
                    if any(not v['complete'] for v in selected.values()):gaps.append(gap(dimension,self.names[str(pid)],'One or more requested inputs are missing or undefined.'))
                    records.append(self.add({'kind':'impact_'+dimension,'player_id':pid,'player_name':self.names[str(pid)],
                        'scope':{'start':min(int(r['SEASON_ID'][:4]) for r in rows),'end':max(int(r['SEASON_ID'][:4]) for r in rows),'phase':phase,'basis':'per_game'},
                        'values':selected,'sources':[provenance(entry,pid)],'seasons':[r['SEASON_ID'] for r in rows],
                        'limitations':['Per-minute rates are not pace-adjusted. Assists depend on role and teammate shot conversion; turnovers also reflect ball-handling responsibilities. Defensive box-score activity is not complete defensive impact. Missing participation is not zero performance.']}))
                except (DataUnavailable,ValueError) as exc:gaps.append(gap(dimension,self.names[str(pid)],exc))
        return {'records':records,'gaps':gaps}

    def team(self):
        records=[];gaps=[]
        for pid in self.subjects:
            for phase in self.contract.phases:
                try:
                    career,rows=self.rows(pid,phase)
                    lo,hi=self.contract.bounds(pid)
                    table='SeasonTotalsRegularSeason' if phase=='Regular Season' else 'SeasonTotalsPostSeason'
                    stints=[r for r in career['data'].get(table,[]) if lo<=int(r['SEASON_ID'][:4])<=hi and r.get('TEAM_ID',0)>0 and r.get('GP')]
                    targets=sorted({(int(r['SEASON_ID'][:4]),int(r['TEAM_ID'])) for r in stints})
                    if len(targets)>4:
                        targets=targets[:2]+targets[-2:]
                        gaps.append(gap('team',self.names[str(pid)],'On/off is bounded to the first and last two team-season stints; it cannot establish a whole-career or whole-window on/off advantage.'))
                    if not targets:gaps.append(gap('team',self.names[str(pid)],'No scoped team stints were returned.'))
                    for year,tid in targets:
                        try:
                            entry=self.data.fetch('on_off',team_id=tid,season=season_label(year),season_type_all_star=phase,per_mode_detailed='Totals',league_id_nullable='00')
                            pair=[]
                            for state in ('On','Off'):
                                found=[r for r in entry['data'].get('Players'+state+'CourtTeamPlayerOnOffSummary',[]) if r.get('VS_PLAYER_ID')==pid]
                                if len(found)!=1:raise DataUnavailable('No unique '+state.lower()+'-court row; historical on/off coverage is unavailable for this sample.')
                                pair.append(found[0])
                            values={}
                            for state,row in zip(('ON','OFF'),pair):
                                for key in ('MIN','OFF_RATING','DEF_RATING','NET_RATING'):
                                    values[state+'_'+key]=metric(number(row.get(key)),state+' '+key.replace('_',' ').lower(),'minutes' if key=='MIN' else 'points / 100 possessions','NBA reported '+key,{'reported':row.get(key)})
                            a,b=values['ON_NET_RATING']['value'],values['OFF_NET_RATING']['value']
                            valid=a is not None and b is not None and all(values[s+'_MIN']['value'] is not None and values[s+'_MIN']['value']>0 for s in ('ON','OFF'))
                            values['NET_DIFF']=metric(a-b if valid else None,'On-minus-off net rating','points / 100 possessions','ON_NET_RATING - OFF_NET_RATING',{'on':a,'off':b})
                            if any(not v['complete'] for v in values.values()):
                                gaps.append(gap('team',self.names[str(pid)]+' '+season_label(year)+' '+phase,'Incomplete ratings or non-positive on/off minutes prevent a comparable team association.'))
                            records.append(self.add({'kind':'impact_team','player_id':pid,'player_name':self.names[str(pid)],
                                'scope':{'start':year,'end':year,'phase':phase,'basis':'per_game'},'context':{'team_id':tid,'team_name':pair[0].get('TEAM_NAME','')},
                                'values':values,'sources':[provenance(career,pid),provenance(entry)],
                                'limitations':['Team on/off association is confounded by teammates, opponents, substitutions and role; it is not an isolated player effect. Separate team stints are not averaged. Off-court minutes may include games without player participation.']}))
                        except (DataUnavailable,ValueError) as exc:gaps.append(gap('team',self.names[str(pid)]+' '+season_label(year)+' '+phase,exc))
                except (DataUnavailable,ValueError) as exc:gaps.append(gap('team',self.names[str(pid)],exc))
        return {'records':records,'gaps':gaps}

    def collect(self,dimension):
        if dimension in KEYS:
            result=self.profile(dimension)
            if dimension=='offense':
                era=self.collect_scoring_environment();result['records']+=era.get('records',[]);result['gaps']+=era.get('gaps',[])
        elif dimension=='team':result=self.team()
        elif dimension=='context':
            support=self.collect_scoring_support();finals=self.collect_scoring_finals()
            result={**support,'records':support.get('records',[])+finals.get('records',[]),'gaps':support.get('gaps',[])+finals.get('gaps',[])}
        elif dimension=='support_followup':result=self.inspect_supporting_cast()
        else:raise ValueError('Unsupported research dimension.')
        self._remember(result)
        return result
