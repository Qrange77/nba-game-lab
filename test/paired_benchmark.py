"""Opt-in, frozen paired evaluation; never imported by the application.

Usage: python -m test.paired_benchmark freeze|run|audit|report --folder PATH
Each command resumes saved artifacts, never overwrites an existing model answer.
"""
import argparse
from datetime import datetime, timezone
import html
from importlib.metadata import version
import json
from pathlib import Path
import subprocess
import tarfile
from threading import Lock
import time
import traceback

from test.benchmark_reference import Sources, build_reference, digest
from test.benchmark_audit import AUDIT_PROMPT, audit_payload, score_extraction

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / 'test/benchmark_cases.json'
PROTOCOL = {
    'version': 1, 'single_batch_no_quality_retries': True,
    'raw': {'messages': 'one user message, identical question', 'tools': False, 'system_prompt': False,
            'max_tokens': 8192, 'timeout': 80, 'num_retries': 0, 'temperature': 'provider default, not overridden'},
    'agent': {'entry': 'production ScoringRun with standard app SYSTEM_PROMPT and verified player IDs',
              'settings': 'unchanged production settings; actual per-call parameters recorded',
              'finish': 'server renderer; record each constituent model finish_reason'},
    'audit': {'model': 'same configured model, blind to answer path', 'max_tokens': 16000,
              'temperature': 0, 'timeout': 100, 'num_retries': 0,
              'numeric_reference': 'independent arithmetic from archived original NBA resultSets',
              'tolerances': {'total_points': 1, 'PPG': .2, 'TS_percentage_points': .2, 'phase_changes': .2},
              'missing': 'coverage gap, not numerical error',
              'relative_TS': 'optional when weighting unspecified; exclude noncomparable methods'},
    'ordering': 'case order frozen; raw first on even case indices, agent first on odd indices',
    'timing': 'source snapshot preparation warms cache; mixed/warm cache, not cold-start or compute-matched',
    'scope': 'three original questions plus three additional player/window combinations; no prompt tuning after freeze',
}


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=True, default=str) + '\n')
    temporary.replace(path)


def code_files():
    paths = [ROOT / 'app.py', ROOT / 'pyproject.toml', ROOT / 'uv.lock', ROOT / 'frontend/package.json']
    paths += list((ROOT / 'backend').rglob('*.py'))
    paths += [p for p in (ROOT / 'frontend/src').rglob('*') if p.is_file()]
    return sorted(p for p in paths if p.exists())


def file_hashes(paths):
    return {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in paths}


def check_frozen(folder):
    manifest = json.loads((folder / 'manifest.json').read_text())
    if file_hashes(code_files()) != manifest['production_files']:
        raise RuntimeError('Production code changed after freeze; preserve this batch and create a new one.')
    if digest((folder / 'cases.json').read_bytes()) != manifest['cases_sha256']:
        raise RuntimeError('Frozen case file changed')
    for name, wanted in manifest['evaluation_files'].items():
        if digest((ROOT / name).read_bytes()) != wanted:
            raise RuntimeError(f'Evaluation code changed after freeze: {name}')
    return manifest


class Recorder:
    def __init__(self, complete=None):
        self.complete = complete
        self.calls = []
        self.lock = Lock()

    def __call__(self, **kwargs):
        if self.complete is None:
            import litellm
            complete = litellm.completion
        else:
            complete = self.complete
        request = {k: v for k, v in kwargs.items() if k not in ('messages', 'tools')}
        record = {'started_at': now(), 'parameters': request,
                  'temperature': kwargs.get('temperature', 'provider default, not overridden'),
                  'message_roles': [m['role'] for m in kwargs['messages']],
                  'messages_sha256': digest(json.dumps(kwargs['messages'], sort_keys=True, default=str).encode()),
                  'tool_names': [t.get('function', {}).get('name') for t in kwargs.get('tools', [])]}
        with self.lock:
            record['index'] = len(self.calls)
            self.calls.append(record)
        start = time.monotonic()
        try:
            response = complete(**kwargs)
            record['response_model'] = getattr(response, 'model', None)
            record['response_id'] = getattr(response, 'id', None)
            reasons = [getattr(c, 'finish_reason', None) for c in response.choices]
            record['finish_reasons'] = reasons
            record['truncated'] = any(str(r).lower() in ('length', 'max_tokens', 'max_output_tokens') for r in reasons)
            usage = getattr(response, 'usage', None)
            record['usage'] = usage.model_dump() if hasattr(usage, 'model_dump') else usage
            return response
        except Exception as exc:
            record['error'] = {'type': type(exc).__name__, 'message': str(exc)}
            raise
        finally:
            record['seconds'] = round(time.monotonic() - start, 4)
            record['ended_at'] = now()


