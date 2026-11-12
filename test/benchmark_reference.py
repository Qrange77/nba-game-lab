"""Independent reference arithmetic over archived, unmodified NBA resultSets.

Only the transport is shared with production. No production scoring, aggregation,
contract or answer is used to construct the reference.
"""
import gzip
import hashlib
import json
from pathlib import Path


def digest(value):
    return hashlib.sha256(value).hexdigest()


def tables(entry):
    return {s['name']: [dict(zip(s['headers'], row)) for row in s['rowSet']]
            for s in entry['raw']['resultSets']}


def select_rows(rows, start, end):
    seasons = {}
    for row in rows:
        if start <= int(row['SEASON_ID'][:4]) <= end and str(row.get('LEAGUE_ID', '00')) == '00' and row['GP']:
            seasons.setdefault(row['SEASON_ID'], []).append(row)
    selected = []
    for season, stints in sorted(seasons.items()):
        totals = [r for r in stints if r['TEAM_ID'] == 0 or r.get('TEAM_ABBREVIATION') == 'TOT']
        if len(totals) > 1:
            raise ValueError(f'Duplicate season totals: {season}')
        if totals:
            selected.append(totals[0])
        elif len(stints) == 1:
            selected.append(stints[0])
        else:
            combined = dict(stints[0])
            for key in ('GP', 'PTS', 'FGA', 'FTA'):
                combined[key] = sum(r[key] for r in stints)
            selected.append(combined)
    if not selected:
        raise ValueError('No source rows in the requested window')
    return selected


def aggregate(rows):
    points, games, attempts, free = (sum(r[k] for r in rows) for k in ('PTS', 'GP', 'FGA', 'FTA'))
    return {'PTS': points, 'PPG': points / games, 'TS': 100 * points / (2 * (attempts + .44 * free))}


class Sources:
    def __init__(self, folder, data):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.data = data
        self.index = {}

    def get(self, kind, **params):
        key = json.dumps([kind, params], sort_keys=True)
        name = digest(key.encode()) + '.json.gz'
        path = self.folder / name
        if not path.exists():
            entry = self.data.fetch(kind, **params)
            blob = json.dumps(entry, sort_keys=True).encode()
            path.write_bytes(gzip.compress(blob, mtime=0))
        else:
            blob = gzip.decompress(path.read_bytes())
        entry = json.loads(blob)
        self.index[key] = {'file': 'sources/' + name, 'sha256': digest(path.read_bytes()),
                           'source_url': entry.get('source_url'), 'parameters': entry.get('parameters'),
                           'fetched_at': entry.get('fetched_at'), 'stale': entry.get('stale', False)}
        return tables(entry)


def build_reference(case, sources):
    facts = []
    for window in case['windows']:
        career = sources.get('career', player_id=window['player_id'], per_mode36='Totals', league_id_nullable='00')
        values = {}
        for phase in case['phases']:
            table = 'SeasonTotalsRegularSeason' if phase == 'Regular Season' else 'SeasonTotalsPostSeason'
            rows = select_rows(career[table], window['start'], window['end'])
            computed = aggregate(rows)
            if case['id'] in ('career', 'windows', 'new_efficiency'):
                weighted = weight_sum = 0
                for row in rows:
                    league = sources.get('league_games', season=row['SEASON_ID'], season_type_all_star=phase,
                                         player_or_team_abbreviation='T')['LeagueGameLog']
                    if not league or len(league) != len({(r['GAME_ID'], r['TEAM_ID']) for r in league}):
                        raise ValueError('Missing or duplicate league team-game rows')
                    points, shots, free = (sum(r[k] for r in league) for k in ('PTS', 'FGA', 'FTA'))
                    league_ts = 100 * points / (2 * (shots + .44 * free))
                    weight = row['FGA'] + .44 * row['FTA']
                    weighted += (100 * row['PTS'] / (2 * weight) - league_ts) * weight
                    weight_sum += weight
                computed['RTS'] = weighted / weight_sum
            values[phase] = computed
            for metric, value in computed.items():
                facts.append(fact(window, phase, metric, value, metric in case['required_metrics'],
                                  [r['SEASON_ID'] for r in rows], case['relative_method_required']))
        if case['phase_changes']:
            for metric in ('PPG', 'TS'):
                facts.append(fact(window, 'Playoffs minus Regular Season', metric + '_CHANGE',
                                  values['Playoffs'][metric] - values['Regular Season'][metric], True,
                                  [], False))
    return {'case': case['id'], 'facts': facts, 'status': 'available'}


def fact(window, phase, metric, value, required, seasons, relative_required):
    ident = f"{window['player_id']}:{phase}:{metric}"
    return {'id': ident, **window, 'phase': phase, 'metric': metric, 'value': value,
            'required': required, 'seasons': seasons,
            'method': 'attempt-weighted player-minus-same-phase-league TS' if metric == 'RTS' else 'aggregate source totals',
            'method_required': metric != 'RTS' or relative_required,
            'tolerance': 1 if metric == 'PTS' else .2,
            'unit': 'points' if metric == 'PTS' else 'points per game' if metric.startswith('PPG') else 'percentage points'}
