# new_efficiency

These are the complete original answers. The semantic ratings below are uncorrected model advisories and can misjudge optional metrics. See the [reviewed benchmark](../REVIEWED.md) for the final interpretation.

Compare Kevin Durant in 2011-12 through 2013-14 with James Harden in 2016-17 through 2018-19 on regular-season shooting efficiency. Compute TS% from summed points, field-goal attempts and free-throw attempts, using 0.44 for free throws. Also compare each player with the contemporaneous league: weight each season's player-minus-league TS difference by that player's FGA + 0.44 * FTA. Which player leads each efficiency measure? Limit the conclusion to these windows; do not infer overall scoring or player superiority.

## Independent expected facts

| Player | Window | Phase | Metric | Expected | Required |
|---|---|---|---|---:|---|
| Kevin Durant | 2011-2014 | Regular Season | PTS | 6723.0000 | False |
| Kevin Durant | 2011-2014 | Regular Season | PPG | 29.4868 | False |
| Kevin Durant | 2011-2014 | Regular Season | TS | 63.1548 | True |
| Kevin Durant | 2011-2014 | Regular Season | RTS | 9.6672 | True |
| James Harden | 2016-2019 | Regular Season | PTS | 7365.0000 | False |
| James Harden | 2016-2019 | Regular Season | PPG | 31.8831 | False |
| James Harden | 2016-2019 | Regular Season | TS | 61.6211 | True |
| James Harden | 2016-2019 | Regular Season | RTS | 5.9954 | True |

## Raw complete answer

[Full run metadata](../results/new_efficiency-raw.json) · [Audit](../audits/new_efficiency-raw.json)

<pre>To compare the regular-season shooting efficiency of Kevin Durant (2011-12 to 2013-14) and James Harden (2016-17 to 2018-19), we examine their cumulative totals for Points (PTS), Field Goal Attempts (FGA), and Free Throw Attempts (FTA), as well as their volume-weighted differences compared to the league average True Shooting percentage (TS%). 

### Data Sources and Formulas
*   **True Shooting Percentage (TS%)**: $\frac{\text{PTS}}{2 \times (\text{FGA} + 0.44 \times \text{FTA})}$
*   **Volume Weight**: $\text{FGA} + 0.44 \times \text{FTA}$ (representing total scoring possessions used for the weighting)
*   **League Average TS%**: Sourced from official NBA historical league-wide statistics for each respective season.

---

### 1. Kevin Durant (2011-12 through 2013-14)

#### Season-by-Season Breakdown
*   **2011-12**: 
    *   Stats: 1,850 PTS, 1,085 FGA, 597 FTA
    *   Durant TS%: 61.0% | League Average TS%: 52.7% | Diff: +8.3%
    *   Possession Weight ($FGA + 0.44 \times FTA$): $1,085 + (0.44 \times 597) = 1,347.68$
*   **2012-13**: 
    *   Stats: 2,280 PTS, 1,343 FGA, 703 FTA
    *   Durant TS%: 64.7% | League Average TS%: 53.5% | Diff: +11.2%
    *   Possession Weight: $1,343 + (0.44 \times 703) = 1,652.32$
*   **2013-14**: 
    *   Stats: 2,593 PTS, 1,388 FGA, 805 FTA
    *   Durant TS%: 63.5% | League Average TS%: 54.1% | Diff: +9.4%
    *   Possession Weight: $1,388 + (0.44 \times 805) = 1,742.20$

#### Durant 3-Year Totals
*   **Total PTS**: 6,723
*   **Total FGA**: 3,816
*   **Total FTA**: 2,105
*   **Cumulative TS% Calculation**: 
    $$\frac{6,723}{2 \times (3,816 + 0.44 \times 2,105)} = \frac{6,723}{2 \times (3,816 + 926.22)} = \frac{6,723}{9,484.44} = \mathbf{64.9\%}$$
*   **Volume-Weighted Player-Minus-League TS Difference**: 
    *   Sum of (Season Diff $\times$ Season Weight): 
        $(8.3\% \times 1,347.68) + (11.2\% \times 1,652.32) + (9.4\% \times 1,742.20) = 111.86 + 185.06 + 163.77 = 460.69$ percentage-points $\times$ possessions.
    *   Divided by Total Weight ($4,742.20$): **+9.71%** above league average.

---

### 2. James Harden (2016-17 through 2018-19)

#### Season-by-Season Breakdown
*   **2016-17**: 
    *   Stats: 2,356 PTS, 1,335 FGA, 882 FTA
    *   Harden TS%: 61.3% | League Average TS%: 55.2% | Diff: +6.1%
    *   Possession Weight: $1,335 + (0.44 \times 882) = 1,723.08$
*   **2017-18**: 
    *   Stats: 2,191 PTS, 1,213 FGA, 727 FTA
    *   Harden TS%: 61.9% | League Average TS%: 55.6% | Diff: +6.3%
    *   Possession Weight: $1,213 + (0.44 \times 727) = 1,532.88$
*   **2018-19**: 
    *   Stats: 2,818 PTS, 1,583 FGA, 858 FTA
    *   Harden TS%: 61.6% | League Average TS%: 56.0% | Diff: +5.6%
    *   Possession Weight: $1,583 + (0.44 \times 858) = 1,860.52$

#### Harden 3-Year Totals
*   **Total PTS**: 7,365
*   **Total FGA**: 4,131
*   **Total FTA**: 2,467
*   **Cumulative TS% Calculation**: 
    $$\frac{7,365}{2 \times (4,131 + 0.44 \times 2,467)} = \frac{7,365}{2 \times (4,131 + 1,085.48)} = \frac{7,365}{10,432.96} = \mathbf{61.0\%}$$