def raw_request(question, model):
    return {'model': model, 'vertex_location': 'global', 'messages': [{'role': 'user', 'content': question}],
            'max_tokens': 8192, 'timeout': 80, 'num_retries': 0}


def freeze(folder):
    if (folder / 'manifest.json').exists():
        raise RuntimeError('This folder is already frozen. Use a new folder for a new batch.')
    from backend.assistant.identity import validate_ids
    from backend.data.nba import NBAData
    from backend.research.engine import MODEL
    cases = json.loads(CASES.read_text())
    # The application permits eight identities per conversation, not per batch.
    identities = list({p['id']: p for c in cases for p in validate_ids([p[0] for p in c['players']])}.values())
    folder.mkdir(parents=True, exist_ok=True)
    save(folder / 'cases.json', cases)
    production = code_files()
    evaluators = [CASES, ROOT / 'test/paired_benchmark.py', ROOT / 'test/benchmark_reference.py', ROOT / 'test/benchmark_audit.py']
    with tarfile.open(folder / 'frozen-code.tar.gz', 'w:gz') as archive:
        for path in production + evaluators:
            archive.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)
    manifest = {'frozen_at': now(), 'model': MODEL, 'protocol': PROTOCOL, 'identities': identities,
                'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'git_dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT)),
                'production_files': file_hashes(production), 'evaluation_files': file_hashes(evaluators),
                'cases_sha256': digest((folder / 'cases.json').read_bytes()),
                'archive_sha256': digest((folder / 'frozen-code.tar.gz').read_bytes()),
                'dependencies': {name: version(name) for name in ('litellm', 'nba_api', 'pydantic')}}
    manifest['production_tree_sha256'] = digest(json.dumps(manifest['production_files'], sort_keys=True).encode())
    save(folder / 'manifest.json', manifest)
    # Freeze questions and source code before any reference retrieval or answers.
    sources = Sources(folder / 'sources', NBAData(budget=480))
    references = []
    for case in cases:
        print(f"Snapshotting source data: {case['id']}", flush=True)
        try:
            references.append(build_reference(case, sources))
        except Exception as exc:
            references.append({'case': case['id'], 'status': 'unavailable', 'facts': [], 'error': str(exc)})
        save(folder / 'reference.json', references)
        save(folder / 'sources.json', sources.index)
    save(folder / 'source-lock.json', {'completed_at': now(), 'reference_sha256': digest((folder / 'reference.json').read_bytes()),
                                     'sources_sha256': digest((folder / 'sources.json').read_bytes())})


def check_sources(folder):
    lock = json.loads((folder / 'source-lock.json').read_text())
    for name in ('reference', 'sources'):
        if digest((folder / (name + '.json')).read_bytes()) != lock[name + '_sha256']:
            raise RuntimeError('Frozen source/reference index changed')
    for item in json.loads((folder / 'sources.json').read_text()).values():
        if digest((folder / item['file']).read_bytes()) != item['sha256']:
            raise RuntimeError('Original source snapshot changed')


