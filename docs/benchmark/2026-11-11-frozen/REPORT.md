# Frozen raw LLM / Agent benchmark

This is the initial strict machine-extraction report. Use the [reviewed report](REVIEWED.md) for quotation repairs, explicit scope adjudication and qualitative findings; original machine outcomes remain below.

Frozen UTC: 2026-11-11T03:42:00.821671+00:00. Model: `vertex_ai/gemini-3.5-flash-lite`.

Production tree: `48213668589f5c864f336b3854ff39ca3f29c299992a0848f4d227423974ba64`. The archive includes the actual dirty working tree, not just Git HEAD.

All six questions were fixed before this batch. The first three are the original course examples; the last three are additional player/window combinations unused in prior debugging. They are not a claim of unseen model training data or new research types.

Raw receives only the identical user question: no system prompt, tools, evidence or history. Agent uses the unchanged production workflow. Sampling parameters retain provider defaults; all explicit settings, response model identifiers, finish reasons, usage and elapsed times are recorded per call. One answer per path is retained, including failures. No quality-based retries or case replacement.

Reference numbers come from archived NBA resultSets and independent arithmetic in the evaluation code. Agent output is never the reference. Totals and rates use summed inputs; traded-season total rows are counted once. TS = 100*PTS/[2*(FGA+0.44*FTA)]. Relative TS uses player-attempt-weighted same-season, same-phase league differences. Optional relative-TS estimates with unspecified/different weighting are not scored as errors.

Numeric tolerance: total points ±1; PPG and phase changes ±0.2; TS and TS changes ±0.2 percentage points. The blind extractor sees no expected numeric values or path label. Exact quoted substrings are checked before deterministic comparison. Missing facts reduce coverage rather than numeric correctness. Scope mismatch, unclear scope and extraction failure remain separate. Semantic reviews are advisory model judgments, not human gold labels. This benchmark checks focal-player scoring; teammate/opponent factual accuracy is not comprehensively scored.

Timing includes mixed/warm caches after source snapshot preparation. Agent has multiple model/tool calls; raw has one. This is not a cold-start or compute-matched speed benchmark. Six single runs do not establish general superiority or statistical significance.

| Case | Path | Required numeric coverage | Correct among checkable | Missing | Scope mismatches | Seconds | Model truncation |
|---|---|---:|---:|---:|---:|---:|---|
| [career](pairs/career.md) | raw | 0/8 | 0/0 | 0 | 0 | 7.2 | False |
| [career](pairs/career.md) | agent | 8/8 | 8/8 | 0 | 0 | 9.4 | False |
| [windows](pairs/windows.md) | raw | 0/4 | 0/0 | 0 | 0 | 6.5 | False |
| [windows](pairs/windows.md) | agent | 4/4 | 4/4 | 0 | 0 | 9.6 | False |
| [postseason](pairs/postseason.md) | raw | 4/12 | 1/4 | 0 | 0 | 3.6 | False |
| [postseason](pairs/postseason.md) | agent | 12/12 | 12/12 | 0 | 0 | 9.1 | False |
| [new_volume](pairs/new_volume.md) | raw | 2/4 | 0/2 | 0 | 0 | 1.6 | False |
| [new_volume](pairs/new_volume.md) | agent | 1/4 | 1/1 | 0 | 0 | 8.4 | False |
| [new_efficiency](pairs/new_efficiency.md) | raw | 1/4 | 0/1 | 0 | 0 | 5.7 | False |
| [new_efficiency](pairs/new_efficiency.md) | agent | 2/4 | 2/2 | 0 | 0 | 6.9 | False |
| [new_postseason](pairs/new_postseason.md) | raw | 4/12 | 2/4 | 0 | 0 | 1.5 | False |
| [new_postseason](pairs/new_postseason.md) | agent | 12/12 | 12/12 | 0 | 0 | 7.5 | False |

Inspect all individual checks and quoted excerpts in the audit files. Coverage is checkable required facts / required facts, and correctness is correct / checkable. Neither is an overall answer-quality grade. Do not discard raw-correct cases, mutual failures or missing answers.

## Reproduce

Use the repository environment and configured model credentials. Run commands from the repository root:

```bash
python -m test.paired_benchmark freeze --folder docs/benchmark/NEW-BATCH
python -m test.paired_benchmark run --folder docs/benchmark/NEW-BATCH
python -m test.paired_benchmark audit --folder docs/benchmark/NEW-BATCH
python -m test.paired_benchmark report --folder docs/benchmark/NEW-BATCH
```

Existing saved answers are never overwritten. A changed production/evaluation tree requires a new batch. Source snapshots are compressed original response entries; their hashes, endpoint parameters, retrieval dates and stale flags are indexed in sources.json. Frozen-code.tar.gz preserves the implementation and evaluator used. Credentials are excluded.
