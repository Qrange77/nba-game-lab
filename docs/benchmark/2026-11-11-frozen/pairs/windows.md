# windows

These are the complete original answers. The semantic ratings below are uncorrected model advisories and can misjudge optional metrics. See the [reviewed benchmark](../REVIEWED.md) for the final interpretation.

Assess whether Kobe Bryant's scoring in 2005-06 through 2007-08 was stronger than Stephen Curry's scoring in 2014-15 through 2016-17. Compare equal three-season windows, regular-season scoring volume, raw shooting efficiency and contemporaneous league-relative efficiency. Show which metric advantages change with the statistical lens.

## Independent expected facts

| Player | Window | Phase | Metric | Expected | Required |
|---|---|---|---|---:|---|
| Kobe Bryant | 2005-2008 | Regular Season | PTS | 7585.0000 | False |
| Kobe Bryant | 2005-2008 | Regular Season | PPG | 31.7364 | True |
| Kobe Bryant | 2005-2008 | Regular Season | TS | 57.0750 | True |
| Kobe Bryant | 2005-2008 | Regular Season | RTS | 3.1897 | False |
| Stephen Curry | 2014-2017 | Regular Season | PTS | 6274.0000 | False |
| Stephen Curry | 2014-2017 | Regular Season | PPG | 26.3613 | True |
| Stephen Curry | 2014-2017 | Regular Season | TS | 64.4736 | True |
| Stephen Curry | 2014-2017 | Regular Season | RTS | 10.2005 | False |

## Raw complete answer

[Full run metadata](../results/windows-raw.json) · [Audit](../audits/windows-raw.json)

<pre>Comparing Kobe Bryant’s three-season scoring peak from **2005-06 through 2007-08** to Stephen Curry’s three-season scoring peak from **2014-15 through 2016-17** is one of the most fascinating debates in modern basketball analytics. It pits historic isolation volume and tough-shot conversion against unprecedented perimeter gravity, historic efficiency, and volume driven by the three-point revolution. 

---

### 1. Regular-Season Scoring Volume

When evaluating pure volume, Kobe Bryant and Stephen Curry approached scoring from different stylistic foundations, yet both produced historic outputs.

*   **Kobe Bryant (2005-06 to 2007-08):**
    *   *2005-06:* 35.4 PPG (The highest single-season average since Michael Jordan in 1986-87)
    *   *2006-07:* 31.6 PPG (Led the NBA)
    *   *2007-08:* 28.3 PPG
    *   **Three-Season Total / Average:** **31.8 PPG**
    *   *Volume Context:* Bryant carried a historically weak post-Shaq Lakers supporting cast, resulting in a massive usage rate (estimated at ~38.7% in 2005-06). He scored 2,832 points in 80 games during the 2005-06 season alone.

*   **Stephen Curry (2014-15 to 2016-17):**
    *   *2014-15:* 23.8 PPG 
    *   *2015-16:* 30.1 PPG (First unanimous MVP, highest PPG in the modern era on under 35 minutes per game)
    *   *2016-17:* 25.3 PPG (Shared floor with high-volume scorer Kevin Durant)
    *   **Three-Season Total / Average:** **26.4 PPG**
    *   *Volume Context:* Curry’s volume is suppressed by playing in Steve Kerr’s ball-movement system and sitting out numerous fourth quarters due to blowout victories (especially in 73-win 2015-16). 

**Volume Advantage:** **Kobe Bryant.** Bryant outscored Curry by 5.4 points per game across the three-season window, playing significantly more total minutes and shouldering a heavier offensive burden as a primary isolation creator.

---

### 2. Raw Shooting Efficiency

Raw efficiency measures the direct conversion of shots into points without adjusting for era or position. 

*   **Kobe Bryant (2005-06 to 2007-08):**
    *   **FG%:** 45.1%
    *   **3P%:** 34.7%
    *   **FT%:** 85.3%
    *   **True Shooting Percentage (TS%):** **56.3%**
    *   *Raw Efficiency Context:* Bryant took an immense number of difficult, contested, late-shot-clock jump shots. Maintaining a 56.3% TS% while taking over 27 shots a game with virtually no spacing is an incredible feat of raw skill, though low by modern efficiency standards.

