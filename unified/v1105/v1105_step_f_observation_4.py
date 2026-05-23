#!/usr/bin/env python3
"""v1105 Step F — 観察 4: 5 役割の仮割り当て表 (3 列形式)

設計書 v4 §2.5 通り、5 役割 (候補保持 / 連想・踏み台 / 即時応答の揺れ /
重要性 emit / 統合判断) を scope × 粒度に「仮割り当て + 観察上の支持 +
留保」3 列形式で割り当てる。

規律:
- 仮割り当てのまま、確定表にしない (GPT 監査 #2)
- selector として動作させない (post-process 観察のみ、ESDE 内部書き戻し 0)
- 「B を selector として使える」「使える可能性」と書かない (GPT 修正必須 D)
- B の意味判定をしない (GPT 追加推奨 6、v1105 主題範囲外、v1105a 送り)
- v1105a の試行設計書の素材として明示

入力 (read-only):
  - unified/v1105/outputs/main/observation_3_intensity_map.parquet (Step E 出力、11 数値)
  - unified/v1104a/outputs/main/observation_4_b_minus_a_cells.parquet (B_cmv/sal/crank 詳細)
  - unified/v1104a/outputs/main/observation_4_scope_filtered.parquet (B-A Jaccard/Recall/Precision)

出力:
  - unified/v1105/outputs/main/observation_4_role_assignment.parquet
  - unified/v1105/v1105_role_assignment_table.md (Step H 観察事実報告に組み込み用)
"""
from __future__ import annotations
import time
from pathlib import Path
import pandas as pd

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V1104A_MAIN = REPO_ROOT / 'unified/v1104a/outputs/main'
V1105_DIR = REPO_ROOT / 'unified/v1105'
V1105_MAIN = V1105_DIR / 'outputs/main'


