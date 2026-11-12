# career

These are the complete original answers. The semantic ratings below are uncorrected model advisories and can misjudge optional metrics. See the [reviewed benchmark](../REVIEWED.md) for the final interpretation.

Assess the claim that Michael Jordan was a stronger scorer than LeBron James over their entire NBA careers. Compare regular-season and playoff scoring volume and efficiency, efficiency relative to each season's league, and bounded teammate and Finals-opponent context. Use completed seasons through 2025-26. Give a conditional judgement, not an overall-player ranking.

## Independent expected facts

| Player | Window | Phase | Metric | Expected | Required |
|---|---|---|---|---:|---|
| Michael Jordan | 1984-2026 | Regular Season | PTS | 32292.0000 | False |
| Michael Jordan | 1984-2026 | Regular Season | PPG | 30.1231 | True |
| Michael Jordan | 1984-2026 | Regular Season | TS | 56.8588 | True |
| Michael Jordan | 1984-2026 | Regular Season | RTS | 3.4229 | False |
| Michael Jordan | 1984-2026 | Playoffs | PTS | 5987.0000 | False |
| Michael Jordan | 1984-2026 | Playoffs | PPG | 33.4469 | True |
| Michael Jordan | 1984-2026 | Playoffs | TS | 56.7591 | True |
| Michael Jordan | 1984-2026 | Playoffs | RTS | 2.8594 | False |
| LeBron James | 1984-2026 | Regular Season | PTS | 43440.0000 | False |
| LeBron James | 1984-2026 | Regular Season | PPG | 26.7818 | True |
| LeBron James | 1984-2026 | Regular Season | TS | 59.0146 | True |
| LeBron James | 1984-2026 | Regular Season | RTS | 4.1945 | False |
| LeBron James | 1984-2026 | Playoffs | PTS | 8521.0000 | False |
| LeBron James | 1984-2026 | Playoffs | PPG | 28.2152 | True |
| LeBron James | 1984-2026 | Playoffs | TS | 58.3384 | True |
| LeBron James | 1984-2026 | Playoffs | RTS | 4.0064 | False |

## Raw complete answer

[Full run metadata](../results/career-raw.json) · [Audit](../audits/career-raw.json)

<pre>To assess whether Michael Jordan was a stronger scorer than LeBron James over their entire NBA careers, we must evaluate them through four analytical lenses: regular-season volume and efficiency, playoff volume and efficiency, era-adjusted relative efficiency, and the contextual constraints of teammates and Finals opponents. 

*(Note: Data is evaluated through the completed 2024-25 season and current 2025-26 trajectories.)*

---

### 1. Regular-Season Volume and Efficiency

*   **Michael Jordan:** Jordan played 15 NBA seasons, averaging **30.1 points per game (PPG)** for his career, the highest mark in NBA history. His career regular-season True Shooting Percentage (**TS%**) was **56.9%**. He captured 10 scoring titles, averaging over 30 PPG in eight different seasons (including a peak of 37.1 PPG in 1986–87).
*   **LeBron James:** LeBron is the NBA’s all-time leading scorer, playing 22+ seasons with a career regular-season average of approximately **27.1 PPG**. His career regular-season **TS%** is significantly higher at **58.9%**. While he has only one scoring title (2007–08), his scoring longevity is unparalleled, having averaged at least 25 PPG for 21 consecutive seasons.

**The Verdict on Regular Season:** Jordan holds a clear advantage in peak scoring volume and raw per-game output (+3.0 PPG). LeBron holds the advantage in longevity and total cumulative volume, paired with a higher raw scoring efficiency (+2.0% TS).

---

### 2. Playoff Volume and Efficiency

*   **Michael Jordan:** In 179 playoff games, Jordan averaged **33.4 PPG** on **56.8% TS**. His playoff scoring output actually *increased* relative to his regular season, and his efficiency remained virtually identical despite facing elite defenses every night. 
*   **LeBron James:** In nearly 300 playoff games, LeBron averaged **28.4 PPG** on **58.3% TS**. Like Jordan, LeBron’s efficiency stays remarkably stable in the postseason, but his volume drops by roughly 1.5 PPG compared to his career regular-season average.

**The Verdict on Playoff Scoring:** Jordan is definitively the superior playoff volume scorer. He outscores LeBron by exactly 5.0 PPG in the postseason while maintaining essentially the same shooting efficiency. 

---

### 3. Efficiency Relative to Era (League-Relative Context)

