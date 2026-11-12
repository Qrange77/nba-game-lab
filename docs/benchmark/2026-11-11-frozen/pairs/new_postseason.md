# new_postseason

These are the complete original answers. The semantic ratings below are uncorrected model advisories and can misjudge optional metrics. See the [reviewed benchmark](../REVIEWED.md) for the final interpretation.

Compare Dwyane Wade in 2005-06 with Kawhi Leonard in 2018-19 as postseason scorers. For each player give whole-postseason points per game and true shooting, plus their changes from the corresponding regular season. Use the entire playoff run, not only the Finals, and limit the conclusion to these one-season samples.

## Independent expected facts

| Player | Window | Phase | Metric | Expected | Required |
|---|---|---|---|---:|---|
| Dwyane Wade | 2005-2006 | Regular Season | PTS | 2040.0000 | False |
| Dwyane Wade | 2005-2006 | Regular Season | PPG | 27.2000 | True |
| Dwyane Wade | 2005-2006 | Regular Season | TS | 57.7472 | True |
| Dwyane Wade | 2005-2006 | Playoffs | PTS | 654.0000 | False |
| Dwyane Wade | 2005-2006 | Playoffs | PPG | 28.4348 | True |
| Dwyane Wade | 2005-2006 | Playoffs | TS | 59.3466 | True |
| Dwyane Wade | 2005-2006 | Playoffs minus Regular Season | PPG_CHANGE | 1.2348 | True |
| Dwyane Wade | 2005-2006 | Playoffs minus Regular Season | TS_CHANGE | 1.5995 | True |
| Kawhi Leonard | 2018-2019 | Regular Season | PTS | 1596.0000 | False |
| Kawhi Leonard | 2018-2019 | Regular Season | PPG | 26.6000 | True |
| Kawhi Leonard | 2018-2019 | Regular Season | TS | 60.6180 | True |
| Kawhi Leonard | 2018-2019 | Playoffs | PTS | 732.0000 | False |
| Kawhi Leonard | 2018-2019 | Playoffs | PPG | 30.5000 | True |
| Kawhi Leonard | 2018-2019 | Playoffs | TS | 61.9247 | True |
| Kawhi Leonard | 2018-2019 | Playoffs minus Regular Season | PPG_CHANGE | 3.9000 | True |
| Kawhi Leonard | 2018-2019 | Playoffs minus Regular Season | TS_CHANGE | 1.3067 | True |

## Raw complete answer

[Full run metadata](../results/new_postseason-raw.json) · [Audit](../audits/new_postseason-raw.json)

<pre>Here is the statistical comparison of Dwyane Wade’s 2005-06 postseason run with Kawhi Leonard’s 2018-19 postseason run, based on the entire playoff runs.

### **Dwyane Wade (2005-06 Postseason)**
* **Playoff Points Per Game (PPG):** 28.4 
* **Playoff True Shooting Percentage (TS%):** 57.3%
* **Change from Regular Season:**
  * **PPG:** +1.2 (Regular Season: 27.2)
  * **TS%:** +0.6% (Regular Season: 56.7%)

### **Kawhi Leonard (2018-19 Postseason)**
* **Playoff Points Per Game (PPG):** 30.5
* **Playoff True Shooting Percentage (TS%):** 61.9%
* **Change from Regular Season:**
  * **PPG:** +3.9 (Regular Season: 26.6)
  * **TS%:** +4.7% (Regular Season: 57.2%)

---

### **Conclusion**
Based strictly on these one-season samples, Kawhi Leonard was the more prolific and efficient postseason scorer. While Dwyane Wade maintained his elite regular-season production while slightly improving his efficiency on a championship run, Kawhi Leonard elevated his scoring volume by nearly 4 points per game and experienced a massive spike in true shooting efficiency (+4.7%), operating as a historically efficient high-volume playoff scorer.</pre>

### Advisory semantic review

```json
{
  "question_coverage": {
    "status": "partial",
    "reason": "Total points (PTS) for regular season and playoffs were omitted for both players.",
    "quote": "",
    "quote_verified": true
  },
  "scope": {
    "status": "respected",
    "reason": "The answer provides stats specifically for the requested players and single-season playoff/regular season windows.",
    "quote": "Here is the statistical comparison of Dwyane Wade\u2019s 2005-06 postseason run with Kawhi Leonard\u2019s 2018-19 postseason run",
    "quote_verified": true
  },
  "conclusion_limits": {
    "status": "respected",
    "reason": "The conclusion correctly restricts its scope to the specified one-season samples.",
    "quote": "Based strictly on these one-season samples, Kawhi Leonard was the more prolific and efficient postseason scorer.",
    "quote_verified": true
  }
}
```

## Agent complete answer

[Full run metadata](../results/new_postseason-agent.json) · [Audit](../audits/new_postseason-agent.json)

<pre># Scoring Claim Review

**Verdict: Contradicted under the selected statistical criteria.**

&gt; Dwyane Wade in 2005-06 was a better postseason scorer than Kawhi Leonard in 2018-19.

This adjudication concerns the selected scoring statistics. It does not rank overall players or establish innate ability, defensive impact, or championship causation.

## Comparison contract

- Subjects: **Dwyane Wade** and **Kawhi Leonard**.
- Scope: 2005-06–2005-06 versus 2018-19–2018-19; Regular Season, Playoffs.
- Statistical lens: postseason.
- Completed-season cutoff: **2025-26**; ongoing seasons are excluded.
- Percentages are recomputed from summed inputs. Missing observations remain missing.
- Relative efficiency uses same-season, same-phase league TS; career aggregation weights each season by FGA + 0.44 × FTA.