ROLE_ASSIGNMENTS = [
    {
        'role': '候補保持',
        'segment': '段 4-b 前段',
        'tentative_assignment': 'CID (全 n_size_bin)',
        'observation_support': (
            'CID 100% self-loop (Step B\' 確認 3,798/3,798、#L30/L33 継承) で動的 trajectory '
            '構造的消失 (traj_stab=NaN、Step C/D 確認)。'
            'density 6 種は CID_n=2 で +0.72-0.99 超強 (Step D/E、Step C couple_hit_rate 15.7%/22.1% と並列)、'
            'CID_n=5/6+ で raw/norm sign_flip (+0.39→-0.39)、CID_all で norm -0.43、'
            '受信側として安定した候補保持の場の特徴を持つ。'
        ),
        'reservations': (
            '動的 trajectory は構造的に消失 (#L33)、候補抽出には他役割が必要。'
            'CID_n=2 だけが Language Couple endpoint と強接触 (15.7%、他 1.4%)、'
            'n_size_bin で内部差異あり、CID 集約だけでは語れない。'
            '保持される候補の絞りは「統合判断」役割の領域。'
        ),
    },
    {
        'role': '連想・踏み台',
        'segment': '段 4-b 本体',
        'tentative_assignment': 'alpha non-self-loop / beta non-self-loop (couple_hit_rate は別レイヤー)',
        'observation_support': (
            'alpha non-self-loop lift_C=0.152 (v1104a 追加調整 1 最強、#L30)、beta=0.091。'
            'alpha_all 集約 Genesis lift_C=0.165 (Step E 強度マップで全 stratum 中最強)。'
            'predecessor 連鎖が機能する場として候補が連想で繋がる構造。'
            'Language couple_hit_rate は beta_all で 0.070/0.092 が最強、'
            'alpha_all は逆に 0.014/0.006 と弱、Genesis と Language は別レイヤーの強度を持つ。'
        ),
        'reservations': (
            'Genesis predecessor (alpha 強) と Language Couple (beta 強) は scope 別に逆方向の強度。'
            '「連想・踏み台」を Genesis 視点で見るか Language 視点で見るかで主担当 scope が異なる。'
            'couple_hit_rate は scope に直接対応せず別レイヤー (§2.2)、v1105a 試行で両層の '
            '組合せ方を決定する必要。'
        ),
    },
    {
        'role': '即時応答の揺れ',
        'segment': '段 4-c 入力側',
        'tentative_assignment': 'ESDE event / ESDE step10',
        'observation_support': (
            'ESDE_event/step10 で trajectory r=+0.64 (stability) / -0.62 (diffusion) 強相関 '
            '(Step D 確認、#L31 v1104a 追加調整 2 再現)。'
            'ESDE_all 集約では r=0.42/-0.48 と細粒の方が強度。'
            'trajectory の動きが応答の絞り度合いと対応する場。'
        ),
        'reservations': (
            'ESDE_window では trajectory r=0/0 で消える (粒度感度、#L26 系列)。'
            '細粒 (event/step10) と集約 (window) で挙動が異なるため、'
            '「即時応答の揺れ」は粒度依存。'
            'CID/alpha/beta scope では trajectory は弱 (alpha 0.137、beta -0.074) または NaN (CID)、'
            'ESDE 細粒 scope 固有の役割。'
        ),
    },
    {
        'role': '重要性 emit',
        'segment': '段 4-c 補助',
        'tentative_assignment': 'ESDE (全粒度) + scope 別に異なる B 性質',
        'observation_support': (
            'v1104a 観察 4 (#L32): ESDE scope で A primary cell=0 / B cell=9 (3 解像度 × 3 metric)、'
            'B のみが拾う独自領域。alpha/beta で B が A の 2.7-7.5 倍広い (recall=1.0)、'
            'CID で B が A subset (precision=1.0)。'
            'B_cmv/B_sal/B_crank の 3 種 boolean が scope 別に異なる pattern。'
        ),
        'reservations': (
            'B が何を意味するか (selector として使えるか) は v1105 主題範囲外、'
            'v1105a 主題で点検 (GPT 追加推奨 6 遵守)。'
            'B の広い/狭い/独自 は scope 別に異なる構造事実として記録するに留める。'
            '「B primary 化が妥当か」の判定は本主題で行わない (selector 化禁止)。'
            'v1105a 初回試行では補助役割で十分 (GPT、§2.6)。'
        ),
    },
    {
        'role': '統合判断',
        'segment': '段 4-c 本体',
        'tentative_assignment': 'CID 集約 (density 6 種から sim_basis × density 種類を v1105a で選択)',
        'observation_support': (
            'CID_all で density norm 系列 r=-0.43 (raw -0.10 と Δ=0.33)、'
            'CID_n=2 で全 6 density 種類 r=+0.72-0.99 超強 (norm 系列 +0.98-0.99)。'
            'beta_all で density norm r=-0.50 (raw -0.35)。'
            'density は集約粒度で強い (#L31)、CID 集約 + 48 次元密度の組み合わせが '
            '応答 Atom 絞りに対応する構造。'
        ),
        'reservations': (
            'sim_basis × density 種類の 6 値の中でどれを「主」とするかは v1105a 試行で判断 '
            '(Step E 強度マップで raw vs norm の 2 軸非対称性 = sign_flip が CID_n=5/n=6+/ESDE_window で '
            '構造として現れる、#33 系列拡張)。'
            '48 次元人為性留保あり (v1103 GPT 監査 5)、Phase Result で必ず添える。'
            'CID_n=2 の超強相関 (+0.99) は他 CID bin と極端に異なる、密度効果の局所性。'
        ),
    },
]


