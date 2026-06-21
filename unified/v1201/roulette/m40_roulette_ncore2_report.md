# 課題#1 — n_core=2 でのルーレット選択 + 頻度グラフ（記録のみ・n_core=5 と並置）報告

## 自己規律宣言（Code A）
① 過去引用済: m35（連続ルーレット: 各(cid,t)で max(.,0)→正規化→`default_rng([0,cid,t])` 一様乱数1つの累積ルーレット、n_core=5 の21CID）、m37（頻度グラフ = picks の value_counts の素カウント、表示は並べ替え/色のみ）、m36（ghost = step10 が host_lost で打ち切られ退化／draw は (cid,t) 毎に独立で cosine 凍結でも t毎に独立）、#30（指標/閾値/濃度の数値化禁止・レア消すな）、spec「n_core 別に後で広げられる構造にする」。
② Taka 逐語（原文）: 「これは n_core=5 かな? 2の場合はどうなる?」。
③ 成否判定は Taka（success/fail 置かない、観察事実のみ）。
④ 集約語なし。

*作成*: 2026-06-17、Code A。*コード*: `m39_roulette_freq_by_ncore.py`（n_core 引数化、既定2）。*出力*: `*_ncore2.*` + `m39_atom_freq_ncore2.html`。**新しい指標・閾値・濃度・「2は5より○○」等の差の数値化/解釈は一切していない**（母集団を n_core=2 に変えて同一アルゴリズムで再実行し、引かれた回数の素のカウントを並置しただけ）。

---

## 0. 忠実性（generalize が m35 を壊していない確認）
- m39 を **n_core=5 で回すと m35 の picks と完全一致**（26,859 行、`picked_atom` 100% 一致 / `rank_of_picked` 100% 一致）。seed が (cid,t) の純関数で n_core 非依存のため＝「広げても既存 n_core=5 は不変」（spec の「広げられる構造」を満たすことの実証）。確認用 ncore5 ファイルは commit しない。

## 1. 母集団（n_core=2、n_core=5 と並置・素の数値）
| | n_core=5 | n_core=2 |
|---|---|---|
| CID 数 | 21 | **180** |
| draw 行数（全step10時点） | 26,859 | **20,602**（CID は8倍だが行は少＝短命） |
| final 内訳 | hosted 16 / reaped 5 | **ghost 8** / hosted 11 / reaped 161 |
- ※n_core=2 は **final=='ghost'（第3の終状態）が 8 個**。n_core=5 には無い（§3）。

## 2. 頻度グラフ（Taka 依頼の本体）= `m39_atom_freq_ncore2.html`
m37 と同一デザイン（① 上位30 atom 具体名 / ② 全325中 引かれた種を頻度順・接頭カテゴリ色、hover で名前・回数）。
- 引かれた atom = **325 / 325 種**（draw は少ないが全 atom が ≥1回。レア消さないは n_core=2 でも保持）。
- 回数: **max 116 / median 65 / min 6**（n_core=5 は max 201 / median 81 / min 8）。
- 上位8（n_core=2）: PER.tasteless 116, ACT.build 111, SPC.direction 108, PER.see 108, PER.feel 107, WLD.artless 107, BOD.mouth 106, BOD.ear 103。
- 上位8（n_core=5・再掲）: PER.sound 201, TIM.moment 176, BOD.ear 167, PRP.clear 162, PER.odorless 161, PRP.bright 160, ELM.light 159, PER.feel 159。
- → **顔ぶれが違う**（共通は BOD.ear / PER.feel 程度）。これは2集団の素のカウントの並置で、差の指標化・「だから○○」は書かない＝判定は Taka。
- rank_of_picked: n_core=2 は **median 124 / mean 133.4 / max 325**（n_core=5 は median 102 / mean 116.4）。rank 1〜325 全域出現は両方共通。

## 3. Ghost — n_core=2 で構造が違う（要・確認、ただし判定しない）
- is_ghost=True = **869 行 / 169 CID**（n_core=5 は 5 行）。内訳:
  - **161 reaped**: 各 host_lost ちょうどで打ち切られ ghost 1 行ずつ（n_core=5 と同じ退化）。
  - **8 final=='ghost'**（n_core=5 に無い終状態）: host_lost 後も t=25000 まで cosine が残る。うち **4 CID が多点の凍結 ghost 相**（cid 230=301行 / 242=201 / 257=151 / 263=51）。
- **凍結 ghost 相での実物（素のカウント、解釈なし）**: cosine が凍っていても picks は一定にならない。
  - cid 230: ghost **301 行で picked は 186 種**（最頻 PER.salty/PER.blind/COM.silence 各4回）。rank min1/median127/max319。
  - cid 242: 201行 → 150種 / cid 257: 151行 → 123種 / cid 263: 51行 → 45種。
  - これは **draw が (cid,t) 毎に独立**（凍った分布から毎回引き直す）という方法の挙動（m36 §4 で既述）。仕様④の予想「Ghost は cosine が凍るので同じ atom が出続けるはず」とは逆向きの記録＝**ここが Taka 確認ポイント**（draw を凍らせたい/argmax にしたい等の意図なら方法側の変更が要る。今は spec どおり毎t独立）。
- alive/ghost 別の rank 分布は `rank_of_picked_dist_alive_ncore2.csv` / `_ghost_ncore2.csv` に分離。

## 4. コスト
- 実測（n_core=2, 180CID）: 約 0.5–0.6s、picks parquet 0.32MB、HTML 4.8MB。`cost_ncore2.json`。

## 5. やらなかったこと
n_core 間の差の指標化（集中度・偏り・距離・相関）、正規化表示、濃度/spike/Δ/エントロピー/閾値、「2は5より○○」「ghost で○○」等の解釈、ghost 相の atom 反復の判定 — **一切していない**。§2 の並置・§3 の種数は素のカウントの読み上げ。

## 6. 一方向保証
読む = `full_cosine_step10_seed0`（m31 生成・非commit）/ `source_events_seed0`。書く = `roulette/`（`m39_*` + `*_ncore2.*`）のみ。physics/inject/ledger 非書込。

---

*以上 課題#1 n_core=2（Code A、2026-06-17）。m39 で母集団を n_core=2(180CID, 20,602 draw) に変え m35/m37 と同一アルゴリズムで再実行（n_core=5 再現で忠実性確認済）。頻度グラフ `m39_atom_freq_ncore2.html`: 325 atom 全て ≥1回, max116 PER.tasteless（n_core=5 の PER.sound 201 と顔ぶれ違い、median 65 vs 81）。Ghost は869行/169CID で、n_core=5 に無い final=='ghost' 8個・うち4個が多点凍結相（cid230=301行で picked 186種）＝凍っても毎t独立 draw で picks 一定にならず（仕様予想と逆、要Taka確認）。差の指標化・解釈は書かない。判定は Taka。*
