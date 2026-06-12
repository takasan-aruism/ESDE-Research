# v12 M5 — ②別チャネル（物理値を上書きしない効かせ口）の調査 + 筋3 配線

日付: 2026-06-12 / 筋3 確定（Atomset=文化、AtomID 主体、別チャネル、CID 間共有・伝播）を受け、
**② の効かせ口を実コードで確認**（Taka「推測で決めない、効かせ口調査を先に」）。実装はまだ。

筋3 骨格4点（踏み外し厳禁）: ①主体=AtomID ②別チャネル＝物理値(state.E/L/θ)を上書きしない
③CID 間共有・伝播 ④センサー地続き。

---

## 0. 結論

- **② の効かせ口は実コードに存在し、新設不要**。最適＝**`torque_factor`**（`virtual_layer_v9.py:432`）。
- torque_factor は**物理の値を書かず**、CID **自身の** torque 過程（存在層の θ 駆動）を**毎 step スケールする係数**。E 直書き（一回注入→物理が上書き撹拌＝前回の干渉）と決定的に違い、**standing な係数バイアス**（撹拌される注入値が無い）。
- per-label スロットが既にある（M3 で使った口）→ **per-Atom 化は `label["atomset_seed"]`（誕生時 rank_1 Atom）経由で自然**。
- **干渉を避けるのは仮説**（torque も最終的に θ に効く）→ **実装後の干渉検査やり直しで検証**（corr(経験,効果) が正に転じるか）。推測で確定しない。

---

## 1. 係数側の効かせ口（実コード調査）

| 効かせ口 | file:line | 種別 | per-label | standing(毎step) | 評価 |
|---|---|---|---|---|---|
| **torque_factor** | `virtual_layer_v9.py:432-441` | **係数**（既存 torque を乗算） | **○** `label["torque_factor"]` | **○** | **◎ 最適** |
| gravity_factor | `:707,765-766` | 係数（近傍 θ 重力強度） | ○ `lid` | ○ | 候補（torque と同系） |
| addressing λ 選択性 | `v1111c.py:105,120` | 係数（exp(-λd) の鋭さ） | △ 現 state 由来、要拡張 | ○ | 候補（最も物理から遠い＝知覚/選択側） |
| capture p_max / ATTENTION_DECAY / FAMILIARITY_DECAY | v105 | 係数だが global | × | 一部 | 不適（global、要改造） |
| LEAKAGE_AMOUNT 等 | v105 | **値注入** | — | — | ✗ 値側 |

### 核心（実コード、`virtual_layer_v9.py:429-441`）
```python
age = window_count - label["born"]
rigidity_factor = 1.0 / (1.0 + self.rigidity_beta * age)
cog_factor = label.get("torque_factor", 1.0)          # ← per-label 係数スロット
torque_mag = energy * rigidity_factor * self._torque_multiplier * cog_factor
for n in label["nodes"]:
    torque = torque_mag * math.sin(label["phase_sig"] - theta_n)
    state.theta[n] += torque                           # 毎 step、CID 自身の θ 駆動
```
- **物理の値を書かない**: torque_factor は θ を直接セットせず、CID 自身の torque 強度を乗算スケール。
- **standing**: 毎 step 適用される持続バイアス（E 直書きの「一回注入→撹拌」と別物）。
- **値側との対比**: 前回の干渉は `state.E[n] += dE`（一回注入を物理が上書き）。torque_factor は注入値が無い。

## 2. なぜ干渉（scramble）を避けると考えるか（仮説）

- E 直書き失敗 = 注入した値を CID 物理（state.E の本来の作者）が毎 step 上書き → cid 特異情報が撹拌（実証済: corr(注入量,効果)≤0）。
- torque_factor = **撹拌される注入値が存在しない**。CID 自身の過程を毎 step バイアスする係数なので、物理に「上書き」される値が無い。standing バイアスは持続して効く。
- **∴ per-Atom 経験 → torque_factor なら、経験の cid/atom 特異情報が物理に掻き消されず効果に乗る、と期待**。
- **要検証（推測で確定しない）**: 実装後に干渉検査やり直し。corr(経験量, 効果) が**正**に転じれば scramble されていない＝係数側が正解。≤0 のままなら torque も撹拌される（別口 or 設計見直し）。

## 3. 筋3 の配線（骨格4点を満たす具体案）

```
① 主体=AtomID:   rate[atom] を per-Atom で積む (経験式 robust_z+衰退+floor は流用、主体だけ atom へ)
                 各 label に atomset_seed (誕生時 rank_1 Atom、M2 の compute_rank_1_atom 流用)
② 別チャネル:    label["torque_factor"] = g(rate[label["atomset_seed"]])
                 ← state.E/L/θ の値は一切書かない。torque 係数だけ。
③ CID 間共有:    同じ atomset_seed を担う CID は同じ rate[atom] を共有
                 (ある CID で育った Atom 文化が、同 Atom を担う他 CID にも乗る)
④ センサー地続き: 橋 (入力 Atom) が rate[atom] を更新 → その Atom を担う全 CID の torque_factor に乗る
                 (1 Atom→複数 CID、検査2 確認済。CID は同じ・受けた文化で振る舞い違う)
v9.7 guard:      torque_factor は v9.7 の口 → slight (効果量監視) + shuffle 対照を維持
                 ([[project-v12-experience-is-v97-pattern]])
```

### 共有・伝播の粒度（③）の設計選択肢（実装時に決める）
- (i) 厳密共有: 同 atomset_seed の CID は完全同一 rate[atom]。
- (ii) 緩い伝播: rate[atom] に加え「近い Atom」(atom_centroids cosine 近傍) に減衰伝播 ＝文化の拡散。
- Taka「緩やかに共有・伝播」に沿うなら (ii) 寄り。まず (i) で干渉が解けるか見て、(ii) は後段。

## 4. 順序（Taka 規定遵守）

1. **② 効かせ口調査 = 完了**（torque_factor 最適、新設不要）。← 本書
2. 次（実装、承認後）: per-Atom 経験 ＋ torque_factor 別チャネル ＋ atomset_seed ＋ CID 間共有 ＋ 橋地続き。
3. **干渉検査やり直し**: per-Atom・別チャネルで corr(経験量, 効果) が正に転じるか（scramble されないか）。
4. 通って初めて over-drive・個性化判定（slight 監視つき）。
5. 「設計能力不足における変は肯定しない」＝干渉を解いてから振らせる。

## ファイル
- 参照: `m5_interference_and_subject.md`（干渉実証・三つの規定）、`m5_port_inventory_and_plan.md`（15 口）、
  `m5_substrate_smoke.py`（現 substrate、②を value→coefficient に差し替える土台）
- 実コード: `virtual_layer_v9.py:432`（torque_factor）、`v1111c.py:105`（λ）、M2 `compute_rank_1_atom`（atomset_seed）