def main():
    V1105_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1105 Step F 観察 4: 5 役割仮割り当て表 (3 列形式) ===')
    t0 = time.time()

    # parquet 本体
    df = pd.DataFrame(ROLE_ASSIGNMENTS)
    out = V1105_MAIN / 'observation_4_role_assignment.parquet'
    df.to_parquet(out, index=False)
    print(f'wrote {out.name} ({len(df)} roles)')

    # md 併記
    md_lines = [
        '# v11.0.5 (v1105) 役割表 (仮割り当て + 観察上の支持 + 留保 形式)',
        '',
        '*作成*: 2026-05-24、Code A (Step F 観察 4 出力)',
        '*親*: 設計書 v4 §2.5 (Web Claude 草案を Step C-E 構造事実で検証)',
        '*位置づけ*: 仮割り当てのまま、確定表ではない。v1105a 試行設計書の素材として明示 '
        '(GPT Auditor 2026-05-24 修正必須 #2 遵守)。',
        '',
        '## 規律宣言',
        '',
        '- selector として動作させない (post-process 観察のみ、ESDE 内部書き戻し 0)',
        '- 「B を selector として使える」「使える可能性」と書かない (GPT 修正必須 D)',
        '- B の意味判定をしない (GPT 追加推奨 6、v1105a 送り)',
        '- 「これが正解」と確定しない (絶対格言 #6 出口の固定、#12 Aruism 判定回避)',
        '- 構造事実の根拠は #L30-L33 + 観察 1/2/3 (Step C/D/E) の 11 数値強度マップから直接導出',
        '',
        '## 5 役割の仮割り当て',
        '',
        '| 役割 | 仮割り当て (scope × 粒度) | 観察上の支持 (構造事実) | 留保 |',
        '|---|---|---|---|',
    ]
    for r in ROLE_ASSIGNMENTS:
        md_lines.append(
            f"| **{r['role']}** ({r['segment']}) | "
            f"{r['tentative_assignment']} | "
            f"{r['observation_support']} | "
            f"{r['reservations']} |"
        )

    md_lines += [
        '',
        '## v1105a 進行条件 (GPT Auditor 2026-05-24、設計書 §2.6 遵守)',
        '',
        'v1105a に進める条件は「5 役割完全確定」ではなく、**試行可能な最小役割表 (3 役割) の成立**:',
        '',
        '| 最小役割 | 主候補 | 観察支持 |',
        '|---|---|---|',
        '| 候補を保持する場 | CID | CID 100% self-loop + density 強 |',
        '| 連想を辿る場 | alpha/beta non-self-loop または couple_hit_rate | predecessor lift / couple_hit_rate 別レイヤー |',
        '| 絞る場 | ESDE event/step10 trajectory + CID/48D density | 細粒 trajectory + 集約 density、粒度依存 |',
        '',
        '**重要性 emit (B) は v1105a 初回では補助役割で十分** (GPT、§2.6)。',
        'B primary 化は v1105a 主題で別途扱う (本主題範囲外)。',
        '',
        '## 設計書 §2.5 Web Claude 草案との対応',
        '',
        '設計書 v4 §2.5 草案を踏襲しつつ、Step C/D/E で得た構造事実で「観察上の支持」と「留保」を拡充。',
        '主要更新点 (v1105 で初観察):',
        '- CID_n=2 の極端な特殊性 (couple_hit_rate 15.7% / density 6 種 +0.99) を「候補保持」「統合判断」に追加',
        '- CID_n=5/n=6+ と ESDE_window での density 6 種全 sign_flip を「統合判断」留保に追加',
        '- alpha (Genesis 強) と beta (Language 強) の scope 別逆方向強度を「連想・踏み台」に追加',
        '',
        '## 最終判定への引き渡し',
        '',
        '各役割の出口 (採用 / 修正 / 削除) 判定 + 役割表全体の整合性評価 + v1105a 試行設計への接続は '
        '**Web Claude Phase Result + Taka 主題評価領域**。',
        'Code A は仮割り当てを構造事実と留保で示すまでが範囲 (絶対格言 #12 judgment 回避遵守)。',
    ]
    out_md = V1105_DIR / 'v1105_role_assignment_table.md'
    out_md.write_text('\n'.join(md_lines), encoding='utf-8')
    print(f'wrote {out_md.name} ({out_md.stat().st_size:,} bytes)')

    print(f'\n--- 5 役割サマリ ---')
    for r in ROLE_ASSIGNMENTS:
        print(f'  [{r["role"]}] {r["segment"]} → {r["tentative_assignment"]}')
    print(f'\nelapsed {time.time()-t0:.1f}s')


if __name__ == '__main__':
    main()
