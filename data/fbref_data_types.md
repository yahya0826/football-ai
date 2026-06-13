# FBref.com 完整数据类型参考

---

## 一、数据层级（4 层）

```
联赛/赛事 (Competition)
  └─ 赛季 (Season)
       ├─ 球队赛季汇总 (Team Season)
       │    ├─ 球员赛季汇总 (Player Season)   ← 11 个 stat_type
       │    └─ 球队赛季统计 (Team Season Stats)
       │
       └─ 比赛 (Match)
            ├─ 赛程/比分 (Schedule/Results)
            ├─ 阵容 (Lineups)
            ├─ 事件流 (Events)：进球、换人、红黄牌时间线
            ├─ 比赛摘要 (Match Summary)
            ├─ 比赛报告 (Match Report)：裁判、观众、场地
            ├─ 球员比赛数据 (Player Match)     ← 同下 stat_type，按球员×比赛级别
            ├─ 球队比赛数据 (Team Match)        ← 逐场球队统计
            └─ 射门事件 (Match Shooting)       ← 每次射门的坐标和 xG
```

---

## 二、全部 Stat Type（11 个球员统计表）

每个 stat_type 在 fbref 页面上是一个独立的 HTML `<table>`，ID 为 `stats_{stat_type}`：

### 1. `standard` — 基础数据

| 关键字段 | 说明 |
|---|---|
| MP | 出场次数 |
| Starts | 首发次数 |
| Min | 出场分钟数 |
| 90s | 90 分钟场次 |
| Gls | 进球 |
| Ast | 助攻 |
| G+A | 进球+助攻 |
| G-PK | 非点球进球 |
| PK | 点球进球 |
| PKatt | 点球尝试 |
| CrdY | 黄牌 |
| CrdR | 红牌 |
| Gls/90 | 每 90 分钟进球 |
| Ast/90 | 每 90 分钟助攻 |
| G+A/90 | 每 90 分钟进球+助攻 |
| G-PK/90 | 每 90 分钟非点球进球 |

### 2. `shooting` — 射门 + xG ⭐

| 关键字段 | 说明 |
|---|---|
| Sh | 射门总数 |
| SoT | 射正次数 |
| SoT% | 射正率 |
| Sh/90 | 每 90 分钟射门 |
| SoT/90 | 每 90 分钟射正 |
| G/Sh | 进球/射门比 |
| G/SoT | 进球/射正比 |
| Dist | 平均射门距离 |
| FK | 任意球射门 |
| xG | 预期进球 |
| npxG | 非点球预期进球 |
| npxG/Sh | 每次射门 npxG |
| G-xG | 实际进球-预期进球 |
| np:G-xG | 非点球进球-非点球预期进球 |

### 3. `passing` — 传球 + xA ⭐

| 关键字段 | 说明 |
|---|---|
| Cmp | 传球成功次数 |
| Att | 传球尝试次数 |
| Cmp% | 传球成功率 |
| TotDist | 传球总距离（码） |
| PrgDist | 渐进传球距离（码） |
| 短传 | Cmp / Att / Cmp%（5-15 码） |
| 中传 | Cmp / Att / Cmp%（15-30 码） |
| 长传 | Cmp / Att / Cmp%（>30 码） |
| Ast | 助攻 |
| xA | 预期助攻 |
| A-xA | 实际助攻-预期助攻 |
| KP | 关键传球 |
| 1/3 | 传入进攻三区 |
| PPA | 传入禁区 |
| CrsPA | 传中入禁区 |
| PrgP | 渐进传球 |

### 4. `passing_types` — 传球方式细分

| 关键字段 | 说明 |
|---|---|
| Live | 活球传球（Cmp/Att） |
| Dead | 死球传球（Cmp/Att） |
| FK | 任意球传球（Cmp/Att） |
| TB | 直塞球 Through Balls（Cmp/Att） |
| Sw | 长传转移（Cmp/Att） |
| Crs | 传中（Cmp/Att） |
| TI | 界外球 Throw-Ins（Cmp/Att） |
| CK | 角球 Corners（Cmp/Att） |
| In | 内旋角球（Cmp/Att） |
| Out | 外旋角球（Cmp/Att） |
| Str | 直传角球（Cmp/Att） |

