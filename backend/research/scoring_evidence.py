"""Contract-bound collectors and deterministic scoring comparisons."""
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.data.nba import DataUnavailable, aggregate, number, provenance, season_rows, season_label
from backend.debate.schemas import Scope
from backend.research.tools import ResearchTools, Season, Finals, metric, compact
from backend.research.support_review import complete_sample

SCORE_KEYS=('GP','MIN','PTS','FGM','FGA','FG3M','FG3A','FTM','FTA','TS_PCT','EFG_PCT','FG_PCT','FG3_PCT','FT_PCT')
COLLECTORS={
    'collect_scoring_profile':'Retrieve both confirmed players in the locked windows, phases and cutoff. Returns scoring totals/rates and actual season coverage. This is the primary scoring evidence, not an overall ability ranking.',
    'collect_scoring_environment':'Retrieve contemporaneous league shooting benchmarks for every returned player-season in the locked scope. Calculate shot-opportunity-weighted relative TS with explicit coverage. Missing pace does not invalidate available TS. No interpolated seasons.',
    'collect_scoring_support':'Compare bounded supporting-cast samples: earliest and latest verified Finals in each selected window; if absent, earliest/latest recorded playoff seasons. Discover contemporary core helpers and rotation minutes/production. No injury or causal claims.',
    'collect_scoring_finals':'Verify Finals appearances inside the locked windows, including defeats. Return series scoring and contemporaneous opponent records. A team record is context, not a complete measure of difficulty.',
    'inspect_supporting_cast':'Investigate a specific evidence-content gap using server-approved matched player/season/phase targets. Reuse cached API inputs; collect a missing phase or check the independent roster/career source. Preserve initial helper candidates; do not manufacture a preferred support ranking.',
}
SCORING_TOOLS=[{'type':'function','function':{'name':name,'description':description,
    'parameters':{'type':'object','properties':{},'additionalProperties':False}}} for name,description in COLLECTORS.items()]


def gap(dimension,subject,reason,status='unavailable'):
    return {'dimension':dimension,'subject':subject,'reason':str(reason)[:500],'status':status}


