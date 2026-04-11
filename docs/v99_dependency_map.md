# v99 プログラム依存ファイル一覧

エントリーポイント: `primitive/v99/v99_internal_axis.py`
作成日: 2026-04-11
対象: v9.9 内的基準軸 (v98c からの派生)

---

## 依存ファイル一覧 (16 ファイル)

| # | ディレクトリ | ファイル | 機能 |
|---|---|---|---|
| 1 | `primitive/v99/` | **v99_internal_axis.py** | エントリー: Information Pickup + 内的基準軸 v9.9 |
| 2 | `primitive/v99/` | **virtual_layer_v9.py** | Self-Referential Feedback Loop (グローバル信号で torque 弱変調) |
| 3 | `autonomy/v82/` | esde_v82_engine.py | Lifecycle Instrumented Autonomy (ラベル死亡監視, island 検出) |
| 4 | `autonomy/v82/` | virtual_layer_v5.py | feedback loop なしの基本実装 |
| 5 | `autonomy/v82/` | engine_accel_v3.py | key/get_latent/set_latent 高速化 |
| 6 | `autonomy/v82/` | engine_accel_v5.py | L dict → ShardedLatentDict cache 局所化 |
| 7 | `cognition/semantic_injection/v4_pipeline/v43/` | esde_v43_engine.py | Physical Layer の island/milestone/semantic pressure |
| 8 | `cognition/semantic_injection/v4_pipeline/v41/` | esde_v41_engine.py | v43 前身、core engine 基礎設計 |
| 9 | `ecology/engine/` | v19g_canon.py | K_LEVELS / BASE_PARAMS / compute_J / select_k_star 定義 |
| 10 | `ecology/engine/` | genesis_state.py | 状態管理 (phase, energy, link topology) |
| 11 | `ecology/engine/` | genesis_physics.py | 5 Forces (Phase Rotation / Flow+Sync / Resonance / Decay / Exclusion) |
| 12 | `ecology/engine/` | chemistry.py | Phase 連携人工化学 (Dust/A/B/C states + 合成・自己触媒) |
| 13 | `ecology/engine/` | realization.py | Latent Field L → Manifest Field S bridge |
| 14 | `ecology/engine/` | autogrowth.py | 閉路 R_ij からの L_ij 消費でループリンク強化 |
| 15 | `ecology/engine/` | intrusion.py | Island 境界微摂動 |
| 16 | `ecology/engine/` | engine_accel.py | 汎用リンク強度計算最適化 |

---

## 依存ツリー

```
v99_internal_axis.py  ← 編集対象 (v9.9)
├── virtual_layer_v9.py              [primitive/v99/, frozen]
├── v19g_canon.py                    [ecology/engine/]
└── esde_v82_engine.py               [autonomy/v82/]
    ├── virtual_layer_v5.py          [autonomy/v82/]
    ├── engine_accel_v3.py           [autonomy/v82/] → genesis_state
    ├── engine_accel_v5.py           [autonomy/v82/] → genesis_state, realization
    ├── esde_v43_engine.py           [cognition/.../v43/]
    │   ├── engine_accel.py          [ecology/engine/]
    │   ├── v19g_canon.py            [ecology/engine/]
    │   ├── genesis_state.py         [ecology/engine/]
    │   ├── genesis_physics.py       [ecology/engine/]
    │   ├── chemistry.py             [ecology/engine/]
    │   ├── realization.py           [ecology/engine/]
    │   ├── autogrowth.py            [ecology/engine/]
    │   └── intrusion.py             [ecology/engine/]
    └── esde_v41_engine.py           [cognition/.../v41/]
        └── [v43 と同じ ecology/engine/ 群を再利用]
```

---

## 押さえどころ

- **3 階層構造**: `v99` (Subject 層) → `autonomy/v82` (Lifecycle/island) → `cognition/.../v43,v41` (Physical/semantic pressure) → `ecology/engine/` (人工物理コア 7 ファイル)
- **物理コア (ecology/engine/)** が最深層。`v19g_canon.py` だけ v99 から直接 import されている (定数群)
- **sys.path 操作で接続**: 動的 import はなし、起動時に autonomy/v82, v43, v41, ecology/engine の順で path 追加
- **v9.9 の編集はすべて Subject 層 (v99_internal_axis.py) に閉じている**。下位 16 ファイルは一切触らない (これが「per_window bit identical」が成立する根拠)
- **v82_engine が v43 と v41 の両方を import** している点はやや異例 (相互利用)。後で見直す価値あり