*   **Stephen Curry (2014-15 to 2016-17):**
    *   **FG%:** 50.4%
    *   **3P%:** 43.6%
    *   **FT%:** 90.8%
    *   **True Shooting Percentage (TS%):** **62.7%**
    *   *Raw Efficiency Context:* Curry achieved the holy grail of scoring: the 50/40/90 club in 2015-16 while averaging 30+ PPG. His effective field goal percentage (eFG%) was driven by historic volume and conversion from beyond the arc.

**Raw Efficiency Advantage:** **Stephen Curry.** A +6.4% gap in True Shooting Percentage is a massive chasm in scoring efficiency, especially given that Curry&#x27;s scoring was achieved on high volume.

---

### 3. Contemporaneous League-Relative Efficiency (rTS%)

Raw shooting numbers favor modern players because modern spacing, rule changes (hand-checking ban evolution), and the three-point revolution have inflated league-wide efficiency. To level the playing field, we look at **True Shooting Relative to League Average (rTS%)**—how much more efficient a player was compared to the average NBA player during their respective window.

*   **League Average TS% (Mid-2000s vs. Mid-2010s):**
    *   *2005-08 Average League TS%:* ~53.8% to 54.0%
    *   *2014-17 Average League TS%:* ~53.4% to 55.2% (rising rapidly during this window)

*   **Kobe Bryant (2005-06 to 2007-08):**
    *    Bryant&#x27;s TS%: ~56.3%
    *   **Estimated rTS%:** **+2.3% to +2.5% above league average**

*   **Stephen Curry (2014-15 to 2016-17):**
    *   Curry&#x27;s TS%: ~62.7%
    *   **Estimated rTS%:** **+8.0% to +9.5% above league average** (Peak 2015-16 was roughly +11% above league average).

**League-Relative Efficiency Advantage:** **Stephen Curry.** Even when adjusting for the tougher defensive eras and lower spacing of the mid-2000s, Curry remains historically superior in converting possessions into points relative to his peers.

---

### 4. How Metric Advantages Shift with the Statistical Lens

The conclusion of this comparison depends entirely on the analytical framework applied:

#### Lens A: The Traditional &amp; Isolation Lens (Favors Bryant)
*   **Metrics used:** PPG, Usage Rate, Shot-Creation Difficulty, Playoff/Clutch ISO scoring.
*   **The Argument:** Bryant generated his scoring entirely out of isolation and pick-and-rolls against set, packed-paint defenses designed specifically to stop him (due to a lack of floor-spacing teammates). He created his own shot from nothing at a higher volume. Curry benefited from a system, elite passing teammates (Draymond Green), and the threat of screens that forced defenses into compromised positions. 
*   **Verdict:** **Bryant wins.**

#### Lens B: The Modern Analytics &amp; Possession-Value Lens (Favors Curry)
*   **Metrics used:** True Shooting Percentage (TS%), Points Per Possession (PPP), Offensive Rating impact, Gravity.
*   **The Argument:** Basketball is ultimately about efficiency and maximizing expected value. Curry’s 2015-16 season is statistically one of the three greatest offensive seasons in NBA history. Furthermore, Curry’s &quot;gravity&quot;—the sheer panic he caused defenses 35 feet from the basket—created open shots for teammates in a way Bryant’s ball-dominant style did not. Curry scored nearly as many points (30.1) on significantly fewer possessions, preserving team ball movement.
*   **Verdict:** **Curry wins.**

---

### Final Assessment

*   **Kobe Bryant’s 2005-08 window** was a masterclass in **maximum individual volume and tough-shot creation**, producing one of the highest-scoring peaks ever witnessed under adverse roster conditions.
*   **Stephen Curry’s 2014-17 window** was a masterclass in **historic efficiency and spatial dominance**, turning perimeter shooting into an unprecedented offensive weapon.

**Summary:** If you value the sheer weight of **points per game and self-created isolation volume**, **Kobe Bryant&#x27;s** scoring peak was stronger. If you value **efficiency, value per possession, and overall offensive footprint**, **Stephen Curry&#x27;s** scoring peak was stronger. Across modern analytical frameworks, Curry’s historic efficiency gives him the edge, but Bryant remains the benchmark for high-usage, high-difficulty volume scoring.</pre>

### Advisory semantic review

