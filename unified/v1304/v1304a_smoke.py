# 観察対象注釈ブロック（v1304a child-ESDE existence check — feasibility + 最小 smoke）
# 系の別: 子 run は各々独立の系。parent-seed は親 profile を一回写すのみ（seed 後注入なし）。
#         other-parent null は full run で（初回 smoke は canon/parent/shuffle/uniform の4群）。F型の異系対応ではない。
# 過去成功との照合: v1303 attention output schema / cw_run.py build_child / v1302 persistent-param 継承。
# 過去失敗の回避: 循環 #CW7（初期条件を同期と読まない・本体 t_mid 以降）/ A 神の手（乖離に閾値でなく null 差）/
#                 D 平均化（per-t・n_core 層化は full run）/ #11 合成（eye 別 child）/ L 意味盛り（"子が注意した" と書かない）/
#                 v1302 教訓（runtime 連続注入しない・persistent-param 一回）/ read-only（親へ feedback しない）。
# 版規律: v1304a=existence check。本 smoke は feasibility+最小 smoke で停止・full run 自動進行しない・成立判定でない。
# 写像: shape-forming 確定（重み付けB不採用）。Stage 1B=親 phase_sig 分布(p_select重み)から子ノード初期θをサンプル(多峰保持)。
#       Stage 1A=circular mean で theta_mu 単独(単峰・#11リスク)は smoke 参考のみ。構造 knob(N/plb/k_sync)は canonical 固定。

import sys, os, json, time, warnings
from pathlib import Path
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")

REPO = Path("/home/takasan/esde/ESDE-Research")
for p in ["autonomy/v82", "ecology/engine", "primitive/v910", "cognition/semantic_injection/v4_pipeline/v43"]:
    sys.path.insert(0, str(REPO / p))
from esde_v82_engine import V82Engine, V82EncapsulationParams
from virtual_layer_v9 import VirtualLayer as VirtualLayerV9

SEED = 0
OUT = REPO / "unified" / "v1304" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)
SCHEMA = REPO / "unified" / "v1303" / "outputs" / "v1303j" / f"v1303_final_attention_output_seed{SEED}.parquet"
PS = REPO / "developmental" / "v105" / "diag_v105_main_v2" / "subjects" / f"per_subject_seed{SEED}.csv"

THETA_KAPPA = 4.0
N_CHILD = 150            # canonical 固定（群間で同一・差は初期θ shape のみ）
PLB, KSYNC = 0.007, 0.1  # canonical 固定
STEPS = 300
WIN = 50
K_SEED = 6               # 群ごと child 本数（smoke）
FORMAL_EYES = ["now_theta", "archive_theta_percentile", "link_rarity", "bgen_static_prior"]
GROUPS = ["canon", "parent", "shuffle", "uniform"]  # other-parent は full run で


def log(m): print(f"[v1304a-smoke] {m}", flush=True)


# ---------------------------------------------------------------------------
# 1. 親 profile（eye 別 marginal 選択分布）+ phase_sig（shape 源・45/228 疎）
# ---------------------------------------------------------------------------
def load_parent_profiles():
    sch = pd.read_parquet(SCHEMA)
    # eye 別 marginal: profile[eye,cid] = mean_t p_select_given_eye_t
    prof = (sch.groupby(["eye_id", "cid"])["p_select_given_eye_t"].mean().reset_index()
            .rename(columns={"p_select_given_eye_t": "w"}))
    ps = pd.read_csv(PS)
    ps["phase_sig"] = pd.to_numeric(ps["v11_m_c_phase_sig"], errors="coerce")
    ps = ps[["cognitive_id", "phase_sig"]].rename(columns={"cognitive_id": "cid"})
    phase = ps.dropna(subset=["phase_sig"]).set_index("cid")["phase_sig"]  # 45 cid
    return prof, phase


def eye_shape_weights(prof, phase, eye):
    """eye の親 profile を phase_sig を持つ 45 cid に絞り重み化。coverage(45cid外に置く質量割合)も返す。"""
    p = prof[prof["eye_id"] == eye].set_index("cid")["w"]
    total = p.sum()
    ps_cids = phase.index
    supported = p.reindex(ps_cids).fillna(0.0)
    mass_on_ps = supported.sum()
    coverage = float(mass_on_ps / total) if total > 0 else 0.0
    w = supported / mass_on_ps if mass_on_ps > 0 else pd.Series(1.0 / len(ps_cids), index=ps_cids)
    return w, coverage


def sample_theta(w, phase, group, rng):
    """Stage 1B: 重み w で cid を N 回引き phase_sig(cid) 中心の von Mises から初期θをサンプル（多峰保持）。"""
    cids = np.array(w.index)
    if group == "canon":
        return None  # attention shaping なし（engine 既定初期化）
    if group == "uniform":
        pw = np.full(len(cids), 1.0 / len(cids))
    elif group == "shuffle":
        pw = rng.permutation(w.to_numpy())   # cid↔attention 対応を壊す（量保持）
    else:  # parent
        pw = w.to_numpy()
    pw = pw / pw.sum()
    drawn = rng.choice(cids, size=N_CHILD, p=pw)
    mu = phase.loc[drawn].to_numpy()
    return rng.vonmises(mu, THETA_KAPPA, N_CHILD) % (2 * np.pi)


