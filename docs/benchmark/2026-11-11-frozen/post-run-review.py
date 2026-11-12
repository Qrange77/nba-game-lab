"""Post-run quotation repair, with original answers and audits left immutable.

Revision 1 was added after the frozen batch exposed Markdown/commas/ellipsis
normalization by the model extractor. It changes anchoring only, not values,
tolerances, required targets or model answers. Every change is logged.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import re
from test.benchmark_audit import check_claim, score_extraction
from test.paired_benchmark import check_frozen, check_sources, digest, now, save


def compact(text):
    chars, indices = [], []
    for index, char in enumerate(text):
        if char.isspace() or char in '*_\\':
            continue
        chars.append(char)
        indices.append(index)
    return ''.join(chars), indices


def anchor(quote, answer):
    if quote and quote in answer:
        return quote
    needle, _ = compact(quote)
    haystack, indices = compact(answer)
    offset = haystack.find(needle) if needle else -1
    if offset < 0:
        return None
    return answer[indices[offset]:indices[offset + len(needle) - 1] + 1]


def canonical(number):
    # A positive sign is optional. A negative sign must never disappear.
    return number.replace(',', '').replace('\u2212', '-').lstrip('+')


def repair_claim(claim, answer):
    corrected = dict(claim)
    for field in ('quote', 'scope_quote'):
        corrected[field] = anchor(claim.get(field, ''), answer) or claim.get(field, '')
    quote = corrected.get('quote', '')
    tokens = re.findall(r'(?<![\d.,])[+\-\u2212]?\d[\d,]*(?:\.\d+)?', quote)
    matched = [n for n in tokens if canonical(n) == canonical(claim.get('number', ''))]
    if matched:
        corrected['number'] = matched[0]
    # The extractor sometimes abbreviates a table scope using literal ellipses.
    # The full answer contract is exact text; it identifies both players/windows.
    if corrected.get('scope_quote') not in answer and '## Comparison contract' in answer:
        start = answer.index('## Comparison contract')
        end = answer.find('\n## ', start + 4)
        corrected['scope_quote'] = answer[start:end if end >= 0 else len(answer)]
    return corrected


def review(folder):
    check_frozen(folder)
    check_sources(folder)
    refs = {r['case']: r for r in json.loads((folder / 'reference.json').read_text())}
    changes = []
    rows = []
    for case in json.loads((folder / 'cases.json').read_text()):
        for path in ('raw', 'agent'):
            name = case['id'] + '-' + path + '.json'
            answer = json.loads((folder / 'results' / name).read_text())['answer']
            original = json.loads((folder / 'audits' / name).read_text())
            extracted = deepcopy(original.get('extracted', {}))
            reference = refs[case['id']]
            facts = {f['id']: f for f in reference['facts']}
            for index, claim in enumerate(extracted.get('claims', [])):
                fixed = repair_claim(claim, answer)
                # The career raw answer explicitly substitutes an incomplete cutoff.
                # This is a separately disclosed scope adjudication, not a numeric error.
                if case['id'] == 'career' and path == 'raw':
                    scope_note = '*(Note: Data is evaluated through the completed 2024-25 season and current 2025-26 trajectories.)*'
                    if scope_note not in answer:
                        raise ValueError('Career scope adjudication no longer matches the original answer')
                    fixed.update(scope='other', scope_quote=scope_note)
                if fixed != claim:
                    changes.append({'file': name, 'id': claim['id'], 'before': claim, 'after': fixed,
                                    'reason': 'Re-anchor formatting to exact answer text; career raw cutoff additionally adjudicated from its explicit note.'})
                extracted['claims'][index] = fixed
            scored = score_extraction(answer, reference, extracted)
            # Show number-only agreement even for wrong-scope answers, without
            # presenting those values as valid responses to the requested period.
            numeric_only = []
            for f in reference['facts']:
                if not f['required']:
                    continue
                claim = next((c for c in extracted.get('claims', []) if c['id'] == f['id']), None)
                if claim:
                    numeric_only.append(check_claim(f, {**claim, 'scope': 'requested'}, answer))
            comparable = [r for r in numeric_only if r['status'] in ('correct', 'incorrect')]
            scored['number_only'] = {'correct': sum(r['status'] == 'correct' for r in comparable),
                                     'checkable': len(comparable),
                                     'note': 'Ignores scope only for diagnostic purposes; not scoped correctness.'}
            scored['status'] = original.get('status')
            scored['original_audit_sha256'] = digest((folder / 'audits' / name).read_bytes())
            scored['extracted'] = extracted
            save(folder / 'reviewed-audits' / name, scored)
            rows.append({'case': case['id'], 'path': path, **{k: scored[k] for k in ('required_count', 'required_comparable', 'required_correct', 'required_missing', 'required_scope_mismatches', 'number_only')}})
    save(folder / 'extraction-review.json', {'revision': 1, 'created_at': now(),
         'review_script_sha256': digest(Path(__file__).read_bytes()),
         'post_run_revision': True, 'original_answers_and_audits_unchanged': True,
         'rule': 'Both paths receive identical Markdown/whitespace/comma quotation repairs. No source values are used during anchoring. Scope adjudication is explicit. Numerical tolerances and required targets are unchanged.',
         'changes': changes, 'summary': rows})
    print(json.dumps(rows, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', required=True)
    review(Path(parser.parse_args().folder).resolve())
