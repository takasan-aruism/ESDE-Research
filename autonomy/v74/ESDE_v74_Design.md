ESDE v7.4 — 大規模 Autonomy テスト
======================================
Date: 2026-03-19
Process: 原文 → 解釈 → 設計 → 実装

============================================================
1. ARCHITECT 原文（Taka）
============================================================

「このテストの規模を拡張して何が起こるか？
 1万ノード 1Win=200step、多Seedでの並列処理、
 にした場合、規模はどの程度になるか？
 暇なのでコマンドライン上で様子が見えるといいかな」

「おそらく大規模テストをすることでその次の一手が明確に示されると思う」

「以前、同じような作業が多かった頃、あまりに時間かかるので
 速度向上のために色々手を加えたことがある。結構差が出る」

============================================================
2. ESDE 解釈
============================================================

v7.3 (N=5000, 50 steps) で見えたパターン:
  - 9 label が位相空間で自発分離
  - R>0 が label 間の橋として出現
  - 1120 born / 9 survived — 生存者の法則が見えた

N=10000, 200 steps に拡張することで:
  - links ~6000 (2×): より多くの二項基盤
  - steps 4×: 1 window 内でより多くの構造変化の機会
  - 6 seeds: 法則が seed 依存か普遍か判明

既存の engine_accel (v2.2-v2.4) は有効:
  - _fast_link_strength_sum: O(degree) lookups
  - exclusion: optimized
  - cycle_finder(C): C extension
  - latent_refresh: optimized

v7.4 固有の追加最適化:
  - _build_degree_map: stress の Ω 計算を O(links) で一括
  - _cached_aa: background seeding の配列を window 内で再利用
  - np.where: triggered ノードの検索をベクトル化
  - agr cache: ループ内定数を事前取得

============================================================
3. 設計
============================================================

■ 物理層: v7.3 と同一ロジック。N と steps だけ拡大。
■ 仮想層: virtual_layer_v2.py そのまま。
■ Stress: dynamic equilibrium (EMA) そのまま。

■ 新機能:
  - ETA 表示: 直近 10 window の平均から残り時間を推定
  - status ファイル: 別ターミナルから監視可能
  - --profile モード: cProfile で 3 window 走らせて Top 30 表示
  - monitor.sh: 全 seed の進捗を 10 秒ごと更新

■ パス: autonomy/v74/ → ESDE-Research/ (2段上)

============================================================
4. 実行計画
============================================================

  Step 1: profile で実測
    python esde_v74_calibrate.py --seed 42 --profile

  Step 2: 単一 seed で 5 window テスト
    python esde_v74_calibrate.py --seed 42 --windows 5

  Step 3: 本番 (一晩)
    bash run_parallel.sh

  Step 4: 結果分析
    6 seed の CSV を比較。label 生存法則の普遍性を検証。

============================================================
End of Document
