# Evidence-driven supporting-cast follow-up

The Lead now checks whether supporting-cast findings answer the question, even when every initial collection succeeded. This revision focuses on teammate sample adequacy; it does not claim to solve arbitrary research questions or infer user preferences.

## Decision rules

- A completed collector can leave a content gap: helper records use the wrong approved phase, essential production/appearance/efficiency fields are missing, or a per-game core candidate has a sparse playoff sample.
- The appearance screen flags a positive GP below half the maximum GP in the returned rotation. This declared heuristic opens an adequacy question; it is not an exclusion rule, teammate-quality score or injury explanation. The maximum is a returned sample reference, not an independently certified team schedule.
- The Lead receives the verified scoring matrix, original scoped helper rows and identified gap IDs. It can request a targeted investigation. A server sufficiency guard prevents premature finish while an actionable required gap remains.
- A sparse playoff helper sample can prompt matched regular-season baselines for both subjects, using the same window position or corresponding career anchor. Original postseason rows remain visible. An explicit supporting-cast phase restriction is preserved separately from the broader scoring phases.
- Existing complete scoped samples are reused first. Missing metrics can be checked through the alternate roster/career source. Conflicting known values remain a disclosed discrepancy; an alternate source is not silently preferred.
- Out-of-scope, exhausted or unsuccessful inquiries remain limitations. Source retries are bounded. No extra investigation is created solely because the answer is unwelcome.

A follow-up task carries its specific gap ID and locked targets. Its researcher gets a fresh context plus the relevant original evidence, and must invoke the assigned collector before producing notes. Model notes without verified collection are rejected as findings. Final numerical claims continue to be server-rendered and audited.

## Real-data demonstration

Use the **Investigate helper samples** card on the home screen. It compares Jordan's 1990-91 and James's 2014-15 scoring and supporting casts.

All four first-round collectors completed successfully. The retrieved Cleveland playoff core list included Kevin Love with **4 recorded games**, versus **20** for the largest returned rotation sample. That content finding triggered one targeted teammate researcher in round 2. Matching regular-season support was retrieved for **both** focal players; Love's regular-season row recorded **75 games**. The original playoff row was retained, and the report explicitly keeps the phases separate.

This case uses no fault injection. [The saved demonstration](examples/support_findings.json) contains the original evidence, public report, investigation targets and graph. Its facts do not establish the cause of an absence or a context-independent ranking of supporting casts.

## Acceptance

- **306 Python tests passed**, including 14 content-follow-up tests; **11 frontend tests** and the production build passed.
- The live content case completed in two rounds, adding only one teammate investigation after four successful first-round collections. Its final report checked **66 numeric claims**.
- **32 helper metrics** were independently recomputed from original cached NBA `resultSets`, without production aggregation helpers. Original and added scopes, both baseline targets, preserved rows and graph dependencies were checked.
- A separate real career case had sufficient findings and ended in **one round**, with no added investigator.
- Tests also cover reusing existing evidence, supporting-cast-only phase restrictions, out-of-window targets, alternate-source conflicts, exhausted sources and preserving original observations.
- Browser checks cover the second-round reason, targeted tool record, original/follow-up sample sections, source links and history restoration.

[Machine-readable results](content-acceptance-results.json) record the evidence checks. Run:

```bash
uv run python -m unittest discover -s test
cd frontend && npm test && npm run build
cd ..
uv run python -m test.live_scoring_review --case support_findings --output-dir output/content-acceptance
uv run python -m test.live_scoring_review --case career --output-dir output/content-acceptance
uv run python -m test.verify_content_acceptance
```

Full local traces are under ignored `output/content-acceptance/`. The same model and NBA services are used as the main application, with cached API inputs where available. Deployment remains outside this work.
