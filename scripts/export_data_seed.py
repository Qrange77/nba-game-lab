"""Export only public NBA responses, never chat history or SQLite free pages.

Run from the repository root: python scripts/export_data_seed.py
"""
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
import shutil
import sqlite3
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    source_path = ROOT / 'data_cache/nba.sqlite3'
    target = ROOT / 'data'
    target.mkdir(exist_ok=True)
    fields = {'raw', 'data', 'source', 'source_url', 'parameters', 'fetched_at', 'fetched_epoch', 'stale'}
    counts = Counter()
    dates = []
    with tempfile.TemporaryDirectory() as folder:
        snapshot = Path(folder) / 'nba.sqlite3'
        source = sqlite3.connect(source_path.as_uri() + '?mode=ro', uri=True)
        output = sqlite3.connect(snapshot)
        try:
            output.execute('CREATE TABLE responses (key TEXT PRIMARY KEY, body TEXT NOT NULL, last_access REAL NOT NULL DEFAULT 0)')
            for key, body in source.execute('SELECT key, body FROM responses ORDER BY key'):
                kind, params = json.loads(key)
                entry = json.loads(body)
                if entry['source'] != 'NBA.com' or not entry['source_url'].startswith('https://stats.nba.com/stats/'):
                    raise ValueError('The cache contains a non-NBA source; review before exporting.')
                if entry['parameters'] != params:
                    raise ValueError('Cache key and source parameters disagree.')
                clean = {field: entry[field] for field in sorted(fields)}
                output.execute('INSERT INTO responses VALUES (?, ?, ?)',
                               (key, json.dumps(clean, separators=(',', ':'), sort_keys=True), entry['fetched_epoch']))
                counts[kind] += 1
                dates.append(entry['fetched_at'])
            output.commit()
        finally:
            source.close()
            output.close()
        if not dates:
            raise ValueError('Refusing to ship an empty snapshot.')
        bundle = target / 'nba_seed.sqlite3.gz'
        with snapshot.open('rb') as src, bundle.open('wb') as dst:
            with gzip.GzipFile(filename='', mode='wb', fileobj=dst, mtime=0) as archive:
                shutil.copyfileobj(src, archive)
        manifest = {
            'provider': 'NBA.com', 'file': bundle.name,
            'sha256': hashlib.sha256(bundle.read_bytes()).hexdigest(),
            'compressed_bytes': bundle.stat().st_size, 'database_bytes': snapshot.stat().st_size,
            'response_count': sum(counts.values()), 'responses_by_kind': dict(sorted(counts.items())),
            'retrieved_at_min': min(dates), 'retrieved_at_max': max(dates),
            'scope': 'Observed API responses collected during project research; not an exhaustive NBA dataset.',
            'contents': 'Original resultSets, normalized tables, query parameters and original retrieval timestamps. No conversations or credentials.',
        }
        (target / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