Raw shooting percentages can be misleading because different eras have drastically different scoring environments. 
*   **Jordan&#x27;s Era (Late 1980s–1998):** Jordan played the bulk of his career during a brutal, physical, low-scoring era characterized by illegal defense rules that allowed heavy ball-watching, hard-fouling interior play, and slower paces. League average TS% during Jordan&#x27;s prime hovered around **53% to 54%**. Therefore, Jordan’s career 56.9% TS was roughly **3 to 4 percentage points above league average**.
*   **LeBron&#x27;s Era (2003–Present):** LeBron’s career spans the modern pacing boom, the three-point revolution, and the implementation of defensive three-second rules that opened up the lane. League average TS% during LeBron&#x27;s career has generally hovered around **55% to 58%**. Consequently, LeBron’s 58.9% TS is typically **1 to 3 percentage points above league average**.

**The Verdict on Relative Efficiency:** While LeBron has a higher *raw* TS%, Jordan was more efficient **relative to his peers**. Jordan consistently separated himself from a lower-scoring, more restrictive league average by a wider margin than LeBron has in a historically efficient offensive era.

---

### 4. Teammate Support and Finals-Opponent Context

A scorer&#x27;s output is heavily influenced by the defensive attention they draw, which is dictated by floor-spacing, teammate quality, and the defensive schemes of their opponents.

*   **Jordan&#x27;s Context:** 
    *   *Teammates:* Jordan played with elite complementary scorers (Scottie Pippen, Toni Kukoc) and historically great floor-spacers later in his career (Steve Kerr, Ron Harper), but the 1980s Bulls and early 90s teams often lacked reliable outside shooting. Teams routinely deployed radical double- and triple-teams (&quot;Jordan Rules&quot;) because his surrounding cast was sometimes limited offensively.
    *   *Finals Opponents:* Jordan faced elite defensive frontlines in the NBA Finals (e.g., the &quot;Bad Boy&quot; Pistons in the conference finals, the Showtime Lakers, the physical Portland Trail Blazers, and defensive stalwarts like the Utah Jazz and Seattle SuperSonics). Despite facing defenses explicitly designed to stop him without modern zone/help-defense rules, Jordan averaged 33.6 PPG across 35 Finals games.
*   **LeBron&#x27;s Context:**
    *   *Teammates:* LeBron has engineered or played in hyper-modern offensive systems surrounded by elite, elite-level shooters (Kyrie Irving, Ray Allen, Kevin Love, Anthony Davis, D&#x27;Angelo Russell) who command massive defensive gravity, preventing opponents from loading up exclusively on him.
    *   *Finals Opponents:* LeBron has faced historically elite defenses in the Finals, most notably the San Antonio Spurs dynasty and the Golden State Warriors (who deployed multi-layered switching and elite wing defenders like Andre Iguodala and Draymond Green). LeBron’s Finals scoring volume is exceptionally high (approx. 28.4 PPG), but he has occasionally had lower-scoring outlier games when defenses successfully forced him to be a distributor rather than a scorer.

**The Verdict on Context:** Jordan faced more restrictive structural defensive rules (illegal defense guidelines that prevented true zone help) and more physical contact, yet maintained higher scoring volume. LeBron faced more complex, scheme-heavy modern defenses, but has benefited from significantly better spatial spacing via modern offensive systems.

---

### Conditional Judgement

Whether Michael Jordan was a &quot;stronger scorer&quot; than LeBron James depends entirely on how one defines scoring strength:

1.  **If &quot;stronger scorer&quot; means peak volume, playoff dominance, and era-adjusted separation:** **Michael Jordan wins.** He is the greatest peak scorer in NBA history. He produced higher raw volume, significantly higher playoff volume (+5 PPG), and created a greater statistical gap between himself and his league-average peers in a much more hostile environment for individual slashers.
2.  **If &quot;stronger scorer&quot; means durability, cumulative output, and high-efficiency baseline longevity:** **LeBron James wins.** LeBron’s ability to maintain a 25+ PPG average for over two decades without a significant physical drop-off is unmatched, and his raw efficiency is slightly higher in a modern context.

**Final Conclusion:** For a single game, a playoff run, or a peak 5-to-10-year prime where maximum offensive output is required against elite defenses, **Michael Jordan is the stronger scorer.**</pre>

### Advisory semantic review

```json
{
  "question_coverage": {
    "status": "partial",
    "reason": "The answer provides PPG and TS% for both players in both the regular season and playoffs, but omits total cumulative points (PTS) and relative true shooting (RTS) metrics.",
    "quote": "Michael Jordan: Jordan played 15 NBA seasons, averaging 30.1 points per game (PPG)... His career regular-season True Shooting Percentage (TS%) was 56.9%... In 179 playoff games, Jordan averaged 33.4 PPG on 56.8% TS.",
    "quote_verified": false
  },
  "scope": {
    "status": "respected",
    "reason": "The extracted metrics correspond directly to the requested players, phases, and career windows.",
    "quote": "Michael Jordan... Regular Season... Playoffs... LeBron James... Regular Season... Playoffs",
    "quote_verified": false
  },
  "conclusion_limits": {
    "status": "respected",
    "reason": "The answer evaluates the claims through conditional lenses without overreaching into unproven causal assertions or overall-player rankings outside of scoring strength.",
    "quote": "Whether Michael Jordan was a \"stronger scorer\" than LeBron James depends entirely on how one defines scoring strength",
    "quote_verified": true
  }
}
```

## Agent complete answer

[Full run metadata](../results/career-agent.json) · [Audit](../audits/career-agent.json)

<pre># Scoring Claim Review

**Verdict: Conditional: the broad claim is not uniformly supported across the selected metrics.**

&gt; Michael Jordan was a stronger scorer than LeBron James over their entire NBA careers across regular-season and playoff scoring volume and efficiency, relative league efficiency, and bounded teammate and Finals-opponent context.

This adjudication concerns the selected scoring statistics. It does not rank overall players or establish innate ability, defensive impact, or championship causation.

## Comparison contract

- Subjects: **Michael Jordan** and **LeBron James**.
- Scope: Recorded careers through 2025-26; Regular Season, Playoffs.
- Statistical lens: overall scoring.
- Completed-season cutoff: **2025-26**; ongoing seasons are excluded.
- Percentages are recomputed from summed inputs. Missing observations remain missing.
- Relative efficiency uses same-season, same-phase league TS; career aggregation weights each season by FGA + 0.44 × FTA.

## Evidence selected by the Writer

- Regular Season / Points per game: Michael Jordan has the larger observed value. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00)
- Regular Season / Contemporaneous relative true shooting: LeBron James has the larger observed value. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00)
- Playoffs / Points per game: Michael Jordan has the larger observed value. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00)

