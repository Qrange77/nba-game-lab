# Scoring Review acceptance

Implementation started November 10, 2026 at 22:32 UTC, under the authorized four-hour limit ending November 11 at 02:32 UTC. Scope: develop, review and test locally; no deployment or external submission.

## Executed plan

1. Preserve the prior research engine and run identical baseline questions.
2. Lock the product to two-player cross-era scoring claims and explicit periods.
3. Implement comparable scoring/league evidence, bounded team context, gap review and checked reports.
4. Update the English interface and three grader examples.
5. Independently recompute source values, run regression/live/browser checks and record remaining requirements.

## Verified results

- **285 automated tests passed**, including 18 scoring-specific contract, computation, planning, follow-up and evidence-access tests. Existing regression tests remain passing.
- **Three real-model scoring cases passed** with API-backed evidence: career, equal windows and postseason changes. **40 independently recomputed values** and all 20 comparison directions match original cached NBA response tables. The independent checker imports no production scoring aggregation helpers.
- **Four boundary cases passed**: vague comparison, defense request, unsupported earlier era and causal teammate swap. Each asks for clarification or states its boundary without statistical collection.
- **One real-model controlled-fault run passed**: the first personal researcher was deliberately stopped before collection. A second-round personal task recovered the evidence; the completed era task was not repeated. The fault injection is explicit in the saved artifact.
- Production frontend type checking and build passed. The existing bundle-size advisory remains; it does not prevent the build.
- Local browser checks passed: ambiguous identity selection, scope clarification and continuation, parallel research progress, completed comparison matrix, core-helper/rotation expansion, authenticated evidence inspection and report history restoration.
- Authenticated evidence isolation passed: the owning browser can retrieve a saved record; another browser receives 404.
- Authored code, UI, documentation and curated examples contain no literal Chinese characters. `git diff --check` passed.

## Comparison with the previous engine

Same model and identical seven questions; the previous source snapshot and full outputs were captured before modification under ignored `output/scoring-baseline-20261110/`. The product-specific comparison below counts published, checked metric pairs matching the approved sample and values. It is **not a universal accuracy score** and does not imply the older engine could not retrieve other useful data.

| Case | Old matching published axes | New independently verified axes | Old / new observed seconds |
|---|---:|---:|---:|
| Career scoring | 3 / 8 | 8 / 8 | 35.73 / 12.25 |
| Equal windows | 2 / 4 | 4 / 4 | 23.14 / 8.41 |
| Postseason changes | 4 / 8 | 8 / 8 | 14.84 / 8.87 |

The new metric pairs total **20 / 20**, versus **9 / 20** meeting these checks in the previous published reports. Career checks reject old values that included an ongoing season. Whole-period weighted relative TS is now calculated from each matching season; single-year relative values cannot substitute for it.

Timings are single observed runs with mixed cached/API evidence and variable model latency. They are not cold-start guarantees or a statistically controlled speed benchmark. Other repeated runs varied. [Machine-readable checks](acceptance-results.json) document the exact criteria.

The separate no-tools/no-system baselines and complete new answers are in the three [README examples](../README.md#three-sample-queries-and-same-model-comparison). The baseline can sound plausible while giving incorrect windows, aggregates or temporal assumptions; it is preserved without editing.

## Defects found and corrected

- Career aggregation could include the ongoing season. The contract now enforces a completed cutoff and filters source rows before calculation.
- Missing early rebounding/turnover inputs incorrectly removed otherwise valid league shooting benchmarks. Missingness now propagates only to dependent metrics.
- The broad engine could end research while required evidence was omitted. Coverage now tracks actual collectors, blocks premature finish and limits follow-ups to retryable gaps.
- A real run proposed a plan incompatible with required roles. The server now repairs invalid plans to the locked contract, logs the repair and filters unsupported investigation promises. Completed dimensions cannot be re-researched as gap tasks.
- Percentages, scope, phase changes and verdict directions are rendered from verified inputs. Researcher prose cannot invent causal interpretation, physicality or overall ability claims in the published report.
- Core helpers previously risked appearing only as names. The report now includes their scoring, efficiency, minutes and games first, followed by expandable rotation details and exact evidence links.

## Teacher requirements and remaining work

| Requirement | Status |
|---|---|
| Lead, parallel fresh-context Researchers, Writer | Implemented and exercised |
| Gap review and bounded follow-up | Implemented; mock and controlled real-model recovery passed |
| Source-grounded findings and inability to answer | Implemented; numeric checks and explicit scope boundaries |
| Existing `/chat` shape and agent-tagged calls | Preserved and regression tested |
| Frontend purpose, audience and instructions | Updated to the scoring-claim workflow |
| Three sample queries, expected answers and endpoints | Included in README |
| Same-model no-tools/no-system paired answers | Three actual paired snapshots included |
| `submission.json` author and research path | Present; existing deployment URL retained |
| Cloud Run deployment and reachability | **Not performed**, explicitly excluded by the user; old URL is not verified for this revision |
| Sign-up-sheet topic approval | **Not confirmed**; sheet access was unavailable and no sheet edits were authorized |
| Data/problem uniqueness and unfamiliarity | Focus differs from the two shown NBA projects; final approval and grading remain the instructor's decision |
| Courseworks / repository submission | **Not performed** |

The project has one listed author and uses NBA.com APIs. A second provider is not required by the stated one-source-per-member rule for that team size. The 50-sample eval and hill-climbing rules belong to the separate Evals + Simple RAG path.

## Deliberate limits

Support begins in 1984-85; earlier entire careers are not silently cropped. The league baseline covers returned paired games, not an independently certified full schedule. Relative TS is descriptive and uses the conventional free-throw coefficient. Team context uses symmetric endpoint case studies, not every teammate-season. Finals opponent win percentage is one limited proxy. None of these supports causal championship credit, injury explanations or a context-independent innate-ability ranking. If required evidence is missing, the report remains partial or insufficient rather than substituting model memory.

## Subsequent Flow Graph revision

The chat research workspace was subsequently upgraded to a live dependency graph. The updated suite has 292 Python tests and 11 frontend checks passing. [Flow Graph acceptance](FLOW-ACCEPTANCE.md) documents the measured parallel run, controlled second-round recovery and UI verification.

## Evidence-content follow-up revision

Supporting-cast review now checks actual sample adequacy after successful collection. A non-injected source case triggers matched second-round research; a sufficient case finishes in one round. The current suite has 306 Python and 11 frontend tests passing. [Content-follow-up acceptance](CONTENT-FOLLOWUP.md) records the source checks, boundaries and preserved observations.