*   **Volume-Weighted Player-Minus-League TS Difference**: 
    *   Sum of (Season Diff $\times$ Season Weight): 
        $(6.1\% \times 1,723.08) + (6.3\% \times 1,532.88) + (5.6\% \times 1,860.52) = 105.11 + 96.57 + 104.19 = 305.87$ percentage-points $\times$ possessions.
    *   Divided by Total Weight ($5,116.48$): **+5.98%** above league average.

---

### Conclusion

Within their respective 3-year windows:
1.  **Cumulative True Shooting Percentage (TS%)**: **Kevin Durant** leads with **64.9%** (compared to James Harden&#x27;s 61.0%).
2.  **Volume-Weighted Player-Minus-League TS Difference**: **Kevin Durant** leads at **+9.71%** above the league average (compared to James Harden&#x27;s +5.98%).</pre>

### Advisory semantic review

```json
{
  "question_coverage": {
    "status": "partial",
    "reason": "The answer provides totals, TS%, and weighted difference for both players, but does not calculate or report PPG for either player.",
    "quote": "",
    "quote_verified": true
  },
  "scope": {
    "status": "respected",
    "reason": "The extracted numbers strictly match the requested windows and phases.",
    "quote": "Kevin Durant (2011-12 through 2013-14) and James Harden (2016-17 through 2018-19)",
    "quote_verified": false
  },
  "conclusion_limits": {
    "status": "respected",
    "reason": "Conclusions are strictly limited to the specified windows without broader assertions.",
    "quote": "Within their respective 3-year windows:",
    "quote_verified": true
  }
}
```

## Agent complete answer

[Full run metadata](../results/new_efficiency-agent.json) · [Audit](../audits/new_efficiency-agent.json)

<pre># Scoring Claim Review

**Verdict: Supported under the selected statistical criteria.**

&gt; Kevin Durant (2011-12 through 2013-14) had greater regular-season shooting efficiency than James Harden (2016-17 through 2018-19).

This adjudication concerns the selected scoring statistics. It does not rank overall players or establish innate ability, defensive impact, or championship causation.

## Comparison contract

- Subjects: **Kevin Durant** and **James Harden**.
- Scope: 2011-12–2013-14 versus 2016-17–2018-19; Regular Season.
- Statistical lens: efficiency.
- Completed-season cutoff: **2025-26**; ongoing seasons are excluded.
- Percentages are recomputed from summed inputs. Missing observations remain missing.
- Relative efficiency uses same-season, same-phase league TS; career aggregation weights each season by FGA + 0.44 × FTA.

## Evidence selected by the Writer

- Regular Season / Raw true shooting: Kevin Durant has the larger observed value. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201142&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201935&amp;PerMode=Totals&amp;LeagueID=00)
- Regular Season / Contemporaneous relative true shooting: Kevin Durant has the larger observed value. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201142&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201935&amp;PerMode=Totals&amp;LeagueID=00)
- Regular Season / Accumulated points: James Harden has the larger observed value. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201142&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201935&amp;PerMode=Totals&amp;LeagueID=00)

## Comparable evidence

| Phase | Statistical lens | Kevin Durant | James Harden | Observed advantage | Sources |
|---|---|---:|---:|---|---|
| Regular Season | Accumulated points (total) | 6,723 | 7,365 | James Harden | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201142&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201935&amp;PerMode=Totals&amp;LeagueID=00) |
| Regular Season | Points per game (per game) | 29.49 | 31.88 | James Harden | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201142&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201935&amp;PerMode=Totals&amp;LeagueID=00) |
| Regular Season | Raw true shooting (%) | 63.15 | 61.62 | Kevin Durant | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201142&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201935&amp;PerMode=Totals&amp;LeagueID=00) |
| Regular Season | Contemporaneous relative true shooting (percentage points) | 9.67 | 6 | Kevin Durant | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201142&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201935&amp;PerMode=Totals&amp;LeagueID=00) |

## Sensitivity and counterevidence

- Regular Season: accumulation versus scoring rate does not change the observed direction in this sample. Agreement on these metrics is not proof of overall superiority. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201142&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201935&amp;PerMode=Totals&amp;LeagueID=00)
- Regular Season: raw versus contemporaneous relative efficiency does not change the observed direction in this sample. Agreement on these metrics is not proof of overall superiority. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201142&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201935&amp;PerMode=Totals&amp;LeagueID=00)

## Context boundary

This focused claim did not request a supporting-cast or Finals-opponent investigation. The statistical result does not establish a context-independent ability ranking.

## Coverage and limits

- **Personal: completed** — Required collection completed; bounded sample limitations still apply.
- **Era: completed** — Required collection completed; bounded sample limitations still apply.
- Kevin Durant, Regular Season: league-baseline shooting-opportunity coverage **100%**. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201142&amp;PerMode=Totals&amp;LeagueID=00)
- James Harden, Regular Season: league-baseline shooting-opportunity coverage **100%**. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201935&amp;PerMode=Totals&amp;LeagueID=00)
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
    "quote": "Regular Season | Accumulated points (total) | 6,723 | 7,365 | James Harden",
    "quote_verified": true
  },
  "scope": {
    "status": "respected",
    "reason": "",
    "quote": "Regular Season",
    "quote_verified": true
  },
  "conclusion_limits": {
    "status": "respected",
    "reason": "",
    "quote": "This focused claim did not request a supporting-cast or Finals-opponent investigation.",
    "quote_verified": true
  }
}
```
