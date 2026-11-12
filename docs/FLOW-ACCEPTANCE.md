# Research Flow Graph acceptance

Implemented November 10, 2026. Design reference: [assistant-ui Flow Graph](https://www.assistant-ui.com/elements/flow-graph). The reference uses React; this application uses a native Vue/SVG adaptation of its dependency columns, curved edges and progressive node reveal. No additional production dependency or deployment was introduced.

## Delivered behavior

- The first execution snapshot contains only Lead. Researchers appear when actually dispatched, start independently and retain their individual outcome.
- Researchers in the same round share a graph column. Actual execution intervals determine the displayed durations and peak concurrency.
- Lead reviews depend on the completed round. A second-round researcher depends on that review, and Writer depends on the last review. No speculative future branches or fake percentage progress are shown.
- Select a node to inspect its task, public execution summary, timestamps and its own tool calls. Each tool result is separately expandable and rendered as text.
- The workspace collapses to a status/round summary. Follow-live, horizontal scrolling and fit/actual-size controls handle larger graphs. Completed multi-round runs fit the overview automatically when following live.
- Graph snapshots persist in conversation history. Older conversations retain the previous coverage list because their execution timestamps were never recorded.
- Failed runs retain successful nodes and stop unfinished nodes. A browser stream interruption marks the local view interrupted rather than claiming success; the saved server outcome can be restored from history.
- Both light and dark themes, keyboard-accessible node buttons and reduced-motion preferences are supported.

## Verification

| Check | Result |
|---|---|
| Python regression and execution-graph tests | **292 passed** |
| Frontend layout, stream ordering/interruption and existing Markdown checks | **11 passed** |
| Vue type checking and production build | Passed; existing bundle-size advisory remains |
| Real-model career research | Four independent researchers; observed peak concurrency **4** |
| Independent interval check | All four researchers overlapped for **3,431 ms** in the captured run |
| Controlled browser follow-up | First personal collection intentionally omitted; round 2 recovered it without repeating era collection |
| Graph dependency and tool-node association audit | Passed for both captured runs |
| Browser interaction | Initial Lead, round 2, node inspection, tool expansion, collapse, fit controls, history restore and both themes checked |
| Failed-run SSE/history persistence | Automated test passed |
| English-only authored source and diff formatting | Passed |

The controlled recovery is a deliberate fault test, not a claim that a natural model failure occurred. All other model calls and NBA retrievals in that run used the real configured services or their API response cache. The captured report remains numerically verified and conditional. [Measured results](flow-acceptance-results.json) contain the concise checks; full local snapshots and browser evidence are retained under ignored `output/flow-acceptance/`.

## Acceptance findings fixed

A real controlled run exposed an existing contract issue: the model sometimes selected volume-only despite an explicit request for both volume and efficiency. The contract now retains both requested lenses, while honoring explicit volume-only requests; a regression test covers both. Theme verification also caught and corrected a scoped CSS selector that made dark-theme nodes unreadable.

## Reproduce

```bash
uv run python -m unittest discover -s test
cd frontend
npm test
npm run build
cd ..
uv run python -m test.live_scoring_review --case career --output-dir output/flow-acceptance
uv run python -m test.live_scoring_review --case windows --inject-gap --output-dir output/flow-acceptance
```

Frontend tests were run with Node 24. The optional `test.verify_flow_acceptance` checker additionally consumes the controlled browser capture in `output/flow-acceptance/browser-gap.json`; its temporary loopback test server is deliberately outside the production application. Real model calls require the credentials documented in README.

## Compatibility

Existing chat response fields remain intact. The additive `research_flow` field is available in chat results and saved turns; the corresponding SSE event contains versioned full snapshots. Each research tool call adds `node_id` while retaining its existing `agent`. Evidence calculation, scoped citations and session ownership remain in place. Deployment and external submission remain outside this work.

## Subsequent content-driven investigation

The initial controlled recovery above is supplemented by a real, non-injected teammate case: all first-round collectors succeed, then a sparse appearance finding triggers a targeted second-round branch. See [content-follow-up acceptance](CONTENT-FOLLOWUP.md). The current totals are 306 Python and 11 frontend tests passing.
