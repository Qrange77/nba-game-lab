# Changes: complete paired answers

Question: Compare Michael Jordan in 1990-91 and LeBron James in 2014-15 on on-court offensive and playmaking contributions across regular season and playoffs. Did higher postseason points per game represent improved performance? Investigate minutes, shot volume and efficiency if the indicators disagree.

Model: `vertex_ai/gemini-3.5-flash-lite`. [Full execution metadata](../changes.json).

## Agent

# On-Court Impact Review

## Answer

**My position: the available evidence does not establish one overall on-court winner. The supported advantages and unresolved dimensions are separated below.**
- **Offense and era:** Michael Jordan leads the selected measures across the requested phases.
- **Playmaking and ball security:** The indicators disagree; one player does not dominate all selected measures.

This position compares observed contributions, not innate ability. Offensive judgement uses PPG and TS; league-relative efficiency is a separate cross-era check. Playmaking uses assists per minute and assists/turnovers, not a complete model of creation.

**Scope:** 1990-91–1990-91 versus 2014-15–2014-15; Regular Season, Playoffs.

## Key evidence

- **Michael Jordan / 1990 / Regular Season**: Assists per 36 minutes **5.38** per 36 minutes; Assists per turnover **2.24** ratio. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00)
- **LeBron James / 2014 / Regular Season**: Assists per 36 minutes **7.38** per 36 minutes; Assists per turnover **1.88** ratio. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00)
- **LeBron James / 2014 / Playoffs**: Points per game **30.05** per game; True shooting **48.67** %. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00)

## Why we investigated further

- **Finding:** LeBron James has higher playoff PPG but lower TS. Check minutes, attempts and per-minute production before interpreting more points as broad improvement. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00)
- **Follow-up: Completed.** Matched minutes, attempts and per-minute scoring are shown below. More PPG alone does not establish broader improvement.
- **What the follow-up changes:** LeBron James has higher playoff PPG but lower shooting efficiency. Minutes/game changed from 36.13 to 42.2, attempts/game from 18.54 to 27.2, and points/36 minutes from 25.17 to 25.64. This separates additional playing/shot opportunity from efficiency; higher PPG is not an across-the-board improvement. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00)

## Evidence by dimension

### Offense and era

| Player / phase | Metric | Value | Source |
|---|---|---:|---|
| LeBron James / Playoffs | Recorded games (games) | 20 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Playoffs | Minutes per game (per game) | 42.2 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Playoffs | Points per game (per game) | 30.05 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Playoffs | True shooting (%) | 48.67 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Playoffs | Points per 36 minutes (per 36 minutes) | 25.64 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Regular Season | Recorded games (games) | 82 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Regular Season | Minutes per game (per game) | 37 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Regular Season | Points per game (per game) | 31.46 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Regular Season | True shooting (%) | 60.5 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Regular Season | Points per 36 minutes (per 36 minutes) | 30.61 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| LeBron James / Regular Season | Recorded games (games) | 69 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Regular Season | Minutes per game (per game) | 36.13 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Regular Season | Points per game (per game) | 25.26 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Regular Season | True shooting (%) | 57.66 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Regular Season | Points per 36 minutes (per 36 minutes) | 25.17 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Playoffs | Recorded games (games) | 17 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Playoffs | Minutes per game (per game) | 40.53 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Playoffs | Points per game (per game) | 31.12 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Playoffs | True shooting (%) | 59.96 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Playoffs | Points per 36 minutes (per 36 minutes) | 27.64 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
### Playmaking and ball security

| Player / phase | Metric | Value | Source |
|---|---|---:|---|
| LeBron James / Playoffs | Recorded games (games) | 20 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Playoffs | Minutes per game (per game) | 42.2 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Playoffs | Assists per game (per game) | 8.45 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Playoffs | Turnovers per game (per game) | 4.1 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Playoffs | Assists per turnover (ratio) | 2.06 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Playoffs | Assists per 36 minutes (per 36 minutes) | 7.21 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Playoffs | Recorded games (games) | 17 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Playoffs | Minutes per game (per game) | 40.53 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Playoffs | Assists per game (per game) | 8.35 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Playoffs | Turnovers per game (per game) | 2.53 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Playoffs | Assists per turnover (ratio) | 3.3 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Playoffs | Assists per 36 minutes (per 36 minutes) | 7.42 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Regular Season | Recorded games (games) | 82 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Regular Season | Minutes per game (per game) | 37 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Regular Season | Assists per game (per game) | 5.52 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Regular Season | Turnovers per game (per game) | 2.46 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Regular Season | Assists per turnover (ratio) | 2.24 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Regular Season | Assists per 36 minutes (per 36 minutes) | 5.38 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| LeBron James / Regular Season | Recorded games (games) | 69 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Regular Season | Minutes per game (per game) | 36.13 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Regular Season | Assists per game (per game) | 7.41 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Regular Season | Turnovers per game (per game) | 3.94 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Regular Season | Assists per turnover (ratio) | 1.88 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Regular Season | Assists per 36 minutes (per 36 minutes) | 7.38 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
### Minutes and attempts follow-up

