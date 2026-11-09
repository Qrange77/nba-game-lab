"""Resolve chat mentions and picker selections to server-verified NBA identities."""
import re
from functools import lru_cache

from backend.data.nba import NBAData, normalize

# A surname deliberately remains ambiguous. Only explicit aliases select a person.
ALIASES = {
    'lebron': 'LeBron James', 'king james': 'LeBron James',
    'mj': 'Michael Jordan', 'steph': 'Stephen Curry', 'steph curry': 'Stephen Curry',
    'kobe': 'Kobe', 'shaq': "Shaquille O'Neal", 'kd': 'Kevin Durant',
    'paolo': 'Paolo Banchero',
}


@lru_cache(maxsize=1)
def player_catalog():
    # Existing cached NBA directory when available, otherwise nba_api's bundled
    # directory. Identity selection never depends on a slow live stats request.
    return NBAData(budget=0).directory()


def resolve_name(query, catalog=None):
    catalog = player_catalog() if catalog is None else catalog
    target = normalize(ALIASES.get(query.strip().casefold(), query))
    exact = [p for p in catalog if normalize(p['name']) == target or str(p['id']) == query.strip()]
    tokens = [p for p in catalog if target in {normalize(word) for word in p['name'].split()}]
    matches = exact or tokens or [p for p in catalog if target and target in normalize(p['name'])]
    return {'players': matches[:25], 'complete': len(matches) <= 25, 'resolved': len(matches) == 1}


def validate_ids(ids, catalog=None):
    catalog = player_catalog() if catalog is None else catalog
    by_id = {p['id']: p for p in catalog}
    if len(ids) > 8 or any(i not in by_id for i in ids):
        raise ValueError('Choose up to eight valid NBA players from the directory.')
    return [by_id[i] for i in dict.fromkeys(ids)]


def mentions(message, catalog=None):
    """Recognize full names, curated aliases, and capitalized surnames.

    Longest matches win so 'Stephen Curry' is not reinterpreted as 'Curry'.
    Other spellings can still be resolved by the model's resolve_player tool.
    """
    catalog = player_catalog() if catalog is None else catalog
    terms = set(ALIASES)
    terms.update(p['name'] for p in catalog)
    surnames = {p['name'].split()[-1] for p in catalog}
    # Avoid interpreting ordinary sentence words / team names as people.
    surnames -= {'May', 'Will', 'Best', 'Long', 'Short', 'King', 'Miles', 'Young', 'Green', 'Brown', 'White', 'Black', 'Love', 'West', 'Wise', 'Price'}
    matches = []
    for term in terms | surnames:
        pattern = r'(?<!\w)' + re.escape(term) + r'(?!\w)'
        for match in re.finditer(pattern, message, re.IGNORECASE):
            matches.append((match.start(), match.end(), match.group()))
    accepted = []
    for start, end, text in sorted(matches, key=lambda m: (-(m[1] - m[0]), m[0])):
        if not any(start < b and end > a for a, b, _ in accepted):
            accepted.append((start, end, text))
    return [text for _, _, text in sorted(accepted)]


def identify(message, selected, choices=None, catalog=None):
    catalog = player_catalog() if catalog is None else catalog
    choices = choices or {}
    resolved, pending = [], []
    for query in mentions(message, catalog):
        result = resolve_name(query, catalog)
        candidates = result['players']
        chosen = choices.get(query)
        if chosen is not None:
            match = next((p for p in candidates if p['id'] == chosen), None)
            if match is None:
                raise ValueError('Select a player from the candidates for this name.')
            resolved.append(match)
        elif result['resolved']:
            resolved.append(candidates[0])
        else:
            selected_matches = [p for p in selected if p['id'] in {c['id'] for c in candidates}]
            if len(selected_matches) == 1:
                resolved.append(selected_matches[0])
            else:
                pending.append({'query': query, **result})
    # A comparison follow-up such as 'compare him with LeBron' retains the
    # selected person behind the pronoun. An explicitly named new subject in
    # other questions replaces the prior focus.
    refers_back = bool(re.search(r'\b(him|them|selected players|these players|those players)\b', message, re.IGNORECASE))
    comparing = bool(re.search(r'\b(compare|with|versus|against|vs)\b', message, re.IGNORECASE))
    focus = selected + resolved if resolved and refers_back and comparing else resolved
    players = list({p['id']: p for p in focus}.values()) if resolved else selected
    return players, pending


def clarification_text(pending):
    return '\n\n'.join(
        f'Which NBA player do you mean by **{group["query"]}**? Choose a candidate below, or enter a full name.'
        if group['players'] else
        f'I could not identify **{group["query"]}**. Enter a full name or use the player selector.'
        for group in pending)
