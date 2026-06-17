# 課題#1 — cosine 分布の確率的選択（連続ルーレット・レア消さない・全CID×全時点・記録のみ）報告

## 自己規律宣言（Code A）
① 過去引用済: m31（`full_cosine_step10_seed0.parquet` = argmax 前の全325 cosine、既存値を読むだけ）、m30（sim=cosine(CID48,atom48) の argmax のみ出力で残りは捨て）、#30（気まぐれ指標禁止・レアを消すな・Ghost 分離）、m27/m33（is_ghost = `t≥host_lost_step`、source_events groupby 'first'）、m34（n_core=5 seed0 = 21 CID）。
② Taka 逐語（原文）: 「cosine 分布を確率的選択という別の表現にしたとき何が見えるか」「意味づけは足さない、選ばれた atom を記録するだけ」「負・極小を0クリップ→合計1正規化→一様乱数1つで累積確率ルーレット」「整数の桁合わせはしない＝連続」「下位は天文学的に低いがゼロにしない（レアを消すのは雑）」「各(cid,t)で1回だけ引く」「seed0 n_core=5 の全21CID、各CIDの全step10時点（hosted/reaped 両方）」「seed 固定・コード冒頭に明示」「Ghost 区間も引くがフラグで分離」。
③ 成否判定は Taka（success/fail 置かない、観察事実のみ）。
④ 集約語なし。

*作成*: 2026-06-17、Code A。*コード*: `m35_roulette_pick.py`。*出力*: `roulette/`。**新しい指標・閾値・濃度・spike・Δ は一切作っていない**（既存 cosine を確率に正規化してルーレットで引き、引いた atom と rank を記録しただけ）。

---

## 1. やったこと（連続ルーレット選択）
- 母集団 = **n_core=5（seed0）の 21 CID**、各 CID の**全 step10 時点**で 1 回ずつ。**引いた (cid,t) = 26,859 行**（alive 26,854 / ghost 5 ※ghost は §3）。
- 各 (cid,t): m31 の全 325 cosine を読み → `max(cosine,0)` で負を0クリップ → 合計1に正規化（確率 = clip(cosine)/合計、桁合わせなし＝連続）→ `u~U[0,1)` を1つ引き累積確率で当たり atom を1個選ぶ。
- **正の下位は一切残す**（閾値をかけない）＝レアを消さない。zero-prob 行（全 atom 非正）= **0 件**。

## 2. 記録（素の数値、判定なし）
**出力**: `roulette_picks_step10_seed0.parquet`（列 = cid, t, is_ghost, picked_atom, picked_atom_cosine, picked_atom_prob, rank_of_picked）。

### 2-1. picked_atom 素の頻度（`picked_atom_freq.csv`）
- **325 atom 全てが ≥1 回引かれた**（picked_count: min 8 / median 81 / max 201）。＝レアを消さない設計のまま、最下位帯の atom も顔を出した（事実）。
- 最多5: PER.sound 201, TIM.moment 176, BOD.ear 167, PRP.clear 162, PER.odorless 161。
- 最少5: COM.muteness 8, COG.unlearned 8, COG.mindless 9, EMO.doubt 10, PER.numb 15。

### 2-2. rank_of_picked 素の分布（`rank_of_picked_dist.csv`、引かれた atom が cosine 何位だったか）
- **rank 1〜325 の全 325 種が出現**。min 1 / median 102 / mean 116.4 / max 325。
- 素のカウント: rank≤10 = **1,816 / 26,859（6.8%）**、rank≥100 = **13,646（50.8%）**、rank≥300 = 469、rank=325 ちょうど = 7 回。
- 「最も下位が顔を出した picks」（rank=325 の実物、`sample_rare_picks.json`）例: cid41/t10330 WLD.unskilled（cosine 0.0287, prob 0.000459, rank325）、cid107/t9950 EMO.despair（cosine 0.0153, prob 0.000226, rank325）。
- ※上の 6.8% / 50.8% は分布表の素のカウントの読み上げで、**閾値・指標化ではない**（「上位ばかりか下位も出たか」の dump）。「だから○○」は書かない＝判定は Taka。

