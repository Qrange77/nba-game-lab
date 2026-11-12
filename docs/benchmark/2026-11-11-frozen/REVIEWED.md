# Reviewed six-question paired benchmark

This is the reviewed result for the frozen batch, not a new round of model answers. All six questions were fixed before the runs. All twelve runs completed; no model call reported output truncation. Configured model: `vertex_ai/gemini-3.5-flash-lite`; recorded response model: `gemini-3.5-flash-lite`. Agent prompts, workflow and production settings were unchanged throughout the batch.

[Protocol](../../BENCHMARK.md) · [Frozen manifest](manifest.json) · [Independent reference](reference.json) · [Original source index](sources.json) · [Initial machine report](REPORT.md) · [Quotation corrections](extraction-review.json).

## Every case, without selection

“Correct/checkable” uses exact source-derived targets, the predeclared numerical tolerance and the requested scope. Coverage is checkable required targets / required targets. Missing targets are not treated as incorrect numbers. These fractions are not whole-answer grades.

| Case | Raw scoped coverage | Raw correct/checkable | Agent scoped coverage | Agent correct/checkable | Important qualification |
|---|---:|---:|---:|---:|---|
| [Career](pairs/career.md) | 0/8 | Not comparable | 8/8 | 8/8 | Raw explicitly substitutes completed 2024-25 plus 2025-26 trajectories. Ignoring this scope problem, 7/8 numeric estimates are within tolerance. |
| [Equal windows](pairs/windows.md) | 4/4 | 2/4 | 4/4 | 4/4 | Raw gets both PPG values within tolerance and both aggregate TS values outside tolerance. |
| [Postseason changes](pairs/postseason.md) | 12/12 | 3/12 | 12/12 | 12/12 | Raw incorrectly reports a positive James TS change; independent totals give a decrease. |
| [Duncan / Nowitzki volume](pairs/new_volume.md) | 4/4 | 0/4 | 4/4 | 4/4 | Both correctly identify Nowitzki as leading both volume measures. Raw's totals and rates are inaccurate; Agent introduces an unasked proposition. |
| [Durant / Harden efficiency](pairs/new_efficiency.md) | 4/4 | 2/4 | 4/4 | 4/4 | Raw's two attempt-weighted relative-TS estimates are within tolerance; its aggregate TS values are not. Both give the correct advantage direction. |
| [Wade / Leonard postseason](pairs/new_postseason.md) | 12/12 | 7/12 | 12/12 | 12/12 | Raw gets all six PPG values/changes and Leonard's playoff TS within tolerance. Agent introduces an unasked proposition. |

Agent matches all **44 required focal-player numeric targets** against independent source arithmetic. This is a narrow numeric result for this batch. It does not establish universal answer superiority, validate every optional statement, verify every teammate/opponent fact, or measure adaptation to arbitrary unfamiliar research dimensions. There are no mutual numeric failures among these required targets in this batch; this is an observed outcome, not a rule for retaining cases. Raw-correct figures, correct directions and Agent defects remain visible above.

## What counts as expected evidence

Career, window and postseason rows come from `playercareerstats` original `SeasonTotalsRegularSeason` and `SeasonTotalsPostSeason` tables. Multi-team season total rows are counted once. PPG is summed points divided by summed games. TS is `100 * summed PTS / (2 * (summed FGA + 0.44 * summed FTA))`. Phase changes are playoff minus corresponding regular-season aggregate values. Relative TS uses same-season, same-phase `leaguegamelog` team-game totals, weighted by player `FGA + 0.44 * FTA`.

The source index archives **80 original response entries**, with parameters, retrieval timestamps, hashes and stale flags; none were stale at snapshot time. Original data are independent of either answer, though both reference transport and Agent can access the same NBA service/cache. The formulas are independently implemented in the evaluation module. Supporting-cast and opponent content is not comprehensively numerically audited here. The three original README questions retain their expected behaviors and source endpoints; extra questions do not replace them.

## Qualitative review and limits

The following review was performed by the coding assistant against the complete frozen answers and source facts. It is not an independent human adjudication. Original model-assisted semantic ratings remain archived, including their mistakes.