### 5. `gca` — 进球与射门创造动作 ⭐

| 关键字段 | 说明 |
|---|---|
| SCA | 射门创造动作（Shot-Creating Actions） |
| SCA90 | 每 90 分钟 SCA |
| SCA-PassLive | SCA 来自活球传球 |
| SCA-PassDead | SCA 来自死球传球 |
| SCA-Drib | SCA 来自盘带 |
| SCA-Sh | SCA 来自射门 |
| SCA-Fld | SCA 来自被犯规 |
| SCA-Def | SCA 来自防守动作 |
| GCA | 进球创造动作（Goal-Creating Actions） |
| GCA90 | 每 90 分钟 GCA |
| GCA-PassLive | GCA 来自活球传球 |
| GCA-PassDead | GCA 来自死球传球 |
| GCA-Drib | GCA 来自盘带 |
| GCA-Sh | GCA 来自射门 |
| GCA-Fld | GCA 来自被犯规 |
| GCA-Def | GCA 来自防守动作 |

### 6. `defense` — 防守 ⭐

| 关键字段 | 说明 |
|---|---|
| Tkl | 抢断次数 |
| TklW | 成功抢断次数 |
| Def 3rd | 防守三区抢断 |
| Mid 3rd | 中场三区抢断 |
| Att 3rd | 进攻三区抢断 |
| DribTkl | 成功拦截盘带者 |
| DribAtt | 面对盘带次数 |
| Tkl% | 盘带拦截成功率 |
| DribPast | 被盘带过掉次数 |
| Blocks | 封堵射门次数 |
| PassBlocks | 封堵传球次数 |
| Int | 拦截次数 |
| Tkl+Int | 抢断+拦截 |
| Clr | 解围次数 |
| Err | 失误导致射门 |

### 7. `possession` — 控球 ⭐

| 关键字段 | 说明 |
|---|---|
| Touches | 触球总数 |
| Def Pen | 防守禁区触球 |
| Def 3rd | 防守三区触球 |
| Mid 3rd | 中场三区触球 |
| Att 3rd | 进攻三区触球 |
| Att Pen | 进攻禁区触球 |
| Live | 活球触球 |
| Take-Ons-Att | 盘带过人尝试 |
| Take-Ons-Succ | 盘带过人成功 |
| Take-Ons-Succ% | 盘带过人成功率 |
| Tkld | 被抢断次数 |
| Carries | 带球次数 |
| Carries-TotDist | 带球总距离 |
| Carries-PrgDist | 渐进带球距离 |
| PrgC | 渐进带球次数 |
| CPA | 带球进入禁区 |
| Miscontrols | 控球失误 |
| Dispossessed | 被断球次数 |
| Rec | 接球次数 |
| PrgR | 渐进传球接球 |

### 8. `playing_time` — 出场时间

| 关键字段 | 说明 |
|---|---|
| Starts | 首发次数 |
| Mn/Start | 平均首发时间 |
| Subs | 替补出场次数 |
| Mn/Sub | 平均替补时间 |
| unSub | 未上场替补次数 |
| PPM | 每场得分（Points Per Match） |
| onG | 在场时球队进球 |
| onGA | 在场时球队失球 |
| +/- | 在场时净胜球 |
| +/-90 | 每 90 分钟净胜球 |
| xG+/- | 在场时 xG 净差值 |

### 9. `misc` — 杂项

| 关键字段 | 说明 |
|---|---|
| Fls | 犯规 |
| Fld | 被犯规 |
| Off | 越位 |
| Crs | 传中 |
| PKwon | 赢得点球 |
| PKcon | 送出点球 |
| OG | 乌龙球 |
| Recov | 球权恢复（Ball Recoveries） |
| AerialsWon | 争顶成功 |
| AerialsLost | 争顶失败 |
| Aerial% | 争顶成功率 |

