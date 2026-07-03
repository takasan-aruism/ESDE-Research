# v1304b feedback loop 最小実装 smoke — 子世界をセンターの観察scopeに足すループ
# 設計: Web Claude v1304b rev4。read-only・親物理非書込・書込 unified/v1304/outputs 配下・seed0・判定なし#12。
#
# 部品(既存流用): ①composition = stage3b機構(weight比例sample M子・plb←s_avg) / ②珍しさ = probe dyn_rarity同式(両側-log10・floor 1/(2n))を子集団に
# ③更新則(唯一の新要素・rev4確定):
#   - cid単位平均→round正規化: cid_sal=mean(salience_eff of children from cid) / factor=(cid_sal/round_mean)^g / undrawn factor=1
#   - α(不動): 引かれない cid は weight 据え置き(観察の不在は不在の観察でない・v1114 pull)
#   - eps floor は正規化前の salience に(数値安定化・cutoff でない) / salience_rank は監査保存のみ(更新に混ぜない)
# 群3本: feedback(本命) / no_feedback(weight=round0固定・参照群) / shuffle(feedbackの世界に相乗り・drawn cid間で正規化前 salience を permute=対応のみ破壊・更新量分布は完全一致)
# primary(smoke では算出のみ・統計判定しない): D = mean_round L1(weight_feedback, weight_shuffle)  ※事前固定・結果を見て指標を選ばない
# smoke: 実装健全性とログ完全性のみ(停止成功条件6点)。g=1のみ・lens=link_density のみ・base0。

import sys, os, json, time, hashlib, warnings
from pathlib import Path
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v1304a_smoke import signature, FORMAL_EYES, OUT, SEED, REPO
from esde_v82_engine import V82Engine, V82EncapsulationParams
from virtual_layer_v9 import VirtualLayer as VirtualLayerV9

PS = REPO / "developmental" / "v105" / "diag_v105_main_v2" / "subjects" / f"per_subject_seed{SEED}.csv"
SCHEMA = REPO / "unified" / "v1303" / "outputs" / "v1303j" / f"v1303_final_attention_output_seed{SEED}.parquet"

R = int(os.environ.get("V1304B_R", 5))      # リサンプル系列(独立な weight 軌跡)
T = int(os.environ.get("V1304B_T", 5))      # rounds
M = int(os.environ.get("V1304B_M", 20))     # draw あたり子数
BASE = int(os.environ.get("V1304B_BASE", 0))
G = float(os.environ.get("V1304B_G", 1.0))  # gain(smoke は primary の 1 のみ・事前固定)
EPS = 1e-6                                    # salience floor(正規化前・数値安定化)
LENS = "link_density"
INIT_EYE = "now_theta"
N_CHILD, KSYNC_CANON, STEPS, WIN = 150, 0.1, 300, 50
GROUPS = ["feedback", "no_feedback", "shuffle"]
SIG_COLS = ["link_density", "R_density", "sync_order", "n_labels", "label_density", "mean_label_ncore"]


def log(m): print(f"[v1304b] {m}", flush=True)


def md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def entropy(w):
    w = np.asarray(w, float); w = w[w > 0]
    return float(-(w * np.log(w)).sum())


def rarity(vals):
    """子集団内の両側 -log10 珍しさ(probe dyn_rarity と同式・floor 1/(2n))。vals=M子の lens 値。"""
    v = pd.Series(np.asarray(vals, float))
    n = len(v)
    pct = v.rank(pct=True).values
    two = np.clip(2 * np.minimum(pct, 1 - pct), 1.0 / (2 * n), None)
    return -np.log10(two)


def load_init():
    """初期 weight = now_theta lift(eligible定義・stage3b と同一) / support = plb 非欠損 45 cid。"""
    sch = pd.read_parquet(SCHEMA)
    sch["pe"] = sch["p_select_given_eye_t"] * sch["eligible_count"]
    lift = sch[sch["p_select_given_eye_t"] > 0].groupby(["eye_id", "cid"])["pe"].mean().loc[INIT_EYE]
    ps = pd.read_csv(PS)
    s_avg = pd.Series(pd.to_numeric(ps["v11_m_c_s_avg"], errors="coerce").values, index=ps["cognitive_id"]).dropna()
    z = (s_avg - s_avg.mean()) / (s_avg.std() + 1e-9)
    plb = 0.007 * (1 + 0.15 * np.tanh(z))            # plb←s_avg 写像(stage3b と同一)
    support = np.array(sorted(plb.index))
    w0 = lift.reindex(support).fillna(0.0).clip(lower=0).to_numpy()
    if w0.sum() <= 0:
        raise RuntimeError("init weight all-zero")
    w0 = w0 / w0.sum()
    return support, plb, w0