def run(folder):
    manifest = check_frozen(folder)
    check_sources(folder)
    from app import SYSTEM_PROMPT
    from backend.assistant.research_tools import AssistantResearchTools
    from backend.research.scoring import ScoringRun
    for index, case in enumerate(json.loads((folder / 'cases.json').read_text())):
        for path in (('raw', 'agent') if index % 2 == 0 else ('agent', 'raw')):
            target = folder / 'results' / f"{case['id']}-{path}.json"
            if target.exists():
                continue
            check_frozen(folder)
            print(f"Running {case['id']}: {path}", flush=True)
            recorder = Recorder()
            start = time.monotonic()
            result = {'case': case['id'], 'path': path, 'question': case['question'], 'started_at': now(), 'answer': ''}
            try:
                if path == 'raw':
                    reply = recorder(**raw_request(case['question'], manifest['model']))
                    result['answer'] = reply.choices[0].message.content or ''
                else:
                    research = AssistantResearchTools(players=[{'id': p, 'name': n} for p, n in case['players']], question=case['question'])
                    events = []
                    answer, calls = ScoringRun([{'role': 'system', 'content': SYSTEM_PROMPT},
                                               {'role': 'user', 'content': case['question']}], research,
                                              events.append, complete=recorder).run()
                    result.update(answer=answer, tool_calls=calls, evidence=research.evidence,
                                  evidence_result=research.summary(), events=events,
                                  answer_origin='production source-bound server renderer')
                result['status'] = 'completed'
            except Exception as exc:
                result.update(status='failed', error={'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()})
            result.update(ended_at=now(), seconds=round(time.monotonic() - start, 3), model_calls=recorder.calls,
                          any_model_truncated=any(c.get('truncated') for c in recorder.calls))
            save(target, result)
            check_frozen(folder)
            print(json.dumps({'case': case['id'], 'path': path, 'status': result['status'],
                              'seconds': result['seconds'], 'truncated': result['any_model_truncated']}), flush=True)


def audit(folder):
    manifest = check_frozen(folder)
    check_sources(folder)
    references = {r['case']: r for r in json.loads((folder / 'reference.json').read_text())}
    for case in json.loads((folder / 'cases.json').read_text()):
        for path in ('raw', 'agent'):
            target = folder / 'audits' / f"{case['id']}-{path}.json"
            if target.exists():
                continue
            result = json.loads((folder / 'results' / target.name).read_text())
            reference = references[case['id']]
            if reference['status'] != 'available' or not result['answer']:
                save(target, {'status': 'unscored', 'reason': 'Reference or answer unavailable'})
                continue
            recorder = Recorder()
            payload = audit_payload(case['question'], result['answer'], reference)
            print(f"Blind extraction: {case['id']} / {path}", flush=True)
            try:
                reply = recorder(model=manifest['model'], vertex_location='global',
                                 messages=[{'role': 'system', 'content': AUDIT_PROMPT},
                                           {'role': 'user', 'content': json.dumps(payload)}],
                                 response_format={'type': 'json_object'}, temperature=0,
                                 max_tokens=16000, timeout=100, num_retries=0)
                full = reply.choices[0].message.content
                extracted = json.loads(full)
                scored = score_extraction(result['answer'], reference, extracted)
                save(target, {'status': 'audited', **scored, 'extracted': extracted,
                              'extractor_response': full, 'model_calls': recorder.calls})
            except Exception as exc:
                save(target, {'status': 'audit_failed', 'error': str(exc), 'model_calls': recorder.calls})


def report(folder):
    manifest = check_frozen(folder)
    check_sources(folder)
    cases = json.loads((folder / 'cases.json').read_text())
    refs = {r['case']: r for r in json.loads((folder / 'reference.json').read_text())}
    lines = ['# Frozen raw LLM / Agent benchmark', '',
             f"Frozen UTC: {manifest['frozen_at']}. Model: `{manifest['model']}`.", '',
             f"Production tree: `{manifest['production_tree_sha256']}`. The archive includes the actual dirty working tree, not just Git HEAD.", '',
             'All six questions were fixed before this batch. The first three are the original course examples; the last three are additional player/window combinations unused in prior debugging. They are not a claim of unseen model training data or new research types.', '',
             'Raw receives only the identical user question: no system prompt, tools, evidence or history. Agent uses the unchanged production workflow. Sampling parameters retain provider defaults; all explicit settings, response model identifiers, finish reasons, usage and elapsed times are recorded per call. One answer per path is retained, including failures. No quality-based retries or case replacement.', '',
             'Reference numbers come from archived NBA resultSets and independent arithmetic in the evaluation code. Agent output is never the reference. Totals and rates use summed inputs; traded-season total rows are counted once. TS = 100*PTS/[2*(FGA+0.44*FTA)]. Relative TS uses player-attempt-weighted same-season, same-phase league differences. Optional relative-TS estimates with unspecified/different weighting are not scored as errors.', '',
             'Numeric tolerance: total points ±1; PPG and phase changes ±0.2; TS and TS changes ±0.2 percentage points. The blind extractor sees no expected numeric values or path label. Exact quoted substrings are checked before deterministic comparison. Missing facts reduce coverage rather than numeric correctness. Scope mismatch, unclear scope and extraction failure remain separate. Semantic reviews are advisory model judgments, not human gold labels. This benchmark checks focal-player scoring; teammate/opponent factual accuracy is not comprehensively scored.', '',
             'Timing includes mixed/warm caches after source snapshot preparation. Agent has multiple model/tool calls; raw has one. This is not a cold-start or compute-matched speed benchmark. Six single runs do not establish general superiority or statistical significance.', '',
             '| Case | Path | Required numeric coverage | Correct among checkable | Missing | Scope mismatches | Seconds | Model truncation |',
             '|---|---|---:|---:|---:|---:|---:|---|']
    pairs = []
    for case in cases:
        pair = [f"# {case['id']}", '', case['question'], '', '## Independent expected facts', '',
                '| Player | Window | Phase | Metric | Expected | Required |', '|---|---|---|---|---:|---|']
        for f in refs[case['id']]['facts']:
            pair.append(f"| {f['name']} | {f['start']}-{f['end'] + 1} | {f['phase']} | {f['metric']} | {f['value']:.4f} | {f['required']} |")
        for path in ('raw', 'agent'):
            name = f"{case['id']}-{path}.json"
            result = json.loads((folder / 'results' / name).read_text())
            audited = json.loads((folder / 'audits' / name).read_text())
            if audited.get('status') == 'audited':
                coverage = f"{audited['required_comparable']}/{audited['required_count']}"
                correctness = f"{audited['required_correct']}/{audited['required_comparable']}"
                missing, mismatch = audited['required_missing'], audited['required_scope_mismatches']
            else:
                coverage = correctness = 'unscored'
                missing = mismatch = '-'
            lines.append(f"| [{case['id']}](pairs/{case['id']}.md) | {path} | {coverage} | {correctness} | {missing} | {mismatch} | {result['seconds']:.1f} | {result['any_model_truncated']} |")
            pair += ['', f'## {path.capitalize()} complete answer', '',
                     f"[Full run metadata](../results/{name}) · [Audit](../audits/{name})", '',
                     '<pre>' + html.escape(result['answer'] or json.dumps(result.get('error'))) + '</pre>', '',
                     '### Advisory semantic review', '', '```json',
                     json.dumps(audited.get('advisory_model_review', {}), indent=2), '```']
        pairs.append((case['id'], '\n'.join(pair) + '\n'))
    lines += ['', 'Inspect all individual checks and quoted excerpts in the audit files. Coverage is checkable required facts / required facts, and correctness is correct / checkable. Neither is an overall answer-quality grade. Do not discard raw-correct cases, mutual failures or missing answers.', '',
              '## Reproduce', '', 'Use the repository environment and configured model credentials. Run commands from the repository root:', '', '```bash',
              'python -m test.paired_benchmark freeze --folder docs/benchmark/NEW-BATCH',
              'python -m test.paired_benchmark run --folder docs/benchmark/NEW-BATCH',
              'python -m test.paired_benchmark audit --folder docs/benchmark/NEW-BATCH',
              'python -m test.paired_benchmark report --folder docs/benchmark/NEW-BATCH', '```', '',
              'Existing saved answers are never overwritten. A changed production/evaluation tree requires a new batch. Source snapshots are compressed original response entries; their hashes, endpoint parameters, retrieval dates and stale flags are indexed in sources.json. Frozen-code.tar.gz preserves the implementation and evaluator used. Credentials are excluded.', '']
    (folder / 'pairs').mkdir(exist_ok=True)
    for name, content in pairs:
        (folder / 'pairs' / f'{name}.md').write_text(content)
    (folder / 'REPORT.md').write_text('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('freeze', 'run', 'audit', 'report'))
    parser.add_argument('--folder', required=True)
    args = parser.parse_args()
    folder = Path(args.folder).resolve()
    {'freeze': freeze, 'run': run, 'audit': audit, 'report': report}[args.command](folder)


if __name__ == '__main__':
    main()