class ScoringEvidence(ResearchTools):
    def __init__(self,contract,support_targets=None,**kwargs):
        super().__init__(**kwargs)
        self.contract=contract
        self.collector_results={}
        self.support_targets=support_targets or []

    @property
    def subjects(self):return (self.contract.left_player,self.contract.right_player)

    def query_evidence(self,p):
        if p.kind!='stats':return super().query_evidence(p)
        lo,hi=self.contract.bounds(p.player_id)
        if p.scope.start is None or p.scope.start<lo or p.scope.end>hi or p.scope.phase not in self.contract.phases:
            raise ValueError('Season evidence must stay inside the locked scoring contract.')
        entry=self.career(p.player_id)
        table='SeasonTotalsRegularSeason' if p.scope.phase=='Regular Season' else 'SeasonTotalsPostSeason'
        rows=season_rows(entry['data'].get(table,[]),p.scope.start,p.scope.end)
        if not rows:raise DataUnavailable('No player scoring rows for this season and phase.')
        return self.add({'kind':'stats','player_id':p.player_id,'player_name':self.names[str(p.player_id)],
            'scope':p.scope.model_dump(),'values':{k:v for k,v in aggregate(rows,p.scope.basis).items() if k in SCORE_KEYS},
            'seasons':[r['SEASON_ID'] for r in rows],'sources':[provenance(entry,p.player_id)],
            'limitations':['Season-specific scoring inputs; the league baseline is collected independently.']})

    def dispatch(self,name,args):
        if name not in COLLECTORS:
            return json.dumps({'error':'This tool is outside the scoring-review contract.'})
        if args:
            return json.dumps({'error':'This collector takes no arguments. The approved contract supplies its scope.'})
        try:
            if name not in self.collector_results:
                result=getattr(self,name)()
                result['collector']=name
                self.collector_results[name]=result
            result=self.collector_results[name]
            self._remember(result)
            return json.dumps(result)
        except (DataUnavailable,ValueError) as exc:
            result={'collector':name,'status':'unavailable','error':str(exc),
                'gaps':[gap(name,str(self.subjects),exc)]}
            self.collector_results[name]=result
            return json.dumps(result)

    def rows(self,pid,phase):
        entry=self.career(pid)
        table='SeasonTotalsRegularSeason' if phase=='Regular Season' else 'SeasonTotalsPostSeason'
        all_rows=entry['data'].get(table,[])
        lo,hi=self.contract.bounds(pid)
        return entry,season_rows(all_rows,lo,hi)

    def scoring_record(self,pid,phase,basis):
        entry,rows=self.rows(pid,phase)
        if not rows:raise DataUnavailable('No participation rows returned in this scoring window and phase.')
        years=sorted({int(r['SEASON_ID'][:4]) for r in rows})
        lo,hi=self.contract.bounds(pid)
        missing=[]
        if self.contract.period=='windows' and phase=='Regular Season':
            missing=sorted(set(range(lo,hi+1))-set(years))
        scope=Scope(start=lo if self.contract.period=='windows' else min(years),
                    end=hi if self.contract.period=='windows' else max(years),phase=phase,basis=basis)
        values={k:v for k,v in aggregate(rows,basis).items() if k in SCORE_KEYS}
        if missing:
            for value in values.values():value['complete']=False
        return self.add({'kind':'scoring_stats','player_id':pid,'player_name':self.names[str(pid)],
            'scope':scope.model_dump(),'values':values,'seasons':[season_label(y) for y in years],
            'scoring_role':'personal','cutoff':self.contract.cutoff,
            'sources':[provenance(entry,pid)],'missing_seasons':missing,
            'limitations':['Counts cover returned NBA participation, not hypothetical full seasons.',
                'Playoff samples include Finals and only recorded appearances; missing postseason participation is not a zero-performance game.',
                *(['Regular-season window has missing participation rows: '+str(missing)] if missing else [])]})

    def collect_scoring_profile(self):
        records=[];gaps=[]
        for pid in self.subjects:
            for phase in self.contract.phases:
                try:
                    for basis in ('totals','per_game'):
                        record=self.scoring_record(pid,phase,basis)
                        records.append(compact(record))
                        if record['missing_seasons']:
                            gaps.append(gap('personal',str(pid),record['limitations'][-1]))
                        if basis=='per_game':
                            missing=[key for key in ('PTS','TS_PCT') if not record['values'].get(key,{}).get('complete')]
                            if missing and not record['missing_seasons']:
                                gaps.append(gap('personal',f'{pid}/{phase}','Required scoring metrics unavailable: '+', '.join(missing)))
                except DataUnavailable as exc:gaps.append(gap('personal',f'{pid}/{phase}',exc))
        return {'records':records,'gaps':gaps,'status':'partial' if gaps else 'completed'}

    def collect_scoring_environment(self):
        summaries=[];inputs=[];gaps=[]
        for pid in self.subjects:
            for phase in self.contract.phases:
                try:
                    entry,rows=self.rows(pid,phase)
                    if not rows:raise DataUnavailable('No scoring participation for a league-relative sample.')
                except DataUnavailable as exc:
                    gaps.append(gap('era',f'{pid}/{phase}',exc));continue
                sources=[provenance(entry,pid)];season_inputs=[];missing=[]
                total_weight=0;covered_weight=0;weighted=0;unknown_weight=False
                def fetch_season(row):
                    year=int(row['SEASON_ID'][:4])
                    pts,fga,fta=(number(row.get(k)) for k in ('PTS','FGA','FTA'))
                    weight=fga+.44*fta if fga is not None and fta is not None else None
                    player_ts=100*pts/(2*weight) if pts is not None and weight else None
                    if player_ts is None:return row,None,None,'Player shooting inputs missing.'
                    try:
                        result=self.query_era_environment(Season(player_id=pid,season=year,phase=phase))
                        environment=self.evidence[result['environment']['id']]
                        league_ts=environment['values']['LEAGUE_TS_PCT']['value']
                        if league_ts is None:raise DataUnavailable('League TS inputs unavailable for this season.')
                        return row,environment,(player_ts-league_ts,weight,player_ts,league_ts),None
                    except (DataUnavailable,ValueError) as exc:
                        # The modern team dashboard is a separate API source; it
                        # can replace unavailable game-log shooting inputs.
                        try:
                            fallback=self.data.fetch('league',season=row['SEASON_ID'],season_type_all_star=phase,
                                per_mode_detailed='Totals',measure_type_detailed_defense='Base',league_id_nullable='00')
                            team_rows=fallback['data'].get('LeagueDashTeamStats',[])
                            if not team_rows or len({r.get('TEAM_ID') for r in team_rows})!=len(team_rows):raise DataUnavailable('No unique league team table.')
                            sums={k:sum(number(r[k]) for r in team_rows) for k in ('PTS','FGA','FTA') if all(number(r.get(k)) is not None for r in team_rows)}
                            if len(sums)!=3:raise DataUnavailable('League team shooting inputs are incomplete.')
                            denominator=2*(sums['FGA']+.44*sums['FTA'])
                            if not denominator:raise DataUnavailable('League shooting denominator is zero.')
                            league_ts=100*sums['PTS']/denominator
                            source=provenance(fallback)
                            return row,{'sources':[source]},(player_ts-league_ts,weight,player_ts,league_ts),None
                        except (DataUnavailable,KeyError,TypeError) as fallback_error:
                            return row,None,None,str(exc)+' Alternative: '+str(fallback_error)
                with ThreadPoolExecutor(max_workers=4) as pool:
                    results=list(pool.map(fetch_season,rows))
                for row,environment,result,error in results:
                    fga,fta=number(row.get('FGA')),number(row.get('FTA'))
                    weight=fga+.44*fta if fga is not None and fta is not None else None
                    if weight is not None:total_weight+=weight
                    else:unknown_weight=True
                    if error:
                        missing.append(row['SEASON_ID']);gaps.append(gap('era',f"{pid}/{row['SEASON_ID']}/{phase}",error));continue
                    relative,weight,player_ts,league_ts=result
                    covered_weight+=weight;weighted+=relative*weight
                    sources+=environment['sources']
                    item={'season':row['SEASON_ID'],'player_ts':player_ts,'league_ts':league_ts,
                          'relative_ts':relative,'shooting_opportunities':weight}
                    season_inputs.append(item);inputs.append(dict(item,player_id=pid,phase=phase))
                years=[int(row['SEASON_ID'][:4]) for row in rows]
                missing_window=(set(range(self.contract.bounds(pid)[0],self.contract.bounds(pid)[1]+1))-
                    {int(r['SEASON_ID'][:4]) for r in rows}) if self.contract.period=='windows' and phase=='Regular Season' else set()
                complete=not missing and not missing_window and len(season_inputs)==len(rows) and total_weight>0
                if missing_window:
                    gaps.append(gap('era',f'{pid}/{phase}','The explicit regular-season window has missing participation rows.'))
                value=weighted/covered_weight if covered_weight else None
                rec=self.add({'kind':'scoring_relative','player_id':pid,'player_name':self.names[str(pid)],
                    'scope':Scope(start=min(years),end=max(years),phase=phase).model_dump(),
                    'scoring_role':'era','values':{
                        'WEIGHTED_RTS':dict(metric(value,'Shot-opportunity-weighted relative TS','percentage points',
                            'sum((player season TS% - league season TS%) * (FGA + 0.44*FTA)) / sum(FGA + 0.44*FTA)',
                            {'season_inputs':season_inputs}),complete=complete),
                        'ERA_COVERAGE':metric(100*covered_weight/total_weight if total_weight and not unknown_weight else None,'Shooting-opportunity coverage','%',
                            '100 * covered shooting opportunities / total returned shooting opportunities'),
                        'SEASONS_COVERED':metric(len(season_inputs),'Covered league-baseline seasons','seasons','count(verified season baselines)')},
                    'sources':sources,'missing_seasons':missing,'season_inputs':season_inputs,
                    'limitations':['Weighted relative TS is an explicit descriptive comparison, not an official NBA impact metric or a causal era correction.',
                        'League baselines use the same season and phase as the player sample. No interpolation is used.',
                        *(['Partial baseline coverage: '+', '.join(missing)+'. No full-window relative-efficiency verdict is supported.'] if missing else [])]})
                summaries.append(compact(rec))
        return {'records':summaries,'season_inputs':inputs,'gaps':gaps,'status':'partial' if gaps else 'completed'}

    def selected_finals(self,pid):
        lo,hi=self.contract.bounds(pid)
        if self.contract.period=='career':result=self.query_finals_path(Finals(player_id=pid))
        else:
            results=[self.query_finals_path(Finals(player_id=pid,season=y)) for y in range(lo,hi+1)]
            result={'series':[r for item in results for r in item['series']],
                    'gaps':[g for item in results for g in item['gaps']]}
        return [r for r in result['series'] if lo<=r['scope']['start']<=hi],result['gaps']

    def coverage_record(self,role,records,gaps,notes):
        rec=self.add({'kind':'scoring_coverage','player_id':self.contract.left_player,
            'player_name':'Comparison coverage','scope':Scope(start=1984,end=self.contract.cutoff).model_dump(),
            'scoring_role':role,'values':{},'sources':[],'limitations':notes,
            'coverage':{'record_ids':[r['id'] for r in records],'gaps':gaps,'notes':notes}})
        return compact(rec)

    def collect_scoring_finals(self):
        records=[];gaps=[]
        for pid in self.subjects:
            try:
                series,missing=self.selected_finals(pid)
                for r in series:
                    r['scoring_role']='opponents'
                    records.append(r)
                gaps += [gap('opponents',str(pid),message) for message in missing]
            except DataUnavailable as exc:gaps.append(gap('opponents',str(pid),exc))
        notes=['All verified Finals within the locked window, including defeats; team regular-season win percentage is a limited competition proxy.']
        return {'records':records,'coverage':self.coverage_record('opponents',records,gaps,notes),
            'gaps':gaps,'status':'partial' if gaps else 'completed'}

    def collect_scoring_support(self):
        records=[];samples=[];gaps=[]
        approved_phases=self.contract.support_phases or self.contract.phases
        for pid in self.subjects:
            try:
                series,_=self.selected_finals(pid)
                anchors=sorted({r['scope']['start'] for r in series})
                _,postseason=self.rows(pid,'Playoffs')
                if not anchors:anchors=sorted({int(r['SEASON_ID'][:4]) for r in postseason})
                phase='Playoffs' if 'Playoffs' in approved_phases else 'Regular Season'
                if not anchors:
                    if 'Regular Season' in approved_phases:
                        _,regular=self.rows(pid,'Regular Season')
                        anchors=sorted({int(r['SEASON_ID'][:4]) for r in regular});phase='Regular Season'
                if not anchors:raise DataUnavailable('No supporting-cast participation in an approved phase.')
                anchors=sorted(set(anchors[:1]+anchors[-1:]))
                for year in anchors:
                    result=self.query_supporting_cast(Season(player_id=pid,season=year,phase=phase))
                    if result.get('status')=='needs_team':
                        gaps.append(gap('teammates',f'{pid}/{year}','Multiple team stints require explicit selection.'));continue
                    all_returned={r['id']:r for r in result.get('core_candidates',[])+result.get('rotation',[])}
                    for r in all_returned.values():r['scoring_role']='teammates'
                    records+=list(all_returned.values())
                    samples.append({'player_id':pid,'season':year,'phase':phase,
                        'core':[r['id'] for r in result.get('core_candidates',[])[:2]],
                        'rotation':[r['id'] for r in result.get('rotation',[])],
                        'selection':'Earliest/latest verified Finals within the window; otherwise earliest/latest recorded playoffs. Core candidates use contemporary scoring; rotation uses total minutes.'})
                    gaps += [gap('teammates',f'{pid}/{year}',reason) for reason in result.get('gaps',[])]
            except DataUnavailable as exc:gaps.append(gap('teammates',str(pid),exc))
        notes=['Supporting-cast cases are bounded samples, not a career-wide ranking of teammate quality.',
               'Games/minutes do not establish injuries, shared court time, causation or hypothetical teammate swaps.']
        return {'records':records,'samples':samples,'coverage':self.coverage_record('teammates',records,gaps,notes),
            'gaps':gaps,'status':'partial' if gaps else 'completed'}

    def inspect_supporting_cast(self):
        if not self.support_targets:raise ValueError('No approved supporting-cast follow-up targets were assigned.')
        records=[];samples=[];gaps=[]
        for target in self.support_targets:
            pid,year,phase=target['player_id'],target['season'],target['phase']
            lo,hi=self.contract.bounds(pid)
            if not lo<=year<=hi or phase not in (self.contract.support_phases or self.contract.phases):
                raise ValueError('Follow-up targets must remain inside the locked comparison.')
            try:
                result=self.query_supporting_cast(Season(player_id=pid,season=year,phase=phase),prefer_roster=target.get('source')=='roster')
                if result.get('status')=='needs_team':raise DataUnavailable('Multiple team stints need explicit selection; no guessed team was used.')
                returned={r['id']:r for r in result.get('core_candidates',[])+result.get('rotation',[])}
                records+=list(returned.values())
                sample={'player_id':pid,'season':year,'phase':phase,
                    'core':[r['id'] for r in result.get('core_candidates',[])[:2]],
                    'rotation':[r['id'] for r in result.get('rotation',[])],
                    'followup':True,'selection':'Evidence-driven matched sample: same approved window position or corresponding career anchor for both subjects. Original core and rotation observations are retained.'}
                samples.append(sample)
                if not complete_sample(sample,self.evidence):gaps.append(gap('teammates',f'{pid}/{year}/{phase}','Comparable core-helper metrics remain incomplete after the targeted source check.'))
                gaps += [gap('teammates',f'{pid}/{year}/{phase}',reason) for reason in result.get('gaps',[])]
            except (DataUnavailable,ValueError) as exc:gaps.append(gap('teammates',f'{pid}/{year}/{phase}',exc))
        return {'records':records,'samples':samples,'gaps':gaps,'status':'partial' if gaps else 'completed'}


