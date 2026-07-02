# v1304a Stage 2 smoke — 構造 knob(plb/k_sync) も attention から形づくる(Stage 1 washout 確認後)
# 差分: Stage 1B の初期θ shape(dense original_phase_sig) に加え、plb←s_avg・k_sync←concentration を
#       attention 加重で群別に決める。scalar knob ゆえ shaping は「分布」でなく attention 加重平均(engine が scalar を取る)。
# 源: plb←v11_m_c_s_avg(45疎・dense twin なし→(a)45制限・coverage報告)、k_sync←v18_v_unified_concentration_birth
#     (228 dense・r_core と r=1.0 の dense twin)、θ←original_phase_sig(228 dense)。
# read-only・親へ feedback なし・物理非書込・停止(full自動進行しない)・成立判定でない #12。

import sys, os, json, time, warnings
from pathlib import Path
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v1304a_smoke import (load_parent_profiles, signature, tbin,
                          FORMAL_EYES, GROUPS, K_SEED, N_CHILD, OUT, SEED, REPO, THETA_KAPPA)
from esde_v82_engine import V82Engine, V82EncapsulationParams
from virtual_layer_v9 import VirtualLayer as VirtualLayerV9

PS = REPO / "developmental" / "v105" / "diag_v105_main_v2" / "subjects" / f"per_subject_seed{SEED}.csv"
STEPS, WIN = 300, 50
PLB_CANON, KSYNC_CANON = 0.007, 0.1


def log(m): print(f"[v1304a-s2] {m}", flush=True)


def load_sources():
    ps = pd.read_csv(PS)
    def num(c): return pd.to_numeric(ps[c], errors="coerce")
    phase = pd.Series(num("original_phase_sig").values, index=ps["cognitive_id"]).dropna()      # 228 dense(角度)
    s_avg = pd.Series(num("v11_m_c_s_avg").values, index=ps["cognitive_id"]).dropna()            # 45 疎(plb源)
    conc = pd.Series(num("v18_v_unified_concentration_birth").values, index=ps["cognitive_id"]).dropna()  # 228 dense(k_sync源)
    return phase, s_avg, conc


def group_weights(prof_eye, group, rng):
    """eye の p_select profile(cid上) を群別の重みベクトルに(canon 以外)。"""
    w = prof_eye.copy()
    if group == "uniform":
        w[:] = 1.0
    elif group == "shuffle":
        w = pd.Series(rng.permutation(w.values), index=w.index)
    return w / w.sum()


def sample_theta(wv, phase, rng):
    cids = np.intersect1d(wv.index, phase.index)
    p = wv.reindex(cids).fillna(0).to_numpy();
    if p.sum() == 0: return None
    p = p / p.sum()
    drawn = rng.choice(cids, size=N_CHILD, p=p)
    return rng.vonmises(phase.loc[drawn].to_numpy(), THETA_KAPPA, N_CHILD) % (2 * np.pi)


def knob_plb(wv, s_avg):
    """attention 加重平均 s_avg を z 化して plb(=cw_run 変換)。coverage も返す(45 疎)。"""
    cids = np.intersect1d(wv.index, s_avg.index)
    p = wv.reindex(cids).fillna(0).to_numpy(); cov = float(p.sum())
    if p.sum() == 0: return PLB_CANON, 0.0
    p = p / p.sum()
    wmean = float((p * s_avg.loc[cids].to_numpy()).sum())
    z = (wmean - s_avg.mean()) / (s_avg.std() + 1e-9)
    return float(0.007 * (1 + 0.15 * np.tanh(z))), cov


def knob_ksync(wv, conc):
    cids = np.intersect1d(wv.index, conc.index)
    p = wv.reindex(cids).fillna(0).to_numpy()
    if p.sum() == 0: return KSYNC_CANON
    p = p / p.sum()
    wmean = float((p * conc.loc[cids].to_numpy()).sum())
    return float(0.05 + (wmean - conc.min()) / (conc.max() - conc.min() + 1e-9) * 0.25)


