# 第 2 段階補足 — N=5000 Genesis 起動確認 報告

**Date**: 2026-05-31
**Author**: Code A
**Status**: **出口: `genesis_starts`** ✓

---

## 0. 経緯

第 2 段階 Step C-H では V82Engine 配管 (常駐 + 外部接続) が動いたが alive_n=0 (N=500 smoke 過小、`run_injection()` 未呼び、VirtualLayer v5 のままで v9 でない)。第 2 段階補足として N=5000 + warmup で Genesis 実起動を確認。

### 過去ドキュメント参照 (Taka 規律 + Code A 新規規律)
全階層調査で `primitive/v918/v918_memory_readout.py` に Phase 1 完成版起動コードを発見:
- N=V82_N=5000 固定
- maturation_windows 期間で `engine.step_window` を繰り返す
- **`engine.run_injection()` を呼ぶ** ← Genesis 起動キー
- **`engine.virtual = VirtualLayerV9(feedback_gamma=0.10, ...)`** に置換 ← v9 必須
- 各種 deviation/semantic_gravity 設定

第 2 段階 v1 でこれを呼んでいなかったため alive_n=0 だった。

---

## 1. 実装

`stage2_n5000_genesis_check.py` で v918_memory_readout.py を subprocess 実行:
```bash
python3 primitive/v918/v918_memory_readout.py \
  --seed 42 --maturation-windows 3 --tracking-windows 1 \
  --window-steps 100 --tag genesis_smoke
```
cwd = `unified/stage2_external_loop/run_n5000/` (出力先制御)

smoke 設定 (warmup):
- maturation_windows=3 (フル 20 の 1/7)
- tracking_windows=1 (フル 10 の 1/10)
- window_steps=100 (フル 500 の 1/5)
- → 推定総 step: 4 × 100 = 400 step、N=5000

---

## 2. 結果

### 実行時間: **187.2 秒** (3 分)
return code 0 で正常終了

### Genesis 起動指標 ✓

| 指標 | 値 |
|---|---|
| **v_labels (生まれた label 数)** | **191** |
| **alive_tracked (生存中 label)** | **191** |
| **links (生存 link 数)** | **3,097** |
| **unique CIDs** | **191** |
| CID 状態分布 | **hosted 163 / ghost 28** |
| mean_social | 0.088 |
| mean_stability | 0.72 |
| mean_spread | 0.92 |
| mean_familiarity | 23.5 |

### Event 駆動 (v914 Layer B)
- 191 CID registered、295 events
- E1_death 42 / E2_fall 22 / E2_rise 27 / **E3_contact 204**
- 全 CID で Q≥0 (audit OK)

### 出力ディレクトリ
`unified/stage2_external_loop/run_n5000/diag_v918_genesis_smoke/`
- aggregates / subjects / labels / network / pickup / pulse / audit / persistence / selfread

---

## 3. 物理層 frozen 維持

- subprocess cwd = `unified/stage2_external_loop/run_n5000/`
- 出力 `diag_v918_genesis_smoke/` は cwd 配下に生成
- **既存 `developmental/v105` 等 / `primitive/v918/diag_v918_main/` は 1 byte も触らず**
- 新規 main run でも書込み先は完全分離

---

## 4. 出口判定

### **`genesis_starts`** ✓

第 2 段階補足の 4 確認項目:

| # | 確認 | 結果 |
|---|---|---|
| 1 | N=5000 + warmup で alive_n が立つか | ✓ **191 CID**、3,097 links |
| 2 | 起動状態で外部接続ループが同じく動くか | 次ステップ (本確認では未実装) |
| 3 | 計算量 (tmux で回す規模か) | **smoke 187 秒**、フル設定なら推定 1-2 時間 |
| 4 | 過去ドキュメント手順と実環境照合 | ✓ v918_memory_readout.py が正規起動経路 |

---

## 5. 第 2 段階配管 (Step C-H) との統合方法

現状:
- 第 2 段階 Step C-H: V82Engine + 外部接続ループ ✓ (alive_n=0)
- 本補足: v918_memory_readout.py 経由 Genesis 起動 ✓ (191 CID)

統合方針 (第 3 段階準備):
- **v918_memory_readout.py の run 関数を改造** (または独自スクリプトで V82Engine + run_injection + VirtualLayerV9 を直接駆動)
- 各 maturation window で外部接続ループを追加
- 第 3 段階 (主体性検証) では shuffle で「Genesis 由来 vs 神の手」を判定

具体実装案 (Code A 提案):
```python
# 独自スクリプト: V82Engine 直接駆動 + 外部接続
engine = V82Engine(seed=42, N=5000, encap_params=encap_params)
engine.virtual = VirtualLayerV9(feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
engine.virtual.deviation_enabled = True
engine.virtual.semantic_gravity_enabled = True
engine.run_injection()  # ← Genesis 起動キー

for w in range(maturation_windows):
    engine.step_window(steps=window_steps)
    # 外部接続ループ (第 2 段階 Step C-H と同じ)
    state = read_genesis_state(engine, w)
    write_external(state)
    new_event = build_source_event(w, read_external())
    inject_to_engine(engine, new_event)
```

---

## 6. Code A 自己点検

### 6.1 「全階層調べる」規律が活きた
新規規律「存在しないと書く前に全階層を調べる」を適用:
- `primitive/v918/v918_memory_readout.py` の run 関数を発見
- `engine.run_injection()` + VirtualLayerV9 が Genesis 起動キーと特定
- 第 2 段階 v1 で見落としていた起動手順を補完

### 6.2 計算量見積もり
- smoke (maturation 3 + tracking 1、window_steps 100): **187 秒**
- フル (maturation 20 + tracking 10、window_steps 500): 推定 1-2 時間
- → **tmux で回す規模**、第 3 段階 main run は別途検討

---

## 7. 出力ファイル

- `stage2_n5000_genesis_check.py` (subprocess 起動スクリプト)
- `stage2_n5000_genesis_check_report.md` (本文書)
- `outputs/main/genesis_check_summary.json` (実行結果)
- `run_n5000/diag_v918_genesis_smoke/` (v918 main run 出力)

---

## 8. 次の進行

| 項目 | 内容 |
|---|---|
| **第 2 段階補足** | **完了**、`genesis_starts` 確定 |
| **第 3 段階** (主体性検証) | V82Engine 直接駆動 + 外部接続 + run_injection 統合スクリプト実装、shuffle 検証 |

Web Claude / Taka 判断:
- 統合スクリプト実装方針 (上記 §5) で OK か
- フル設定 (maturation 20、tracking 10) で main run するか、smoke 継続か

---

**第 2 段階補足 end. Genesis 起動成功 (191 CID)、第 3 段階準備完了。**