def scoring_matrix(evidence,contract):
    rows=[]
    for phase in contract.phases:
        for key,basis,kind,label in (
            ('PTS','totals','scoring_stats','Accumulated points'),
            ('PTS','per_game','scoring_stats','Points per game'),
            ('TS_PCT','per_game','scoring_stats','Raw true shooting'),
            ('WEIGHTED_RTS','per_game','scoring_relative','Contemporaneous relative true shooting')):
            sides=[]
            for pid in (contract.left_player,contract.right_player):
                record=next((r for r in evidence.values() if r.get('kind')==kind and r.get('player_id')==pid
                    and r.get('scope',{}).get('phase')==phase and r.get('scope',{}).get('basis')==basis),None)
                value=record.get('values',{}).get(key,{}) if record else {}
                sides.append({'record':record,'value':value.get('value'),'complete':bool(value.get('complete'))})
            left,right=sides
            comparable=left['complete'] and right['complete'] and left['value'] is not None and right['value'] is not None
            direction=('left' if left['value']>right['value'] else 'right' if left['value']<right['value'] else 'tie') if comparable else 'unavailable'
            rows.append({'phase':phase,'metric':key,'basis':basis,'label':label,'left':left['value'],'right':right['value'],
                'unit':(left['record'] or right['record'] or {}).get('values',{}).get(key,{}).get('unit',''),
                'direction':direction,'complete':comparable,
                'left_id':left['record']['id'] if left['record'] else None,
                'right_id':right['record']['id'] if right['record'] else None,
                'left_scope':left['record']['scope'] if left['record'] else None,
                'right_scope':right['record']['scope'] if right['record'] else None})
    return rows


def adjudicate(matrix,contract):
    relevant=matrix
    if contract.lens=='volume':relevant=[r for r in matrix if r['metric']=='PTS']
    if contract.lens=='efficiency':relevant=[r for r in matrix if r['metric'] in ('TS_PCT','WEIGHTED_RTS')]
    if contract.lens=='postseason':relevant=[r for r in matrix if r['phase']=='Playoffs']
    if not relevant or any(not r['complete'] for r in relevant):return 'insufficient_data'
    directions={r['direction'] for r in relevant}-{'tie'}
    if directions=={'left'}:return 'supported'
    if directions=={'right'}:return 'contradicted'
    return 'conditional'
