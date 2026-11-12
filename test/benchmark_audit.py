"""Blind answer extraction followed by deterministic source-number checks."""
import json
import re


AUDIT_PROMPT = """Extract explicit claims from the supplied answer for each target, without calculating or guessing missing numbers. You do not know which system wrote it. No expected values are supplied. Return JSON:
{"claims":[{"id":"target id","quote":"exact answer substring containing the claimed number","number":"exact numeric substring, including a negative sign when present","scope":"requested|other|unclear","scope_quote":"exact answer substring establishing player, phase and window","method":"aggregate|attempt_weighted|season_mean|unknown"}],"review":{"question_coverage":{"status":"complete|partial|absent|uncertain","reason":"...","quote":"exact answer substring or empty for an omission"},"scope":{"status":"respected|violated|uncertain","reason":"...","quote":"..."},"conclusion_limits":{"status":"respected|violated|uncertain","reason":"...","quote":"..."}}}.
Only extract requested window aggregates or explicitly reported postseason-minus-regular-season changes. Do not use single-season rows as a multi-season aggregate. Omit a target if its value is not explicitly present. Repeated metric names in different phases must not be conflated. TS is expressed as a percentage, not a fraction. number must be one plain numeric expression, not a range or bound. If the answer only gives a range/bound, omit it and mention this in the review. For tables, quote the complete row and use scope_quote for its header or nearby scope. Scope requested means the answer explicitly assigns the value to the requested sample; it does not certify its truth. If it explicitly substitutes another season/window mark other. Do not judge numerical correctness. Evaluate question coverage, scope and conclusion limits conservatively, admitting uncertainty. Descriptive statistics do not prove causation, hypothetical era transfers or overall player greatness. Do not require a particular winner or a conditional verdict if a narrow metric has a clear leader."""


def check_claim(fact, claim, answer):
    row = {'id': fact['id'], 'required': fact['required'], 'expected': fact['value'],
           'tolerance': fact['tolerance'], 'unit': fact['unit']}
    if not claim:
        return {**row, 'status': 'not_stated'}
    row['extraction'] = claim
    quote, number, scope_quote = (claim.get(k, '') for k in ('quote', 'number', 'scope_quote'))
    numeric_tokens = re.findall(r'(?<![\d.,])[+\-\u2212]?\d[\d,]*(?:\.\d+)?', quote)
    if not quote or quote not in answer or not number or number not in numeric_tokens or not scope_quote or scope_quote not in answer:
        return {**row, 'status': 'unverifiable_extraction'}
    if claim.get('scope') == 'other':
        return {**row, 'status': 'scope_mismatch'}
    if claim.get('scope') != 'requested':
        return {**row, 'status': 'unclear_scope'}
    if fact['metric'] == 'RTS' and claim.get('method') != 'attempt_weighted' and not fact['method_required']:
        return {**row, 'status': 'method_not_comparable'}
    normalized = number.replace(',', '').replace('\u2212', '-')
    if not re.fullmatch(r'[+\-]?\d+(?:\.\d+)?', normalized):
        return {**row, 'status': 'unverifiable_extraction'}
    observed = float(normalized)
    return {**row, 'observed': observed, 'status': 'correct' if abs(observed - fact['value']) <= fact['tolerance'] + 1e-9 else 'incorrect'}


def audit_payload(question, answer, reference):
    targets = [{k: v for k, v in f.items() if k not in ('value', 'tolerance', 'required', 'seasons')}
               for f in reference['facts']]
    return {'question': question, 'answer': answer, 'targets': targets}


def score_extraction(answer, reference, extracted):
    claims = extracted.get('claims', [])
    ids = [c.get('id') for c in claims]
    # Duplicate extractions are ambiguous, never silently choose a favorable one.
    by_id = {c['id']: c for c in claims if ids.count(c.get('id')) == 1}
    checks = [check_claim(f, by_id.get(f['id']), answer) for f in reference['facts']]
    required = [r for r in checks if r['required']]
    comparable = [r for r in required if r['status'] in ('correct', 'incorrect')]
    review = extracted.get('review', {})
    for item in review.values():
        quote = item.get('quote', '')
        item['quote_verified'] = not quote or quote in answer
    return {'checks': checks, 'required_count': len(required), 'required_comparable': len(comparable),
            'required_correct': sum(r['status'] == 'correct' for r in comparable),
            'required_missing': sum(r['status'] == 'not_stated' for r in required),
            'required_scope_mismatches': sum(r['status'] == 'scope_mismatch' for r in required),
            'advisory_model_review': review,
            'note': 'Only extracted, quote-verified numeric claims are scored. Missing facts are coverage gaps, not numeric errors. Semantic review is model-judged and advisory.'}
