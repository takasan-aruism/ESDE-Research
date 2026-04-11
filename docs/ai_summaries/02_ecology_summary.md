# Ecology — AI 向け要約

*原本*: docs/ESDE_Ecology_Report.md (242 行)
*要約時点*: v9.9 完了前 (2026-04-11)
*対象読者*: 未来の Claude

---

## このフェーズが答えた問い

Genesis の global observer (k\*=4) は本当に単一か、それとも複数の local observer の集合体か。

## 用語

- **global observer**: 全 5000 ノードを統合した k-selector の出力
- **local observer**: 2×2 grid の各領域 (r0–r3) 単独の k-selector
- **divergence**: local k\* ≠ global k\* のウィンドウ
- **long_drift**: ≥5 ウィンドウの連続 divergence episode
- **short_burst**: <5 ウィンドウの divergence
- **mismatch pattern**: divergence 中の (global_k, r0_k, r1_k, r2_k, r3_k) 状態

## 確定したこと

- **観測者は複数**: local observer は global より安定。seed 456 では global=k3 だが全 region=k4
- **divergence はデフォルト**: 40–68% のウィンドウで local ≠ global
- **long_drift が支配的レジーム**: 20 seeds で 80%、60 seeds でも 70–80%
- **spatial asymmetry は small sample artifact**: v2.2 で見えた r2/r3 の安定性は 20 seeds で消失
- **k\*=4 は rate [0.0018, 0.0022] で robust**: mean global_k = 3.8、中央値 4.0

## 却下された方針

- 初期 2×2 grid で見えた spatial asymmetry (r2/r3 が more stable) → 20 seeds 拡張で均等分布に変化、artifact と判明
- observer が quiet regime (≤2 divergence window) を示す可能性 → 60 seeds 中 1 例のみ、デフォルトではない

## 核心的発見

1. **Global observer は lossy compression**: local observer が「正しい」k を保持する間、global はそれを消失させる。最頻出 divergence 状態は g3_r4444 (global が wrong、全 region が right)。
2. **Divergence は離散エピソード**: ノイズでなく、short-burst (<5w) と long-drift (≥5w) の 2 クラスに分類される。
3. **Local persistence は強い**: 単一 region 内で max 24/25 windows (96%) の連続同一 k\* を観測。
4. **Regime は 60 seeds・3 rate でも stable**: long_drift 70–80%、short_burst 17.5–30% の比率は perturbation 耐性を持つ。

## 次フェーズへの橋渡し

Ecology は observer 複数性を決定的に示した。「global の k\*」という単一視点は lossy compression に過ぎず、local observer が真の解像度を保持している。これは後の Cognition / Primitive で「主体は複数あり、それぞれ独自の世界を見ている」というアプローチの基礎になる。observer ecology は静的コンセンサスでなく metastable distributed regime として機能することが確認された。

## 原本を読むべきタイミング

- local vs global observer stability を詳しく知りたいとき (v2.1–v2.3)
- divergence episode の temporal structure や分類を確認したいとき (v2.4)
- regime robustness を rate perturbation データで検証したいとき (v2.6)