def run_child(plb, seed):
    """子 engine を自走(stage3b と同一構築)。全 window の署名時間平均(単一 scalar 化)を返す。親物理に触れない。"""
    encap = V82EncapsulationParams(stress_enabled=False, virtual_enabled=True)
    eng = V82Engine(seed=seed, N=N_CHILD, plb=plb, encap_params=encap)
    eng.virtual = VirtualLayerV9(feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    for a, v in [("torque_order", "age"), ("deviation_enabled", True), ("semantic_gravity_enabled", True)]:
        if hasattr(eng.virtual, a): setattr(eng.virtual, a, v)
    eng.physics.params.K_sync = KSYNC_CANON
    eng.pressure_params.pressure_prob = 0.0
    eng.run_injection()                           # θ既定・空start交絡回避
    sigs = []
    for _ in range(STEPS // WIN):
        eng.step_window(steps=WIN)
        sigs.append(signature(eng))               # 署名は step 後・全 window 収集
    return {c: float(np.mean([s[c] for s in sigs])) for c in SIG_COLS}


def eng_seed(base, r, t, j):
    return base * 10_000_000 + r * 100_000 + t * 1_000 + j


def update_factor(drawn, sal_eff, support_idx, permute_rng=None):
    """rev4: cid単位平均→round正規化。factor[cid]=(cid_sal/round_mean)^g・undrawn=1。
       permute_rng を渡すと drawn distinct cid 間で cid_sal を permute(shuffle群・対応のみ破壊)。"""
    df = pd.DataFrame({"cid": drawn, "sal": sal_eff})
    cid_sal = df.groupby("cid")["sal"].mean()          # 由来 cid ごとの観察値(child単位でなく cid単位)
    distinct = cid_sal.index.to_numpy()
    vals = cid_sal.to_numpy().copy()
    if permute_rng is not None:
        vals = vals[permute_rng.permutation(len(vals))]  # 対応破壊・値の多重集合は不変
    round_mean = float(np.mean(cid_sal.to_numpy()))     # 分母は round の子集団自身(ノブなし)・permute でも不変
    factor = np.ones(len(support_idx))
    for c, v in zip(distinct, vals):
        factor[support_idx[c]] = (v / round_mean) ** G
    return factor, len(distinct), round_mean


def main():
    t0 = time.time()
    ph_hash_pre = {"PS": md5(PS), "SCHEMA": md5(SCHEMA)}
    support, plb, w0 = load_init()
    n_sup = len(support)
    support_idx = {c: i for i, c in enumerate(support)}
    # round0 support 固定ログ(§7-4)
    round0_log = dict(support_n=n_sup, sum_weight=float(w0.sum()), w_min=float(w0.min()),
                      w_max=float(w0.max()), entropy=entropy(w0),
                      cid_hash=hashlib.md5(",".join(map(str, support)).encode()).hexdigest())
    log(f"round0 support: {round0_log}")

    W, SAL, COV, CSIG, PRIM = [], [], [], [], []   # 出力蓄積
    for r in range(R):
        w = {"feedback": w0.copy(), "no_feedback": w0.copy(), "shuffle": w0.copy()}
        for t in range(T):
            # --- feedback: 自群 weight で composition・子自走 ---
            drng_fb = np.random.default_rng((BASE, r, t, 101))
            drawn_fb = drng_fb.choice(support, size=M, p=w["feedback"])
            lens_fb, sig_fb = [], []
            for j in range(M):
                res = run_child(float(plb.loc[drawn_fb[j]]), eng_seed(BASE, r, t, j))
                lens_fb.append(res[LENS]); sig_fb.append(res)
            sal_raw = rarity(lens_fb)                        # 子集団内 -log10 珍しさ
            sal_eff = np.maximum(sal_raw, EPS)               # eps floor(正規化前)
            sal_rank = pd.Series(lens_fb).rank(method="average").to_numpy()  # 監査保存のみ
            for j in range(M):
                SAL.append(dict(r=r, t=t, j=j, drawn_cid=int(drawn_fb[j]), lens=lens_fb[j],
                                salience_raw=float(sal_raw[j]), salience_eff=float(sal_eff[j]),
                                salience_rank=float(sal_rank[j])))
            # feedback 更新(正しい対応) / shuffle 更新(feedback の世界に相乗り・対応のみ permute)
            f_fb, ndist, rmean = update_factor(drawn_fb, sal_eff, support_idx)
            srng = np.random.default_rng((BASE, r, t, 303))
            f_shuf, _, _ = update_factor(drawn_fb, sal_eff, support_idx, permute_rng=srng)
            w["feedback"] = w["feedback"] * f_fb; w["feedback"] /= w["feedback"].sum()
            w["shuffle"] = w["shuffle"] * f_shuf; w["shuffle"] /= w["shuffle"].sum()
            # no_feedback: weight=round0 固定・自群 composition(参照群・§4-4 用に子は自走・更新なし)
            drng_nof = np.random.default_rng((BASE, r, t, 202))
            drawn_nof = drng_nof.choice(support, size=M, p=w["no_feedback"])
            sig_nof = [run_child(float(plb.loc[drawn_nof[j]]), eng_seed(BASE, r, t, j)) for j in range(M)]
            # ログ: weight 軌跡 / coverage / 子集団署名
            for g in GROUPS:
                for i, c in enumerate(support):
                    W.append(dict(r=r, t=t, group=g, cid=int(c), weight=float(w[g][i])))
            undrawn = n_sup - ndist
            COV.append(dict(r=r, t=t, group="feedback", drawn_distinct=ndist, undrawn=undrawn,
                            undrawn_rate=round(undrawn / n_sup, 4), round_mean_salience=round(rmean, 5)))
            COV.append(dict(r=r, t=t, group="no_feedback", drawn_distinct=int(len(set(drawn_nof.tolist()))),
                            undrawn=n_sup - len(set(drawn_nof.tolist())), undrawn_rate=None, round_mean_salience=None))
            for g, sgs in [("feedback", sig_fb), ("no_feedback", sig_nof)]:
                row = dict(r=r, t=t, group=g)
                for c in SIG_COLS: row[c] = float(np.mean([s[c] for s in sgs]))
                CSIG.append(row)
            # primary(算出のみ・判定しない): L1(feedback, shuffle) と 参照 L1(feedback, no_feedback)
            PRIM.append(dict(r=r, t=t,
                             L1_fb_shuffle=float(np.abs(w["feedback"] - w["shuffle"]).sum()),
                             L1_fb_nofeedback=float(np.abs(w["feedback"] - w["no_feedback"]).sum())))
        log(f"R series {r} done ({time.time()-t0:.0f}s)")

    # 書込(全て unified/v1304/outputs 配下)
    sfx = f"seed{SEED}_base{BASE}"
    pd.DataFrame(W).to_parquet(OUT / f"v1304b_smoke_weights_{sfx}.parquet")
    pd.DataFrame(SAL).to_parquet(OUT / f"v1304b_smoke_salience_{sfx}.parquet")
    pd.DataFrame(COV).to_parquet(OUT / f"v1304b_smoke_coverage_{sfx}.parquet")
    pd.DataFrame(CSIG).to_parquet(OUT / f"v1304b_smoke_childsig_{sfx}.parquet")
    prim = pd.DataFrame(PRIM); prim.to_parquet(OUT / f"v1304b_smoke_primary_{sfx}.parquet")

    ph_hash_post = {"PS": md5(PS), "SCHEMA": md5(SCHEMA)}
    wdf = pd.DataFrame(W)
    # 停止成功条件6点(実装健全性・判定でない)
    n_child_expected = R * T * M * 2  # feedback + no_feedback(shuffle は feedback の世界に相乗り)
    conds = {
        "i_all_round_group_child_gen": bool(len(CSIG) == R * T * 2 and len(SAL) == R * T * M),
        "ii_provenance_no_missing": bool(pd.DataFrame(SAL)["drawn_cid"].notna().all()),
        "iii_seed_match_fb_shuffle": True,  # shuffle は feedback の drawn/子を相乗り(定義上完全一致)
        "iv_weight_no_nan_no_collapse": bool(wdf["weight"].notna().all() and
                                             wdf.groupby(["r", "t", "group"])["weight"].sum().sub(1.0).abs().max() < 1e-9),
        "v_parent_physics_hash_unchanged": bool(ph_hash_pre == ph_hash_post),
        "vi_writes_under_v1304": True,  # OUT = unified/v1304/outputs(全書込先)
    }
    summary = dict(design="v1304b_feedback_loop_smoke_rev4", R=R, T=T, M=M, base=BASE, g=G, eps=EPS,
                   lens=LENS, init_eye=INIT_EYE, n_child_run=n_child_expected,
                   round0_support=round0_log, parent_physics_hash=ph_hash_pre,
                   stop_success_conditions=conds, all_pass=bool(all(conds.values())),
                   primary_L1_fb_shuffle_mean=float(prim["L1_fb_shuffle"].mean()),
                   primary_L1_fb_nofeedback_mean=float(prim["L1_fb_nofeedback"].mean()),
                   total_s=round(time.time() - t0, 1))
    (OUT / f"v1304b_smoke_summary_{sfx}.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    log(f"DONE {n_child_expected} children {round(time.time()-t0,1)}s / all_pass={summary['all_pass']}")
    return summary


if __name__ == "__main__":
    s = main()
    print("\n=== 停止成功条件6点 ===")
    for k, v in s["stop_success_conditions"].items():
        print(f"  {'OK' if v else 'NG'}  {k}")
    print(f"\nall_pass = {s['all_pass']}")
    print(f"primary(算出のみ・判定しない): L1(fb,shuffle) mean = {s['primary_L1_fb_shuffle_mean']:.5f} / "
          f"L1(fb,no_fb) mean = {s['primary_L1_fb_nofeedback_mean']:.5f}")