| Player / phase | Metric | Value | Source |
|---|---|---:|---|
| Michael Jordan / Regular Season | Recorded games (games) | 82 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Regular Season | Minutes per game (per game) | 37 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Regular Season | Points per game (per game) | 31.46 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Regular Season | Field-goal attempts per game (per game) | 22.4 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Regular Season | Free-throw attempts per game (per game) | 8.18 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Regular Season | True shooting (%) | 60.5 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Regular Season | Points per 36 minutes (per 36 minutes) | 30.61 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Playoffs | Recorded games (games) | 17 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Playoffs | Minutes per game (per game) | 40.53 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Playoffs | Points per game (per game) | 31.12 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Playoffs | Field-goal attempts per game (per game) | 22.12 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Playoffs | Free-throw attempts per game (per game) | 8.71 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Playoffs | True shooting (%) | 59.96 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| Michael Jordan / Playoffs | Points per 36 minutes (per 36 minutes) | 27.64 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) |
| LeBron James / Playoffs | Recorded games (games) | 20 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Playoffs | Minutes per game (per game) | 42.2 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Playoffs | Points per game (per game) | 30.05 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Playoffs | Field-goal attempts per game (per game) | 27.2 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Playoffs | Free-throw attempts per game (per game) | 8.35 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Playoffs | True shooting (%) | 48.67 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Playoffs | Points per 36 minutes (per 36 minutes) | 25.64 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Regular Season | Recorded games (games) | 69 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Regular Season | Minutes per game (per game) | 36.13 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Regular Season | Points per game (per game) | 25.26 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Regular Season | Field-goal attempts per game (per game) | 18.54 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Regular Season | Free-throw attempts per game (per game) | 7.65 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Regular Season | True shooting (%) | 57.66 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
| LeBron James / Regular Season | Points per 36 minutes (per 36 minutes) | 25.17 | [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) |
### Contemporary league benchmark

