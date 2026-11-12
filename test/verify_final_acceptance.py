"""Audit fresh local runs against original-source references and actual traces.

This is targeted course acceptance, not a grading prediction or a new raw benchmark.
"""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from test.context_audit import Sources, audit_case
from test.paired_benchmark import check_sources
from test.verify_flow_acceptance import inspect
from test.benchmark_reference import select_rows, tables

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / 'docs/benchmark/2026-11-11-frozen'


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def numeric_case(result, case, reference):
    scoring = result['evidence_result']['scoring']
    contract = scoring['contract']
    targets = {(f['player_id'], f['phase'], f['metric']): f['value'] for f in reference['facts']}
    # The frozen postseason rubric did not require relative TS. Independently
    # recompute those extra rendered rows instead of assuming they were audited.
    index = json.loads((FROZEN / 'sources.json').read_text())
    def original(kind, **params):
        item = index[json.dumps([kind, params], sort_keys=True)]
        return tables(json.loads(gzip.decompress((FROZEN / item['file']).read_bytes())))
    for window in case['windows']:
        pid = window['player_id']
        for phase in case['phases']:
            if (pid, phase, 'RTS') in targets or not any(r['metric'] == 'WEIGHTED_RTS' for r in scoring['matrix']):
                continue
            source = original('career', player_id=pid, per_mode36='Totals', league_id_nullable='00')
            rows = select_rows(source['SeasonTotalsRegularSeason' if phase == 'Regular Season' else 'SeasonTotalsPostSeason'],
                               window['start'], window['end'])
            weighted = opportunities = 0
            for row in rows:
                league = original('league_games', season=row['SEASON_ID'], season_type_all_star=phase,
                                  player_or_team_abbreviation='T')['LeagueGameLog']
                pts, fga, fta = (sum(r[k] for r in league) for k in ('PTS', 'FGA', 'FTA'))
                weight = row['FGA'] + .44 * row['FTA']
                weighted += (100 * row['PTS'] / (2 * weight) - 100 * pts / (2 * (fga + .44 * fta))) * weight
                opportunities += weight
            targets[pid, phase, 'RTS'] = weighted / opportunities
    require(set(contract['phases']) == set(case['phases']), 'Wrong phase selection')
    for side, window in zip(('left', 'right'), case['windows'], strict=True):
        require(contract[side+'_player'] == window['player_id'], 'Wrong comparison subject/order')
        if case['id'] != 'career':
            require((contract[side+'_start'], contract[side+'_end']) == (window['start'], window['end']), 'Wrong explicit window')
    if case['id'] == 'career':
        require(contract['period'] == 'career' and contract['cutoff'] == 2025, 'Wrong career cutoff')
    checked = 0
    for row in scoring['matrix']:
        require(row['complete'], 'Incomplete required comparison')
        metric = {('PTS', 'totals'): 'PTS', ('PTS', 'per_game'): 'PPG',
                  ('TS_PCT', 'per_game'): 'TS', ('WEIGHTED_RTS', 'per_game'): 'RTS'}[row['metric'], row['basis']]
        for side in ('left', 'right'):
            pid = contract[side+'_player']
            wanted = targets[pid, row['phase'], metric]
            require(math.isclose(row[side], wanted, rel_tol=1e-10, abs_tol=1e-8), 'Source-reference mismatch')
            record = result['evidence'][row[side+'_id']]
            require(record['player_id'] == pid and record['scope']['phase'] == row['phase'], 'Wrong source identity/phase')
            checked += 1
        direction = 'tie' if math.isclose(row['left'], row['right'], abs_tol=1e-9) else 'left' if row['left'] > row['right'] else 'right'
        require(row['direction'] == direction, 'Wrong comparison direction')
    changes = 0
    if case['phase_changes']:
        records = [r for r in result['evidence'].values() if r['kind'] == 'scoring_change']
        require(len(records) == 2, 'Missing phase-change records')
        for record in records:
            for actual, expected in (('PTS_CHANGE', 'PPG_CHANGE'), ('TS_PCT_CHANGE', 'TS_CHANGE')):
                target = targets[record['player_id'], 'Playoffs minus Regular Season', expected]
                require(math.isclose(record['values'][actual]['value'], target, abs_tol=1e-8), 'Wrong postseason change')
                changes += 1
    expected_verdict = 'comparison' if case['cohort'] == 'additional_frozen' else 'conditional'
    require(scoring['verdict'] == expected_verdict, 'Wrong claim/comparison framing or unqualified overall conclusion')
    return {'case': case['id'], 'numeric_matrix_checks': checked, 'phase_change_checks': changes,
            'scope_matches_original_question': True, 'seconds': result['seconds']}