## Evidence selected by the Writer

- Playoffs / Accumulated points: Kawhi Leonard has the larger observed value. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2548&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=202695&amp;PerMode=Totals&amp;LeagueID=00)
- Playoffs / Points per game: Kawhi Leonard has the larger observed value. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2548&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=202695&amp;PerMode=Totals&amp;LeagueID=00)
- Regular Season / Accumulated points: Dwyane Wade has the larger observed value. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2548&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=202695&amp;PerMode=Totals&amp;LeagueID=00)

## Comparable evidence

| Phase | Statistical lens | Dwyane Wade | Kawhi Leonard | Observed advantage | Sources |
|---|---|---:|---:|---|---|
| Regular Season | Accumulated points (total) | 2,040 | 1,596 | Dwyane Wade | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2548&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=202695&amp;PerMode=Totals&amp;LeagueID=00) |
| Regular Season | Points per game (per game) | 27.2 | 26.6 | Dwyane Wade | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2548&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=202695&amp;PerMode=Totals&amp;LeagueID=00) |
| Regular Season | Raw true shooting (%) | 57.75 | 60.62 | Kawhi Leonard | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2548&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=202695&amp;PerMode=Totals&amp;LeagueID=00) |
| Regular Season | Contemporaneous relative true shooting (percentage points) | 4.19 | 4.66 | Kawhi Leonard | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2548&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=202695&amp;PerMode=Totals&amp;LeagueID=00) |
| Playoffs | Accumulated points (total) | 654 | 732 | Kawhi Leonard | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2548&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=202695&amp;PerMode=Totals&amp;LeagueID=00) |
| Playoffs | Points per game (per game) | 28.43 | 30.5 | Kawhi Leonard | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2548&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=202695&amp;PerMode=Totals&amp;LeagueID=00) |
| Playoffs | Raw true shooting (%) | 59.35 | 61.92 | Kawhi Leonard | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2548&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=202695&amp;PerMode=Totals&amp;LeagueID=00) |
| Playoffs | Contemporaneous relative true shooting (percentage points) | 4.66 | 6.87 | Kawhi Leonard | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2548&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=202695&amp;PerMode=Totals&amp;LeagueID=00) |

## Sensitivity and counterevidence

- Regular Season: accumulation versus scoring rate does not change the observed direction in this sample. Agreement on these metrics is not proof of overall superiority. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2548&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=202695&amp;PerMode=Totals&amp;LeagueID=00)
- Regular Season: raw versus contemporaneous relative efficiency does not change the observed direction in this sample. Agreement on these metrics is not proof of overall superiority. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2548&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=202695&amp;PerMode=Totals&amp;LeagueID=00)
- Playoffs: accumulation versus scoring rate does not change the observed direction in this sample. Agreement on these metrics is not proof of overall superiority. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2548&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=202695&amp;PerMode=Totals&amp;LeagueID=00)
- Playoffs: raw versus contemporaneous relative efficiency does not change the observed direction in this sample. Agreement on these metrics is not proof of overall superiority. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2548&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=202695&amp;PerMode=Totals&amp;LeagueID=00)

### Regular-season to postseason changes

| Subject | Points-per-game change | TS change (percentage points) | Sources |
|---|---:|---:|---|
| Dwyane Wade | 1.23 | 1.6 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2548&amp;PerMode=Totals&amp;LeagueID=00) |
| Kawhi Leonard | 3.9 | 1.31 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=202695&amp;PerMode=Totals&amp;LeagueID=00) |

## Context boundary

This focused claim did not request a supporting-cast or Finals-opponent investigation. The statistical result does not establish a context-independent ability ranking.

## Coverage and limits

- **Personal: completed** — Required collection completed; bounded sample limitations still apply.
- **Era: completed** — Required collection completed; bounded sample limitations still apply.
- Dwyane Wade, Playoffs: league-baseline shooting-opportunity coverage **100%**. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2548&amp;PerMode=Totals&amp;LeagueID=00)
- Dwyane Wade, Regular Season: league-baseline shooting-opportunity coverage **100%**. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2548&amp;PerMode=Totals&amp;LeagueID=00)
- Kawhi Leonard, Regular Season: league-baseline shooting-opportunity coverage **100%**. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=202695&amp;PerMode=Totals&amp;LeagueID=00)
- Kawhi Leonard, Playoffs: league-baseline shooting-opportunity coverage **100%**. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=202695&amp;PerMode=Totals&amp;LeagueID=00)
- Era-relative TS is a descriptive benchmark, not a causal correction for rules, physicality, spacing or defensive difficulty.
- True shooting uses the conventional 0.44 free-throw coefficient. It estimates shooting opportunities rather than counting actual possessions.
- Supporting-cast cases and opponent records are contextual samples. No teammate-swap or championship-credit calculation is justified.
- Linked evidence records retain exact scope, formulas, season inputs, original API parameters and retrieval timestamps. Aggregate citations use multiple API inputs; inspect the full source set in the evidence panel.
- No total player score is produced. All displayed advantages are specific to a metric and sample.</pre>

### Advisory semantic review

```json
{
  "question_coverage": {
    "status": "complete",
    "reason": "",
    "quote": "",
    "quote_verified": true
  },
  "scope": {
    "status": "respected",
    "reason": "",
    "quote": "",
    "quote_verified": true
  },
  "conclusion_limits": {
    "status": "respected",
    "reason": "",
    "quote": "",
    "quote_verified": true
  }
}
```
