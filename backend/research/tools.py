"""Historical context from NBA APIs, including pre-dashboard seasons."""
import json
import copy
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from backend.assistant.research_tools import AssistantResearchTools, TOOLS as BASE_TOOLS
from backend.data.nba import DataUnavailable, aggregate, number, provenance, season_label, current_season
from backend.debate.schemas import Scope, Query, PlayerAwards


class Player(BaseModel):
    model_config = ConfigDict(extra='forbid')
    player_id: int = Field(gt=0, description='Confirmed NBA player ID.')


class Season(Player):
    season: int = Field(ge=1946, le=2100, description='Season START year: 1990 means 1990-91.')
    phase: str = Field(default='Regular Season', pattern='^(Regular Season|Playoffs)$')
    team_id: int | None = Field(default=None, gt=0)

    @model_validator(mode='after')
    def available(self):
        if self.season > current_season():
            raise ValueError('Future seasons are unavailable.')
        return self


class Finals(Player):
    season: int | None = Field(default=None, ge=1946, le=2100, description='One season START year, or null for all verified career Finals appearances, wins and losses.')


class Game(BaseModel):
    model_config = ConfigDict(extra='forbid')
    event_id: str = Field(min_length=1,max_length=40,description='Exact ESPN event_id returned by find_games. Never invent an ID.')
    date: str = Field(default='',description='Requested game date YYYY-MM-DD; validates the event selection.')


MODELS = {'query_career_profile': Player, 'query_supporting_cast': Season,
          'query_era_environment': Season, 'query_finals_path': Finals, 'query_game_context':Game}
DESCRIPTIONS = {
    'query_game_context':'Retrieve a verified ESPN game box score for BOTH teams with exact basic statistics, locally computed shooting and possession estimates, sources and citable evidence IDs. Call find_games first. Team evidence uses negative subject IDs (not NBA player IDs); copy these into report claims only. Supports sourced game investigation without treating box-score association as causation.',
    'query_career_profile': 'Get a verified season/team inventory, career regular-season and playoff production (per-game and totals), and honors. Use this inventory before choosing context samples. All available seasons are included; current seasons may be incomplete.',
    'query_supporting_cast': 'Retrieve one verified team-season supporting cast, including pre-1996 rosters via roster + individual career APIs. Returns core candidates and the main rotation with minutes, production, efficiency and games played. Select the core helper using comparable contemporary criteria, then use rotation depth/availability as background. Games played do not establish injuries or actual shared minutes. Requires explicit season; select team_id if traded.',
    'query_era_environment': 'Compute one season league environment from ALL returned team-game logs: team points per game, league TS%, estimated possessions per 48 minutes and estimated offensive rating. Also retrieves the focal player season and relative TS percentage-point difference. Team scoring context is not an individual-player scoring average. Preserve phase, sample size, estimates and coverage.',
    'query_finals_path': 'Find all verified Finals appearances from career team stints + team histories, including defeats. Identify opponents and series via league playoff game IDs, retrieve focal player Finals game logs and opponent regular-season strength. Returns citable series metrics, opponent records, game counts and missing coverage. Optional season drills into one series. No inferred Finals labels from win totals.',
}
EXTRA_TOOLS = [{'type':'function','function':{'name':name,'description':DESCRIPTIONS[name],
                 'parameters':model.model_json_schema()}} for name,model in MODELS.items()]
TOOLS = copy.deepcopy(BASE_TOOLS) + EXTRA_TOOLS
for tool in TOOLS:
    if tool['function']['name']=='query_evidence':
        tool['function']['description']='Retrieve player season/career statistics or one season of game logs. For league baselines use query_era_environment, which supports historical team-game APIs. Use compare_players only for distinct people; compare phases of one player by retrieving each scope separately.'
        tool['function']['parameters']['properties']['kind']['enum']=['stats','awards','games']
METRICS = ('GP','MIN','PTS','REB','AST','STL','BLK','TOV','TS_PCT','EFG_PCT','FG_PCT','FG3_PCT','FT_PCT','SEASONS')