```json
{
  "question_coverage": {
    "status": "partial",
    "reason": "The answer provides three-season PPG and TS averages for both players, but does not provide exact total PTS or exact aggregated RTS numbers, only giving ranges for RTS.",
    "quote": "Three-Season Total / Average: 31.8 PPG",
    "quote_verified": false
  },
  "scope": {
    "status": "respected",
    "reason": "The extracted values correspond to the requested three-season regular season windows for both players.",
    "quote": "Kobe Bryant (2005-06 to 2007-08)... Stephen Curry (2014-15 to 2016-17)",
    "quote_verified": false
  },
  "conclusion_limits": {
    "status": "respected",
    "reason": "The extracted claims directly reflect the text without overstepping into unstated calculations.",
    "quote": "",
    "quote_verified": true
  }
}
```

## Agent complete answer

[Full run metadata](../results/windows-agent.json) · [Audit](../audits/windows-agent.json)

<pre># Scoring Claim Review

**Verdict: Conditional: the broad claim is not uniformly supported across the selected metrics.**

&gt; Kobe Bryant&#x27;s scoring in 2005-06 through 2007-08 was stronger than Stephen Curry&#x27;s scoring in 2014-15 through 2016-17

This adjudication concerns the selected scoring statistics. It does not rank overall players or establish innate ability, defensive impact, or championship causation.

## Comparison contract

- Subjects: **Kobe Bryant** and **Stephen Curry**.
- Scope: 2005-06–2007-08 versus 2014-15–2016-17; Regular Season.
- Statistical lens: overall scoring.
- Completed-season cutoff: **2025-26**; ongoing seasons are excluded.
- Percentages are recomputed from summed inputs. Missing observations remain missing.
- Relative efficiency uses same-season, same-phase league TS; career aggregation weights each season by FGA + 0.44 × FTA.

## Evidence selected by the Writer

- Regular Season / Points per game: Kobe Bryant has the larger observed value. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=977&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201939&amp;PerMode=Totals&amp;LeagueID=00)
- Regular Season / Raw true shooting: Stephen Curry has the larger observed value. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=977&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201939&amp;PerMode=Totals&amp;LeagueID=00)
- Regular Season / Contemporaneous relative true shooting: Stephen Curry has the larger observed value. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=977&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201939&amp;PerMode=Totals&amp;LeagueID=00)

## Comparable evidence

| Phase | Statistical lens | Kobe Bryant | Stephen Curry | Observed advantage | Sources |
|---|---|---:|---:|---|---|
| Regular Season | Accumulated points (total) | 7,585 | 6,274 | Kobe Bryant | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=977&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201939&amp;PerMode=Totals&amp;LeagueID=00) |
| Regular Season | Points per game (per game) | 31.74 | 26.36 | Kobe Bryant | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=977&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201939&amp;PerMode=Totals&amp;LeagueID=00) |
| Regular Season | Raw true shooting (%) | 57.08 | 64.47 | Stephen Curry | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=977&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201939&amp;PerMode=Totals&amp;LeagueID=00) |
| Regular Season | Contemporaneous relative true shooting (percentage points) | 3.19 | 10.2 | Stephen Curry | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=977&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201939&amp;PerMode=Totals&amp;LeagueID=00) |

## Sensitivity and counterevidence

- Regular Season: accumulation versus scoring rate does not change the observed direction in this sample. Agreement on these metrics is not proof of overall superiority. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=977&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201939&amp;PerMode=Totals&amp;LeagueID=00)
- Regular Season: raw versus contemporaneous relative efficiency does not change the observed direction in this sample. Agreement on these metrics is not proof of overall superiority. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=977&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201939&amp;PerMode=Totals&amp;LeagueID=00)

## Context boundary

This focused claim did not request a supporting-cast or Finals-opponent investigation. The statistical result does not establish a context-independent ability ranking.

## Coverage and limits

- **Personal: completed** — Required collection completed; bounded sample limitations still apply.
- **Era: completed** — Required collection completed; bounded sample limitations still apply.
- Stephen Curry, Regular Season: league-baseline shooting-opportunity coverage **100%**. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=201939&amp;PerMode=Totals&amp;LeagueID=00)
- Kobe Bryant, Regular Season: league-baseline shooting-opportunity coverage **100%**. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=977&amp;PerMode=Totals&amp;LeagueID=00)
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