- **Career:** Raw explicitly says “Data is evaluated through the completed 2024-25 season and current 2025-26 trajectories.” That is a scope substitution relative to the requested completed 2025-26 cutoff, even when individual rounded values agree. Agent declares the requested completed cutoff and distinguishes rate, accumulation and efficiency. Both use a conditional framing. The benchmark does not certify the whole supporting-cast or Finals narrative.
- **Equal windows:** Both identify Bryant's rate advantage and Curry's efficiency advantage. Raw's “Bryant generated his scoring entirely out of isolation and pick-and-rolls” and claims about gravity/overall offensive footprint go beyond the requested, verified descriptive metrics. Agent explicitly treats relative TS as descriptive rather than a causal era correction. Raw's relative-TS ranges are retained but not scored as directly comparable exact attempt-weighted estimates.
- **Original postseason:** Both address the requested phases and three-season windows. Raw says James's true shooting rises “+2.3%”; independent source totals instead give approximately −2.89 percentage points. Its explanation involving “increased defensive intensity and physicality” is not established by these scoring totals. Agent reports the correct phase changes and restricts the verdict to the samples.
- **New volume:** Raw answers the volume question directly and gets the winning direction right despite inaccurate numbers. Its omission of TS is appropriate because TS was not requested. Agent provides correct requested numbers, but rewrites a neutral question as “Tim Duncan leads total points and points per game” before marking that proposition contradicted. That proposition was not asserted by the user. It also includes unrequested efficiency material, making the response less focused. Numeric success therefore does not mean clean task framing.
- **New efficiency:** Both answer both requested efficiency measures and identify Durant as the leader. Raw's relative-TS estimates are within tolerance, while its cumulative TS arithmetic is inconsistent with source inputs. Omission of PPG is appropriate because PPG was not requested. Agent remains explicit about sample and causation limits, although it adds unrequested volume rows.
- **New postseason:** Both use the complete playoff run rather than Finals-only figures and both identify Leonard's higher playoff PPG/TS. Raw misstates several regular-season TS values and TS changes. Agent's numbers are correct, but it rewrites the neutral comparison as “Dwyane Wade in 2005-06 was a better postseason scorer than Kawhi Leonard in 2018-19” and then contradicts that invented proposition. Its narrative could also make the conflicting TS-change advantage clearer: Wade's +1.60 percentage-point change exceeds Leonard's +1.31, while Leonard has the higher postseason TS level. Those are different questions.

The blind semantic grader incorrectly penalized optional/unrequested omissions in several raw answers: TS for the volume question, PPG for the efficiency question, and total points for the postseason questions. Those advisory penalties are **rejected**, not counted as answer defects. It also missed the career cutoff issue and the Agent's neutral-question framing problem. These failures are why semantic model ratings are not treated as gold labels or an automatic overall-quality score.

The current batch establishes required numeric correctness for the Agent, with the qualitative issues above still open. No production fix was made after observing these extra cases, and no result was regenerated to make the table look better.

## Post-run extraction revision

The frozen extractor sometimes normalized Markdown, removed thousands separators or abbreviated a scope quotation with literal ellipses. Strict quote verification then left real claims unscored. Both paths receive the same supplementary quotation-anchoring repair: restore literal Markdown/whitespace spans, original comma formatting and positive signs; never invent numbers or remove negative signs. All edits, before/after claims, original-audit hashes and the repair-script hash are in [extraction-review.json](extraction-review.json). Original machine audits and complete model answers are unchanged.

The explicitly substituted career cutoff is separately recorded as a scope adjudication. For transparency, a number-only diagnostic of 7/8 is retained for raw even though none of its eight targets is accepted for the requested completed cutoff. Numerical tolerances, required targets, source references and questions were not changed after results. The supplementary repair was added **after** the runs, rather than represented as part of the original preregistration. [Exact supplementary script](post-run-review.py).

Corrected per-claim files: [career raw](reviewed-audits/career-raw.json), [career Agent](reviewed-audits/career-agent.json), [windows raw](reviewed-audits/windows-raw.json), [windows Agent](reviewed-audits/windows-agent.json), [postseason raw](reviewed-audits/postseason-raw.json), [postseason Agent](reviewed-audits/postseason-agent.json), [volume raw](reviewed-audits/new_volume-raw.json), [volume Agent](reviewed-audits/new_volume-agent.json), [efficiency raw](reviewed-audits/new_efficiency-raw.json), [efficiency Agent](reviewed-audits/new_efficiency-agent.json), [new postseason raw](reviewed-audits/new_postseason-raw.json), [new postseason Agent](reviewed-audits/new_postseason-agent.json).

## Runtime and reproducibility

Per-call records preserve explicit generation settings, elapsed time, usage, request model, response model, response ID and finish reason. Unspecified sampling values are labeled provider defaults; the benchmark does not invent their resolved values. Raw has one call with an 8,192-token cap; Agent uses its existing multiple-call workflow. The six cases alternate which path runs first. No answer was retried to improve quality. Provider/internal behavior cannot be completely controlled or made deterministic by this harness.

Sources were snapshotted first, warming the cache. These timings are mixed/warm cache rather than cold start, and the paths are not compute-matched. All raw answers completed in roughly 1.5–7.2 seconds and Agent workflows in roughly 6.9–9.6 seconds in this batch. Evaluation/extraction time is recorded separately, not included as answer-generation latency. The small single-run sample does not justify a statistical generalization.

The initial frozen code archive and manifest preserve the actual uncommitted production tree and original evaluator. Use the commands in [the protocol](../../BENCHMARK.md) to create a new batch. For this batch's supplementary review, run:

```bash
python -m test.benchmark_review --folder docs/benchmark/2026-11-11-frozen
```

The unchanged original three complete answer pairs satisfy the README comparison evidence requirement; this work adds no raw-comparison product UI and performs no deployment.