### 10. `keeper` — 基础守门员

| 关键字段 | 说明 |
|---|---|
| GA | 失球数 |
| GA90 | 每 90 分钟失球 |
| SoTA | 面对射正次数 |
| Saves | 扑救次数 |
| Save% | 扑救率 |
| W | 胜场 |
| D | 平场 |
| L | 负场 |
| CS | 零封场次 |
| CS% | 零封率 |
| PKatt | 面对点球次数 |
| PKA | 点球失球 |
| PKsv | 扑出点球 |
| PKm | 点球射失 |

### 11. `keeper_adv` — 高级守门员 ⭐

| 关键字段 | 说明 |
|---|---|
| PSxG | 射门后预期进球 |
| PSxG/SoT | 每次射正的 PSxG |
| PSxG+/- | PSxG - GA（扑救质量，正值=优于预期） |
| PSxG/90 | 每 90 分钟 PSxG |
| Att (GK) | 门将传球尝试 |
| Thr | 手抛球 |
| Launch% | 长传比例 |
| AvgLen | 平均传球距离 |
| Opp | 面对传中次数 |
| Stp | 摘/击出传中 |
| Stp% | 传中处理成功率 |
| #OPA | 禁区外防守动作 |
| AvgDist | 平均出击距离 |

> ⭐ = 高级/进阶数据（需要 Opta 数据源，2017-18 赛季起覆盖 Top 20+ 赛事）

---

## 三、比赛级别数据

比赛页面 URL 格式：`https://fbref.com/en/matches/{8位ID}/{Team1-Team2-Date-League}`

| 数据 | worldfootballR 函数 | Python (soccerdata) | 内容 |
|---|---|---|---|
| 赛程/比分 | `fb_match_results()` | `read_schedule()` | 联赛整赛季赛程和比分 |
| 比赛报告 | `fb_match_report()` | — | 裁判、观众数、场馆 |
| 比赛摘要 | `fb_match_summary()` | — | 进球时间线、红黄牌、换人 |
| 首发阵容 | `fb_match_lineups()` | `read_lineup()` | 首发 11 人 + 替补名单 |
| 射门事件 | `fb_match_shooting()` | — | 每次射门的球员、坐标、xG、PSxG、结果 |
| 球员比赛统计 | `fb_advanced_match_stats()` | `read_player_match_stats()` | 11 个 stat_type，单场比赛级别 |
| 事件流 | — | `read_events()` | 进球、红黄牌、换人事件 |

---

## 四、球队级别数据

| 数据 | worldfootballR 函数 | Python (soccerdata) | 内容 |
|---|---|---|---|
| 球队赛季统计 | `fb_season_team_stats()` | `read_team_season_stats()` | 球队汇总 standard/shooting/passing/defense 等 |
| 球队比赛日志 | `fb_team_match_log_stats()` | `read_team_match_stats()` | 球队逐场 shooting/passing/keeper 等 |
| 球队比赛比分 | `fb_team_match_results()` | — | 特定球队的所有比赛比分 |
| 球队球员统计 | `fb_team_player_stats()` | — | 某球队所有球员的赛季数据 |
| 球队进球日志 | `fb_team_goal_logs()` | — | 球队进球和失球的时间线 |
| 球队薪资 | `fb_squad_wages()` | — | 球员薪资（通过 Capology） |

---

## 五、联赛级别数据

| 数据 | worldfootballR 函数 | 内容 |
|---|---|---|
| 联赛 URL 列表 | `fb_league_urls()` | 获取指定国家/性别/赛季的联赛链接 |
| 球队 URL 列表 | `fb_teams_urls()` | 某联赛的所有球队链接 |
| 球员 URL 列表 | `fb_player_urls()` | 某球队的所有球员链接 |
| 比赛 URL 列表 | `fb_match_urls()` | 某联赛赛季的所有比赛链接 |
| 积分榜 | `fb_season_team_stats(stat_type="league_table")` | 联赛排名 |
| 主场/客场积分榜 | `stat_type="league_table_home_away"` | 分主客场的积分榜 |
| Big 5 高级预聚合数据 | `fb_big5_advanced_season_stats()` | 五大联赛预聚合的高级数据 |