## Comparable evidence

| Phase | Statistical lens | Michael Jordan | LeBron James | Observed advantage | Sources |
|---|---|---:|---:|---|---|
| Regular Season | Accumulated points (total) | 32,292 | 43,440 | LeBron James | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| Regular Season | Points per game (per game) | 30.12 | 26.78 | Michael Jordan | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| Regular Season | Raw true shooting (%) | 56.86 | 59.01 | LeBron James | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| Regular Season | Contemporaneous relative true shooting (percentage points) | 3.42 | 4.19 | LeBron James | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| Playoffs | Accumulated points (total) | 5,987 | 8,521 | LeBron James | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| Playoffs | Points per game (per game) | 33.45 | 28.22 | Michael Jordan | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| Playoffs | Raw true shooting (%) | 56.76 | 58.34 | LeBron James | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| Playoffs | Contemporaneous relative true shooting (percentage points) | 2.86 | 4.01 | LeBron James | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |

## Sensitivity and counterevidence

- Regular Season: accumulation versus scoring rate changes the observed advantage. The broad claim therefore depends on this choice of lens. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00)
- Regular Season: raw versus contemporaneous relative efficiency does not change the observed direction in this sample. Agreement on these metrics is not proof of overall superiority. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00)
- Playoffs: accumulation versus scoring rate changes the observed advantage. The broad claim therefore depends on this choice of lens. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00)
- Playoffs: raw versus contemporaneous relative efficiency does not change the observed direction in this sample. Agreement on these metrics is not proof of overall superiority. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00)

### Regular-season to postseason changes

| Subject | Points-per-game change | TS change (percentage points) | Sources |
|---|---:|---:|---|
| Michael Jordan | 3.32 | -0.1 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) |
| LeBron James | 1.43 | -0.68 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |

## Core helpers and rotation context

The same anchor rule is used for both subjects: earliest and latest verified Finals in the approved window, otherwise recorded playoff endpoints. These are case studies, not complete-career teammate rankings.

| Focal player / sample | Core helper candidate | PPG | MPG | Recorded games | TS% | Sources |
|---|---|---:|---:|---:|---:|---|
| Michael Jordan / 1990-91 / Playoffs | Scottie Pippen | 21.65 | 41.41 | 17 | 56.37 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=937&amp;PerMode=Totals&amp;LeagueID=00) |
| Michael Jordan / 1990-91 / Playoffs | Horace Grant | 13.29 | 39.18 | 17 | 61.95 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=270&amp;PerMode=Totals&amp;LeagueID=00) |
| Michael Jordan / 1997-98 / Playoffs | Scottie Pippen | 16.81 | 39.91 | 21 | 50.01 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) |
| Michael Jordan / 1997-98 / Playoffs | Toni Kukoc | 13.1 | 30.27 | 21 | 56.06 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) |
| LeBron James / 2006-07 / Playoffs | Zydrunas Ilgauskas | 12.55 | 32.43 | 20 | 55.31 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| LeBron James / 2006-07 / Playoffs | Drew Gooden | 11.4 | 30.27 | 20 | 52.26 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| LeBron James / 2019-20 / Playoffs | Anthony Davis | 27.71 | 36.61 | 21 | 66.47 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| LeBron James / 2019-20 / Playoffs | Kentavious Caldwell-Pope | 10.71 | 28.96 | 21 | 56 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |

