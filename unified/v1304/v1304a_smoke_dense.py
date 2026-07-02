# v1304a Stage 1B 再 smoke — dense θ角度源 original_phase_sig(228/228) で fair に washout を確認
# 観察対象注釈は v1304a_smoke.py と同じ。差分=角度源を v11_m_c_phase_sig(45疎) → original_phase_sig(228 dense) に置換。
# original_phase_sig は v11_m_c_phase_sig の dense 版(45重複で循環角度差 0.000・完全一致)を実測確認済。
# read-only・親へ feedback なし・物理非書込・停止(full 自動進行しない)・成立判定でない #12。

import sys, os, json, time, warnings
from pathlib import Path
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v1304a_smoke import (load_parent_profiles, eye_shape_weights, sample_theta, run_child,
                          tbin, FORMAL_EYES, GROUPS, K_SEED, N_CHILD, OUT, SEED, REPO)

PS = REPO / "developmental" / "v105" / "diag_v105_main_v2" / "subjects" / f"per_subject_seed{SEED}.csv"


def log(m): print(f"[v1304a-dense] {m}", flush=True)


def load_dense_phase():
    ps = pd.read_csv(PS)
    ph = pd.to_numeric(ps["original_phase_sig"], errors="coerce")
    return (pd.DataFrame({"cid": ps["cognitive_id"], "phase_sig": ph})
            .dropna(subset=["phase_sig"]).set_index("cid")["phase_sig"])  # 228 cid


def main():
    t0 = time.time()
    prof, _sparse = load_parent_profiles()
    phase = load_dense_phase()
    log(f"dense phase source: original_phase_sig {len(phase)}/228 cid")

    cov_rows, rows = [], []
    for eye in FORMAL_EYES:
        w, coverage = eye_shape_weights(prof, phase, eye)   # 同じ関数・source が dense
        cov_rows.append(dict(eye=eye, coverage_on_phase_cids=round(coverage, 4)))
        for group in GROUPS:
            for k in range(K_SEED):
                rng = np.random.default_rng(hash(("dense", eye, group, k)) % (2**32))
                theta_init = sample_theta(w, phase, group, rng)
                for s in run_child(theta_init, seed=1304 * 1000 + k):
                    rows.append(dict(eye=eye, group=group, seed=k, **s, tbin=tbin(s["t"])))
        log(f"eye {eye} done ({time.time()-t0:.0f}s) coverage={coverage:.3f}")

    df = pd.DataFrame(rows); cov = pd.DataFrame(cov_rows)
    df.to_parquet(OUT / f"v1304a_smoke_dense_signatures_seed{SEED}.parquet")
    cov.to_parquet(OUT / f"v1304a_smoke_dense_coverage_seed{SEED}.parquet")

    sig_cols = ["alive_ratio", "link_density", "R_density", "sync_order", "n_labels", "label_density"]
    # t区分別に group 平均 + 各量の group 間レンジ(max-min)=区別性の粗い目安
    tmid = df[df.tbin == "t_mid"].groupby(["eye", "group"])[sig_cols].mean().reset_index()
    tlate = df[df.tbin == "t_late"].groupby(["eye", "group"])[sig_cols].mean().reset_index()
    tmid.to_parquet(OUT / f"v1304a_smoke_dense_tmid_means_seed{SEED}.parquet")

    # parent vs canon の差を eye/量別に(判定でなく素の記述・seed 分散も)
    def group_spread(tb):
        g = df[df.tbin == tb]
        rows2 = []
        for eye in FORMAL_EYES:
            for c in sig_cols:
                sub = g[g.eye == eye]
                gm = sub.groupby("group")[c].mean()
                # parent - canon, と全群レンジ, と canon群のseed間std(noise床)
                canon_std = sub[sub.group == "canon"].groupby("seed")[c].mean().std()
                rows2.append(dict(tbin=tb, eye=eye, sig=c,
                                  parent_minus_canon=round(float(gm.get("parent", np.nan) - gm.get("canon", np.nan)), 4),
                                  group_range=round(float(gm.max() - gm.min()), 4),
                                  canon_seed_std=round(float(canon_std), 4)))
        return pd.DataFrame(rows2)
    spread = pd.concat([group_spread("t_mid"), group_spread("t_late")], ignore_index=True)
    spread.to_parquet(OUT / f"v1304a_smoke_dense_spread_seed{SEED}.parquet")

    summary = dict(design="v1304a_stage1B_dense_resmoke", angle_source="original_phase_sig(228 dense)",
                   N_child=N_CHILD, k_seed=K_SEED, n_runs=len(FORMAL_EYES)*len(GROUPS)*K_SEED,
                   total_s=round(time.time()-t0, 1))
    (OUT / f"v1304a_smoke_dense_summary_seed{SEED}.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    log(f"DONE {summary['n_runs']} runs {summary['total_s']}s")
    return cov, tmid, tlate, spread


if __name__ == "__main__":
    cov, tmid, tlate, spread = main()
    pd.set_option("display.width", 220)
    print("\n=== dense coverage (original_phase_sig・~1.0 なら親 profile を全部写せる) ===")
    print(cov.to_string(index=False))
    print("\n=== t_mid 署名平均(eye×group) ===")
    print(tmid.round(3).to_string(index=False))
    print("\n=== parent−canon 差 vs 全群レンジ vs canon seed間std(noise床)・washout 判断材料 ===")
    print("  (parent_minus_canon が canon_seed_std を超えれば noise 以上・超えなければ washout) ")
    print(spread[spread.tbin=="t_mid"].round(4).to_string(index=False))
    print("--- t_late ---")
    print(spread[spread.tbin=="t_late"].round(4).to_string(index=False))