---

## 六、单个球员数据

| 数据 | worldfootballR 函数 | 内容 |
|---|---|---|
| 球员比赛日志 | `fb_player_match_logs()` | 单球员逐场比赛数据（可指定 stat_type） |
| 球员进球日志 | `fb_player_goal_logs()` | 单球员全部进球的时间线 |
| 球探报告 | `fb_player_scouting_report()` | 与同位置球员的完整对比报告 |

---

## 七、数据获取方式

### Python（推荐 `soccerdata` 包）

```python
import soccerdata as sd

fbref = sd.FBref(leagues="ENG-Premier League", seasons="2024-2025")

# 球员赛季数据（支持 5 个 stat_type）
fbref.read_player_season_stats(stat_type="standard")
fbref.read_player_season_stats(stat_type="shooting")
fbref.read_player_season_stats(stat_type="keeper")
fbref.read_player_season_stats(stat_type="playing_time")
fbref.read_player_season_stats(stat_type="misc")

# 球队赛季数据（支持 5 个 stat_type）
fbref.read_team_season_stats(stat_type="standard")
fbref.read_team_season_stats(stat_type="shooting")
fbref.read_team_season_stats(stat_type="keeper")
fbref.read_team_season_stats(stat_type="playing_time")
fbref.read_team_season_stats(stat_type="misc")

# 赛程
fbref.read_schedule()

# 比赛阵容
fbref.read_lineup(match_id="db261cb0")

# 比赛事件
fbref.read_events(match_id="db261cb0")
```

### Python（直接爬取 `pandas.read_html`）

```python
import pandas as pd

url = "https://fbref.com/en/comps/9/shooting/Premier-League-Stats"
df = pd.read_html(url, attrs={"id": "stats_shooting"})[0]
df.to_csv("premier_league_shooting.csv", index=False)
```

### R（`worldfootballR` 包，功能最全）

```r
library(worldfootballR)

# 支持全部 11 个 stat_type
fb_player_season_stats(country = "ENG", gender = "M", tier = "1st",
                       season_end_year = 2025, stat_type = "shooting")
```

---

## 八、赛事编码参考

### 五大联赛
| ID | 赛事 | League ID (soccerdata) |
|---|---|---|
| 9 | 英超 Premier League | `ENG-Premier League` |
| 12 | 西甲 La Liga | `ESP-La Liga` |
| 13 | 法甲 Ligue 1 | `FRA-Ligue 1` |
| 20 | 德甲 Bundesliga | `GER-Bundesliga` |
| 11 | 意甲 Serie A | `ITA-Serie A` |

### 其他联赛
| 赛事 | League ID (soccerdata) |
|---|---|
| 荷甲 Eredivisie | `NED-Eredivisie` |
| 葡超 Primeira Liga | — |
| 比甲 Belgian Pro League | — |
| 土超 Süper Lig | — |
| 巴甲 Série A | — |
| 阿根廷甲 | — |
| J1 联赛 | — |
| K League 1 | — |

### 国际赛事
| ID | 赛事 |
|---|---|
| 8 | UEFA Champions League |
| 19 | UEFA Europa League |
| 882 | UEFA Europa Conference League |
| 1 | FIFA World Cup |

> 注：`soccerdata` 包默认只支持五大联赛和国际赛事，其他联赛需要自定义配置。

---

## 九、数据覆盖层级

| 层级 | 覆盖范围 | 说明 |
|---|---|---|
| Basic | 40+ 国家 | 进球、出场、比赛、红黄牌 |
| Intermediate | 40+ 国家 | 传中、抢断、射门、拦截 |
| Advanced | 20+ 赛事 | Opta 提供：xG/xA/渐进传球/对抗/SCA 等 |
| Positional | 2014-15 起 | 按赛季级别的位置数据 |
