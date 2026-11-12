"""Deployment snapshot checks: actual restore, offline retrieval and safe failure."""
import json
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from backend.data.nba import NBAData, DataUnavailable
from backend.data.seed import initialize_cache
from backend.paths import PROJECT_ROOT


class DataSeedTests(unittest.TestCase):
    def test_shipped_snapshot_restores_real_sources_and_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / 'cache.sqlite3'
            self.assertTrue(initialize_cache(destination))
            with closing(sqlite3.connect(destination)) as db, db:
                keys = {row[0] for row in db.execute('SELECT key FROM responses')}
                manifest = json.loads((PROJECT_ROOT / 'data/manifest.json').read_text())
                self.assertEqual(len(keys), manifest['response_count'])
                index = json.loads((PROJECT_ROOT / 'docs/benchmark/2026-11-11-frozen/sources.json').read_text())
                self.assertFalse(set(index) - keys, 'Frozen benchmark source queries must be shipped.')
                key = json.dumps(['career', {'player_id': 893, 'per_mode36': 'Totals', 'league_id_nullable': '00'}], sort_keys=True)
                original = json.loads(db.execute('SELECT body FROM responses WHERE key=?', (key,)).fetchone()[0])
            with patch.object(NBAData, '_live', side_effect=AssertionError('No network in this test')):
                data = NBAData(destination, budget=0)
                entry = data.fetch('career', player_id=893, per_mode36='Totals', league_id_nullable='00')
                self.assertEqual(entry['raw'], original['raw'])
                self.assertEqual(entry['fetched_at'], original['fetched_at'])
                with patch('backend.data.nba.time.time', return_value=original['fetched_epoch'] + 90 * 86400):
                    stale = NBAData(destination, budget=0).fetch('career', player_id=893, per_mode36='Totals', league_id_nullable='00')
                self.assertTrue(stale['stale'])
                self.assertIn('refresh_error', stale)
                with self.assertRaises(DataUnavailable):
                    data.fetch('career', player_id=-12345)
            with closing(sqlite3.connect(destination)) as db, db:
                db.execute('CREATE TABLE preservation_marker (value TEXT)')
            self.assertFalse(initialize_cache(destination))
            with closing(sqlite3.connect(destination)) as db, db:
                self.assertIsNotNone(db.execute("SELECT name FROM sqlite_master WHERE name='preservation_marker'").fetchone())

    def test_corrupt_bundle_is_rejected_without_publishing_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            bundle = root / 'nba_seed.sqlite3.gz'
            bundle.write_bytes(b'broken archive')
            (root / 'manifest.json').write_text(json.dumps({'sha256': 'incorrect'}))
            destination = root / 'cache.sqlite3'
            with self.assertRaisesRegex(ValueError, 'checksum'):
                initialize_cache(destination, bundle)
            self.assertFalse(destination.exists())


if __name__ == '__main__':
    unittest.main()
