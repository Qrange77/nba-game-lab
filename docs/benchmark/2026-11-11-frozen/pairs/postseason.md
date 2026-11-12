# postseason

These are the complete original answers. The semantic ratings below are uncorrected model advisories and can misjudge optional metrics. See the [reviewed benchmark](../REVIEWED.md) for the final interpretation.

Assess the claim that Michael Jordan had stronger postseason scoring than LeBron James. Compare Jordan's 1990-91 through 1992-93 with James's 2011-12 through 2013-14, using postseason points per game, true shooting and their changes from the corresponding regular seasons. Limit conclusions to these equal three-season samples.

## Independent expected facts

| Player | Window | Phase | Metric | Expected | Required |
|---|---|---|---|---:|---|
| Michael Jordan | 1990-1993 | Regular Season | PTS | 7525.0000 | False |
| Michael Jordan | 1990-1993 | Regular Season | PPG | 31.3542 | True |
| Michael Jordan | 1990-1993 | Regular Season | TS | 58.2142 | True |
| Michael Jordan | 1990-1993 | Playoffs | PTS | 1954.0000 | False |
| Michael Jordan | 1990-1993 | Playoffs | PPG | 33.6897 | True |
| Michael Jordan | 1990-1993 | Playoffs | TS | 57.2135 | True |
| Michael Jordan | 1990-1993 | Playoffs minus Regular Season | PPG_CHANGE | 2.3355 | True |
| Michael Jordan | 1990-1993 | Playoffs minus Regular Season | TS_CHANGE | -1.0007 | True |
| LeBron James | 2011-2014 | Regular Season | PTS | 5808.0000 | False |
| LeBron James | 2011-2014 | Regular Season | PPG | 27.0140 | True |
| LeBron James | 2011-2014 | Regular Season | TS | 63.2724 | True |
| LeBron James | 2011-2014 | Playoffs | PTS | 1841.0000 | False |
| LeBron James | 2011-2014 | Playoffs | PPG | 27.8939 | True |
| LeBron James | 2011-2014 | Playoffs | TS | 60.3860 | True |
| LeBron James | 2011-2014 | Playoffs minus Regular Season | PPG_CHANGE | 0.8800 | True |
| LeBron James | 2011-2014 | Playoffs minus Regular Season | TS_CHANGE | -2.8864 | True |

## Raw complete answer

[Full run metadata](../results/postseason-raw.json) · [Audit](../audits/postseason-raw.json)

<pre>To assess the claim that Michael Jordan had stronger postseason scoring than LeBron James, we can compare their statistics across two specific, highly dominant three-season peaks: Michael Jordan’s first three-peat span (1990–91 to 1992–93) and LeBron James’s first three championship seasons (2011–12 to 2013–14). 

Below is the statistical breakdown using postseason points per game (PPG), true shooting percentage (TS%), and the differential (change) between their postseason performance and the corresponding regular seasons.

---

### Data Summary (Averages across the 3-season samples)

#### **Michael Jordan (1990–91 to 1992–93)**
* **Postseason PPG:** **33.8**
* **Postseason True Shooting Percentage (TS%):** **56.6%**
* **Scoring Change (Postseason PPG minus Regular Season PPG):** **+1.6** *(Reg Season: 32.2 PPG)*
* **Efficiency Change (Postseason TS% minus Regular Season TS%):** **-1.3%** *(Reg Season: 57.9% TS)*

#### **LeBron James (2011–12 to 2013–14)**
* **Postseason PPG:** **28.7**
* **Postseason True Shooting Percentage (TS%):** **60.3%**
* **Scoring Change (Postseason PPG minus Regular Season PPG):** **+1.6** *(Reg Season: 27.1 PPG)*
* **Efficiency Change (Postseason TS% minus Regular Season TS%):** **+2.3%** *(Reg Season: 58.0% TS)*

---

### Comparative Assessment

#### 1. Postseason Points Per Game (Volume)
* **Advantage: Michael Jordan**
* **Analysis:** Jordan holds a decisive edge in raw scoring volume. During this three-season window, Jordan averaged **33.8 PPG** in the playoffs, compared to James’s **28.7 PPG**—a difference of 5.1 points per game. Jordan&#x27;s scoring load was historically heavy, including a 1992 postseason where he averaged 34.5 PPG and a 1993 finals performance where he averaged a record 41.0 PPG against the Phoenix Suns. 

#### 2. True Shooting Percentage (Scoring Efficiency)
* **Advantage: LeBron James**
* **Analysis:** James was the more efficient postseason scorer during their respective samples. James posted a **60.3% TS**, while Jordan sat at **56.6% TS**. While Jordan’s efficiency was elite for a high-volume guard in the early 1990s (surpassing league averages significantly), James benefited from playing in an era with more spacing and maintaining a higher proportion of shots at the rim and from behind the arc. 

#### 3. Change from Regular Season (Contextual Escalation)
* **Volume Escalation (Tie):** Both players elevated their scoring volume by the exact same margin when transitioning from the regular season to the playoffs. Both Jordan and James increased their scoring output by **+1.6 PPG** in the postseason compared to their regular-season baselines.
* **Efficiency Escalation (Advantage: LeBron James):** James actually became *more* efficient in the postseason compared to his regular season during this window, seeing his True Shooting rise by **+2.3%**. Conversely, Jordan experienced a slight dip in efficiency in the postseason, with his TS% dropping by **-1.3%** relative to his regular season, largely due to the increased defensive intensity and physicality playoff opponents directed at him as the primary offensive focal point.

