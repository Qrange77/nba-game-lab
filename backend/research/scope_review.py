"""Validate explicit season notation without guessing a missing comparison scope."""
import re

from backend.research.contract import ScoringContract
from backend.data.nba import current_season, season_label


def current_question_users(messages):
    """Retain clarification replies, but do not inherit a completed report's scope."""
    start = 0
    for index, message in enumerate(messages):
        if message['role'] == 'assistant' and re.match(r'# (?:Scoring (?:Claim Review|Comparison)|On-Court Impact Review)\b', str(message.get('content', ''))):
            start = index + 1
    return [str(m.get('content', '')) for m in messages[start:] if m['role'] == 'user']


def requested_context(users, contract):
    """Latest explicit scope choice wins; short date replies preserve prior intent."""
    for text in reversed(users):
        if re.search(r'(?i)(?:no|without|omit|exclude|skip) (?:team |teammate |supporting.cast |opponent )?context|context (?:is )?not needed', text):
            return False
        # A negative mention is not a request to collect that dimension.
        positive = re.sub(r'(?i)(?:no|without|omit|exclude|skip) (?:teammates?|supporting.casts?|rotation|(?:finals[ -])?opponents?)(?:\s+(?:or|and)\s+(?:teammates?|opponents?))?', '', text)
        if re.search(r'(?i)teammate|supporting.cast|rotation|finals[ -]opponent|competitive.context', positive):
            return True
        if positive != text:
            return False
        if re.search(r'(?i)(?:volume|efficiency)[ -]only|only (?:scoring )?(?:volume|efficiency)', text):
            return False
        if re.search(r'(?i)scoring (?:ability|impact|performance)|better scorer|stronger scorer|comprehensive (?:scoring|review)', text):
            return contract.lens == 'overall_scoring'
    if contract.period == 'windows' or contract.lens in ('volume', 'efficiency'):
        return False
    return contract.include_context


def completed_cutoff_matches(messages):
    latest = next((str(m.get('content', '')) for m in reversed(messages) if m['role'] == 'user'), '')
    return list(re.finditer(r'\bcompleted\s+seasons?\s+(?:through|up to)\s+(\d{4})[-\u2013](\d{2})\b', latest, re.I))


def completed_cutoff_issue(messages):
    matches = completed_cutoff_matches(messages)
    if len(matches) > 1:
        return 'Choose one completed-season cutoff for this comparison.'
    if matches:
        year, suffix = map(int, matches[0].groups())
        if (year + 1) % 100 != suffix:
            return 'Please use a valid consecutive-year season label, such as '+season_label(year)+'.'
        if year >= current_season():
            return 'That season is ongoing or in the future. Choose completed seasons through '+season_label(current_season()-1)+' or an earlier cutoff.'
    return ''


def completed_cutoff_fact(messages):
    """Recognize an explicit completed-season cutoff in the latest user message."""
    matches = completed_cutoff_matches(messages)
    if len(matches) != 1:
        return None
    year, suffix = map(int, matches[0].groups())
    if (year + 1) % 100 != suffix or not 1984 <= year < current_season():
        return None
    return {'season': season_label(year), 'start_year': year, 'completed': True}


def cutoff_clarification(contract, fact):
    return bool(fact and contract.action == 'clarify' and re.search(
        r'(?i)cutoff|completed season|season start year|start.year notation', contract.question))


def apply_completed_cutoff(contract, fact):
    """The user's validated earlier cutoff also overrides an incorrect model default."""
    if not fact or contract.action != 'review' or contract.cutoff == fact['start_year']:
        return contract
    return ScoringContract.model_validate({**contract.model_dump(), 'cutoff': fact['start_year']})


def repair_equal_windows(contract, messages, names):
    if contract.action != 'clarify' or contract.period != 'windows':
        return contract
    if not re.search(r'(?i)unequal|different lengths|not equal|same length|different start and end years|identical season ranges', contract.question):
        return contract
    season = r'(\d{4})[-\u2013](\d{2})'
    window = re.compile(season + r'\s*(?:through|to|\u2013)\s*' + season, re.I)
    users = [str(m.get('content', '')) for m in reversed(messages) if m['role'] == 'user']
    latest = next((text for text in users if re.search(season, text)), '')
    if not re.search(r'(?i)scor|shoot|efficien|points', ' '.join(users)):
        return contract
    selected = []
    for side in ('left', 'right'):
        pid = getattr(contract, side + '_player')
        name = names.get(str(pid))
        if not name:
            return contract
        mention = re.search(r'(?<!\w)' + re.escape(name) + r'(?!\w)', latest, re.I)
        if not mention:
            return contract
        # Associate each range with its explicit preceding full player name.
        following = latest[mention.end():]
        other = names.get(str(contract.right_player if side == 'left' else contract.left_player), '')
        next_name = re.search(re.escape(other), following, re.I) if other else None
        match = window.search(following[:next_name.start()] if next_name else following)
        if not match:
            return contract
        lo, suffix_lo, hi, suffix_hi = map(int, match.groups())
        if (lo + 1) % 100 != suffix_lo or (hi + 1) % 100 != suffix_hi:
            return contract
        if (lo, hi) != (getattr(contract, side + '_start'), getattr(contract, side + '_end')):
            return contract
        selected.append((lo, hi))
    if selected[0][1] - selected[0][0] != selected[1][1] - selected[1][0]:
        return contract
    try:
        return ScoringContract.model_validate({**contract.model_dump(), 'action': 'review', 'question': ''})
    except ValueError:
        return contract
