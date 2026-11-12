# Shipped NBA source snapshot

`nba_seed.sqlite3.gz` contains 403 NBA.com API responses collected for this project. The compressed file is about 9.24 MB (8.81 MiB), below the assignment's 100 MB per-file limit. It expands to about 67 MB. `manifest.json` records its SHA-256 checksum, exact sizes, endpoint counts and original retrieval-date range in UTC.

The snapshot includes career totals for 64 player queries, 75 league game-log queries, 112 team-player dashboard queries, plus awards, player game logs, team histories, rosters, the directory, league aggregates and available on/off responses. Counts are API requests, not numbers of unique seasons or players across the entire dataset. It is not an exhaustive archive of every NBA player, season or endpoint.

## Contents and provenance

The SQLite database has one `responses` table. Each row contains its endpoint kind and parameters as the key, original NBA `resultSets`, normalized tables, source URL and original retrieval timestamps. `last_access` is initialized from the retrieval timestamp rather than exporting local access history. Export reconstructs a new database, so unused SQLite pages are not included. Conversation records, browser cookies, model credentials and model answers are not part of this dataset.

The source is NBA.com, accessed through `nba-api`; the project does not claim ownership of the underlying data or grant redistribution rights beyond those of the source. API endpoint URLs, arguments and retrieval dates remain available in each response for inspection.

## Loading

FastAPI startup verifies the archive checksum and database integrity, then restores it atomically to `data_cache/nba.sqlite3` if that file does not exist. Existing caches are left intact. `data_cache/` is ignored by Git so runtime updates do not change the versioned snapshot.

The tools use the restored responses through their existing cache path. Retrieval timestamps are not reset: expired entries trigger a bounded refresh attempt, with a disclosed stale fallback if the refresh fails. Queries absent from the snapshot require live NBA access; if access fails, the tools report unavailable data. The LLM still requires Vertex AI access. Shipping this snapshot does not make the entire application offline.

## Regeneration

After deliberately collecting additional source data, run from the repository root:

```bash
uv run python scripts/export_data_seed.py
uv run python -m unittest test.test_data_seed
```

Review and commit the new archive and manifest together. The export reads the local cache without modifying it, preserves source timestamps and validates source provenance. Do not substitute `chat_history/` or saved model answers for the source snapshot. The separate frozen benchmark under `docs/benchmark/` remains unchanged and supports reproduction of the original comparison results.
