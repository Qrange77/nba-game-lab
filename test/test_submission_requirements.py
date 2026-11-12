"""Keep the three grader queries and actual no-tools baselines reproducible."""
import ast
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / 'docs/benchmark/2026-11-11-frozen'


class SubmissionRequirementsTests(unittest.TestCase):
    def test_frontend_cards_and_readme_use_the_three_exact_grader_questions(self):
        cases = json.loads((ROOT / 'test/benchmark_cases.json').read_text())[:3]
        app = (ROOT / 'frontend/src/App.vue').read_text()
        prompts = [ast.literal_eval(quote + content + quote)
                   for quote, content in re.findall(r'prompt:\s*([\'"])(.*?)\1', app)]
        self.assertEqual(prompts[:3], [case['question'] for case in cases])
        readme = (ROOT / 'README.md').read_text()
        self.assertEqual(re.findall(r'^> (.+)$', readme, re.M), [case['question'] for case in cases])
        sections = re.split(r'^### [123]\.', readme, flags=re.M)[1:]
        for section, endpoints in zip(sections, (('playercareerstats', 'leaguegamelog'),
                ('playercareerstats.SeasonTotalsRegularSeason', 'leaguegamelog'),
                ('playercareerstats.SeasonTotalsRegularSeason', 'SeasonTotalsPostSeason')), strict=True):
            for endpoint in endpoints:
                self.assertIn(endpoint, section)

    def test_each_original_query_has_actual_same_model_untruncated_paired_answers(self):
        for case in json.loads((ROOT / 'test/benchmark_cases.json').read_text())[:3]:
            with self.subTest(case=case['id']):
                raw = json.loads((FROZEN / f"results/{case['id']}-raw.json").read_text())
                agent = json.loads((FROZEN / f"results/{case['id']}-agent.json").read_text())
                self.assertEqual(raw['question'], case['question'])
                self.assertEqual(agent['question'], case['question'])
                self.assertTrue(raw['answer'].strip() and agent['answer'].strip())
                self.assertFalse(raw['any_model_truncated'] or agent['any_model_truncated'])
                self.assertEqual(len(raw['model_calls']), 1)
                call = raw['model_calls'][0]
                self.assertEqual(call['message_roles'], ['user'])
                self.assertEqual(call['tool_names'], [])
                self.assertTrue(all(c['parameters']['model'] == call['parameters']['model'] for c in agent['model_calls']))
                self.assertTrue((FROZEN / f"pairs/{case['id']}.md").is_file())

    def test_required_root_files_and_submission_structure_are_present(self):
        for name in ('app.py', 'pyproject.toml', 'uv.lock', 'README.md', 'submission.json'):
            self.assertTrue((ROOT / name).is_file(), name)
        submission = json.loads((ROOT / 'submission.json').read_text())
        self.assertEqual(submission['path'], 'research')
        self.assertTrue(submission['authors'] and all(isinstance(a, str) and a.strip() for a in submission['authors']))
        self.assertRegex(submission['deploy_url'], r'^https://[^/]+')


if __name__ == '__main__':
    unittest.main()
