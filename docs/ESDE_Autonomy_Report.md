# ESDE Autonomy Report

*Phase: Autonomy (v8.0–)*
*Status: 未着手。Cognition phase (v3.0–v7.4) 完了を受けて開始。*
*Team: Taka (Architect) / Claude (Implementation)*
*Started: March 21, 2026*
*Last updated: March 21, 2026*
*Prerequisites: Cognition complete (see ESDE_Cognition_Report_Final.md)*

---

## Cognition からの引き継ぎ

Cognition phase (v3.0–v7.4) で確立された事実:

| 事実 | 検証規模 |
|------|---------|
| 物理層は動的平衡を自律維持 (sI ≈ 1.0) | 12 seeds, N=10000 |
| R+ ≈ 8 は N にスケールしない | N=5000 vs N=10000 |
| label は位相周波数グループ（空間クラスタではない） | 空間分析, seed=42 |
| R>0 は label 間の境界に出現 | 空間分析, seed=42 |
| label 生存法則: 遅い + 静か + 5 ノード | 1120 born → 9 survived |
| 動的平衡は seed 非依存（普遍） | 12 seeds 全一致 |
| budget=1 は配分比率であってエネルギーではない | v7.3 実装分析 |
| N は重要でない。ルールが構造を生む | v7.4 スケーリング結果 |

## Cognition が残した問い

**中心課題:** budget=1 の仮想エネルギーから、label 単体では
ありえない存在（スケール 3）をどう生むか。

Genesis の precedent:
```
ノード (スケール 1) → リンク → サイクル (スケール 2)
  物理法則: plb, rate, K_sync, decay
  物理的根拠: ノードが隣接ノードとエネルギーを交換する
  結果: k*=4 が自発的に出現（設計していない）
```

Autonomy で必要なこと:
```
label (スケール 2) → ??? → 新しい存在 (スケール 3)
  法則: 未定義
  物理的根拠: 観測データから導出すべき
  結果: 未知
```

## アーキテクチャ方針

**Taka 原文:** 「設計可能な数式はある程度物理的な根拠が伴えば許される」

**制約:**
- 数式の設計は許される。恣意は許されない。線引きは物理的根拠
- 仮説は不十分。条件を変えながら点を打ち続ける
- 関係性の近似値を数式化できたならラッキー

**方向性候補（未検証）:**
- label 間の位相干渉（物理的根拠: label は位相グループ）
- label 間の橋（物理的根拠: R>0 が label 間に出現した）
- ESDE NLP (Phase 8) との統一言語による外部入力接続
- label 集合の法則化（個別シミュレーション不要、法則だけ持ち歩く）

## 計算リソースの知見

| 層 | CPU 割合 | スケーリング |
|---|---|---|
| 物理層 | 99% | N に線形 |
| 仮想層 | < 0.1% | label 数に線形（~20） |
| Stress | < 1% | links に線形 |

仮想層の追加演算は本質的に安価。スマホレベルで搭載可能。
N=1000–5000 で十分（N を増やしても構造は変わらない）。

## NLP 統合の展望

**Taka 原文:** 「ESDE は NLP 的な開発が先行した。Genesis 以降を
優先したのは直感的にどこかで行き詰まるだろうと考えたから」

NLP 側（Phase 8）: テキスト → 48 次元意味座標
Autonomy 側: label → phase_sig (位相角)
接続に必要: 48 次元 ↔ label パラメータの統一言語（未設計）
ローカル LLM: QwQ-32B が Ryzen にセットアップ済み

## Version Changelog

| Version | Date | Author | Core Addition | Key Result |
|---------|------|--------|---------------|------------|
| (empty) | | | | |

---

*Autonomy phase は開始されたが、実装はまだない。
Cognition が物理層と仮想層の「床」を完成させた。
Autonomy はその床の上に「スケール 3 の存在」を
生む法則を見つけることが目標。
「金貨 1 枚を置いた。まだ経済はない。」*
