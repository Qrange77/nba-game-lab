"""Independent context audit using original NBA resultSets, never production math.

Archive the exact inputs so the audit can be reproduced without the local cache.
This verifies every returned context row in the chosen runs, not every NBA season.
"""
import argparse
import gzip
import hashlib
import json
import math
import re
import sqlite3
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

ROOT = Path(__file__).resolve().parents[1]
ENDPOINTS = {'career': 'playercareerstats', 'team_players': 'teamplayerdashboard',
             'roster': 'commonteamroster', 'team_history': 'teamyearbyyearstats',
             'league_games': 'leaguegamelog', 'games': 'playergamelog'}
BASE = ('GP', 'MIN', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV')


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def label(year):
    return f'{year}-{(year + 1) % 100:02d}'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source_key(kind, params):
    return json.dumps([kind, params], sort_keys=True)


def raw_table(entry, name):
    tables = [r for r in entry['raw']['resultSets'] if r['name'] == name]
    require(len(tables) == 1, 'Missing or ambiguous original table: '+name)
    return [dict(zip(tables[0]['headers'], row, strict=True)) for row in tables[0]['rowSet']]


class Sources:
    def __init__(self, folder, cache=None):
        self.folder = Path(folder)
        self.cache = cache
        self.index = {} if cache else json.loads((self.folder / 'sources.json').read_text())

    def get(self, kind, **params):
        key = source_key(kind, params)
        if self.cache:
            with sqlite3.connect(f'file:{self.cache}?mode=ro', uri=True) as db:
                found = db.execute('SELECT body FROM responses WHERE key=?', (key,)).fetchone()
            require(found is not None, 'No original response for '+key)
            entry = json.loads(found[0])
            # Deliberately exclude the normalized tables consumed by production.
            entry = {k: v for k, v in entry.items() if k != 'data'}
            data = json.dumps(entry, sort_keys=True).encode()
            filename = 'sources/'+digest(data)+'.json.gz'
            target = self.folder / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(gzip.compress(data, mtime=0))
            self.index[key] = {'file': filename, 'sha256': digest(data), 'fetched_at': entry['fetched_at'],
                               'parameters': params, 'endpoint': entry['source_url'], 'stale': entry['stale']}
        else:
            require(key in self.index, 'Unarchived source: '+key)
            item = self.index[key]
            data = gzip.decompress((self.folder / item['file']).read_bytes())
            require(digest(data) == item['sha256'], 'Original response hash changed')
            entry = json.loads(data)
        return entry

    def cited(self, record, kind, **filters):
        sources = [s for s in record['sources'] if s.get('endpoint', '').endswith('/'+ENDPOINTS[kind])
                   and all(s['parameters'].get(k) == v for k, v in filters.items())]
        require(len(sources) == 1, 'Missing/ambiguous source citation for '+kind)
        entry = self.get(kind, **sources[0]['parameters'])
        require(entry['fetched_at'] == sources[0]['fetched_at'], 'Source version differs from cited response')
        return entry


def career(sources, pid):
    return sources.get('career', player_id=pid, per_mode36='Totals', league_id_nullable='00')


def history(sources, tid, season):
    entry = sources.get('team_history', team_id=tid, league_id='00', per_mode_simple='Totals')
    rows = [r for r in raw_table(entry, 'TeamStats') if r['YEAR'] == label(season)]
    require(len(rows) == 1, 'Team/season history is not unique')
    return rows[0]


def metrics(rows):
    """Direct arithmetic from raw counts; null inputs stay unavailable."""
    totals = {key: sum(float(r[key]) for r in rows) if rows and all(r.get(key) is not None for r in rows) else None
              for key in (*BASE, 'FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA')}
    gp = totals['GP']
    values = {key: totals[key] if key == 'GP' else totals[key] / gp if totals[key] is not None and gp else None
              for key in BASE}
    for metric, numerator, denominator in (
        ('FG_PCT', ('FGM',), ('FGA',)), ('FG3_PCT', ('FG3M',), ('FG3A',)),
        ('FT_PCT', ('FTM',), ('FTA',)), ('TS_PCT', ('PTS',), ('FGA', 'FTA')),
        ('EFG_PCT', ('FGM', 'FG3M'), ('FGA',)),
    ):
        if any(totals[k] is None for k in (*numerator, *denominator)):
            values[metric] = None
            continue
        n = totals[numerator[0]] + (.5 * totals['FG3M'] if metric == 'EFG_PCT' else 0)
        d = 2 * (totals['FGA'] + .44 * totals['FTA']) if metric == 'TS_PCT' else totals[denominator[0]]
        values[metric] = 100 * n / d if d else None
    return values


def check_values(record, expected):
    require(set(record['values']) == set(expected), 'Unexpected/missing context metrics: '+record['id'])
    for key, value in expected.items():
        actual = record['values'][key]['value']
        require((actual is None and value is None) or
                (actual is not None and value is not None and math.isclose(actual, value, rel_tol=1e-10, abs_tol=1e-9)),
                f"{record['id']} {key}: {actual} != {value}")
        require(record['values'][key]['complete'] == (value is not None), 'Incorrect completeness flag: '+key)
    return len(expected)


def stint_rows(entry, phase, year, team=None):
    table = 'SeasonTotalsPostSeason' if phase == 'Playoffs' else 'SeasonTotalsRegularSeason'
    return [r for r in raw_table(entry, table) if r['SEASON_ID'] == label(year) and r.get('GP', 0) > 0
            and r.get('LEAGUE_ID', '00') == '00' and r.get('TEAM_ID', 0) > 0
            and (team is None or r['TEAM_ID'] == team)]


def helper_rows(record, sources):
    team = record['context']['team_id']
    year, phase = record['scope']['start'], record['scope']['phase']
    focal = record['context']['focal_player_id']
    require(record['scope']['end'] == year and record['scope']['basis'] == 'per_game', 'Wrong helper scope')
    require(len(stint_rows(sources.cited(record, 'career', player_id=focal), phase, year, team)) == 1,
            'Focal player did not participate for the cited team and phase')
    if any(s.get('endpoint', '').endswith('/teamplayerdashboard') for s in record['sources']):
        entry = sources.cited(record, 'team_players', team_id=team, season=label(year), season_type_all_star=phase)
        rows = raw_table(entry, 'PlayersSeasonTotals')
        require(all(r.get('TEAM_ID', team) == team for r in rows), 'Dashboard contains a different team')
    else:
        roster = sources.cited(record, 'roster', team_id=team, season=label(year))
        members = raw_table(roster, 'CommonTeamRoster')
        require(all(r['TeamID'] == team for r in members), 'Wrong roster team')
        rows = []
        for member in members:
            matching = stint_rows(career(sources, member['PLAYER_ID']), phase, year, team)
            require(len(matching) <= 1, 'Duplicate team-specific career rows')
            if matching:
                rows.append(dict(matching[0], PLAYER_NAME=member['PLAYER']))
        sources.cited(record, 'career', player_id=record['player_id'])
    eligible = [r for r in rows if r.get('GP', 0) > 0 and r['PLAYER_ID'] != focal]
    require(len({r['PLAYER_ID'] for r in eligible}) == len(eligible), 'Duplicate helper identity')
    return eligible


def bounds(contract, pid):
    if contract['period'] == 'career':
        return 1984, contract['cutoff']
    side = 'left' if pid == contract['left_player'] else 'right'
    return contract[side+'_start'], contract[side+'_end']


def expected_finals(contract, pid, sources):
    lo, hi = bounds(contract, pid)
    rows = raw_table(career(sources, pid), 'SeasonTotalsPostSeason')
    found = set()
    for row in rows:
        year, team = int(row['SEASON_ID'][:4]), row['TEAM_ID']
        if lo <= year <= hi and team and row.get('GP', 0) > 0 and row.get('LEAGUE_ID', '00') == '00':
            if history(sources, team, year)['NBA_FINALS_APPEARANCE'] in ('LEAGUE CHAMPION', 'FINALS APPEARANCE'):
                found.add((year, team))
    return found


def audit_final(record, sources):
    pid, context, scope = record['player_id'], record['context'], record['scope']
    year, team, opp = scope['start'], context['team_id'], context['opponent_id']
    require(scope == {'start': year, 'end': year, 'phase': 'Playoffs', 'basis': 'per_game'}, 'Wrong Finals scope')
    require(context['series'] == 'NBA Finals' and team != opp, 'Invalid Finals identities')
    require(len(stint_rows(sources.cited(record, 'career', player_id=pid), 'Playoffs', year, team)) == 1,
            'Finals team is not a recorded playoff stint')
    own_entry = sources.cited(record, 'team_history', team_id=team)
    opp_entry = sources.cited(record, 'team_history', team_id=opp)
    own = next(r for r in raw_table(own_entry, 'TeamStats') if r['YEAR'] == label(year))
    opponent = next(r for r in raw_table(opp_entry, 'TeamStats') if r['YEAR'] == label(year))
    require({own['NBA_FINALS_APPEARANCE'], opponent['NBA_FINALS_APPEARANCE']} ==
            {'LEAGUE CHAMPION', 'FINALS APPEARANCE'}, 'Both teams must be opposite finalists')
    entry = sources.cited(record, 'league_games', season=label(year), season_type_all_star='Playoffs')
    games = raw_table(entry, 'LeagueGameLog')
    pairs = {}
    for row in games:
        pairs.setdefault(row['GAME_ID'], []).append(row)
    selected = [rs for rs in pairs.values() if {r['TEAM_ID'] for r in rs} == {team, opp}]
    require(4 <= len(selected) <= 7 and all(len(rs) == 2 for rs in selected), 'Invalid Finals schedule')
    ids = {rs[0]['GAME_ID'] for rs in selected}
    require(sorted(ids) == record['game_ids'], 'Wrong/incomplete Finals game IDs')
    own_games = [next(r for r in rs if r['TEAM_ID'] == team) for rs in selected]
    opp_games = [next(r for r in rs if r['TEAM_ID'] == opp) for rs in selected]
    for rs in selected:
        require({r['WL'] for r in rs} == {'W', 'L'}, 'Game results do not agree')
    require({r['TEAM_NAME'] for r in own_games} == {context['team_name']} and
            {r['TEAM_NAME'] for r in opp_games} == {context['opponent_name']}, 'Wrong displayed team/opponent name')
    wins = sum(r['WL'] == 'W' for r in own_games)
    losses = len(own_games) - wins
    require((wins == 4 and losses < 4) if own['NBA_FINALS_APPEARANCE'] == 'LEAGUE CHAMPION'
            else (losses == 4 and wins < 4), 'Series result disagrees with championship record')
    log = sources.cited(record, 'games', player_id=pid, season=label(year), season_type_all_star='Playoffs')
    played = [dict(r, GP=1) for r in raw_table(log, 'PlayerGameLog') if r['Game_ID'] in ids]
    require(played and len({r['Game_ID'] for r in played}) == len(played), 'Duplicate/missing player Finals appearances')
    expected = metrics(played)
    expected.update(SERIES_WINS=wins, SERIES_LOSSES=losses, OPP_REG_WINS=opponent['WINS'],
                    OPP_WIN_PCT=100 * opponent['WIN_PCT'])
    require(abs(opponent['WIN_PCT'] - opponent['WINS'] / (opponent['WINS'] + opponent['LOSSES'])) <= .00051,
            'Opponent official win percentage disagrees with W/L beyond rounding')
    return check_values(record, expected)


def check_report(case, samples, finals):
    """Check every context table row and the exact raw-source links in the export."""
    evidence = case['evidence']
    names = {r['player_id']: r['player_name'] for r in finals}
    for sample in samples:
        names[sample['player_id']] = sample['player_name']
    helper_expected = {}
    for sample in samples:
        for ident in sample['core']:
            record = evidence[ident]
            helper_expected[(names[sample['player_id']]+' / '+label(sample['season'])+' / '+sample['phase'],
                             record['player_name'])] = record
    final_expected = {(r['player_name'], label(r['scope']['start']), r['context']['opponent_name']): r for r in finals}
    helpers_seen, finals_seen, numeric = set(), set(), 0

    def number(cell, value):
        require(cell == 'Unavailable' if value is None else abs(float(cell.replace(',', '')) - value) <= .00501,
                'Published context number differs from the source-derived value: '+cell)

    def citations(cell, record):
        links = [urlsplit(url) for url in re.findall(r'\]\(([^)]+)\)', cell)]
        for source in record['sources']:
            endpoint = urlsplit(source['endpoint'])
            params = source.get('request_parameters', {})
            require(any(link.netloc == endpoint.netloc and link.path == endpoint.path and
                        all(parse_qs(link.query, keep_blank_values=True).get(k) == [str(v)] for k, v in params.items()) for link in links),
                    'Export omits an underlying source citation: '+source['endpoint'])

    for line in case['response'].splitlines():
        if not line.startswith('|'):
            continue
        cells = [p.strip() for p in line.strip('|').split('|')]
        if len(cells) == 7 and tuple(cells[:2]) in helper_expected:
            key = tuple(cells[:2])
            require(key not in helpers_seen, 'Duplicate published helper row')
            helpers_seen.add(key)
            record = helper_expected[key]
            for cell, metric in zip(cells[2:6], ('PTS', 'MIN', 'GP', 'TS_PCT'), strict=True):
                number(cell, record['values'][metric]['value'])
                numeric += 1
            citations(cells[6], record)
        if len(cells) == 8 and tuple(cells[:3]) in final_expected:
            key = tuple(cells[:3])
            require(key not in finals_seen, 'Duplicate published Finals row')
            finals_seen.add(key)
            record = final_expected[key]
            series = cells[3].split('\u2013')
            require(len(series) == 2, 'Wrong published series result')
            for cell, metric in zip(series + cells[4:7], ('SERIES_WINS', 'SERIES_LOSSES', 'PTS', 'TS_PCT', 'OPP_WIN_PCT'), strict=True):
                number(cell, record['values'][metric]['value'])
                numeric += 1
            citations(cells[7], record)
    require(helpers_seen == set(helper_expected), 'Missing published core helper rows')
    require(finals_seen == set(final_expected), 'Missing published Finals rows')
    return numeric


def audit_case(case, sources):
    evidence = case['evidence']
    scoring = case['evidence_result']['scoring']
    contract = scoring['contract']
    helpers = [r for r in evidence.values() if r['kind'] == 'supporting_cast']
    finals = [r for r in evidence.values() if r['kind'] == 'finals_series']
    samples = scoring['support_samples']
    checked, groups = 0, {}
    for record in helpers:
        c, scope = record['context'], record['scope']
        pid = c['focal_player_id']
        lo, hi = bounds(contract, pid)
        require(pid in (contract['left_player'], contract['right_player']) and lo <= scope['start'] <= hi,
                'Helper is outside the comparison')
        require(scope['phase'] in (contract['support_phases'] or contract['phases']), 'Unapproved helper phase')
        sources.cited(record, 'career', player_id=pid)
        if any(s.get('endpoint', '').endswith('/teamplayerdashboard') for s in record['sources']):
            sources.cited(record, 'team_players', team_id=c['team_id'], season=label(scope['start']),
                          season_type_all_star=scope['phase'])
        else:
            sources.cited(record, 'career', player_id=record['player_id'])
            sources.cited(record, 'roster', team_id=c['team_id'], season=label(scope['start']))
        key = pid, scope['start'], scope['phase'], c['team_id']
        if key not in groups:
            groups[key] = helper_rows(record, sources)
        raw = [r for r in groups[key] if r['PLAYER_ID'] == record['player_id']]
        require(len(raw) == 1 and raw[0]['PLAYER_NAME'] == record['player_name'], 'Wrong helper identity/name')
        checked += check_values(record, metrics(raw))
        require(record['total_minutes'] == raw[0]['MIN'], 'Wrong total minutes used for rotation order')
    for (pid, year, phase, team), rows in groups.items():
        got = {r['player_id'] for r in helpers if r['context']['focal_player_id'] == pid and
               r['scope']['start'] == year and r['scope']['phase'] == phase and r['context']['team_id'] == team}
        require(got == {r['PLAYER_ID'] for r in rows}, 'Returned helper ledger omits or adds source participants')
    for sample in samples:
        pid, year, phase = sample['player_id'], sample['season'], sample['phase']
        require(sample['core'] and sample['rotation'], 'Empty helper selection')
        team = evidence[sample['core'][0]]['context']['team_id']
        rows = groups[pid, year, phase, team]
        by_minutes = sorted(rows, key=lambda r: -r['MIN'])
        core = sorted(by_minutes, key=lambda r: -r['PTS'] / r['GP'])[:2]
        require([evidence[i]['player_id'] for i in sample['core']] == [r['PLAYER_ID'] for r in core], 'Wrong core selection')
        require([evidence[i]['player_id'] for i in sample['rotation']] == [r['PLAYER_ID'] for r in by_minutes[:8]], 'Wrong rotation selection')
        require([r['id'] for r in sample['rotation_records']] == sample['rotation'], 'Public rotation is incomplete')
        for record in sample['rotation_records']:
            original = evidence[record['id']]
            require(all(record[k] == original[k] for k in ('player_id', 'player_name', 'scope', 'context')) and
                    set(record['values']) == set(original['values']) and all(
                        record['values'][k].get(field) == original['values'][k].get(field)
                        for k in record['values'] for field in ('value', 'unit', 'complete', 'formula')),
                    'Public rotation differs from the audited ledger')
    for pid in (contract['left_player'], contract['right_player']):
        expected = expected_finals(contract, pid, sources)
        actual = {(r['scope']['start'], r['context']['team_id']) for r in finals if r['player_id'] == pid}
        require(actual == expected, 'Missing/extra Finals appearances, including defeats')
        original = [s for s in samples if s['player_id'] == pid and not s.get('followup')]
        years = sorted(y for y, _ in expected)
        if not years:
            lo, hi = bounds(contract, pid)
            years = sorted({int(r['SEASON_ID'][:4]) for r in raw_table(career(sources, pid), 'SeasonTotalsPostSeason')
                            if lo <= int(r['SEASON_ID'][:4]) <= hi and r.get('GP', 0) > 0})
        require(sorted(s['season'] for s in original) == sorted(set(years[:1] + years[-1:])), 'Wrong helper anchor seasons')
    final_checks = sum(audit_final(r, sources) for r in finals)
    report_checks = check_report(case, samples, finals)
    results = Counter('win' if r['values']['SERIES_WINS']['value'] == 4 else 'defeat' for r in finals)
    return {'id': case['id'], 'helper_records': len(helpers), 'helper_samples': len(samples),
            'helper_numeric_checks': checked, 'finals_series': len(finals), 'finals_numeric_checks': final_checks,
            'published_context_numeric_checks': report_checks, 'export_citations_checked': True,
            'finals_results': dict(results), 'all_returned_context_metrics_checked': True,
            'source_membership_selection_scope_and_finals_completeness_checked': True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder', default='docs/context-review')
    parser.add_argument('--capture', nargs='+', help='Full run artifacts to audit and archive')
    args = parser.parse_args()
    folder = ROOT / args.folder
    folder.mkdir(parents=True, exist_ok=True)
    sources = Sources(folder, ROOT / 'data_cache/nba.sqlite3' if args.capture else None)
    cases = [json.loads((ROOT / p).read_text()) for p in args.capture] if args.capture else json.loads((folder / 'cases.json').read_text())
    results = [audit_case(case, sources) for case in cases]
    if args.capture:
        subset = [{**{k: case[k] for k in ('id', 'question', 'response')},
                   'evidence': {k: r for k, r in case['evidence'].items() if r['kind'] in ('supporting_cast', 'finals_series')},
                   'evidence_result': {'scoring': {k: case['evidence_result']['scoring'][k] for k in ('contract', 'support_samples')}}}
                  for case in cases]
        (folder / 'cases.json').write_text(json.dumps(subset, indent=2)+'\n')
        (folder / 'sources.json').write_text(json.dumps(sources.index, indent=2, sort_keys=True)+'\n')
        lock = {p.name: digest(p.read_bytes()) for p in (folder / 'cases.json', folder / 'sources.json')}
        (folder / 'integrity.json').write_text(json.dumps(lock, indent=2)+'\n')
    else:
        lock = json.loads((folder / 'integrity.json').read_text())
        for name, sha in lock.items():
            require(digest((folder / name).read_bytes()) == sha, 'Archived case/source index changed: '+name)
    report = {'status': 'passed', 'cases': results, 'original_responses': len(sources.index),
              'limits': 'All returned context rows in these runs; not all historical rosters, arbitrary questions, injury/causal explanations or a ranking of opponent difficulty.'}
    if args.capture:
        (folder / 'results.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
