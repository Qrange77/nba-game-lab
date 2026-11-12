"""Neutral NBA lookups and deterministic checks against saved evidence."""
import copy
import json

from backend.assistant.tools import TOOLS as GAME_TOOLS, run_tool as run_game_tool
from backend.debate.tools import DEBATE_TOOLS, DebateTools
from backend.debate.schemas import Audit, Claim, Params
from backend.debate.comparison import comparison_summary
from backend.debate.tools import scope_text
from backend.assistant.identity import resolve_name
from backend.data.nba import normalize
from pydantic import Field, ValidationError


class Answer(Params):
    answer: str = Field(min_length=1, max_length=20000, description='Neutral English-only markdown answer. Cite source URLs from evidence, state scopes and missing coverage. No fixed player allegiance.')
    claims: list[Claim] = Field(max_length=8, description='Numeric historical claims in the answer, copied from retrieved evidence. Use exact unrounded values. Keep the answer within these checked claims; clarify or report unavailable data when needed.')
    limitations_only: bool = Field(default=False, description='True only for a clarification or inability-to-answer response containing no historical numeric assertions. Explain the missing scope or evidence instead of inventing statistics.')

SHARED_NAMES = frozenset({
    'resolve_player', 'query_evidence', 'compare_players', 'find_counterexamples',
    'find_comparative_edges', 'player_awards', 'compare_awards',
    'query_competitive_context', 'compare_competitive_context',
    'query_performance_context',
})
SHARED_TOOLS = copy.deepcopy([t for t in DEBATE_TOOLS if t['function']['name'] in SHARED_NAMES])
for tool in SHARED_TOOLS:
    tool['function']['description'] = tool['function']['description'].replace(
        'the TWO LOCKED players', 'the two supplied players')
    # Shared schema files also support the retired debate engine. Its allegiance
    # instructions must never reach the neutral assistant.
    encoded = json.dumps(tool).replace(' In Debate use the configured supported player.', '').replace(' In Debate use the configured opponent.', '')
    tool.clear()
    tool.update(json.loads(encoded))
TOOLS = GAME_TOOLS + SHARED_TOOLS + [{'type': 'function', 'function': {
    'name': 'submit_answer', 'description': 'Check historical numeric claims against saved evidence and submit a neutral final answer. Invalid claims must be corrected before publication. Checks numbers, identities, scopes and comparison directions; does not prove causal or qualitative conclusions.',
    'parameters': Answer.model_json_schema(),
}}]


class AssistantResearchTools(DebateTools):
    def __init__(self, data=None, evidence=None, players=None, catalog=None, question=None):
        super().__init__(config=None, data=data)
        self.evidence = copy.deepcopy(evidence or {})
        self.names = {str(p['id']): p['name'] for p in players or []}
        self.catalog = catalog
        self.question = question
        self.game_roster_names = set()
        self.pending = []
        self.submission = None
        self.checks = []
        self.used_evidence = set()

    def allowed(self, ident):
        if self.catalog is not None and str(ident) not in self.names:
            raise ValueError('Resolve this player with resolve_player before querying. Do not invent or guess NBA IDs.')

    def resolve_player(self, p):
        if self.question is not None:
            query = normalize(p.query)
            known = {normalize(name) for name in self.names.values()} | self.game_roster_names
            if query not in normalize(self.question) and query not in known:
                return {'error': 'Resolve the name exactly as written by the user, or use a confirmed selection / retrieved roster name. Do not expand an ambiguous name into a guessed full name.'}
        result = resolve_name(p.query, self.catalog) if self.catalog is not None else self.data.resolve(p.query)
        if not result.get('resolved'):
            selected = [player for player in result.get('players', []) if str(player['id']) in self.names]
            if len(selected) == 1:
                result = {'players': selected, 'complete': True, 'resolved': True}
        if not result.get('resolved'):
            self.pending = [{'query': p.query, **result}]
        return result

    def game_identity_error(self, args):
        if self.catalog is None or not args.get('player_name'):
            return None
        known = {normalize(name) for name in self.names.values()} | self.game_roster_names
        if normalize(args['player_name']) not in known:
            return {'error': 'Confirm this player with resolve_player using the original user wording, or retrieve game_players first. Do not query a guessed full name.'}
        return None

    def observe_game_result(self, name, result):
        if name != 'game_players':
            return
        try:
            result = json.loads(result) if isinstance(result, str) else result
            self.game_roster_names.update(normalize(p['player_name']) for p in result.get('players', []) if p.get('player_name'))
        except (ValueError, TypeError, AttributeError):
            pass

    def run(self, name, args):
        if name not in SHARED_NAMES:
            return {'error': f"Unknown assistant research tool '{name}'."}
        result = super().run(name, args)
        if name == 'resolve_player':
            for player in result.get('players', []) if result.get('resolved') else []:
                self.names[str(player['id'])] = player['name']
        self._remember(result)
        return result

    def _remember(self, result):
        if isinstance(result, dict):
            if result.get('player_name'):
                # New subjects can legitimately emerge from sourced roster or
                # teammate results. These names may be resolved without guessing.
                self.game_roster_names.add(normalize(result['player_name']))
            if result.get('id') in self.evidence:
                self.used_evidence.add(result['id'])
            for value in result.values():
                self._remember(value)
        elif isinstance(result, list):
            for value in result:
                self._remember(value)

    def submit_answer(self, args):
        try:
            draft = Answer.model_validate(args)
        except ValidationError as exc:
            return {'status': 'revise', 'error': str(exc)}
        checked = self.audit_argument(Audit(claims=draft.claims))
        if self.used_evidence and not draft.claims and not draft.limitations_only:
            checked.update(valid=False, errors=[{'error': 'Submit structured claims for the historical facts in the answer. For a clarification or inability-to-answer response without numeric assertions, set limitations_only=true.'}])
        self.checks.append({'valid': checked['valid'], 'errors': checked['errors']})
        if checked['valid']:
            self.submission = {'answer': draft.answer, **checked}
        return {'status': 'accepted' if checked['valid'] else 'revise', **checked}

    def summary(self):
        if hasattr(self, 'research_summary'):
            return self.research_summary
        cards = self.submission['cards'] if self.submission else []
        cited = {c['evidence_id'] for c in cards}
        records = [self.evidence[key] for key in self.used_evidence | cited if key in self.evidence]
        sources = {json.dumps(s, sort_keys=True): s for r in records for s in r.get('sources', [])}
        comparisons = []
        for record in records:
            if record.get('kind') == 'comparison' and 'left' in record and 'right' in record:
                request = {'left_player': record['left']['player_id'], 'right_player': record['right']['player_id'],
                           'left_scope': record['left']['scope'], 'right_scope': record['right']['scope']}
                if not record['left'].get('award_categories'):
                    comparisons.append(comparison_summary(record, request, self.names, scope_text))
        return {'cards': cards, 'comparisons': comparisons, 'sources': list(sources.values()),
                'limitations': list(dict.fromkeys(note for r in records for note in r.get('limitations', []))),
                'verification': {'status': 'checked' if self.submission else 'not_submitted',
                                 'checked_claims': len(cards), 'attempts': self.checks,
                                 'note': 'Checks cover submitted historical numeric claims, their identities, scopes and comparison directions. They do not validate every sentence or establish causation.'}}

    def dispatch(self, name, args):
        if name == 'submit_answer':
            return json.dumps(self.submit_answer(args))
        if name in SHARED_NAMES:
            return json.dumps(self.run(name, args))
        return run_game_tool(name, args)
