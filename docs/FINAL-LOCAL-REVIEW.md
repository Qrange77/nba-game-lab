# Local instructor-requirement audit

**Decision:** the tested local implementation satisfies the checkable Deep Research requirements. No reproduced local blocker remains after the fixes below. This is not a promise of full marks: topic originality, data unfamiliarity and creativity require instructor judgement. Deployment and external submission were excluded from this audit.

Source: the instructor-supplied **Project 2: A Data Exploration Agent** assignment, including the Deep Research and README sections. The separate Evals + Simple RAG requirements are not requirements of the `research` path.

## Requirement checks

| Teacher item | Local finding | Evidence |
|---|---|---|
| Basics: root files and submission metadata | Required files exist; JSON contains one author and `path=research`. The existing deployment URL is syntactically valid but not verified for this revision. | Submission regression checks; `submission.json`. |
| Functionality: clear purpose and correct research answers | All three README questions complete directly from the homepage after the identity fix. Independent source checks pass for every rendered comparison value and the requested postseason changes. | [Fresh runs and checks](final-local-acceptance/results.json); browser records below. |
| Data: tool access, supported claims and limits | Original NBA response tables support the numerical findings. All returned context rows in the two reviewed cases pass independent checks. A controlled no-source/no-cache case states insufficient evidence and publishes zero numeric claims. | Original-source benchmark/context archives; controlled-failure run. |
| Data: unique dataset/problem and unfamiliar information | The question focuses on cross-era scoring lenses, league benchmarks and helper-sample adequacy, distinct from the two supplied prediction/clutch topics. NBA is a familiar domain; tool-use gains are evidenced, but instructor acceptance and registration are unconfirmed. | README question and paired answers; this remains an external judgement. |
| Deep Research: three different agent jobs | Lead resolves scope and plans; Researchers collect independently; Writer selects evidence and report structure, with server-checked numerical rendering. | Actual agent-tagged tool records and execution graph. |
| Deep Research: one-turn parallel fan-out in fresh contexts | One Lead plan starts four Researchers with measured overlap of **2,765 ms**. All five starts across both rounds have fresh two-message contexts; only the follow-up receives its relevant original evidence. | [Observed workflow metadata](final-local-acceptance/results.json); support run. |
| Deep Research: findings trigger more research, with a cap | Four successful first-round collections reveal a sparse helper sample. One second-round teammate investigation collects matched baselines; original observations remain. No failure was injected in this case. Limits remain three rounds, eight starts and 240 seconds. | Support run, flow/regression checks and [content method](CONTENT-FOLLOWUP.md). |
| Deep Research: clarify vague input and cite accurately | Vague/unsupported questions stop without statistical collection. Repeated surnames after explicit full names no longer cause false identity questions. A real browser citation opens the exact scoped record and original inputs. | Boundary runs; identity regressions; browser source record. |
| Project 1 `/chat` shape and agent-tagged sub-agent calls | Required response/session/tool fields remain. Real non-streaming `/chat` runs pass; all returned tool calls retain agent tags. Own-session evidence returns 200; another browser gets 404. | Additional API cases and regression tests. |
| README: audience, data/loading, three queries and expected sources, same-model plain answers | Present. Each example has adjacent actual answer summaries/numbers and linked full original outputs. Raw calls contain only the same user question, no tools/system/history; both paths use the same model. | Submission regression checks and frozen original call metadata. |
| Creativity: frontend changed from the starter | Custom scoring workflow, live expandable dependency graph, progressive rounds, evidence inspection and folded report details are implemented and exercised. The quality score is the instructor's decision. | Browser observations/screenshots; frontend tests. |

## Executed cases

