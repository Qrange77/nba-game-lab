# Raw LLM comparison protocol

The current frozen batch is [2026-11-11-frozen](benchmark/2026-11-11-frozen/REVIEWED.md). It supplements the historical development acceptance tests; it does not replace or relabel them.

The course Deep Research route asks for three sample queries, their expected answers and source endpoints, and same-model answers without tools or a system prompt alongside the Agent answers. It does not require a raw comparison panel in the product UI. This evaluation therefore lives in the README and reviewable artifacts.

## Before the answers

The batch freezes the actual production working tree, the three original questions, three additional player/window combinations, evaluation code and numerical tolerances. Original NBA response tables are archived before either answer is generated. The manifest records hashes, configured model, dependency versions, identity validation, parameters and the evaluation protocol. No credentials are archived.

The additional questions are new to this project's debugging examples. They are not guaranteed to be absent from model training, and they do not test arbitrary new research dimensions. No question is replaced after seeing results. Production prompts, routing and settings remain frozen during the batch.

## Two independent paths

Raw gets one user message containing the exact question, with no system, tools, evidence or conversation history. Its output allowance is 8,192 tokens. Agent receives the same question through the existing production ScoringRun with the standard application system prompt and verified player selections. Each starts a fresh conversation.

The same configured model is used. Sampling defaults remain unchanged and are recorded as provider defaults when unspecified. Per-call records include explicit generation parameters, request and response model identifiers, timestamps, elapsed time, token usage, finish reasons, truncation and errors. Agent has multiple calls and source access; this is a tool/workflow comparison, not a compute-matched comparison. There is one answer per path per question, with alternating execution order. Production-internal retries remain visible. Saved answers are never overwritten.

## Independent checks

The reference builder reads original NBA resultSets through the existing data transport. It independently implements season selection, traded-season deduplication, totals, PPG, TS and contemporaneous relative TS. It never imports production scoring/aggregation functions or reads an Agent answer to construct expected values.

A blind extractor receives the question, answer and target descriptions, without expected values or a raw/Agent label. It locates exact numeric and scope quotations. Deterministic code checks the quoted numbers against source-derived values. Tolerances fixed before the runs are one point for totals, 0.2 points per game, and 0.2 percentage points for TS and changes. Alternative relative-TS aggregation methods are excluded where the question did not specify weighting. Missing values, scope mismatch, unclear scope and extraction failures are separate from numerical errors. Required-fact coverage and accuracy among checkable values have separate denominators.

Semantic coverage and conclusion-limit judgments are model-assisted and advisory. They are not independent human gold labels. Review the quoted passages and source facts before drawing a conclusion. Focal-player scoring is checked numerically; supporting-cast and opponent facts are not comprehensively scored by this benchmark.

All raw-correct cases, mutual errors, missing answers, failures and truncation remain in the report. The report makes no statistical generalization from six single runs. Source preparation warms the cache, so timings do not represent cold starts. The historical 9/20-to-20/20 published-axis comparison is an earlier Agent-version comparison, not raw-LLM accuracy.

## Commands

From the repository root, use the configured project environment:

```bash
python -m unittest test.test_paired_benchmark
python -m test.paired_benchmark freeze --folder docs/benchmark/NEW-BATCH
python -m test.paired_benchmark run --folder docs/benchmark/NEW-BATCH
python -m test.paired_benchmark audit --folder docs/benchmark/NEW-BATCH
python -m test.paired_benchmark report --folder docs/benchmark/NEW-BATCH
```

A changed production/evaluation tree requires a new batch. The source index records endpoint parameters, retrieval times, stale flags and compressed snapshot hashes. Full answers, audits and per-call metadata remain linked from the batch report. Historical examples in docs/examples remain historical rather than being silently overwritten.

The completed batch also preserves an explicitly post-run quotation-repair revision. Run `python -m test.benchmark_review --folder docs/benchmark/2026-11-11-frozen` to reproduce that review. The original frozen evaluator and audits remain unchanged; the reviewed report records the revision and rejects erroneous advisory penalties for unrequested metrics.