Core candidates are selected by contemporary scoring production, not by career reputation or an overall ability score. The main rotation is retained by total minutes; its full minutes, production and availability rows appear in the supporting-cast details below the report. Games played do not identify injuries or actual shared court time.

## Finals opposition within the selected scope

| Subject | Season | Opponent | Team series W–L | Player PPG | Player TS% | Opponent regular-season win% | Sources |
|---|---|---|---:|---:|---:|---:|---|
| Michael Jordan | 1990-91 | Los Angeles Lakers | 4–1 | 31.2 | 61.17 | 70.7 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) |
| Michael Jordan | 1991-92 | Portland Trail Blazers | 4–2 | 35.83 | 61.7 | 69.5 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) |
| Michael Jordan | 1992-93 | Phoenix Suns | 4–2 | 41 | 55.77 | 75.6 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) |
| Michael Jordan | 1995-96 | Seattle SuperSonics | 4–2 | 27.33 | 53.78 | 78 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) |
| Michael Jordan | 1996-97 | Utah Jazz | 4–2 | 32.33 | 53.24 | 78 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) |
| Michael Jordan | 1997-98 | Utah Jazz | 4–2 | 33.5 | 51.59 | 75.6 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00) |
| LeBron James | 2006-07 | San Antonio Spurs | 0–4 | 22 | 42.82 | 70.7 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| LeBron James | 2010-11 | Dallas Mavericks | 2–4 | 17.83 | 54.15 | 69.5 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| LeBron James | 2011-12 | Oklahoma City Thunder | 4–1 | 28.6 | 55.75 | 71.2 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| LeBron James | 2012-13 | San Antonio Spurs | 4–3 | 25.29 | 52.94 | 70.7 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| LeBron James | 2013-14 | San Antonio Spurs | 1–4 | 28.2 | 67.95 | 75.6 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| LeBron James | 2014-15 | Golden State Warriors | 2–4 | 35.83 | 47.68 | 81.7 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| LeBron James | 2015-16 | Golden State Warriors | 4–3 | 29.71 | 56.24 | 89 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| LeBron James | 2016-17 | Golden State Warriors | 1–4 | 33.6 | 63.03 | 81.7 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| LeBron James | 2017-18 | Golden State Warriors | 0–4 | 34 | 61.98 | 70.7 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |
| LeBron James | 2019-20 | Miami Heat | 4–2 | 29.83 | 67.05 | 60.3 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00) |

Opponent regular-season record is one limited proxy. Finals wins and defeats are included; Finals-only player data must not be described as the whole postseason.

## Coverage and limits

- **Personal: completed** — Required collection completed; bounded sample limitations still apply.
- **Era: completed** — Required collection completed; bounded sample limitations still apply.
- **Teammates: completed** — Required collection completed; bounded sample limitations still apply.
- **Opponents: completed** — Required collection completed; bounded sample limitations still apply.
- LeBron James, Regular Season: league-baseline shooting-opportunity coverage **100%**. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&amp;PerMode=Totals&amp;LeagueID=00)
- Michael Jordan, Playoffs: league-baseline shooting-opportunity coverage **100%**. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00)
- Michael Jordan, Regular Season: league-baseline shooting-opportunity coverage **100%**. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&amp;PerMode=Totals&amp;LeagueID=00)
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
    "reason": "All required targets for Michael Jordan and LeBron James across regular season and playoffs for volume, efficiency, and relative efficiency are explicitly present in the answer's table.",
    "quote": "| Regular Season | Accumulated points (total) | 32,292 | 43,440 | LeBron James |",
    "quote_verified": true
  },
  "scope": {
    "status": "respected",
    "reason": "The answer provides career-spanning figures explicitly matching the requested players, phases, and metrics.",
    "quote": "Scope: Recorded careers through 2025-26; Regular Season, Playoffs.",
    "quote_verified": true
  },
  "conclusion_limits": {
    "status": "respected",
    "reason": "The answer avoids general overall-player rankings and restricts its conclusions to the evaluated scoring metrics.",
    "quote": "This adjudication concerns the selected scoring statistics. It does not rank overall players or establish innate ability, defensive impact, or championship causation.",
    "quote_verified": true
  }
}
```
