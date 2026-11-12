"""Reject corrupted context facts, selection, coverage, public rows and citations."""
import copy
import json
import re
import unittest
from pathlib import Path

from test.context_audit import Sources, audit_case, check_report, metrics

FOLDER = Path(__file__).resolve().parents[1] / 'docs/context-review'


class ContextAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = json.loads((FOLDER / 'cases.json').read_text())[0]

    def setUp(self):
        self.case = copy.deepcopy(self.original)
        self.sources = Sources(FOLDER)

    def record(self, kind):
        return next(r for r in self.case['evidence'].values() if r['kind'] == kind)

    def test_original_raw_tables_and_blank_query_parameters_replay_offline(self):
        result = audit_case(self.case, self.sources)
        self.assertEqual(result['finals_series'], 16)
        self.assertEqual(result['finals_results'], {'win': 10, 'defeat': 6})
        self.assertTrue(result['export_citations_checked'])

    def test_incorrect_helper_value_or_total_minutes_is_rejected(self):
        for field in ('GP', 'total_minutes'):
            with self.subTest(field=field):
                self.case = copy.deepcopy(self.original)
                record = self.record('supporting_cast')
                if field == 'GP':
                    record['values']['GP']['value'] += 1
                else:
                    record['total_minutes'] += 100
                with self.assertRaises(AssertionError):
                    audit_case(self.case, self.sources)

    def test_opponent_record_error_is_rejected(self):
        self.record('finals_series')['values']['OPP_WIN_PCT']['value'] += 5
        with self.assertRaises(AssertionError):
            audit_case(self.case, self.sources)

    def test_a_different_helpers_career_citation_is_rejected(self):
        record = next(r for r in self.case['evidence'].values() if r['kind'] == 'supporting_cast'
                      and any(s.get('endpoint', '').endswith('/commonteamroster') for s in r['sources']))
        own = next(s for s in record['sources'] if s.get('parameters', {}).get('player_id') == record['player_id'])
        own['parameters']['player_id'] = 999999
        with self.assertRaises(AssertionError):
            audit_case(self.case, self.sources)

    def test_omitted_defeat_is_rejected(self):
        record = next(r for r in self.case['evidence'].values() if r['kind'] == 'finals_series'
                      and r['values']['SERIES_LOSSES']['value'] == 4)
        del self.case['evidence'][record['id']]
        with self.assertRaisesRegex(AssertionError, 'Missing/extra Finals'):
            audit_case(self.case, self.sources)

    def test_wrong_core_and_incomplete_public_rotation_are_rejected(self):
        for core in (True, False):
            with self.subTest(core=core):
                self.case = copy.deepcopy(self.original)
                sample = self.case['evidence_result']['scoring']['support_samples'][0]
                if core:
                    sample['core'][0] = sample['rotation'][-1]
                else:
                    sample['rotation_records'].pop()
                with self.assertRaises(AssertionError):
                    audit_case(self.case, self.sources)

    def test_changed_public_metric_is_rejected(self):
        sample = self.case['evidence_result']['scoring']['support_samples'][0]
        sample['rotation_records'][0]['values']['PTS']['value'] += 10
        with self.assertRaisesRegex(AssertionError, 'Public rotation differs'):
            audit_case(self.case, self.sources)

    def test_wrong_finals_games_or_phase_are_rejected(self):
        for phase in (True, False):
            with self.subTest(phase=phase):
                self.case = copy.deepcopy(self.original)
                record = self.record('finals_series')
                if phase:
                    record['scope']['phase'] = 'Regular Season'
                else:
                    record['game_ids'].pop()
                with self.assertRaises(AssertionError):
                    audit_case(self.case, self.sources)

    def test_incorrect_published_value_and_missing_source_link_are_rejected(self):
        scoring = self.case['evidence_result']['scoring']
        finals = [r for r in self.case['evidence'].values() if r['kind'] == 'finals_series']
        for missing_link in (True, False):
            with self.subTest(missing_link=missing_link):
                self.case = copy.deepcopy(self.original)
                if missing_link:
                    self.case['response'], count = re.subn(r'\[Evidence\]\(https://stats.nba.com/stats/teamplayerdashboard[^)]+\)',
                                                          '', self.case['response'])
                    self.assertGreater(count, 0)
                else:
                    self.case['response'] = self.case['response'].replace('| Scottie Pippen | 21.65 |', '| Scottie Pippen | 99 |')
                with self.assertRaises(AssertionError):
                    check_report(self.case, scoring['support_samples'], finals)

    def test_unavailable_shooting_inputs_are_not_converted_to_zero_efficiency(self):
        result = metrics([{'GP': 1, 'PTS': 5, 'FGA': None, 'FTA': 0}])
        self.assertIsNone(result['TS_PCT'])
        self.assertEqual(result['PTS'], 5)


if __name__ == '__main__':
    unittest.main()