def workflow(result):
    flow = result['research_flow']
    initial = [n for n in flow['nodes'] if n['role'] == 'researcher' and n['round'] == 1]
    overlap = min(n['ended_ms'] for n in initial) - max(n['started_ms'] for n in initial)
    require(overlap > 0 and flow['peak_parallel'] == 4 and len(initial) == 4, 'No measured first-round parallelism')
    plans = [json.loads(c['result']) for c in result['tool_calls'] if c['name'] == 'plan_research']
    require(len(plans) == 1 and len(plans[0]['tasks']) == 4, 'Initial fan-out was not one Lead decision')
    tasks = result['evidence_result']['research']['tasks']
    require(len(tasks) == 5 and sum(t['round'] == 2 for t in tasks) == 1, 'Unexpected follow-up dispatch')
    contexts = result['researcher_initial_contexts']
    require(len(contexts) == len(tasks), 'Missing researcher context observations')
    fields = ['confirmed_players', 'contract', 'evidence_gap', 'original_evidence', 'required_collector', 'task']
    for context in contexts:
        require(context['initial_messages'] == 2 and context['roles'] == ['system', 'user'], 'Researcher inherited a conversation')
        require(context['payload_fields'] == fields, 'Unexpected cross-researcher context')
        if not context['gap_id']:
            require(not context['original_evidence_ids'], 'Initial researcher inherited another result')
        else:
            require(context['dimension'] == 'teammates' and context['original_evidence_ids'], 'Follow-up lacks targeted evidence')
    checks = result['evidence_result']['research']['content_checks']
    require(len(checks) == 1 and checks[0]['kind'] == 'sparse_helper_sample' and checks[0]['status'] == 'completed', 'Missing real content-gap review')
    require(not result['controlled_gap_injected'], 'Content example must not inject a fault')
    require(all(t['round'] <= 3 for t in tasks) and len(tasks) <= 8 and result['seconds'] < 240, 'Research budget exceeded')
    return {'single_decision_fan_out': 4, 'measured_overlap_ms': overlap, 'fresh_contexts_observed': len(contexts),
            'content_driven_rounds': 2, 'targeted_followups': 1, 'fault_injected': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', default='docs/final-local-acceptance/runs')
    parser.add_argument('--output', default='docs/final-local-acceptance/results.json')
    args = parser.parse_args()
    folder = ROOT / args.input_dir
    check_sources(FROZEN)
    cases = json.loads((ROOT / 'test/benchmark_cases.json').read_text())[:3]
    references = {r['case']: r for r in json.loads((FROZEN / 'reference.json').read_text())}
    numeric = [numeric_case(inspect(folder / (c['id']+'.json')), c, references[c['id']]) for c in cases]
    extra = []
    all_cases = json.loads((ROOT / 'test/benchmark_cases.json').read_text())
    for name in ('new_volume', 'new_efficiency'):
        case = next(c for c in all_cases if c['id'] == name)
        result = json.loads((folder / (name+'.json')).read_text())
        checked = numeric_case(result, case, references[name])
        require(result['evidence_result']['scoring']['contract']['request_kind'] == 'comparison', 'Invented directional claim')
        require(result['api_checks'] == {'chat_status': 200, 'project1_required_response_fields_preserved': True,
                'own_evidence_status': 200, 'other_browser_evidence_status': 404}, 'API/evidence access failed')
        excluded = ('Raw true shooting', 'Contemporaneous relative true shooting') if name == 'new_volume' else ('Accumulated points', 'Points per game')
        require(not any(text in result['response'] for text in excluded), 'Answer exceeded requested metric lens')
        extra.append({**checked, 'narrow_answer_focus': True, 'neutral_framing': True, 'live_api_and_owned_citations': True})
    support = inspect(folder / 'support_findings.json')
    trace = workflow(support)
    sources = Sources(ROOT / 'docs/context-review')
    contexts = [audit_case(json.loads((folder / (name+'.json')).read_text()), sources) for name in ('career', 'support_findings')]
    boundaries = []
    for name, expected in (('vague', 'clarify'), ('outside_scope', 'outside_scope'), ('early_era', 'unsupported_era'), ('causal', 'causal_limit')):
        result = json.loads((folder / (name+'.json')).read_text())
        contract = json.loads(next(c['result'] for c in result['tool_calls'] if c['name'] == 'confirm_scoring_contract'))
        require(contract['action'] == expected and not result['evidence'], 'Wrong scope boundary')
        require(not any(c['name'].startswith('collect_') for c in result['tool_calls']), 'Boundary triggered statistical collection')
        boundaries.append({'case': name, 'action': expected, 'statistical_collection_calls': 0})
    unavailable = json.loads((folder / 'controlled_source_unavailable.json').read_text())
    require(unavailable['controlled_fault'] and all(unavailable['checks'].values()), 'Missing-source behavior failed')
    result = {'status': 'passed', 'fresh_original_queries': numeric, 'additional_live_api_queries': extra, 'path_workflow': trace,
              'independent_context_checks': contexts, 'boundaries': boundaries,
              'controlled_source_unavailable': {'verdict': unavailable['evidence_result']['scoring']['verdict'],
                  'checked_numeric_claims': 0, 'fault_injected': True, 'seconds': unavailable['seconds']},
              'inputs': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.glob('*.json')},
              'limits': 'Local targeted acceptance; source snapshots may be warm. No grading guarantee, registration approval, deployment or remote submission verification.'}
    target = ROOT / args.output
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