- Michael Jordan / Regular Season: weighted relative TS **7.06** percentage points. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) [Evidence](https://stats.nba.com/stats/leaguegamelog?Counter=0&Direction=ASC&LeagueID=00&PlayerOrTeam=T&Season=1990-91&SeasonType=Regular+Season&Sorter=DATE&DateFrom=&DateTo=)
- LeBron James / Playoffs: weighted relative TS **-3.96** percentage points. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) [Evidence](https://stats.nba.com/stats/leaguegamelog?Counter=0&Direction=ASC&LeagueID=00&PlayerOrTeam=T&Season=2014-15&SeasonType=Playoffs&Sorter=DATE&DateFrom=&DateTo=)
- LeBron James / Regular Season: weighted relative TS **4.25** percentage points. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=2544&PerMode=Totals&LeagueID=00) [Evidence](https://stats.nba.com/stats/leaguegamelog?Counter=0&Direction=ASC&LeagueID=00&PlayerOrTeam=T&Season=2014-15&SeasonType=Regular+Season&Sorter=DATE&DateFrom=&DateTo=)
- Michael Jordan / Playoffs: weighted relative TS **5.25** percentage points. [Evidence](https://stats.nba.com/stats/playercareerstats?PlayerID=893&PerMode=Totals&LeagueID=00) [Evidence](https://stats.nba.com/stats/leaguegamelog?Counter=0&Direction=ASC&LeagueID=00&PlayerOrTeam=T&Season=1990-91&SeasonType=Playoffs&Sorter=DATE&DateFrom=&DateTo=)

## Coverage and limits

- Historical box-score evidence is not equivalent to modern tracking or lineup data. Missing historical coverage does not count against a player.
- Steals, blocks and rebounds describe recorded activity; matchup difficulty, positioning, deterrence and defensive schemes are not measured here.
- On/off comparisons are confounded by lineup, opponent and substitution choices. No causal team/winning impact is established.
- Small or unequal appearance samples and stale API responses remain limitations. No synthetic overall impact score is used.

## Raw LLM

To evaluate Michael Jordan in the 1990–91 NBA season and LeBron James in the 2014–15 NBA season, we must examine how their offensive roles, playmaking volume, and efficiency shifted from the regular season to the playoffs. 

This comparison is particularly interesting because both players were at historical inflection points: Jordan was breaking through to win his first NBA championship, while LeBron was carrying a depleted Cleveland Cavaliers team to the NBA Finals in his first year back with the franchise.

---

### Part 1: Regular Season vs. Postseason Statistical Profile

#### **Michael Jordan (1990–91)**
*Coached by Phil Jackson | Triangle Offense implementation | Age: 27*

* **Regular Season (82 games):**
  * **Minutes:** 37.0 MPG
  * **Points:** 31.5 PPG
  * **Assists:** 5.5 APG
  * **Usage Rate (USG%):** 32.8%
  * **Efficiency:** 53.9% FG | 31.2% 3PT | 851 FT% | **60.5% True Shooting (TS%)**
  * **Offensive Rating (Team):** 114.6 (1st in NBA)

* **Playoffs (17 games):**
  * **Minutes:** 40.5 MPG (+3.5)
  * **Points:** 31.1 PPG (-0.4)
  * **Assists:** 8.4 APG (+2.9)
  * **Usage Rate (USG%):** 33.5%
  * **Efficiency:** 52.4% FG | 38.5% 3PT | 833 FT% | **60.2% True Shooting (TS%)**

#### **LeBron James (2014–15)**
*Coached by David Blatt | Isolation & High-Pick-and-Roll heavy | Age: 30*

* **Regular Season (69 games):**
  * **Minutes:** 36.1 MPG
  * **Points:** 25.3 PPG
  * **Assists:** 7.4 APG
  * **Usage Rate (USG%):** 31.4%
  * **Efficiency:** 48.8% FG | 35.4% 3PT | 710 FT% | **56.6% True Shooting (TS%)**
  * **Offensive Rating (Team):** 111.8 (4th in NBA)

* **Playoffs (20 games):**
  * **Minutes:** 42.2 MPG (+6.1)
  * **Points:** 30.1 PPG (+4.8)
  * **Assists:** 8.5 APG (+1.1)
  * **Usage Rate (USG%):** 39.8% (+8.4)
  * **Efficiency:** 41.7% FG | 22.7% 3PT | 731 FT% | **47.7% True Shooting (TS%)**

---

### Part 2: On-Court Offensive and Playmaking Contributions

#### **Michael Jordan (1990–91): The Complete Offensive Engine**
In 1990–91, Jordan’s transition from a volume-scoring isolation guard to a willing facilitator within Phil Jackson’s triangle offense bore fruit. 
* **Scoring:** Jordan maintained virtually identical elite scoring output and hyper-efficient scoring (60.2% TS in the playoffs is elite for a perimeter player). 
* **Playmaking:** The most notable leap in Jordan's postseason was his playmaking. He jumped from 5.5 to **8.4 assists per game**. Facing traps and double-teams from the Knicks, 76ers, and Pistons, Jordan trusted his teammates (like John Paxson and Scottie Pippen) and operated effectively as a primary distributor out of the post and double-teams.

#### **LeBron James (2014–15): The Solo Carry-Job**
By the 2015 playoffs, injuries to Kevin Love (out in the first round) and Kyrie Irving (injured in the NBA Finals) forced LeBron into an unprecedented heliocentric offensive role.
* **Scoring:** LeBron’s points per game jumped significantly from 25.3 to **30.1 PPG**.
* **Playmaking:** Already a primary offensive hub, LeBron maintained elite playmaking numbers (**8.5 APG**), creating open shots for a depleted roster of shooters (J.R. Smith, Iman Shumpert, Matthew Dellavedova).

---

### Part 3: Did Higher Postseason Points Per Game Represent Improved Performance for LeBron?

For LeBron James, the superficial indicator—**higher postseason points per game (30.1 vs. 25.3)**—suggests an elevated scoring level in the playoffs. However, a deeper investigation into **minutes, shot volume, and efficiency** reveals that this higher scoring output **did not** represent improved offensive performance. In fact, it was a symptom of extreme offensive necessity that severely hurt his efficiency.

#### **1. Minutes and Shot Volume Discrepancy**
* **Minutes:** LeBron played 6.1 more minutes per game in the playoffs (42.2 MPG) compared to the regular season (36.1 MPG). Naturally, more floor time yields higher counting stats.
* **Shot Volume & Usage:** LeBron’s Usage Rate skyrocketed from a regular-season 31.4% to a staggering **39.8% in the playoffs**. In the NBA Finals against the Golden State Warriors, he essentially became the entire Cavaliers offense, launching a massive volume of shots out of necessity.

#### **2. The Efficiency Collapse**
While Jordan’s efficiency remained virtually identical between the regular season and playoffs (TS% dropped by a negligible 0.3%), **LeBron’s efficiency cratered:**
* **Field Goal Percentage:** Dropped from 48.8% to **41.7%**.
* **Three-Point Percentage:** Dropped from 35.4% to an abysmal **22.7%**.
* **True Shooting Percentage (TS%):** Plummeted by nearly 9 percentage points, from **56.6% down to 47.7%**. 

To put a 47.7% TS in perspective, it is well below league average. LeBron was scoring more points simply because he was taking drastically more shots (rising from 18.5 field goal attempts per game in the regular season to **26.8 FGA** in the playoffs) on much worse shooting, caused by defensive attention, fatigue, and the lack of secondary playmakers on the floor.

---

### Conclusion

* **Michael Jordan (1990–91)** demonstrated true offensive growth and adaptability in the postseason. His scoring remained lethal and hyper-efficient, while his playmaking expanded dramatically (8.4 APG) without sacrificing efficiency or requiring a massive spike in usage. His postseason run was an apex demonstration of offensive mastery within a team system.
* **LeBron James (2014–15)** put on one of the greatest individual resilience displays in NBA history, carrying a crippled roster to two wins in the NBA Finals. However, his higher postseason points per game **did not** represent improved performance; rather, they represented a forced, high-volume necessity. The indicators (soaring minutes and usage paired with a collapsing True Shooting percentage) prove that his high-scoring postseason was achieved through sheer force of volume at the expense of efficiency.
