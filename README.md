# NBA Game Lab

## Current Baseline

An English-language NBA assistant that queries ESPN and NBA.com data to answer
questions about games, players, statistics, honors, and player comparisons.

The baseline includes a player selector, name clarification, conversation history,
source links, evidence cards, and checks for submitted historical numeric claims.
Answers are neutral. The Lead / Researcher / Writer workflow is not implemented yet.

## Planned Project 2: Deep Research

Extend the baseline to investigate specific NBA questions through a research team:

- **Lead:** clarify ambiguous questions, plan tasks, and choose relevant research
  dimensions rather than running every comparison automatically.
- **Researchers:** investigate independent tasks in parallel with separate
  contexts, covering areas such as regular-season performance, playoffs,
  comparable career stages, and teammate context where data is available.
- **Follow-up research:** let the Lead inspect findings and request targeted
  investigation when evidence is missing, within a fixed turn limit.
- **Writer:** produce a neutral, accurately cited report that distinguishes
  supported conclusions from uncertainty and data limitations.

Document the data sources and three sample questions with same-model, no-tool
comparisons, then deploy and validate the completed workflow on Google Cloud Run.
