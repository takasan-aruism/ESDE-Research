# v12 Atomset cid_align — (い) 調査報告 + (あ) STEP 3 結果（軸整合バグ修正込み）

**指示書**: (い)=調査ベースに作り直し（演算から始めない、Taka「適当に演算して解決したことがない」）。(あ)=STEP 3（行き先 Atom argmax）進行。

*作成*: 2026-06-15、Code A。*コード*: `m13_step3_destination.py` + 調査1 inline + 調査2 agent。
**crown 禁止。観察事実のみ。判定は Taka。**

---

## 0. 一文結論

(い) 3 調査の結論: **旧 STEP 2 関門は f を見落としたアーティファクト**（調査1: change は f 主導、f=0 で change=0 が必ず成立）。**identity は change(瞬間・surprise) でなく行き先(蓄積) に在る**（調査2: 過去の MAD-DT/B_Gen 知見）→ (い) は (あ) STEP 3 に統合（調査3）。
(あ) STEP 3 で**致命的な軸整合バグを発見・修正**（v1103 列はアルファベット順、cid_align は slot_keys 順＝prototype の 84-87% は scramble だった）。**正しく整合して測ると、行き先は支配的アトラクタに大きく潰れる**（raw: PER.see 56%、norm: WLD.artless 72%）＝Atom 空間の個体差は**弱い**。これは sober な事実。意味づけは Taka。

---

## 1. (い) 調査1: f(robust_z) は change の主因か（演算でなく観察）

**問い**: 旧関門は change を「カウント5種」で重回帰 R² 0.062 → 「独立」と読んだ。だが change の主因が f なら、低 R² は「独立」でなく「f を見落としたから」。

**観察結果（seed0, 147 CID）**:
- per-CID corr(f, change) **中央値 0.745**、corr>0.7 が **61%** → change は f 主導。
- **f<0.1 の chunk で change>0 は 0/1384 = 0%** → f≈0 なら change=0 が**必ず**成立（数学的に当然: align 更新 = α·f·ev、f=0 で align 不変）。

**∴ 旧 STEP 2 関門はアーティファクト**。R² 0.062 が低いのは「cid_align が独立な identity を持つ」からでなく、「change が f(surprise) を追い、生カウントは f を直接捉えない」から。**旧関門は「独立」を示していない。** Taka 指摘（いきなり演算で組んだ）が正しかった。

## 2. (い) 調査2: 過去の surprise vs identity 分離（agent 調査、過去資料）

| 機構 | 時期 | 結論 |
|---|---|---|
| D1/D2/D3 deviation | v9.3 | 偏り検知は機能したが**全 label 同時適用で個体因果が消失**（同時性問題） |
| **MAD-DT** | v9.10 | robust_z と同系譜。各 CID が「自分の通常」基準（軸スケール自動補正）。**surprise の検知機構** |
| **B_Gen「個体差が潰れる」** | v9.11 | **deviation を直接入力すると個体差が潰れる**→ M_c 経由の間接効果のみに（直接入力回避が architectural 成果） |
| surprise vs identity | — | surprise=robust_z(個体内・履歴の珍しさ)、**identity=行き先(蓄積した座標)**。robust_z は「どの経験が重要か」を重み付けるが、**identity は行き先に在る** |

**含意**: f=robust_z は surprise（いつもと違う度）＝**「皆に起こる」量で、個体が誰かでない**。過去の B_Gen 教訓「deviation 直接入力は個体差を潰す」と同型。**identity は f(change) でなく行き先(蓄積)に求めるべき**（調査ソース: `docs/ESDE_Primitive_Report.md`、`primitive/v911/v911_genesis_budget_audit.md`、`docs/ai_summaries/05_primitive_summary.md`）。

## 3. (い) 調査3: change(瞬間) でなく行き先(蓄積)（→(あ)に統合）

調査1+2 から: change は f 主導(surprise・皆同じ)、identity は行き先(蓄積)。**∴ (い) を「change の独立性」で演算し直すのは見る場所が違う。行き先(=(あ) STEP 3)で問うべき。** **(い) は独立演算でなく (あ) に吸収。** 演算（f を足した再関門）はしない（調査が「不要」と示した）。