def metric(value, label, unit, formula, inputs=None):
    return dict(value=value, label=label, unit=unit, formula=formula, inputs=inputs or {},
                complete=value is not None, games=None, covered_seasons=[])


def compact(record):
    return {k:v for k,v in record.items() if k != 'values'} | {
        'values':{k:{a:b for a,b in v.items() if a in ('value','unit','label','complete','formula')}
                  for k,v in record.get('values',{}).items()}}


def date_key(row):
    raw = row.get('GAME_DATE','')
    for fmt in ('%Y-%m-%d','%b %d, %Y','%Y-%m-%dT%H:%M:%S'):
        try:
            return datetime.strptime(raw,fmt)
        except ValueError:
            pass
    raise DataUnavailable('An unrecognized game date prevents reliable series selection.')


class ResearchTools(AssistantResearchTools):
    def query_evidence(self,p):
        record=super().query_evidence(p)
        if p.kind=='stats':
            record={k:v for k,v in record.items() if k!='id'}
            record['values']=dict(record['values'],SEASONS=metric(len(set(record.get('seasons',[]))),
                'NBA seasons with returned participation','seasons','count(distinct returned season labels)'))
            return self.add(record)
        return record

    def dispatch(self, name, args):
        if name=='query_evidence' and args.get('kind')=='league':
            scope=args.get('scope',{})
            if scope.get('start') is not None and scope.get('start')==scope.get('end'):
                return self.dispatch('query_era_environment',{'player_id':args.get('player_id'),
                    'season':scope['start'],'phase':scope.get('phase','Regular Season')})
        if name not in MODELS:
            return super().dispatch(name,args)
        try:
            p = MODELS[name].model_validate(args)
            if hasattr(p,'player_id'):
                self.allowed(p.player_id)
            result = getattr(self,name)(p)
            self._remember(result)
            return json.dumps(result)
        except (ValidationError, ValueError, DataUnavailable) as exc:
            return json.dumps({'error':str(exc),'status':'unavailable',
                'next_action':'Use a different supported query or report this specific gap. Missing is not zero.'})

    def career(self,pid):
        return self.data.fetch('career',player_id=pid,per_mode36='Totals',league_id_nullable='00')

    def query_game_context(self,p):
        from backend.assistant.tools import _game, _team, _team_advanced_inputs
        from backend.assistant.advanced_stats import TEAM_METRICS, calculate
        data,competition=_game(p.date,p.event_id)
        participants=competition['competitors']
        if competition.get('status',{}).get('type',{}).get('state')=='pre':
            raise DataUnavailable('The selected game has not started.')
        game_date=datetime.fromisoformat(competition['date'].replace('Z','+00:00'))
        game_date=game_date.astimezone(ZoneInfo('America/New_York'))
        year=game_date.year if game_date.month>=7 else game_date.year-1
        phase='Playoffs' if data.get('header',{}).get('season',{}).get('type')==3 else 'Regular Season'
        source={'provider':'ESPN','url':f'https://www.espn.com/nba/game/_/gameId/{p.event_id}',
            'endpoint':'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary',
            'parameters':{'event':p.event_id},'fetched_at':datetime.now(timezone.utc).isoformat(),'stale':False}
        records=[]
        for own,opponent in ((participants[0],participants[1]),(participants[1],participants[0])):
            name=own['team']['displayName']
            inputs=_team_advanced_inputs(data,competition,name)
            opp_inputs=_team_advanced_inputs(data,competition,opponent['team']['displayName'])
            inputs.update({'OPP_'+k:v for k,v in opp_inputs.items()})
            metrics=calculate(inputs,TEAM_METRICS,'all')
            values={key.upper():dict(value,label=value.get('label',key),complete=value.get('value') is not None)
                    for key,value in metrics.items()}
            for key,value in inputs.items():
                if not key.startswith('OPP_'):
                    values[key]=metric(value,key,'game total','ESPN box score', {key:value})
            own_score=number(own.get('score'));opp_score=number(opponent.get('score'))
            values['POINT_MARGIN']=metric(own_score-opp_score if own_score is not None and opp_score is not None else None,
                'Team scoring margin','points','team score - opponent score')
            stats={r['name']:r.get('displayValue') for r in _team(data,competition,name,'teams').get('statistics',[])}
            for key,field in (('REB','totalRebounds'),('AST','assists'),('STL','steals'),('BLK','blocks')):
                if field in stats:values[key]=metric(number(stats[field]),key,'game total','ESPN box score')
            rec=self.add({'kind':'game_team','player_id':-int(own['team']['id']),'player_name':name,
                'scope':Scope(start=year,end=year,phase=phase,basis='totals').model_dump(),
                'context':{'team_name':name,'event_id':p.event_id,'sample':'single game'},
                'date':p.date or game_date.date().isoformat(),'values':values,'sources':[source],
                'limitations':['Single-game team box score, not season statistics or individual-player statistics.',
                    'Possessions and ratings are estimates; box-score differences alone do not prove why a team won.',
                    'Game data may be provisional until the provider marks the game completed.']})
            records.append(rec)
        comparison=self._comparison(records[0],records[1],list(records[0]['values']))
        return {'event_id':p.event_id,'teams':[compact(r) for r in records],
                'comparison':comparison,'source':source}

    def stints(self, pid, season=None, phase='Playoffs'):
        entry=self.career(pid)
        table='SeasonTotalsPostSeason' if phase=='Playoffs' else 'SeasonTotalsRegularSeason'
        rows=[r for r in entry['data'].get(table,[]) if r.get('TEAM_ID') and number(r.get('GP'))
              and (season is None or str(r.get('SEASON_ID'))==season_label(season))]
        return entry,rows

    def query_career_profile(self,p):
        entry=self.career(p.player_id)
        inventory=[]
        for r in entry['data'].get('SeasonTotalsRegularSeason',[]):
            inventory.append({'season':r['SEASON_ID'],'team_id':r.get('TEAM_ID'),
                'team':r.get('TEAM_ABBREVIATION'),'games':r.get('GP')})
        results=[]
        for phase in ('Regular Season','Playoffs'):
            for basis in ('per_game','totals'):
                record=self.query_evidence(Query(player_id=p.player_id,scope=Scope(phase=phase,basis=basis)))
                record=dict(record,values={k:v for k,v in record['values'].items() if k in METRICS})
                results.append(compact(record))
        honors=self.player_awards(PlayerAwards(player_id=p.player_id))
        return {'career':results,'honors':compact(honors),'season_inventory':inventory,
                'coverage':'All returned NBA seasons; ongoing seasons and the latest API retrieval are not a frozen career endpoint.'}

    def query_supporting_cast(self,p,prefer_roster=False):
        career,stints=self.stints(p.player_id,p.season,p.phase)
        team_ids=sorted({r['TEAM_ID'] for r in stints})
        if not team_ids:
            raise DataUnavailable('No verified participation in this season and phase.')
        if p.team_id is None and len(team_ids)>1:
            return {'status':'needs_team','teams':team_ids,'message':'Select a verified team stint.'}
        team=p.team_id or team_ids[0]
        if team not in team_ids:
            raise ValueError('Team is not a verified player stint.')
        sources=[provenance(career,p.player_id)]
        member_sources={}
        gaps=[]
        try:
            if prefer_roster:raise DataUnavailable('Use the independent roster/career source for this targeted check.')
            entry=self.data.fetch('team_players',team_id=team,season=season_label(p.season),
                season_type_all_star=p.phase,per_mode_detailed='Totals',measure_type_detailed_defense='Base')
            rows=entry['data'].get('PlayersSeasonTotals',[])
            sources.append(provenance(entry))
        except DataUnavailable:
            rows=[]
        fallback=not bool(rows)
        if fallback:
            roster=self.data.fetch('roster',team_id=team,season=season_label(p.season))
            sources.append(provenance(roster))
            members=roster['data'].get('CommonTeamRoster',[])
            if not members or any(r.get('TeamID')!=team for r in members):
                raise DataUnavailable('No verified historical roster returned.')
            def get_member(member):
                try:
                    e,rs=self.stints(member['PLAYER_ID'],p.season,p.phase)
                    rs=[r for r in rs if r.get('TEAM_ID')==team]
                    if len(rs)!=1:
                        raise DataUnavailable('No unique team/season participation row.')
                    return dict(rs[0],PLAYER_NAME=member['PLAYER']),provenance(e,member['PLAYER_ID']),None
                except DataUnavailable as exc:
                    return None,None,member['PLAYER']+': '+str(exc)
            with ThreadPoolExecutor(max_workers=4) as pool:
                fetched=list(pool.map(get_member,members))
            rows=[r for r,_,_ in fetched if r]
            member_sources={r['PLAYER_ID']:s for r,s,_ in fetched if r and s}
            sources += [s for _,s,_ in fetched if s]
            gaps += [g for _,_,g in fetched if g]
        if not any(r.get('PLAYER_ID')==p.player_id for r in rows):
            raise DataUnavailable('The focal player is absent from the retrieved team sample.')
        records=[]
        for r in rows:
            if not number(r.get('GP')) or r.get('PLAYER_ID')==p.player_id:
                continue
            vals=aggregate([dict(r,SEASON_ID=season_label(p.season))])
            rec=self.add({'kind':'supporting_cast','player_id':r['PLAYER_ID'],'player_name':r['PLAYER_NAME'],
                'scope':Scope(start=p.season,end=p.season,phase=p.phase).model_dump(),
                'context':{'team_id':team,'team_name':next((s.get('TEAM_ABBREVIATION',str(team)) for s in stints if s['TEAM_ID']==team),str(team)),'focal_player_id':p.player_id},
                'values':{k:v for k,v in vals.items() if k in METRICS},
                'total_minutes':number(r.get('MIN')),
                'sources':([member_sources[r['PLAYER_ID']],provenance(roster),provenance(career,p.player_id)] if fallback else sources),
                'limitations':[
                    'Team-season games and minutes do not establish shared court time or reasons for absences.',
                    *(['Historical roster snapshot plus exact team-specific career rows; midseason roster coverage may be incomplete.'] if fallback else [])]})
            records.append(rec)
            self.names[str(r['PLAYER_ID'])]=r['PLAYER_NAME']
        records.sort(key=lambda r:-(r['total_minutes'] or 0))
        core=sorted(records,key=lambda r:-(r['values']['PTS']['value'] or 0))[:3]
        return {'team_id':team,'season':season_label(p.season),'phase':p.phase,
            'core_candidates':[compact(r) for r in core],
            'rotation':[compact(r) for r in records[:8]],
            'selection_rule':'Core candidates are the top three non-focal scorers in this returned sample, not an overall ability ranking. Rotation is top eight non-focal players by total minutes. Explain the final helper selection using production, role, efficiency and availability.',
            'status':'partial' if gaps else 'completed','gaps':gaps}

    def league_games(self,season,phase):
        entry=self.data.fetch('league_games',season=season_label(season),
            season_type_all_star=phase,player_or_team_abbreviation='T')
        rows=entry['data'].get('LeagueGameLog',[])
        pairs={}
        for r in rows:
            ident=r.get('GAME_ID')
            if not ident or not r.get('TEAM_ID'):
                raise DataUnavailable('Game/team identifiers missing in league logs.')
            pairs.setdefault(ident,[]).append(r)
        if not pairs or any(len(rs)!=2 or len({r['TEAM_ID'] for r in rs})!=2 for rs in pairs.values()):
            raise DataUnavailable('League logs do not contain exactly two unique team rows per returned game.')
        return entry,rows,pairs

    def query_era_environment(self,p):
        entry,rows,pairs=self.league_games(p.season,p.phase)
        def total(key):
            values=[number(r.get(key)) for r in rows]
            return sum(values) if values and all(v is not None for v in values) else None
        totals={key:total(key) for key in ('PTS','FGA','FTA','FGM','FG3M','FG3A','FTM','OREB','TOV','MIN')}
        def ratio(numerator,denominator,scale=100):
            return scale*numerator/denominator if numerator is not None and denominator else None
        shooting=(totals['FGA']+.44*totals['FTA']) if all(totals[k] is not None for k in ('FGA','FTA')) else None
        possessions=(totals['FGA']+.44*totals['FTA']-totals['OREB']+totals['TOV']) if all(totals[k] is not None for k in ('FGA','FTA','OREB','TOV')) else None
        ts=ratio(totals['PTS'],2*shooting if shooting is not None else None)
        values={
            'LEAGUE_TEAM_PPG':metric(ratio(totals['PTS'],len(rows),1),'League team points per game','points/team game','sum(PTS) / paired team-game rows'),
            'LEAGUE_TS_PCT':metric(ts,'League true shooting','%','100 * sum(PTS) / (2 * (sum(FGA) + 0.44 * sum(FTA)))'),
            'EST_PACE':metric(ratio(possessions,totals['MIN'],240),'Estimated possessions per 48 minutes','estimated possessions/48 min','estimated possessions * 240 / sum(team player-minutes)'),
            'EST_OFF_RATING':metric(ratio(totals['PTS'],possessions),'Estimated league offensive rating','estimated points/100 possessions','100 * sum(PTS) / estimated possessions'),
            'LEAGUE_GAMES':metric(len(pairs),'Returned league games','games','unique paired game IDs'),
        }
        for code,made,attempted,label in (
            ('LEAGUE_FG_PCT','FGM','FGA','League field goal percentage'),
            ('LEAGUE_FG3_PCT','FG3M','FG3A','League three-point percentage'),
            ('LEAGUE_FT_PCT','FTM','FTA','League free throw percentage'),
            ('LEAGUE_3PAR','FG3A','FGA','League three-point attempt share')):
            values[code]=metric(ratio(totals[made],totals[attempted]),label,'%',f'100 * sum({made}) / sum({attempted})')
        for key in ('EST_PACE','EST_OFF_RATING'):values[key]['estimated']=True
        missing=[key for key,value in values.items() if value['value'] is None]
        record=self.add({'kind':'era_environment','player_id':p.player_id,
            'player_name':self.names.get(str(p.player_id),str(p.player_id)),
            'scope':Scope(start=p.season,end=p.season,phase=p.phase).model_dump(),
            'values':values,'sources':[provenance(entry)],'limitations':[
                'Coverage is the returned paired team-game dataset, not an independently certified complete schedule.',
                'Pace and offensive rating are labelled box-score estimates; missing inputs affect only the dependent metric.',
                'League PPG is a team average, not the mean player scoring average or an individual impact metric.',
                *(['Unavailable environment metrics: '+', '.join(missing)] if missing else [])]})
        player=self.query_evidence(Query(player_id=p.player_id,scope=Scope(start=p.season,end=p.season,phase=p.phase)))
        player_ts=player['values']['TS_PCT']['value']
        relative=self.add({'kind':'relative_efficiency','player_id':p.player_id,'player_name':player['player_name'],
            'scope':player['scope'],'values':{'REL_TS':metric(player_ts-ts if player_ts is not None and ts is not None else None,
                'Player true shooting above contemporaneous league','percentage points','player TS% - league TS%',{'player_ts':player_ts,'league_ts':ts})},
            'sources':player['sources']+record['sources'],'limitations':record['limitations']})
        return {'environment':compact(record),'player':compact(player),'relative_efficiency':compact(relative),
                'unavailable_metrics':missing}

    def query_finals_path(self,p):
        if p.season is not None and p.season>current_season():
            raise ValueError('Future seasons unavailable.')
        career,stints=self.stints(p.player_id,p.season)
        histories={}
        gaps=[]
        verified=[]
        for team in sorted({r['TEAM_ID'] for r in stints}):
            try:
                e=self.data.fetch('team_history',team_id=team,league_id='00',per_mode_simple='Totals')
                histories[team]=e
            except DataUnavailable as exc:
                gaps.append(str(team)+': '+str(exc))
        for stint in stints:
            year=stint['SEASON_ID']
            rows=histories.get(stint['TEAM_ID'],{}).get('data',{}).get('TeamStats',[])
            row=next((r for r in rows if r.get('YEAR')==year),None)
            if row is None:
                gaps.append(year+': team history unavailable')
            elif row.get('NBA_FINALS_APPEARANCE') in ('LEAGUE CHAMPION','FINALS APPEARANCE'):
                verified.append((stint,row))
        series=[]
        for stint,history in sorted(verified,key=lambda pair:pair[0]['SEASON_ID']):
            year=int(stint['SEASON_ID'][:4]);team=stint['TEAM_ID']
            try:
                entry,rows,pairs=self.league_games(year,'Playoffs')
                own=[r for r in rows if r['TEAM_ID']==team]
                if not own:
                    raise DataUnavailable('Finalist has no playoff game rows.')
                last=max(own,key=date_key)
                opponent=next(r for r in pairs[last['GAME_ID']] if r['TEAM_ID']!=team)
                opp_id=opponent['TEAM_ID']
                opp_history=self.data.fetch('team_history',team_id=opp_id,league_id='00',per_mode_simple='Totals')
                opp_season=next((r for r in opp_history['data'].get('TeamStats',[]) if r.get('YEAR')==stint['SEASON_ID']),None)
                if not opp_season or opp_season.get('NBA_FINALS_APPEARANCE') not in ('LEAGUE CHAMPION','FINALS APPEARANCE'):
                    raise DataUnavailable('Opponent could not be independently verified as a finalist.')
                selected=[r for r in own if {x['TEAM_ID'] for x in pairs[r['GAME_ID']]}=={team,opp_id}]
                ids={r['GAME_ID'] for r in selected}
                if not 4<=len(ids)<=7:
                    raise DataUnavailable('Finals series game count is incomplete or invalid.')
                game_entry=self.data.fetch('games',player_id=p.player_id,season=stint['SEASON_ID'],season_type_all_star='Playoffs')
                played=[dict(r,SEASON_ID=stint['SEASON_ID'],GP=1) for r in game_entry['data'].get('PlayerGameLog',[]) if r.get('Game_ID') in ids]
                if not played or len({r['Game_ID'] for r in played})!=len(played):
                    raise DataUnavailable('No unique verified player Finals appearances.')
                vals={k:v for k,v in aggregate(played).items() if k in METRICS}
                vals.update({
                    'SERIES_WINS':metric(sum(r['WL']=='W' for r in selected),'Team Finals wins','games','count(WL == W)'),
                    'SERIES_LOSSES':metric(sum(r['WL']=='L' for r in selected),'Team Finals losses','games','count(WL == L)'),
                    'OPP_REG_WINS':metric(number(opp_season.get('WINS')),'Opponent regular-season wins','wins','NBA team history WINS'),
                    'OPP_WIN_PCT':metric(100*number(opp_season['WIN_PCT']) if number(opp_season.get('WIN_PCT')) is not None else None,'Opponent regular-season win percentage','%','100 * NBA WIN_PCT'),
                })
                sources=[provenance(career,p.player_id),provenance(histories[team]),provenance(entry),provenance(opp_history),provenance(game_entry,p.player_id)]
                rec=self.add({'kind':'finals_series','player_id':p.player_id,
                    'player_name':self.names.get(str(p.player_id),str(p.player_id)),
                    'scope':Scope(start=year,end=year,phase='Playoffs').model_dump(),
                    'context':{'team_id':team,'team_name':last['TEAM_NAME'],'opponent_id':opp_id,'opponent_name':opponent['TEAM_NAME'],'series':'NBA Finals'},
                    'game_ids':sorted(ids),'values':vals,'sources':sources,'limitations':[
                        'Player metrics cover only the verified Finals games; this record is narrower than the Playoffs phase label.',
                        'Opponent regular-season record is context, not a causal measure of Finals difficulty or a complete strength ranking.']})
                series.append(compact(rec))
            except DataUnavailable as exc:
                gaps.append(stint['SEASON_ID']+': '+str(exc))
        return {'series':series,'verified_finalist_seasons':[s['SEASON_ID'] for s,_ in verified],
            'status':'partial' if gaps else 'completed','gaps':gaps,
            'coverage':'All returned NBA playoff team stints were checked against team-history Finals labels. Both wins and defeats included. Series player participation is checked separately; unverified series remain gaps.'}
