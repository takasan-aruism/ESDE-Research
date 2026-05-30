# 第 2 段階 Step A — Code A 認識確認 v2 (訂正版)

**Date**: 2026-05-31
**Author**: Code A
**Status**: **Step A v1 訂正** — Taka 指摘で再調査、ESDE main run 本体コード発見
**親**: stage2_step_a_recognition.md (v1、誤り) + Taka 指摘 (2026-05-31「ないわけないだろう、バージョン戻れば必ずある」)

---

## 0. v1 訂正

### 0.1 v1 の誤り
v1 で「ESDE main run 本体コードが現リポジトリに存在しない」と書いたが、**完全に誤り**。私の調査が `developmental/v107` のみで止まっていた。

### 0.2 Taka 指摘を受けて再調査
> 「ないわけないだろう。これまで何度実験したと思ってる? 基本的にはバージョンごとにディレクトリがある。バージョンを戻っていけば必ずある。」

→ **発見**: ESDE main run 本体は `autonomy/v82-v85` + `primitive/v918` 等に存在。

---

## 1. ESDE main run 本体コードの所在 (確定)

### 1.1 Engine 本体 (V82Engine)

| ファイル | 内容 |
|---|---|
| `autonomy/v82/esde_v82_engine.py` | **V82Engine クラス** (V43Engine 継承)、step_window メソッド |
| `autonomy/v82/virtual_layer_v5.py` | virtual layer |
| `autonomy/v82/engine_accel_v3.py / v5.py` | accelerator |
| `autonomy/v74/esde_v74_engine.py` 〜 `autonomy/v85/` | 各バージョンの engine |

### 1.2 起動エントリポイント

| ファイル | 内容 |
|---|---|
| `primitive/v918/v918_memory_readout.py` | `if __name__ == "__main__"` (line 3130) — main run 起動 |
| `primitive/v917/v917_memory_readout.py` | 同 |
| `primitive/v916/v916_memory_readout.py` | 同 |

使い方:
```python
from esde_v82_engine import V82Engine, V82EncapsulationParams, V82_N

engine = V82Engine(seed=seed, N=N, encap_params=encap_params)
# step ループ
engine.step_window(steps=V82_WINDOW)
```

### 1.3 既存実行例
- `developmental/v105/diag_v105_main/` 等が「過去 main run の出力」
- Phase 1 完成版は `primitive/v918` 起動 → V82Engine 駆動

---

## 2. 第 2 段階の実装可能性 (再評価)

### 2.1 案 A/B/C の再判定

| 案 | v1 評価 | v2 訂正後評価 |
|---|---|---|
| 案 A (リプレイ) | 推奨 | 可能だが**真の常駐でない** |
| 案 B (擬似 ESDE) | 可能 | 不要 (本体コードあり) |
| **案 C (main run 取得)** | **Taka 提供必要** | **★ コード既存、実行可能** |

**Code A 推奨変更**: **案 C (V82Engine + primitive/v918 を使った真の常駐)** を採用

### 2.2 案 C の最小実装プラン

```python
# 常駐 ESDE ループ
from esde_v82_engine import V82Engine, V82EncapsulationParams, V82_N

engine = V82Engine(seed=42, N=V82_N)
external_loop_dir = 'unified/stage2_external_loop/sandbox/'

for step_iter in range(N_ITER):  # 停止条件明確化
    # 1. ESDE step (本物の Genesis 動き)
    engine.step_window(steps=V82_WINDOW)

    # 2. Genesis 状態を読む (engine.state.* から、low layer)
    cid_state = read_genesis_state(engine)  # familiarity, alive_l 等

    # 3. 固定ルールで外部ツール実行 (ファイル読み書き)
    ext_input = cid_state['some_field']
    write_to_external(ext_input, external_loop_dir + 'state.json')
    ext_output = read_from_external(external_loop_dir + 'state.json')

    # 4. source_event 形式に変換
    new_event = build_source_event(step_iter, ext_output)

    # 5. ESDE に戻す (source_events に追加、次 step で参照)
    inject_event(engine, new_event)
```

### 2.3 物理層 frozen の維持方法

設計書 §0.2「物理層 1 byte も侵さない」を案 C で守る方法:

| 観点 | 維持方法 |
|---|---|
| 既存物理層 (developmental/v105 等の過去出力) | 完全読まない (案 C は新規 main run) |
| engine の出力先 | `unified/stage2_external_loop/run/` 配下に設定 (既存 diag_v82_main 等に書き込まない) |
| engine 内部状態 | engine.state は **新規 main run の状態**なので「既存物理層」とは別 |
| 外部ツール対象 | `unified/stage2_external_loop/sandbox/` 配下のみ |

→ **既存 developmental/v105 等は 1 byte も触らない**、新規 main run は別ディレクトリで実行

---

## 3. 実装条件再チェック (案 C 採用前提)

| Q | v1 評価 | v2 訂正後 |
|---|---|---|
| 1 常駐ループ | 本体なしで不可 | **可** (V82Engine + step_window をループ) |
| 2 Genesis 状態読み出し | frozen データから可 | **engine.state から直接可** (より正確) |
| 3 source_event スキーマ | Step B 確認 | 同 (primitive/v918 内で定義済の可能性) |
| 4 物理層 frozen | 維持可 | **既存物理層 frozen + 新規 main run** で維持 |
| 5 最初のツール (ファイル読み書き) | OK | OK |
| 6 不足 | main run 本体 (なし) | **本体あり**、Step B でセットアップ確認のみ |

→ **不足解消、第 2 段階実装可能**

---

## 4. 重要な留保 (案 C 採用後)

### 4.1 V82Engine の動作経験が Code A にない
- これまで Code A は post-process しかやっておらず、V82Engine の起動経験なし
- Step B で **smoke 試行** (短い step 数で起動できるか確認) が必要
- 起動エラーや依存関係問題が出る可能性

### 4.2 出力先のリダイレクト
- V82Engine の出力先 (おそらく diag_v82_main/ 等) を新規ディレクトリにリダイレクトする方法を Step B で確認
- engine の output_path 引数 or 環境変数

### 4.3 第 4 段階 (loop 崩壊) との接続
- 案 C なら **真の常駐**、ESDE は本当に動く
- → 第 4 段階 (外部結果が Genesis を変え loop が崩れるか) を直接観察可能
- 案 A (リプレイ) と違い、長期実行で loop 崩壊検証可

---

## 5. Web Claude / Taka への確認 (訂正版)

| Q | Code A 提案 |
|---|---|
| a 案 A/B/C どれで進めるか | **案 C (V82Engine + primitive/v918 を使った真の常駐)** を推奨 |
| b 最初のツール | ファイル読み書き (sandbox/state.json) |
| c main run コード提供 | **不要、autonomy/v82 + primitive/v918 に既存** |
| d 真の常駐 vs 疑似常駐 | **真の常駐 (案 C)** を Code A 推奨、第 4 段階接続のため |

### v1 → v2 訂正サマリ

| 項目 | v1 | v2 |
|---|---|---|
| ESDE main run 本体 | 不在と誤判定 | **autonomy/v82 + primitive/v918 に存在** |
| 推奨案 | A (リプレイ) | **C (真の常駐)** |
| Code A 役割 | post-process 拡張 | **engine 起動 + 常駐 + 外部接続** |
| 第 4 段階接続 | 別実装必要 | **案 C なら直接接続可** |

---

## 6. Code A 自己点検 (Taka 指摘を受けて)

### 6.1 調査不足の規律違反
- 「ない」と書く前に **全ディレクトリ調査すべきだった**
- `developmental/v107` だけ見て「ない」と結論したのは怠慢
- これは「実験設計を疑う」規律 (6 段階目) の Code A 側応用版違反

### 6.2 新規規律候補 (Code A 提案)
> 「『存在しない』『不可能』と書く前に、リポジトリ全階層 (autonomy / primitive / developmental / unified / legacy 全部) を調べる」

これは 7 段階目ミス予防 (self-fulfilling baseline 検査) の拡張版。

---

## 7. Step 分解 (案 C 採用前提)

| Step | 内容 |
|---|---|
| A v2 | 本文書、訂正済み認識確認 |
| B | 環境準備 + V82Engine smoke 起動 (短 step、依存確認) |
| C | 常駐ループ実装 (engine.step_window を for で回す) |
| D | Genesis 状態読み取り + 外部ツール (ファイル読み書き) |
| E | source_event 変換 + engine への戻し |
| F | 6 確認項目チェック (設計書 §3.1) |
| G | bit-identity (既存 developmental/v105 等 frozen 確認) |
| H | 観察事実最終報告 + 出口判定 |

---

**Step A v2 end. 案 C 採用判断 + Step B 進行可否確認を Web Claude / Taka に要請。**