def run_child(theta_init, plb, k_sync, seed):
    encap = V82EncapsulationParams(stress_enabled=False, virtual_enabled=True)
    eng = V82Engine(seed=seed, N=N_CHILD, plb=plb, encap_params=encap)
    eng.virtual = VirtualLayerV9(feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    for a, v in [("torque_order", "age"), ("deviation_enabled", True), ("semantic_gravity_enabled", True)]:
        if hasattr(eng.virtual, a): setattr(eng.virtual, a, v)
    eng.physics.params.K_sync = k_sync
    eng.pressure_params.pressure_prob = 0.0
    if theta_init is not None: eng.state.theta[:] = theta_init
    eng.run_injection()
    sigs = [dict(win=-1, t=0, **signature(eng))]
    for w in range(STEPS // WIN):
        eng.step_window(steps=WIN); sigs.append(dict(win=w, t=(w + 1) * WIN, **signature(eng)))
    return sigs


def main():
    t0 = time.time()
    prof, _ = load_parent_profiles()
    phase, s_avg, conc = load_sources()
    log(f"sources: phase {len(phase)}(dense) / s_avg {len(s_avg)}(疎・plb) / conc {len(conc)}(dense・k_sync)")

    knob_rows, rows = [], []
    for eye in FORMAL_EYES:
        pe = prof[prof.eye_id == eye].set_index("cid")["w"]
        for group in GROUPS:
            krng = np.random.default_rng(hash(("s2knob", eye, group)) % (2**32))
            if group == "canon":
                plb, ks, cov = PLB_CANON, KSYNC_CANON, np.nan
            else:
                wv = group_weights(pe, group, krng)
                plb, cov = knob_plb(wv, s_avg)
                ks = knob_ksync(wv, conc)
            knob_rows.append(dict(eye=eye, group=group, plb=round(plb, 5), k_sync=round(ks, 4),
                                  plb_coverage_on_45=round(float(cov), 3) if not np.isnan(cov) else np.nan))
            for k in range(K_SEED):
                srng = np.random.default_rng(hash(("s2", eye, group, k)) % (2**32))
                wv = None if group == "canon" else group_weights(pe, group, srng)
                theta_init = None if group == "canon" else sample_theta(wv, phase, srng)
                for s in run_child(theta_init, plb, ks, seed=1304 * 1000 + k):
                    rows.append(dict(eye=eye, group=group, seed=k, **s, tbin=tbin(s["t"])))
        log(f"eye {eye} done ({time.time()-t0:.0f}s)")

    df = pd.DataFrame(rows); knobs = pd.DataFrame(knob_rows)
    df.to_parquet(OUT / f"v1304a_stage2_signatures_seed{SEED}.parquet")
    knobs.to_parquet(OUT / f"v1304a_stage2_knobs_seed{SEED}.parquet")

    sig_cols = ["link_density", "R_density", "sync_order", "n_labels", "label_density"]
    rows2 = []
    for tb in ["t_mid", "t_late"]:
        g = df[df.tbin == tb]
        for eye in FORMAL_EYES:
            sub = g[g.eye == eye]
            for c in sig_cols:
                gm = sub.groupby("group")[c].mean()
                canon_std = sub[sub.group == "canon"].groupby("seed")[c].mean().std()
                rows2.append(dict(tbin=tb, eye=eye, sig=c,
                                  parent_minus_canon=round(float(gm.get("parent", np.nan) - gm.get("canon", np.nan)), 4),
                                  group_range=round(float(gm.max() - gm.min()), 4),
                                  canon_seed_std=round(float(canon_std), 4)))
    spread = pd.DataFrame(rows2); spread.to_parquet(OUT / f"v1304a_stage2_spread_seed{SEED}.parquet")
    (OUT / f"v1304a_stage2_summary_seed{SEED}.json").write_text(json.dumps(dict(
        design="v1304a_stage2_smoke", note="scalar knob=attention加重平均(分布でない)・plb源45疎・k_sync源228dense",
        n_runs=len(FORMAL_EYES)*len(GROUPS)*K_SEED, total_s=round(time.time()-t0, 1)), indent=2, ensure_ascii=False))
    log(f"DONE {len(FORMAL_EYES)*len(GROUPS)*K_SEED} runs {round(time.time()-t0,1)}s")
    return knobs, spread


if __name__ == "__main__":
    knobs, spread = main()
    pd.set_option("display.width", 220)
    print("\n=== 群別 knob(attention加重・parent/shuffle/uniform で違うか)+ plb coverage(45疎) ===")
    print(knobs.to_string(index=False))
    print("\n=== parent−canon 差 vs 全群レンジ vs canon noise床(t_mid)・Stage2で乖離が立つか ===")
    print(spread[spread.tbin=="t_mid"].round(4).to_string(index=False))
    print("--- t_late ---")
    print(spread[spread.tbin=="t_late"].round(4).to_string(index=False))
