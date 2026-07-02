# v1304a probe 報告 — 「管に書ける動的な珍しさ」は有るか（子 run なし・相関スキャン・停止）

*作成*: 2026-07-03、Code A。**read-only・子 run なし・既存 readout のみ・スキャンで停止（§5・composition 検証へ自動前進しない）・判定なし #12。**
*成果物*: `v1304a_probe.py` + `outputs/v1304a_probe_scan_part1.parquet` / `v1304a_probe_dynbgen_part2.parquet`。

---

## 0. 出口一点への答え：**NO**（s_avg と bgen 水準で相関する動的珍しさは無い）
- Part 2 の全候補で **|corr(動的bgen, s_avg)| の最大 = 0.399**（E_mean rarity within_ncore）。**bgen 較正点 0.545 に届く候補はゼロ**。
- ＝ **Taka 案「動的 bgen ライク（step 毎物理量の珍しさ）なら自然と差が出る」は、実証済チャネル s_avg に対しては支持されない**。動的珍しさは現行動的 eye 同様、s_avg 管には乗らない。
- ただし Part 1 に別の含み（動的 eye は他の dense 量と 0.6–0.7 で相関・未実証チャネル候補）。→ (ii) の cheapest ルート（動的珍しさ→s_avg）は死ぬが、(ii) 全体は死なない。判定は Taka。

## 1. Part 2 — 動的 bgen（step 毎物理量の −log10 珍しさ）× s_avg
各物理量（ledger の per-(cid,t) core 集約）に two-sided −log10 珍しさを global / within_ncore で適用し lift 化、s_avg（45 支持）と相関。bgen 較正点 0.545 併記。
| 動的 bgen の元 | scope | \|corr(s_avg)\| 最大 | 較正点到達 |
|---|---|---|---|
| **E_mean（エネルギー）** | within_ncore | **0.399** | ✗ |
| C（意識資源） | within_ncore | 0.229 | ✗ |
| theta_resultant | global | 0.218 | ✗ |
| R_positive（閉路数） | within_ncore | 0.213 | ✗ |
| R_mean | global | 0.175 | ✗ |
| Q / link_count / S_mean | — | ≤0.11 | ✗ |
- **最良は E_mean rarity 0.40 だが bgen 0.545 未満**。bgen 自体が「小さいが robust」な分離（audit 済）だったので、0.40 の候補は分離が出ても更に小さく実質検出困難。→ 動的珍しさは s_avg 管に届かない。
- 2 lift 定義（eligible/alive）で符号・大小はほぼ不変（E_mean 0.40/0.37 等）＝定義依存は小。

## 2. Part 1 — 既存動的 eye lift × dense per-cid 量（地形図・|corr| top）
| eye | dense 量 | corr | 備考 |
|---|---|---|---|
| archive_theta | last_attention_size | 0.69 | attention 自己相関(やや循環) |
| archive_theta | last_n_partners | 0.66 | 同上 |
| now_theta | last_n_partners / attention_size | −0.64 | 同上 |
| **link_rarity** | **v18_cognitive_gain_final** | **0.63** | より独立 |
| archive_theta | C_at_run_end | 0.61 | より独立 |
| archive_theta | n_observed_as_target | 0.56 | |
- 動的 eye は **dense 量とは強く相関する**（s_avg には乗らないのに）。ただし (i) attention_size/n_partners は attention 自己相関で循環気味、(ii) **どれも v1302 級の実証済チャネルでない**（子物理 param がこれを読む経路＋transfer 証明が別途要る）。＝「将来チャネル候補の地形図」であって管ではない。

## 3. 読みの規律（probe の限界）
- **候補発見器であって証明でない**：Part1 102本・Part2 32本のスキャン＝偶然の当たり混入。当たり候補は採用前に **Stage 3b 同型の composition 検証（別データ/別 base）が必須**。
- 相関に閾値を置かない（bgen 0.545 は較正点・カットオフでない）。2 lift 定義併記。新 run/新 ledger なし。

## 4. (ii)/(iii) 分岐への材料（判定は Taka）
- **(ii) の cheapest ルート（動的珍しさ→実証済 s_avg 管）は死んだ**：動的 bgen の最良 0.40 < 0.545。Taka 案は s_avg に対しては通らない。
- **(ii) 全体は死んでいない**：動的 eye は last_attention_size(0.69)・cognitive_gain(0.63)・C_at_run_end(0.61) 等の dense 量と相関＝**別チャネルの候補**。ただし (a) 子物理 param がそれを読む経路が要る、(b) v1302 級の transfer 実証が要る、(c) 一部は attention 自己相関で循環＝**高コストで不確実**。
- **(iii)（feedback / 動的統計）は事実として残る**：チャネル相関に依存せず注意を効かせる路線。動的珍しさが管に乗らない以上、これが有力候補として残る。
- 分岐の採否は Taka（probe は事実提供のみ）。

## 5. 実施範囲・停止
- 実施：Part1（3動的eye×2定義×17 dense量）・Part2（8物理量×2 scope×2定義の動的珍しさ×s_avg）・bgen 較正点併記。read-only・子 run なし・数分。
- スキャンのみで**停止**。候補が出ても composition 検証へ自動前進しない。採否・(ii)/(iii) 分岐は Taka。

## 6. 一文サマリ
v1304a probe（子 run なし・read-only・#12）── 出口一点「s_avg と bgen 水準で相関する動的珍しさが有るか」への答えは **NO**（Part2：step 毎物理量の −log10 珍しさ×s_avg の最大は E_mean rarity within_ncore の 0.399 で bgen 較正点 0.545 に未達＝Taka 案「動的 bgen なら自然と差が出る」は s_avg 管に対して不支持・現行動的 eye 同様届かない）、ただし Part1 で動的 eye は last_attention_size 0.69/cognitive_gain 0.63/C_at_run_end 0.61 等の dense 量と相関＝別チャネル候補の地形図はあるが未実証・一部循環・高コスト、ゆえ (ii) の cheapest（動的珍しさ→s_avg）は死ぬが (ii) 全体は死なず (iii) feedback も事実として残る、probe は候補発見器で証明でない（採用前に Stage3b 同型検証必須・閾値置かず・2 lift 定義併記・新run 禁止）、分岐判定は Taka。
