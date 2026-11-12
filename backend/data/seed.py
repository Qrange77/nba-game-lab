"""Restore the shipped NBA snapshot into a new deployment's writable cache."""
import gzip
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile

from backend.paths import PROJECT_ROOT


def initialize_cache(destination=None, bundle=None):
    """Install once at server startup; preserve existing data and retrieval dates."""
    destination = Path(destination) if destination is not None else PROJECT_ROOT / 'data_cache/nba.sqlite3'
    bundle = Path(bundle) if bundle is not None else PROJECT_ROOT / 'data/nba_seed.sqlite3.gz'
    if destination.exists():
        return False
    manifest = json.loads(bundle.with_name('manifest.json').read_text())
    if hashlib.sha256(bundle.read_bytes()).hexdigest() != manifest['sha256']:
        raise ValueError('The bundled NBA snapshot checksum does not match its manifest.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='nba-seed-', suffix='.sqlite3', dir=destination.parent)
    try:
        with os.fdopen(fd, 'wb') as output, gzip.open(bundle, 'rb') as source:
            shutil.copyfileobj(source, output)
        with closing(sqlite3.connect(temporary)) as db:
            if db.execute('PRAGMA quick_check').fetchone() != ('ok',):
                raise ValueError('The bundled NBA snapshot failed SQLite validation.')
            if db.execute('SELECT COUNT(*) FROM responses').fetchone()[0] != manifest['response_count']:
                raise ValueError('The bundled NBA snapshot has an unexpected response count.')
        # Publish atomically without replacing a cache created by another worker.
        try:
            os.link(temporary, destination)
        except FileExistsError:
            return False
        return True
    finally:
        Path(temporary).unlink(missing_ok=True)
