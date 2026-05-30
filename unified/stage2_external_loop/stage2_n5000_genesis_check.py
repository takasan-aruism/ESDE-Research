#!/usr/bin/env python3
"""第 2 段階補足 — N=5000 + warmup で Genesis 起動確認

v918_memory_readout.py を subprocess で実行し、alive_n が立つことを確認する。
N=V82_N=5000 は固定 (run 関数内)、maturation/tracking で warmup を制御。

smoke 設定:
- maturation_windows=3、tracking_windows=1、window_steps=100
- 想定 step 数: 3*100 + 1*100 = 400 step、N=5000、おそらく 30 秒〜数分

物理層 frozen 維持:
- 出力 diag_v918_{tag} は cwd 直下に作られる
- cwd を unified/stage2_external_loop/run_n5000/ にして実行
- 既存 developmental/v105 等は触らない
"""
import subprocess, sys, time, json
from pathlib import Path
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
STAGE2 = REPO / 'unified/stage2_external_loop'
RUN_DIR = STAGE2 / 'run_n5000'
RUN_DIR.mkdir(parents=True, exist_ok=True)
OUT = STAGE2 / 'outputs/main'

V918_SCRIPT = REPO / 'primitive/v918/v918_memory_readout.py'

# smoke 設定
SEED = 42
MATURATION = 3
TRACKING = 1
WINDOW_STEPS = 100
TAG = 'genesis_smoke'


def main():
    print('=== N=5000 Genesis 起動確認 ===\n')
    print(f'  scripts: {V918_SCRIPT}')
    print(f'  cwd: {RUN_DIR}')
    print(f'  params: seed={SEED}, maturation={MATURATION}, tracking={TRACKING}, '
          f'window_steps={WINDOW_STEPS}, tag={TAG}')
    print(f'  N=V82_N=5000 (固定)\n')

    cmd = [
        sys.executable, str(V918_SCRIPT),
        '--seed', str(SEED),
        '--maturation-windows', str(MATURATION),
        '--tracking-windows', str(TRACKING),
        '--window-steps', str(WINDOW_STEPS),
        '--tag', TAG,
    ]
    print(f'[1] subprocess 起動: {" ".join(cmd[-9:])}\n')
    t0 = time.time()
    result = subprocess.run(cmd, cwd=str(RUN_DIR), capture_output=True, text=True,
                              timeout=900)  # 15 分 timeout
    elapsed = time.time() - t0
    print(f'  return code: {result.returncode}')
    print(f'  elapsed: {elapsed:.1f}s')

    # stdout / stderr 最後の方
    print(f'\n  stdout 末尾 (最後 20 行):')
    for line in result.stdout.split('\n')[-20:]:
        print(f'    {line}')
    if result.stderr:
        print(f'\n  stderr 末尾 (最後 10 行):')
        for line in result.stderr.split('\n')[-10:]:
            print(f'    {line}')

    if result.returncode != 0:
        print('\n  ✗ subprocess 失敗')
        # 出力を保存
        (OUT / 'genesis_check_stdout.txt').write_text(result.stdout)
        (OUT / 'genesis_check_stderr.txt').write_text(result.stderr)
        return

    # 出力ディレクトリ確認
    output_dir = RUN_DIR / f'diag_v918_{TAG}'
    print(f'\n[2] 出力ディレクトリ確認: {output_dir.relative_to(REPO)}')
    if not output_dir.exists():
        print(f'  ✗ 出力ディレクトリなし')
        return
    for sub in output_dir.iterdir():
        if sub.is_dir():
            n_files = len(list(sub.iterdir()))
            print(f'  {sub.name}/ : {n_files} files')

    # per_window CSV から alive_n / alive_l 確認
    print(f'\n[3] alive_n / alive_l 確認 (per_window_seed{SEED}.csv)')
    per_window_csv = output_dir / 'aggregates' / f'per_window_seed{SEED}.csv'
    if not per_window_csv.exists():
        print(f'  ✗ per_window CSV なし')
        return
    df = pd.read_csv(per_window_csv)
    print(f'  rows: {len(df)}')
    print(f'  columns (head): {list(df.columns)[:15]}')

    # alive 系列カラムを探す
    alive_cols = [c for c in df.columns if 'alive' in c.lower()]
    print(f'\n  alive 関連カラム: {alive_cols}')

    if alive_cols:
        print(f'\n--- 各 window の alive 状態 ---')
        print(df[['window'] + alive_cols if 'window' in df.columns
                  else alive_cols].to_string(index=False))

        # 結果集約
        max_alive_n = max(df[c].max() for c in alive_cols if 'alive_n' in c.lower())
        print(f'\n  ★ max alive_n: {max_alive_n}')
        if max_alive_n > 0:
            print(f'  ✓ Genesis 起動成功!')
        else:
            print(f'  ✗ alive_n が立たず、Genesis 未起動')

    # per_subject (CID 関連) も確認
    print(f'\n[4] CID 確認 (per_subject_seed{SEED}.csv)')
    per_sub_csv = output_dir / 'subjects' / f'per_subject_seed{SEED}.csv'
    if per_sub_csv.exists():
        sdf = pd.read_csv(per_sub_csv)
        print(f'  per_subject rows: {len(sdf)}')
        print(f'  columns (head): {list(sdf.columns)[:10]}')
        if 'cognitive_id' in sdf.columns:
            print(f'  unique CIDs: {sdf["cognitive_id"].nunique()}')
            if 'final_state' in sdf.columns:
                print(f'  final_state 分布: {sdf["final_state"].value_counts().to_dict()}')

    # 結果サマリ JSON 保存
    summary = {
        'elapsed_sec': elapsed,
        'returncode': result.returncode,
        'output_dir': str(output_dir.relative_to(REPO)),
        'max_alive_n': int(max_alive_n) if alive_cols else None,
        'genesis_started': bool(alive_cols and max_alive_n > 0),
        'n_cids': int(sdf["cognitive_id"].nunique()) if per_sub_csv.exists() and 'cognitive_id' in sdf.columns else 0,
    }
    (OUT / 'genesis_check_summary.json').write_text(json.dumps(summary, indent=2))
    print(f'\n=== 完了、{elapsed:.1f}s ===')


if __name__ == '__main__':
    main()