## 3. Ghost の扱いと、観察された事実（要・確認）
- is_ghost = `t≥host_lost_step`（m27/m33 定義）を列に持たせ、`rank_of_picked_dist_alive.csv` / `_ghost.csv` に分離。判定ロジックは m33 と同一。
- **観察事実（仕様の前提と食い違うので明示）**: step10 の full_cosine は **reaped 5 CID とも host_lost_step ちょうどで終わっている**（cid26 t末=20000=host_lost、cid22 11000、cid9 8000、cid180 17000、cid82 6000。いずれも **reaped_step は NaN**）。step10 trajectory が host_lost で打ち切られているため、`t≥host_lost` を満たすのは**各 reaped の境界1点ずつ＝計5行**しかない。
  - → **step10 では「cosine が凍った ghost 相を多点で観察」ができない**（1 CID あたり ghost 1点）。仕様④の「Ghost は cosine が凍るので同じ atom が出続けるはず」を step10 で検証する材料が、このデータには実質無い（1点では「出続ける」を見られない）。
  - ghost 5行の実物: cid9 EXS.void(rank186) / cid22 ECO.money(rank66) / cid26 PRP.sharp(rank70) / cid82 PRP.bright(rank79) / cid180 WLD.art(rank116)。
  - これは私の ghost 判定のバグではなく**データの実態**（m33 の cid26「Ghost帯」も実は host_lost=t末の0幅、境界線のみ。コミット `0864015 ghost平らは言い過ぎ` の訂正と整合）。ghost 相を多点で見たい場合はトラジェクトリを host_lost 以降へ延ばす別データが要る（＝Taka 判断、ここでは延ばしていない）。

## 4. 実装で委ねられていた選択（透明性のため明示、仕様の解釈変更ではない）
- **乱数 seed**: 各 (cid,t) の draw = `np.random.default_rng([0, cid, t]).random()` の純関数。SEED=0 をコード冒頭に明示。→ 同じ config を何度回しても同一（Web Claude 検証可）＋ 後で n_core を広げ別 CID が増えても既存 (cid,t) の draw は不変（順序非依存＝「広げられる構造」）。
- **クリップ**= `max(cosine,0)`（負のみ0化）。正値には閾値を一切かけない（「レアを消すのは雑」に従う）。
- **rank_of_picked** = cosine 降順で厳密に上の atom 数 +1（1始まり）。仕様が記録列として明示したもので、閾値判定ではない。

## 5. コスト（`cost.json`）+ 拡張概算
- 実測（step10 seed0, 21 CID）: **0.61s**、picks parquet **0.431 MB**（commit 可）。
- 拡張概算（全 n_core に広げると step10 seed0 で全 62,906 行＝m31 の全行）。4粒度×24seed の粗概算 ≈ 62,906×24 行規模（粒度で行数差あり、m31/m32 と同方針の粗概算）。parquet は行数比例で軽い（21CID で 0.43MB → 全 n_core 1seed で ~1MB 目安）。

## 6. やらなかったこと（明示）
「意味あるレア」の判定・閾値、spike・Δ・濃度・エントロピー・集中度・「目立ち度」の数値化、atom×atom 網・CID 投影・センター接続・effect_size・位相化・複数 CID の目立ちの合成、「この結果はこういう意味」の解釈は**一切していない**。§2 の % は分布表の素の読み上げのみ。

## 7. 一方向保証 + grep
- 読む = frozen（`full_cosine_step10_seed0`〔m31 生成・非commit、再生成 ~3.5s〕／`source_events_seed0`）。書く = `roulette/` のみ。
- grep（`m35`）: 物理/inject/ledger 書込 = **docstring 宣言行のみ・実コード0件**。禁止指標（spike/entropy/threshold/concentrat/gini/std/percentile/effect_size/位相/濃度/集中）= **実コード0件**（宣言行のみ）。`to_parquet/to_csv/write_text` 宛先は**全て roulette/**。

---

*以上 課題#1 連続ルーレット選択（Code A、2026-06-17）。n_core=5 の 21 CID × 全 step10 時点 26,859 行で、全325 cosine を max(.,0)→正規化→一様乱数1つの累積確率ルーレットで各 (cid,t) 1回引き、picked_atom と rank_of_picked を記録。素の頻度（325 atom 全て ≥1回, min8/max201）と rank 分布（1〜325 全域, rank≤10=6.8%/rank≥100=50.8%）を dump。seed=default_rng([0,cid,t]) 固定。**Ghost は step10 データが host_lost で打ち切られ各 reaped 境界1点ずつ＝計5行で、凍った ghost 相の多点観察はこのデータでは不可（要・Taka 確認）**。指標化・解釈・次手段は書かない。判定は Taka。*
