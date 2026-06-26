# v1303 Step B — コスト feasibility 訂正所見（実測・着手前の停止報告）

*作成*: 2026-06-27、Code A。
*位置づけ*: Step B1 smoke 着手の plumbing 検証中に判明した **再走コストの 30倍過小見積もり**の訂正。判定（どう進めるか）は Taka / Web Claude。本書は観察事実のみ（#12）。
*規律*: read-only 計測のみ。親 diag 非書込。書込は本 md と `unified/v1303/` のみ。

---

## 1. 何が起きたか（一文）
③ phys_core の決定論的再走の前提コスト「~5min/seed」（inventory §5.2 / Step B 指示 §5.2、技術仕様書 §8.4 由来）は **v918 系（primitive・N 小）の値**で、**anchor の v105 main_v2（N=5000・α/β/salience/leakage 込み）では実測 ~2.7h/seed**（30倍以上）だった。

## 2. 実測（read-only）
| 計測 | 値 | 出所 |
|---|---|---|
| **main_v2 seed0 実 run 全体** | **9649 s ≈ 2.68 h** | `developmental/v105/run_logs_main_v2/seed0.log`「seed=0 DONE in 9649s」 |
| per-window（full run, 認知込み） | 125–147 s/window | 同ログ「seed=0 w=20..69 … 144s/…/125s」 |
| **純物理のみ**（engine 単体・認知層なし）run_injection | 60 s | 本日実測 `engine.run_injection()` N=5000 |
| **純物理のみ** step_window(500) | **~130 s/window**（alive_n=5000, alive_l~3000） | 本日実測 ×複数 window |

## 3. 含意（判定でなく構造事実）
1. **per-window コストは物理層（N=5000）が支配**。純物理 step_window ~130s ≈ full run per-window ~130–147s。**認知層（α/β/disposition/capture/observation）の寄与は相対的に小さい。**
2. ∴「認知層を外した軽量物理のみ再走」をしても **高速化しない**（物理が下限）。当初の高速化アイデア（physics-only driver）は無効。
3. **N=5000 を下げる/window を減らす/tracking を縮める＝いずれも不可**：物理を変えると既算出 alignment（②, N=5000・mat20/track50/win500）と CID 宇宙が一致せず join 不能（F型）。faithful 再走は **mat20+track50=70 window × ~130s + injection 60s ≈ 2.5–2.7h/seed が floor**。
4. **snapshot 計装の追加コスト**は物理に対し副次（read-only・state 不書込）だが、5000 node × 2500 snapshot の保持で tracking に +数十%。
5. スケール再見積もり：
   - **smoke（seed0）単体 ≈ 2.7h + 計装 overhead ≈ 3〜3.5h**。
   - **本番 24 seed**：直列 ~65h。`-j24`（24 core）で理論 ~2.7h wall だが各 seed が 1 core を 2.7h 占有＋メモリ（5000 node 物理×24 並走）。main_v2 実績は **-j8 で 3 バッチ ≈ 8h wall**（24×2.7h/8≈8h）。`-j24` 一発はメモリ・キャッシュ競合次第で wall は延びうる。

## 4. なぜ今止めるか（#5/J型）
Step B0 で私が報告した「単一 seed ~5 min」は inventory（v918 由来）を無批判に引き継いだ誤りで、**Taka の「24並列一発で smoke→本番」承認はこの 30倍過小値の上で得たもの**。実コスト（seed0 だけで ~3h、本番 ~8h）は承認の前提を変えるため、**~3h の compute を投じる前に停止して訂正**する（配管工思考でなく、前提が崩れたら止める）。計装スクリプト `unified/v1303/v1303_ledger.py` は実装済・plumbing は物理コストで頭打ち（バグでなく時間）。

## 5. 進め方の選択肢（判定は Taka / Web Claude）
| 案 | 内容 | コスト |
|---|---|---|
| **A. このまま seed0 smoke** | 計装付き full 再走 seed0 を background で回し（~3h）、ledger schema・3レンズ join・欠損判定・健全性1/2 を実 data で検証 → 報告 → 承認後 24seed 本番 | seed0 ~3h、本番 ~8h(-j8)〜 |
| **B. 部分 seed 本番** | smoke 通過後、24 全 seed でなく代表 seed（例 0,1,2 の n_core 層化が揃う分）に絞る | 比例縮小 |
| **C. snapshot 粒度/対象の見直し** | step10→step50 等に粗くする（物理コストは不変だが post/memory 減）/ member-union node のみ snapshot | 物理 floor は不変、限定効果 |
| **D. 再走以外の③代替を再検討** | ③ phys_core を第一段階で「再走必須・コスト高」として留保し、まず①②（既存のみ・即時）の2レンズ ledger を先に組んで配線を確定、③は別途長時間ジョブに分離 | ①②は分〜時間、③分離 |

**Code A 推奨（参考・判定はしない）**: smoke の目的＝バグ出しは ③ の有無で大きく変わる（join/欠損/健全性1/2 が ③ 依存）。よって **案 A（seed0 を 1 本だけ ~3h 回して schema を確定）→ 結果を見て本番規模を Taka が決める**が、smoke→本番の伝統的順（§6.1）と最も整合。ただし ~3h の background compute を投じる承認が要る。

---

## 6. 一文サマリ
v1303 Step B 着手の plumbing 検証中、③再走の前提コスト「~5min/seed」は v918 系の値で **anchor の v105 main_v2（N=5000・α/β込み）では実測 ~2.7h/seed**（`run_logs_main_v2/seed0.log` の DONE in 9649s）であり、純物理 step_window ~130s/window が full run per-window とほぼ同じ＝**コストは物理層 N=5000 が支配**ゆえ認知層を外す軽量再走でも高速化せず、N/window/tracking を変えると既算出 alignment と CID 宇宙が一致せず join 不能（F型）で faithful 再走は ~2.7h/seed が floor、smoke(seed0)単体で ~3h・本番24seed は -j8 実績換算 ~8h wall という 30倍の訂正を、Step B0 の私の誤った ~5min 引き継ぎ（Taka 承認の前提）を正すため ~3h の compute 投入前に停止報告し、進め方（A:seed0 smoke を ~3h 回す / B:部分seed / C:粒度見直し / D:①②先行・③分離）を Taka / Web Claude の判定に委ねる（Code A 推奨は案A だが判定せず）。
