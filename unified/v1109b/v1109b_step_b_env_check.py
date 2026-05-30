#!/usr/bin/env python3
"""v1109b Step B — 環境準備 + #L65 兆候のサンプル数再確認"""
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1108A = REPO / 'unified/v1108a/outputs/main'
GE = REPO / 'unified/grammar_exploration'
V1109B = REPO / 'unified/v1109b/outputs/main'


def main():
    V1109B.mkdir(parents=True, exist_ok=True)
    print('=== v1109b Step B — 環境準備 ===\n')

    # データ存在
    hist = pd.read_parquet(V1108A / 'self_dialogue_with_atom_probs.parquet')
    print(f'self_dialogue: {len(hist):,} rows')
    print(f'  atom_top columns: {sum(1 for c in hist.columns if c.startswith("atom_top"))}')
    print(f'  prob_top columns: {sum(1 for c in hist.columns if c.startswith("prob_top"))}')

    # #L65 兆候のサンプル数
    print('\n--- #L65 兆候のサンプル数 ---')
    samples = []

    # start/end 分離: 327 events
    paths = pd.read_parquet(GE / 'I_grammar_paths.parquet')
    samples.append({'sign': 'start/end 経路', 'n': len(paths)})
    # PER.see → TIM.appear 81%
    per_paths = paths[paths['start'] == 'PER.see']
    samples.append({'sign': 'PER.see → TIM.appear', 'n': len(per_paths)})
    # 順序 npmi 6 ペア
    npmi = pd.read_parquet(GE / 'case_5_pmi_ordered.parquet')
    samples.append({'sign': 'npmi > 0.5', 'n': int((npmi['npmi'] > 0.5).sum())})
    # 役割切替 87%
    role = pd.read_parquet(GE / 'II_role_rules.parquet')
    samples.append({'sign': '役割切替 STRONG_*', 'n': int((role['rule_type'] != 'MIXED').sum())})
    # マルコフ超え連鎖 6 個
    triples = pd.read_parquet(GE / 'a_triples_lift.parquet')
    samples.append({'sign': 'マルコフ超え 3 連鎖', 'n': int((triples['log_lift'] > 1.0).sum())})
    # 文脈依存 STRICT 4 atom
    ctx = pd.read_parquet(GE / 'IV_full_context_dependent.parquet')
    samples.append({'sign': '文脈依存 STRICT', 'n': int(ctx['context_dependent_strict'].sum())})

    samples_df = pd.DataFrame(samples)
    samples_df.to_parquet(V1109B / 'env_check_samples.parquet', index=False)
    print(samples_df.to_string(index=False))

    # 統計安定性評価
    print('\n--- shuffle 統計安定性評価 (n ≥ 30 で OK、< 30 は留保) ---')
    samples_df['stability'] = samples_df['n'].apply(
        lambda n: 'OK' if n >= 30 else 'LIMITED' if n >= 10 else 'UNRELIABLE')
    print(samples_df.to_string(index=False))

    print('\n=== Step B 完了 ===')


if __name__ == '__main__':
    main()