# ---------------------------------------------------------------------------
# 2. 子 engine（in-memory・shape-forming 初期θ・構造 knob canonical 固定・自走）
# ---------------------------------------------------------------------------
def signature(eng):
    N = eng.state.n_nodes
    al = list(eng.state.alive_n)
    aln, ll = len(al), len(eng.state.alive_l)
    sync = float(abs(np.mean(np.exp(1j * eng.state.theta[al])))) if al else 0.0
    rpos = sum(1 for k in eng.state.alive_l if eng.state.R.get(k, 0) > 0)
    labs = eng.virtual.labels
    ncs = [len(i["nodes"]) if isinstance(i, dict) else len(i.nodes) for i in labs.values()]
    return dict(alive_ratio=aln / N, link_density=ll / N, R_density=rpos / max(ll, 1),
                sync_order=sync, n_labels=len(labs), label_density=len(labs) / N,
                mean_label_ncore=float(np.mean(ncs)) if ncs else 0.0)


def run_child(theta_init, seed):
    encap = V82EncapsulationParams(stress_enabled=False, virtual_enabled=True)
    eng = V82Engine(seed=seed, N=N_CHILD, plb=PLB, encap_params=encap)
    eng.virtual = VirtualLayerV9(feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    for a, v in [("torque_order", "age"), ("deviation_enabled", True), ("semantic_gravity_enabled", True)]:
        if hasattr(eng.virtual, a): setattr(eng.virtual, a, v)
    eng.physics.params.K_sync = KSYNC
    eng.pressure_params.pressure_prob = 0.0
    if theta_init is not None:
        eng.state.theta[:] = theta_init            # shape-forming（seed 時一回のみ・以降注入なし）
    eng.run_injection()                            # 空 start 交絡回避（v1302 教訓）
    sigs = [dict(win=-1, t=0, **signature(eng))]   # t0（injection 直後・親情報が入っただけ）
    for w in range(STEPS // WIN):
        eng.step_window(steps=WIN)
        sigs.append(dict(win=w, t=(w + 1) * WIN, **signature(eng)))
    return sigs


# ---------------------------------------------------------------------------
# 3. 最小 smoke（4 eye × 4 群 × K seed・t 区分署名）
# ---------------------------------------------------------------------------
def tbin(t):
    if t == 0: return "t0"
    if t <= 100: return "t_short"
    if t <= 250: return "t_mid"
    return "t_late"


def main():
    t0 = time.time()
    prof, phase = load_parent_profiles()
    log(f"parent profiles: eyes={sorted(prof.eye_id.unique())} / phase_sig cids={len(phase)} (45/228 疎)")

    cov_rows, rows = [], []
    for eye in FORMAL_EYES:
        w, coverage = eye_shape_weights(prof, phase, eye)
        cov_rows.append(dict(eye=eye, coverage_on_phase_cids=round(coverage, 4),
                             mass_off_phase_cids=round(1 - coverage, 4)))
        for group in GROUPS:
            for k in range(K_SEED):
                rng = np.random.default_rng(hash((eye, group, k)) % (2**32))
                theta_init = sample_theta(w, phase, group, rng)
                sigs = run_child(theta_init, seed=1304 * 1000 + k)
                for s in sigs:
                    rows.append(dict(eye=eye, group=group, seed=k, **s, tbin=tbin(s["t"])))
        log(f"eye {eye} done ({time.time()-t0:.0f}s) coverage={coverage:.2f}")

    df = pd.DataFrame(rows)
    cov = pd.DataFrame(cov_rows)
    df.to_parquet(OUT / f"v1304a_smoke_signatures_seed{SEED}.parquet")
    cov.to_parquet(OUT / f"v1304a_smoke_coverage_seed{SEED}.parquet")

    # health（崩壊してないか＝構造を持った乖離か）
    health = df.groupby(["eye", "group"]).agg(
        min_alive_ratio=("alive_ratio", "min"), mean_alive_ratio=("alive_ratio", "mean")).reset_index()

    # first-look 区別性（判定でなく素の記述）: t_mid で parent vs canon/null の署名平均差
    sig_cols = ["alive_ratio", "link_density", "R_density", "sync_order", "n_labels", "label_density"]
    mid = df[df.tbin == "t_mid"].groupby(["eye", "group"])[sig_cols].mean().reset_index()
    mid.to_parquet(OUT / f"v1304a_smoke_tmid_means_seed{SEED}.parquet")

    summary = dict(design="v1304a_feasibility_smoke", mapping="shape-forming Stage 1B (phase_sig 分布サンプル)",
                   N_child=N_CHILD, steps=STEPS, k_seed=K_SEED, eyes=FORMAL_EYES, groups=GROUPS,
                   n_child_runs=len(FORMAL_EYES) * len(GROUPS) * K_SEED, total_s=round(time.time() - t0, 1))
    (OUT / f"v1304a_smoke_summary_seed{SEED}.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    log(f"DONE {summary['n_child_runs']} child runs, {summary['total_s']}s")
    return df, cov, health, mid


if __name__ == "__main__":
    df, cov, health, mid = main()
    pd.set_option("display.width", 200)
    print("\n=== coverage (親 attention mass のうち phase_sig 45cid に載る割合) ===")
    print(cov.to_string(index=False))
    print("\n=== health (min alive_ratio・崩壊してないか) ===")
    print(health.to_string(index=False))
    print("\n=== t_mid 署名平均（eye×group・first-look 区別性・判定でない） ===")
    print(mid.round(3).to_string(index=False))
