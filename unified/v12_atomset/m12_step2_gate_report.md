# v12 Atomset cid_align — STEP 2 関門報告: 準・循環性チェック（+ Q/C カラム検証）

**指示書 v2 STEP 2（関門・選択肢 C）**: cid_align が v1114 既存入力（生イベントカウント）の遅延コピー（自明）か、独立な新情報（経験の累積=往復の履歴）か。**通過時のみ Taka に STEP 3 進行可否を確認。**

*作成*: 2026-06-15、Code A。*コード*: `m11_step2_circularity_gate.py`。*出力*: `run_step2/step2_per_cid_r2.parquet`。
**crown なし。独立は必要条件であって個性化の証明でない。判定は Taka。**

---

## 0. 前提検証: Q/C カラムが silent-death していないか（Web Claude 指摘）

`.get(col, 0)` はカラム不在で黙って 0 になり、数字（40次元）では気づけない。実データで確認：

- **カラム実在**: v107 `df.columns` に `Q_remaining_at_window_end`・`C_at_window_end` 両方 True。source 分布も多様（nunique 36 / 59、全0でない）。
- **各 align 次元が LIVE（値が意味ある分布、全部同じでない）**:

| 次元 | 軸 | std | nunique | 判定 |
|---|---|---|---|---|
| a18 | ontological **material**（Q_remaining/q0） | 0.101 | 325,759 | **LIVE** |
| a22 | ontological **semantic**（C_at_window_end） | 0.036 | 308,752 | **LIVE** |
| a28-31 | **resonance**（C_at_window_end） | 0.171/0.124/0.086/0.13 | — | **LIVE** |
| a44 | value_gen **functional**（q_spent=q0−Q_remaining） | 0.094 | — | **LIVE** |

→ **Q/C 系は全て生きている**（silent-death 起きていない）。真にゼロは (a) epist levels 2-4（R_familiarity が 30/60/150 に届かず＝v106 同様 degenerate）、(b) symmetry（delta_* が v107 に無く flag 済、pulse_log join は STEP 3 前）のみ。

---

## 1. 関門結果（per-CID R²、主）

対象 CID: **3098 / 5224**（n_chunks≥12、R² に十分な長さ）。

```
per-CID R² 分布: 中央値=0.062  平均=0.244  25%=0.000  75%=0.410
  [0.0,0.1): 1663 ########################################
  [0.1,0.2):  281 ######
  [0.2,0.3):  193 ####
  [0.3,0.4):  172 ####
  [0.4,0.5):  122 ##
  [0.5,0.6):   98 ##
  [0.6,0.7):   98 ##
  [0.7,0.8):  108 ##
  [0.8,0.9):  132 ###
  [0.9,1.0):  231 #####
  R²<0.3: 69% | 0.3-0.7: 16% | R²>0.7: 15%
```

**n_core 別（集団平均の罠を避ける層化）**:
| n_core | n | median R² | <0.3 | >0.7 |
|---|---|---|---|---|
| 2 | 1957 | 0.010 | 67% | 19% |
| 3 | 227 | 0.078 | 66% | 14% |
| 4 | 296 | 0.153 | 68% | 9% |
| 5 | 615 | 0.136 | 75% | **5%** |

→ **n_core が大きいほど R²>0.7（自明コピー）の割合が減る**（19%→5%）＝大きい CID ほど生カウントから独立（状態が豊か）。

**単相関（cid_align 変化量 vs 各カウント）中央 |corr|**: alpha_formation 0.330 / beta_formation 0.256 / pulse 0.234 / ingestion 0.064 / c_conversion 0.064。いずれも中〜低。

**系全体（副）**: R²（seed別）中央値=0.187。per-CID 中央値（0.062）との食い違いは小（集約で像が大きく変わる事象は無し）。

## 2. 正直な留保（crown 回避）

1. **二峰性**: 分布は二峰（[0,0.1) に 1663 と [0.9,1.0) に 231）。**15% の CID（>0.7）は align 変化がほぼ生カウントの再表現**＝それらでは cid_align は自明寄り。高 R² CID（231）は **n_core=2 が 83%**（小さい CID、event 数が少ないわけではない n_chunks中央30）。小さい CID ほど状態次元が乏しく align 変化が count に従う。
2. **「独立」の正確な意味**: cid_align は event stream の TRANSFORM（cumulative + 非-count 状態 R_familiarity/C/Q/lifespan + f重み(robust_z, 履歴依存) + 正規化 + 48次元方向）。R² 0.062 が低いのは「per-chunk align 変化が per-chunk 生カウントで線形予測できない」＝**履歴・状態を含む非線形累積**だから。**全く別系の信号ではない（同じ stream + 状態の非線形累積）**。「独立」は「生カウントの遅延コピーでない」の意であって「無相関」ではない。

## 3. 判定（判定線への該当）

- **per-CID R² 中央値 = 0.062 < 0.3、かつ R²<0.3 が 69%（過半）** → 判定線「中央値 < 0.3 が過半 → 独立 → 関門通過」に該当。
- 全 n_core 帯で median R² < 0.3。系全体（副）0.187 も <0.3 で per-CID と整合。

→ **関門通過候補**。ただし §2 の留保（15% は自明寄り・小 CID、cid_align は同 stream の非線形累積であって無相関でない）を付す。**「通過＝個性化成立」ではない（crown 禁止）。独立は STEP 3（行き先が cid 特異か）の必要条件。**

---

## 4. Taka への確認（指示書: 通過時のみ STEP 3 進行可否を確認）

関門は数値上**通過候補**（R² 中央値 0.062、69% が <0.3、大 CID ほど独立）。**STEP 3（本実装: raw/norm 両方・行き先 Atom argmax 実計算・null 2種）へ進んでよいか**、判定をお願いします。

加えて Web Claude 推奨の **symmetry（pulse_log delta_* join で +5 次元、45/48 へ）を STEP 3 の前に入れるか**も、合わせてご判断ください（行き先の偏り緩和に効く）。

物理書込ゼロ（grep 確認、parquet 読込 + 分析のみ）。crown なし、判定は Taka。

---

*以上 STEP 2 関門（Code A、2026-06-15）。Q/C 系 LIVE 確認（silent-death なし）。per-CID R² 中央値 0.062 < 0.3・69%<0.3・大 CID ほど独立 → 通過候補。留保: 15% は自明寄り(小CID)、cid_align は同 stream の非線形累積で無相関ではない。STEP 3 進行可否 + symmetry 追加可否を Taka 判断待ち。*