---

## 4. (あ) STEP 3: 行き先 Atom（argmax）— 致命的バグ修正込み

### 4.1 発見・修正した軸整合バグ（重要）
- v1103 `atom_centroids_48d_*.parquet` の48列は**アルファベット順**（epistemological.creation..）。
- cid_align は v106 `AXES_ORDER`(=`slot_keys()`) 順（temporal 先頭・level は意味順）で組む。
- **両者の列順が違う → そのまま cosine すると軸 scramble = 行き先が無意味**。
- **prototype（cid_align_investigation.md の 84-87% cid 特異）はこの scramble をしていた**＝あの数字は信頼できない。
- **修正**: v1103 raw/norm を `slot_keys()` 順に並べ替えてから cosine（列名スキーム同一で並べ替え可、検証済）。

### 4.2 正しく整合した結果（raw/norm 両方、null 2種、5224 CID）

| | raw centroid | norm centroid |
|---|---|---|
| 行き先 top1 | **PER.see 56%** | **WLD.artless 72%** |
| 行き先 top3 計 | 73% | 85% |
| 多様性(種数) | 44 種 | 21 種 |
| real==null-B(順序shuffle) | 43%（順序/履歴で変わる） | 78%（ほぼ集合で決まる） |
| real==null-A(別seed個体) | 32%（別個体と別 atom が 68%） | 53%（半数は別個体と同 atom＝潰れ） |
| 一致率 中央(副,絶対値信じない) | 0.641 | 0.629 |
| n_core 別 多様性 | n2:14 / n5:25 種 | n2:9 / n5:11 種 |

### 4.3 観察事実（判定しない）
1. **行き先は支配的アトラクタに大きく潰れる**: raw は PER.see に 56%(top3 73%)、norm は WLD.artless に 72%(top3 85%)。**「各 CID が固有 atom に分かれる」像ではない**。prototype の楽観（個性化成立）は scramble の産物。
2. **raw と norm で像が割れる**（D.92/Δ0.208 反転を実観測）: raw の方が分散し順序依存(real==nullB 43%)、norm はより潰れ集合依存(78%)。raw=潜在(未定義軸込み)、norm=顕在(足場上)。
3. **大 CID(n_core5) はやや多様**（raw 25種 vs n2 14種）＝調査の「大 CID ほど状態豊か」と整合。
4. **弱いが個体差の痕跡はある**: raw で 68% は別個体と別 atom、order でも 57% 変わる。だが支配アトラクタ込みなので「個性化成立」とは書けない（crown 禁止）。

---

## 5. 総括（判定は Taka）

- **(い)**: 旧関門はアーティファクト（change は f 主導）。identity は行き先に求めるべき（調査2）→ (あ) に統合。**(い) の独立演算は不要**（調査が示した）。Taka 方針「調査→だからこうすべき→必要なら演算」に従い、演算せず統合と結論。
- **(あ) STEP 3**: 軸整合バグを修正（prototype の 84-87% は scramble で無効）。**正しく測ると行き先は支配アトラクタに潰れ、Atom 空間の個体差は弱い**。raw>norm で分散・順序依存。これは sober な事実。
- **次にどうするか（Taka 判断領域）**: (a) 弱い個体差(raw の 68% 別 atom・n5 で多様)を掘るか、(b) 支配アトラクタ潰れの原因（cid_align が共通の温度勾配に流れる？symmetry 5次元欠落の影響？）を調べるか、(c) 設計の前提（行き先で個体差が出る）自体を見直すか。**Code A は事実のみ。判定は Taka。**

物理書込ゼロ（grep 確認、全 STEP）。crown なし。

---

*以上（Code A、2026-06-15）。(い) 3調査: change は f 主導(旧関門アーティファクト)・identity は行き先(調査2 B_Gen/MAD-DT)→(あ)統合・演算不要。(あ) STEP 3: 軸整合バグ修正(prototype 84-87% は scramble)、正しく測ると行き先は支配アトラクタ潰れ(raw PER.see56%/norm WLD.artless72%)=個体差弱い、raw>norm 分散。判定は Taka。*