| Case | Observed outcome | Independent numeric checks | Observed seconds |
|---|---|---:|---:|
| Career Jordan / James | Conditional metric-specific answer; requested completed cutoff | 16 comparison values | 10.55 |
| Equal Bryant / Curry windows | Bryant volume / Curry efficiency; equal periods | 8 comparison values | 10.07 |
| Jordan / James postseason | Jordan playoff PPG; James playoff TS; correct phase changes | 16 comparison values + 4 changes | 8.40 |
| Duncan / Nowitzki, volume only | Neutral answer remains neutral; no unasked efficiency rows | 4 comparison values | 13.85 |
| Durant / Harden, efficiency only | Neutral answer remains neutral; no unasked volume rows | 4 comparison values | 10.36 |
| Helper adequacy | Real source finding adds one targeted round-two researcher | Full context audit, including original and added samples | 14.98 |
| Vague / defense / pre-1984 / causal swap | Clarification or explicit boundary, zero statistical collection | Scope checks | Not a performance benchmark |
| All sources unavailable, empty cache | Explicit insufficient-data answer, no numeric claims | Controlled failure, deliberately injected | 8.72 |

These are single observed runs with available cached inputs, not cold-start or latency guarantees. The context checks include repeated facts across cases; they are not an overall accuracy percentage. [Context audit scope and original inputs](CONTEXT-REVIEW.md).

## Defects found and fixed in this audit

1. Homepage examples used slightly different text from the README/raw questions; the career button omitted the fixed cutoff. All three now use the exact frozen grader questions. A regression check verifies the match.
2. The postseason question names Michael Jordan and LeBron James explicitly, then uses their surnames. Identity resolution incorrectly asked the user to select both people again. It now uses unambiguous identities anywhere in the current message to resolve repeated surnames, preserves ambiguity when two explicitly named players share a surname, and gives current full names priority over an old picker selection.
3. A repeated ambiguous surname could create duplicate clarification cards. It now asks once and accepts a full-name reply while preserving the original question. Genuinely ambiguous names still require a choice.
4. The README career comparison showed audit counts more clearly than the answers. It now presents both paths' actual PPG/TS values, with the raw cutoff substitution disclosed. Historical outputs were not edited.

The failed identity observation is retained as [before-fix evidence](final-local-acceptance/browser-postseason-identity-before-ax.txt). The fresh successful browser check is separate; the failed attempt is not relabeled as a pass.

## Verification and reproduction

**363 Python tests and 15 frontend tests passed.** Frontend type checking/build and `uv lock --check` also passed. The existing frontend bundle-size advisory does not prevent the build. Source/answer hashes in the historical six-question raw benchmark remain unchanged.

```bash
uv run python -m unittest discover -s test
cd frontend && npm test && npm run build
cd ..
uv run python -m test.verify_final_acceptance --output output/final-local-replay.json
```

The last command replays the archived run evidence against original-source references without making NBA/model calls. [Machine-readable results](final-local-acceptance/results.json) · [Revision/test record](final-local-acceptance/manifest.json).

Browser evidence: [career](final-local-acceptance/browser-career-ax.txt), [equal windows](final-local-acceptance/browser-windows-expanded-ax.txt), [postseason](final-local-acceptance/browser-postseason-ax.txt), [opened source](final-local-acceptance/browser-source-ax.txt). [Career image](final-local-acceptance/browser-career.jpg) · [Window image](final-local-acceptance/browser-windows.jpg) · [Postseason image](final-local-acceptance/browser-postseason.jpg).

## Items not certified

- The sign-up sheet required authentication in the available read-only view; the existing browser connection could not read it. This does not establish that registration is absent. No sheet edits or messages were sent.
- Topic uniqueness/data unfamiliarity and the creativity score cannot be guaranteed by passing tests. The README explains the exact source-derived research problem and preserves the same-model comparisons for the instructor to assess.
- This is an audit of the local working tree. Final GitHub publication, grader permissions and Courseworks submission are not certified.
- Cloud Run, GitHub continuous deployment, deployed data-loading/packaging, the final URL and availability until grading remain for the later deployment stage.