---

### Conclusion

Within the limits of these two specific three-season samples:

* **Michael Jordan** had the stronger postseason scoring **volume**, outscoring James by over five points per game while matching James&#x27;s ability to elevate his scoring output relative to the regular season.
* **LeBron James** had the stronger postseason scoring **efficiency**, maintaining a significantly higher True Shooting percentage and actually improving his efficiency from the regular season to the playoffs, whereas Jordan&#x27;s efficiency dipped slightly. 

Therefore, whether Jordan&#x27;s scoring was &quot;stronger&quot; depends entirely on how one weighs volume versus efficiency: **Jordan was a more prolific postseason scorer, while James was a more efficient one.**</pre>

### Advisory semantic review

```json
{
  "question_coverage": {
    "status": "partial",
    "reason": "Total points (PTS) for regular season and playoffs for both players were not provided, only per-game and percentage metrics.",
    "quote": "",
    "quote_verified": true
  },
  "scope": {
    "status": "respected",
    "reason": "All extracted values correspond strictly to the requested three-season samples for both players.",
    "quote": "Michael Jordan (1990\u201391 to 1992\u201393) and LeBron James (2011\u201312 to 2013\u201314)",
    "quote_verified": false
  },
  "conclusion_limits": {
    "status": "respected",
    "reason": "Conclusions are appropriately limited to the specified samples and metrics.",
    "quote": "Within the limits of these two specific three-season samples:",
    "quote_verified": true
  }
}
```

## Agent complete answer

[Full run metadata](../results/postseason-agent.json) · [Audit](../audits/postseason-agent.json)

<pre># Scoring Claim Review

**Verdict: Conditional: the broad claim is not uniformly supported across the selected metrics.**

&gt; Michael Jordan had stronger postseason scoring than LeBron James in their respective three-season windows (Jordan 1990-91 through 1992-93 vs LeBron 2011-12 through 2013-14) using postseason points per game, true shooting, and regular-season changes.

This adjudication concerns the selected scoring statistics. It does not rank overall players or establish innate ability, defensive impact, or championship causation.

## Comparison contract

- Subjects: **Michael Jordan** and **LeBron James**.
- Scope: 1990-91–1992-93 versus 2011-12–2013-14; Regular Season, Playoffs.
- Statistical lens: postseason.
- Completed-season cutoff: **2025-26**; ongoing seasons are excluded.
- Percentages are recomputed from summed inputs. Missing observations remain missing.
- Relative efficiency uses same-season, same-phase league TS; career aggregation weights each season by FGA + 0.44 × FTA.

## Evidence selected by the Writer

- Playoffs / Points per game: Michael Jordan has the larger observed value. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00)
- Playoffs / Raw true shooting: LeBron James has the larger observed value. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00)
- Playoffs / Contemporaneous relative true shooting: LeBron James has the larger observed value. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00)

## Comparable evidence

| Phase | Statistical lens | Michael Jordan | LeBron James | Observed advantage | Sources |
|---|---|---:|---:|---|---|
| Regular Season | Accumulated points (total) | 7,525 | 5,808 | Michael Jordan | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| Regular Season | Points per game (per game) | 31.35 | 27.01 | Michael Jordan | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| Regular Season | Raw true shooting (%) | 58.21 | 63.27 | LeBron James | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| Regular Season | Contemporaneous relative true shooting (percentage points) | 4.81 | 9.82 | LeBron James | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| Playoffs | Accumulated points (total) | 1,954 | 1,841 | Michael Jordan | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| Playoffs | Points per game (per game) | 33.69 | 27.89 | Michael Jordan | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| Playoffs | Raw true shooting (%) | 57.21 | 60.39 | LeBron James | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| Playoffs | Contemporaneous relative true shooting (percentage points) | 3.22 | 7.33 | LeBron James | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |

## Sensitivity and counterevidence

- Regular Season: accumulation versus scoring rate does not change the observed direction in this sample. Agreement on these metrics is not proof of overall superiority. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00)
- Regular Season: raw versus contemporaneous relative efficiency does not change the observed direction in this sample. Agreement on these metrics is not proof of overall superiority. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00)
- Playoffs: accumulation versus scoring rate does not change the observed direction in this sample. Agreement on these metrics is not proof of overall superiority. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00)
- Playoffs: raw versus contemporaneous relative efficiency does not change the observed direction in this sample. Agreement on these metrics is not proof of overall superiority. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00)

### Regular-season to postseason changes

| Subject | Points-per-game change | TS change (percentage points) | Sources |
|---|---:|---:|---|
| Michael Jordan | 2.34 | -1 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) |
| LeBron James | 0.88 | -2.89 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |

## Context boundary

This focused claim did not request a supporting-cast or Finals-opponent investigation. The statistical result does not establish a context-independent ability ranking.

## Coverage and limits

- **Personal: completed** — Required collection completed; bounded sample limitations still apply.
- **Era: completed** — Required collection completed; bounded sample limitations still apply.
- Michael Jordan, Playoffs: league-baseline shooting-opportunity coverage **100%**. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00)
- Michael Jordan, Regular Season: league-baseline shooting-opportunity coverage **100%**. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00)
- LeBron James, Regular Season: league-baseline shooting-opportunity coverage **100%**. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00)
- LeBron James, Playoffs: league-baseline shooting-opportunity coverage **100%**. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00)
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
