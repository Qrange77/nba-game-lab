# Focused-answer acceptance

Historical focus-only revision. The later [Writer/UI acceptance](WRITER-REVIEW.md) adds neutral-question handling, concise summaries and expandable details.

This production revision fixes narrow volume/efficiency presentation and makes counterevidence explicit. It does not change player data, formulas, research fan-out, gap checks or the directional verdict policy. It does not fix neutral-question claim framing.

## Behavior

- Volume reports show accumulated points and points per game. Efficiency reports show raw TS and contemporaneous relative TS. The same selection reaches the Writer, report highlights, comparison table and response matrix. Hidden rows cannot return as Writer-selected counterevidence. Full source evidence remains available for provenance inspection.
- Sensitivity notes compare the requested metric family, naming the player favored by each metric rather than saying only that the direction changes.
- When both phases are in scope, the change table follows the requested lens: PPG changes for volume, TS changes for efficiency, both for broad/postseason reports.
- Level-versus-change notes separately identify the higher playoff value and the larger playoff-minus-regular-season change. They do not imply that every change is positive or that playoff conditions caused the difference. Missing changes remain unavailable, not zero.
- Broad scoring/postseason reports retain the existing comprehensive matrix. Supporting-cast investigations requested by the user retain their contextual statistics. This revision does not add arbitrary per-metric selections beyond the existing contract lenses.
- Unrequested efficiency caveats and league-coverage percentages are omitted from volume-only reports. Generic context sections are omitted when context was not requested.

## Verification

All **330 Python tests** passed, including nine new focus/counterevidence tests. They exercise API/Writer/report consistency, hidden counterevidence, the Writer fallback, phase-specific columns, missing values, broad-question compatibility and opposing level/change advantages. Existing frontend code and assets were unchanged.

Three real-model runs use the exact additional questions from the earlier benchmark, with the normal production engine and no injected faults:

| Case | Requested lens | Visible metric family | Independent required checks |
|---|---|---|---:|
| [Duncan / Nowitzki](examples/answer-focus/new_volume.json) | Volume | Total points and PPG | 4/4 |
| [Durant / Harden](examples/answer-focus/new_efficiency.json) | Efficiency | TS and weighted relative TS | 4/4 |
| [Wade / Leonard](examples/answer-focus/new_postseason.json) | Postseason | Existing broad matrix plus explicit phase changes | 12/12 |

The postseason report explicitly says: “The playoff raw true shooting comparison favors Kawhi Leonard; the playoff-minus-regular-season change favors Dwyane Wade.” Its table retains the underlying values and citations. This describes two different statistical questions, not a causal or overall-player conclusion.

All three reports passed their production numeric-evidence audits. Twenty required focal-player values agree with the independent original-response reference in the earlier frozen batch, using its unchanged tolerances. Model calls reported no truncation. These are three targeted live acceptance runs, not a new same-model raw/Agent comparison or a general accuracy estimate. [Recorded checks](examples/answer-focus/checks.json) and [production hashes/questions](examples/answer-focus/manifest.json) preserve the new run context. The files also retain complete answers, evidence, tool calls, model parameters and finish reasons.

The earlier [six-question paired benchmark](benchmark/2026-11-11-frozen/REVIEWED.md) remains an immutable historical comparison of the previous production revision. Its 44/44 result is not relabeled as a new result for this revision. Existing historical answers are unchanged; newly generated answers use the updated renderer.

## Teacher requirements versus our checks

The supplied Project 2 brief requires these Deep Research behaviors: at least three agent shapes, parallel fresh-context Researchers launched by Lead, bounded gap-driven follow-up, clarification of vague questions and accurate citations. The shared README requirements include three queries, expected answers and source endpoints, plus same-model answers without tools or a system prompt next to Agent answers. Functionality is also judged on the deployed agent actually answering its research questions correctly.

The brief does not prescribe a unit-test count, a numeric acceptance threshold, 44 checks, six evaluation questions, an independent arithmetic implementation or a raw-comparison product screen. These are our verification choices. The 50-sample suite, two scorer types and two hill-climbing rounds belong to the separate Evals + Simple RAG path. Deployment and submission remain separate unfinished course steps.

Re-run the behavioral checks from the repository root:

```bash
uv run python -m unittest test.test_answer_focus test.test_scoring_review
uv run python -m unittest discover -s test
```
