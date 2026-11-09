"""Identity boundaries, neutral sessions and evidence checks without live calls."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
import app
from backend.assistant.identity import identify, resolve_name
from backend.assistant.research_tools import AssistantResearchTools, TOOLS
from test.test_debate import FakeData, tool_call, response


def player(ident, name):
    return dict(id=ident, name=name, from_year='2000', to_year='2025', active=False,
                source='test directory', stale=False)


CATALOG = [player(1, 'Stephen Curry'), player(2, 'Seth Curry'), player(3, 'LeBron James')]


class IdentityTests(unittest.TestCase):
    def test_full_names_aliases_and_ambiguous_surnames(self):
        for query in ('Compare curry and LeBron', 'Compare Curry and king james'):
            selected, pending = identify(query, [], catalog=CATALOG)
            self.assertEqual([p['id'] for p in selected], [3])
            self.assertEqual({p['id'] for p in pending[0]['players']}, {1, 2})
        selected, pending = identify('Stephen Curry versus LeBron James', [], catalog=CATALOG)
        self.assertEqual([p['id'] for p in selected], [1, 3])
        self.assertFalse(pending)
        self.assertEqual(resolve_name('steph', CATALOG)['players'][0]['id'], 1)

    def test_picker_can_disambiguate_but_does_not_override_full_name(self):
        selected, pending = identify('Curry playoff statistics', [CATALOG[1]], catalog=CATALOG)
        self.assertFalse(pending)
        self.assertEqual(selected[0]['id'], 2)
        selected, pending = identify('Stephen Curry playoff statistics', [CATALOG[1]], catalog=CATALOG)
        self.assertFalse(pending)
        self.assertEqual(selected[0]['id'], 1)
        with self.assertRaises(ValueError):
            identify('Curry', [], {'Curry': 3}, CATALOG)

    def test_comparison_followup_keeps_the_selected_pronoun_subject(self):
        selected, pending = identify('Compare him with LeBron James', [CATALOG[0]], catalog=CATALOG)
        self.assertEqual([p['id'] for p in selected], [1, 3])
        self.assertFalse(pending)


class BaselineSessions(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        for target, value in (( 'HISTORY_DIR', Path(folder.name)), ('player_catalog', lambda: CATALOG)):
            patcher = patch.object(app, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.client = TestClient(app.app)

    def test_ambiguous_chat_is_paused_and_resumed_without_duplicate_turn(self):
        with patch.object(app, 'run_agent') as agent:
            result = self.client.post('/chat', json={'message': 'Compare Curry and LeBron'}).json()
            agent.assert_not_called()
        sid = result['session_id']
        self.assertEqual(result['player_clarifications'][0]['query'], 'Curry')
        self.assertFalse(result['tool_calls'])
        bad = self.client.post('/chat', json={'message': 'ignored', 'session_id': sid,
            'resume_pending': True, 'identity_choices': {'Curry': 3}})
        self.assertEqual(bad.status_code, 400)
        def answer(messages, **kwargs):
            self.assertEqual(messages[-1]['content'], 'Compare Curry and LeBron')
            self.assertEqual(set(kwargs['research'].names), {'2', '3'})
            messages.append({'role': 'assistant', 'content': 'Which season and metrics?'})
            return 'Which season and metrics?', []
        with patch.object(app, 'run_agent', side_effect=answer):
            done = self.client.post('/chat', json={'message': 'ignored', 'session_id': sid,
                'resume_pending': True, 'identity_choices': {'Curry': 2}}).json()
        self.assertEqual({p['id'] for p in done['selected_players']}, {2, 3})
        self.assertFalse(done['player_clarifications'])
        saved = self.client.get('/sessions/' + sid).json()
        self.assertEqual(len(saved['turns']), 1)
        self.assertIsNone(saved['pending_identity'])
        self.assertEqual(saved['selected_players'], done['selected_players'])

    def test_validated_ids_and_selection_changes_in_existing_session(self):
        with patch.object(app, 'run_agent') as agent:
            bad = self.client.post('/chat', json={'message': 'His stats?', 'player_ids': [999]})
            self.assertEqual(bad.status_code, 400)
            agent.assert_not_called()
        contexts = []
        def answer(messages, **kwargs):
            contexts.append(copy.deepcopy(messages))
            messages.append({'role': 'assistant', 'content': 'Which season?'})
            return 'Which season?', []
        with patch.object(app, 'run_agent', side_effect=answer):
            first = self.client.post('/chat', json={'message': 'His stats?', 'player_ids': [1]}).json()
            sid = first['session_id']
            second = self.client.post('/chat', json={'message': 'His stats?', 'session_id': sid, 'player_ids': [2]}).json()
        self.assertEqual(second['selected_players'][0]['id'], 2)
        systems = [m['content'] for m in contexts[-1] if m['role'] == 'system' and m['content'].startswith('Confirmed NBA identities:')]
        self.assertEqual(len(systems), 1)
        self.assertIn('Seth Curry', systems[0])
        self.assertNotIn('Stephen Curry', systems[0])

    def test_full_name_reply_continues_original_pending_question(self):
        initial = self.client.post('/chat', json={'message': 'Curry playoff statistics'}).json()
        def answer(messages, **kwargs):
            self.assertEqual(messages[-1]['content'], 'Curry playoff statistics')
            self.assertEqual(kwargs['research'].names, {'2': 'Seth Curry'})
            return 'Which season?', []
        with patch.object(app, 'run_agent', side_effect=answer):
            result = self.client.post('/chat', json={'message': 'Seth Curry', 'session_id': initial['session_id']}).json()
        self.assertFalse(result['player_clarifications'])
        self.assertEqual(result['selected_players'][0]['id'], 2)

    def test_stream_sends_structured_candidates_and_restores_them(self):
        with patch.object(app, 'run_agent') as agent:
            result = self.client.post('/chat/stream', json={'message': 'How did Curry perform in the playoffs?'})
            agent.assert_not_called()
        self.assertEqual(result.status_code, 200)
        events = [json.loads(line[6:]) for line in result.text.splitlines() if line.startswith('data: ')]
        done = next(e['data'] for e in events if e['type'] == 'done')
        restored = self.client.get('/sessions/' + done['session_id']).json()
        self.assertEqual(restored['pending_identity']['groups'], done['player_clarifications'])
        self.assertIn('nba_browser', self.client.cookies)

    def test_retired_sessions_are_preserved_but_cannot_resume_stance(self):
        self.client.get('/sessions')
        owner = self.client.cookies['nba_browser']
        sid = '00000000-0000-0000-0000-000000000001'
        app.save_history(owner, {'session_id': sid, 'mode': 'debate', 'title': 'Old debate',
            'updated_at': '2026-01-01', 'turns': [], 'messages': []})
        self.assertEqual(self.client.get('/sessions').json(), [])
        self.assertEqual(self.client.post('/chat', json={'session_id': sid, 'message': 'Continue'}).status_code, 409)
        self.assertTrue(app.history_path(owner, sid).exists())


class EvidenceBaselineTests(unittest.TestCase):
    def test_bad_claim_is_rejected_and_corrected_claim_keeps_sources(self):
        tools = AssistantResearchTools(data=FakeData())
        evidence = tools.run('compare_players', {'left_player': 1, 'right_player': 2})
        claim = dict(evidence_id=evidence['id'], metric='PTS', player_id=1,
            scope=evidence['left']['scope'], value=20, other_value=16, relation='higher')
        bad = tools.submit_answer({'answer': 'Unsupported', 'claims': [dict(claim, value=99)]})
        self.assertFalse(bad['valid'])
        self.assertIsNone(tools.submission)
        good = tools.submit_answer({'answer': 'Sourced comparison', 'claims': [claim]})
        self.assertTrue(good['valid'])
        summary = tools.summary()
        self.assertEqual(summary['verification']['checked_claims'], 1)
        self.assertEqual(len(summary['verification']['attempts']), 2)
        self.assertTrue(summary['sources'])
        self.assertTrue(summary['comparisons'])

    def test_model_ambiguity_stops_following_calls_before_data_lookup(self):
        tools = AssistantResearchTools(data=FakeData(), catalog=CATALOG)
        # The preflight cannot recognize every spelling; the model can resolve it.
        first = response(calls=[tool_call('resolve_player', {'query': 'Curry'}).tool_calls[0],
            tool_call('query_evidence', {'player_id': 1}).tool_calls[0]])
        with patch.object(app.litellm, 'completion', return_value=SimpleNamespace(choices=[SimpleNamespace(message=first)])), \
             patch.object(tools.data, 'fetch') as fetch:
            answer, log = app.run_agent([{'role': 'user', 'content': 'Tell me about a player'}], research=tools)
        fetch.assert_not_called()
        self.assertTrue(tools.pending)
        self.assertIn('Curry', answer)
        self.assertEqual(json.loads(log[-1]['result'])['status'], 'skipped')

    def test_shared_schemas_do_not_expose_allegiance_or_debate_actions(self):
        encoded = json.dumps(TOOLS)
        for name in ('plan_argument', 'submit_argument', 'style_argument', 'audit_argument'):
            self.assertNotIn('"name": "' + name + '"', encoded)
        self.assertNotIn('In Debate', encoded)
        self.assertIn('submit_answer', encoded)

    def test_missing_evidence_can_be_reported_without_forcing_a_statistic(self):
        tools = AssistantResearchTools(data=FakeData())
        tools.run('query_evidence', {'player_id': 1})
        self.assertFalse(tools.submit_answer({'answer': 'An unchecked answer', 'claims': []})['valid'])
        result = tools.submit_answer({'answer': 'The retrieved sample cannot establish which player had weaker teammates.',
                                      'claims': [], 'limitations_only': True})
        self.assertTrue(result['valid'])
        self.assertFalse(result['cards'])

    def test_model_cannot_expand_ambiguous_input_into_guessed_identity(self):
        tools = AssistantResearchTools(data=FakeData(), catalog=CATALOG, question='What about Curry?')
        guessed = tools.run('resolve_player', {'query': 'Stephen Curry'})
        self.assertIn('error', guessed)
        self.assertFalse(tools.names)
        self.assertIsNotNone(tools.game_identity_error({'player_name': 'Stephen Curry'}))
        actual = tools.run('resolve_player', {'query': 'Curry'})
        self.assertFalse(actual['resolved'])
        selected = AssistantResearchTools(data=FakeData(), catalog=CATALOG, players=[CATALOG[1]], question='What about Curry?')
        self.assertEqual(selected.run('resolve_player', {'query': 'Curry'})['players'][0]['id'], 2)
        self.assertIsNone(selected.game_identity_error({'player_name': 'Seth Curry'}))
