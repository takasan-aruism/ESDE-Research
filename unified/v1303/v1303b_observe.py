#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# v1303b Step B — 同じ CID 内で3レンズが時間方向にどれだけ反復・安定・同時変動するか
#                  を既存 ledger の後処理で読む（観察A〜E + shuffle 2種）
#
# 規律宣言（Code A / 失敗記録12型・v1303b 設計）
#  1. 読: 既存 ledger（unified/v1303/outputs/v1303_ledger_seed0.parquet）READ-ONLY。
#     書: unified/v1303/outputs/v1303b/ のみ。**再走しない**（後処理のみ・Step E 不要）。
#  2. 失敗型回避:
#     B型 → 既存 ledger 後処理のみ。cid-label shuffle は対照限定（関係生成にしない）。
#     C型 → shuffle 2種で交絡を切る。予測を出口にしない。dominant_fraction を時間構造証拠にしない。
#     D型 → 全 CID 平均の相関を出さない。cid 個別・n_core 別。
#     #11 → 3レンズを合成しない（ペア/レンズ別）。③主軸=node θ・link(S/R)は別枠補助(観察E)。
#     L型 → Atom を意味解釈しない（名前でなく再出現パターン）。乾いた指標名。
#     #12/J型 → (a)/(b) 判定しない。観察事実のみ。観察を A〜E に絞る。seed0 のみ。
#  3. 実装ガード: hosted_available のみ(観察D は ghost 遷移)。min_points=30。
#     C/Q は window 粒度（step10 で大半不変）ゆえ観察C の C/Q は window 粒度補助注記。
#  判定は Web Claude / Taka。
# ─────────────────────────────────────────────────────────────────────────────
import numpy as np
import pandas as pd
from pathlib import Path
from collections import Counter

REPO = Path(__file__).resolve().parents[2]
LEDGER = REPO / "unified" / "v1303" / "outputs" / "v1303_ledger_seed0.parquet"
OUT = REPO / "unified" / "v1303" / "outputs" / "v1303b"
OUT.mkdir(parents=True, exist_ok=True)

MIN_POINTS = 30
N_SHUFFLE = 200
SEED = 42
LAGS = [1, 5, 10, 50, 100]


# ── 指標関数（乾いた操作定義） ───────────────────────────────────────────────
def run_lengths(arr):
    if len(arr) == 0:
        return [0]
    r = [1]
    for i in range(1, len(arr)):
        if arr[i] == arr[i - 1]:
            r[-1] += 1
        else:
            r.append(1)
    return r


def return_interval_same(arr):
    # 同じ atom に戻る間隔（出現 index の差分）の中央値
    pos = {}
    gaps = []
    for i, a in enumerate(arr):
        if a in pos:
            gaps.append(i - pos[a])
        pos[a] = i
    return float(np.median(gaps)) if gaps else np.nan


def entropy(arr):
    vc = Counter(arr)
    n = len(arr)
    return float(-sum((c / n) * np.log2(c / n) for c in vc.values())) if n else np.nan


def autocorr(x, lag):
    if len(x) <= lag:
        return np.nan
    a = x[:-lag]
    b = x[lag:]
    if np.std(a) < 1e-12 or np.std(b) < 1e-12:
        return np.nan
    return float(np.corrcoef(a, b)[0, 1])


def pctl(observed, null_samples):
    # 観測値が shuffle null 分布の何 percentile か（0-1）
    arr = np.array([v for v in null_samples if not np.isnan(v)])
    if len(arr) == 0 or np.isnan(observed):
        return np.nan
    return float((arr < observed).mean())


# ── 観察A/B/C を 1 cid の時系列から計算（observed） ──────────────────────────
def metrics_for_series(atoms, theta, C, Q):
    n = len(atoms)
    out = {}
    # A: rank_1 再出現
    rl = run_lengths(atoms)
    out["mean_run_length"] = float(np.mean(rl))
    out["max_run_length"] = int(np.max(rl))
    switches = sum(1 for i in range(1, n) if atoms[i] != atoms[i - 1])
    out["switch_per_1000"] = switches / (n * 10) * 1000  # t は step10 刻み
    out["return_interval_same_atom_med"] = return_interval_same(atoms)
    out["dominant_atom_fraction"] = Counter(atoms).most_common(1)[0][1] / n  # 補助
    out["atom_entropy"] = entropy(atoms)                                     # 補助
    # B: θ 自己相関（複数 lag）
    for lag in LAGS:
        out[f"theta_autocorr_lag{lag}"] = autocorr(theta, lag)
    out["theta_std"] = float(np.std(theta))
    # C: 同時変動（step10 主軸 = θ_jump × atom_changed）
    atom_changed = np.array([atoms[i] != atoms[i - 1] for i in range(1, n)])
    theta_jump = np.abs(np.diff(theta))
    if atom_changed.sum() > 0 and (~atom_changed).sum() > 0:
        out["theta_jump_at_atomchange_med"] = float(np.median(theta_jump[atom_changed]))
        out["theta_jump_baseline_med"] = float(np.median(theta_jump[~atom_changed]))
    else:
        out["theta_jump_at_atomchange_med"] = np.nan
        out["theta_jump_baseline_med"] = np.nan
    # high/low theta 期で atom 変化率
    med_th = np.median(theta)
    hi = theta[1:] >= med_th
    if hi.sum() > 0 and (~hi).sum() > 0:
        out["atom_change_rate_high_theta"] = float(atom_changed[hi].mean())
        out["atom_change_rate_low_theta"] = float(atom_changed[~hi].mean())
    else:
        out["atom_change_rate_high_theta"] = np.nan
        out["atom_change_rate_low_theta"] = np.nan
    # C/Q delta at atom change（window 粒度・補助注記）
    C_delta = np.abs(np.diff(C))
    Q_delta = np.abs(np.diff(Q))
    if atom_changed.sum() > 0:
        out["C_absdelta_at_atomchange_med"] = float(np.median(C_delta[atom_changed]))
        out["Q_absdelta_at_atomchange_med"] = float(np.median(Q_delta[atom_changed]))
    else:
        out["C_absdelta_at_atomchange_med"] = np.nan
        out["Q_absdelta_at_atomchange_med"] = np.nan
    return out


# 時間構造の証拠にする主指標（within-cid time shuffle で pctl を出す対象）
TIME_STRUCT_KEYS = (
    ["mean_run_length", "max_run_length", "switch_per_1000", "return_interval_same_atom_med"]
    + [f"theta_autocorr_lag{l}" for l in LAGS]
    + ["theta_jump_at_atomchange_med"]
)


def main():
    df = pd.read_parquet(LEDGER)
    h = df[df["phys_core_status"].eq("hosted_available")].copy().sort_values(["cid", "t"])
    rng = np.random.RandomState(SEED)

    rows = []
    for cid, g in h.groupby("cid"):
        g = g.sort_values("t")
        atoms = g["rank_1_atom"].values
        theta = g["core_node_theta_resultant_length"].values.astype(float)
        C = g["C_at_window_end"].values.astype(float)
        Q = g["Q_remaining_at_window_end"].values.astype(float)
        n = len(atoms)
        if n < MIN_POINTS:
            continue
        nc = int(g["n_core"].iloc[0]) if not pd.isna(g["n_core"].iloc[0]) else -1
        obs = metrics_for_series(atoms, theta, C, Q)

        # within-cid time shuffle（主対照）: 行の時間順を joint 破壊し主指標 null を作る
        null = {k: [] for k in TIME_STRUCT_KEYS}
        idx = np.arange(n)
        for _ in range(N_SHUFFLE):
            p = rng.permutation(idx)
            m = metrics_for_series(atoms[p], theta[p], C[p], Q[p])
            for k in TIME_STRUCT_KEYS:
                null[k].append(m[k])
        rec = {"cid": int(cid), "n_core": nc, "n_points": n}
        rec.update(obs)
        for k in TIME_STRUCT_KEYS:
            rec[f"{k}__timeshuf_pctl"] = pctl(obs[k], null[k])
            valid = [v for v in null[k] if not np.isnan(v)]
            rec[f"{k}__timeshuf_mean"] = float(np.mean(valid)) if valid else np.nan
        rows.append(rec)

    res = pd.DataFrame(rows)

    # within-n_core cid-label shuffle（補助対照）= n_core peer 内での観測値 percentile
    #   （cid 間 edge を作らず、その cid が同 n_core 仲間の中で際立つかの対照のみ）
    for k in TIME_STRUCT_KEYS:
        res[f"{k}__ncorepeer_pctl"] = res.groupby("n_core")[k].rank(pct=True)

    res.to_parquet(OUT / "v1303b_obs_ABC_seed0.parquet", index=False)

    # 観察D: ghost 遷移 cid で pre-ghost vs mid-life の反復・安定（後処理・遷移）
    drows = []
    for cid, g in df[df["cid"].isin(
            df.groupby("cid")["cid_status"].apply(
                lambda s: ("hosted" in set(s)) and ("ghost" in set(s))).pipe(
                lambda x: x[x].index))].groupby("cid"):
        gh = g[g["cid_status"].eq("hosted")].sort_values("t")
        if len(gh) < MIN_POINTS:
            continue
        host_lost = gh["t"].max()  # 最後の hosted t（ghost 化直前）
        atoms = gh["rank_1_atom"].values
        theta = gh["core_node_theta_resultant_length"].values.astype(float)
        Cv = gh["C_at_window_end"].values.astype(float)
        Qv = gh["Q_remaining_at_window_end"].values.astype(float)
        n = len(gh)
        pre_n = max(5, n // 5)  # 末尾 20%（最低5点）= pre-ghost 窓
        def block(sl):
            a = atoms[sl]; th = theta[sl]
            rl = run_lengths(a)
            return (float(np.mean(rl)),
                    float(np.median(np.abs(np.diff(th)))) if len(th) > 1 else np.nan,
                    float(np.mean(th)),
                    float(np.mean(Cv[sl])), float(np.mean(Qv[sl])))
        pre = block(slice(n - pre_n, n))
        mid = block(slice(0, n - pre_n))
        drows.append({
            "cid": int(cid), "n_core": int(gh["n_core"].iloc[0]) if not pd.isna(gh["n_core"].iloc[0]) else -1,
            "host_lost_t": int(host_lost), "pre_ghost_points": pre_n, "mid_points": n - pre_n,
            "run_len_mid": mid[0], "run_len_pre_ghost": pre[0],
            "theta_jump_mid": mid[1], "theta_jump_pre_ghost": pre[1],
            "theta_mean_mid": mid[2], "theta_mean_pre_ghost": pre[2],
            "C_mean_mid": mid[3], "C_mean_pre_ghost": pre[3],
            "Q_mean_mid": mid[4], "Q_mean_pre_ghost": pre[4],
        })
    dres = pd.DataFrame(drows)
    dres.to_parquet(OUT / "v1303b_obs_D_ghost_seed0.parquet", index=False)

    # 観察E（補助・別枠）: R_positive が立つ稀瞬間の前後で②③①の素を記録（link を主軸にしない）
    erows = []
    for cid, g in h.groupby("cid"):
        g = g.sort_values("t").reset_index(drop=True)
        rp = g["core_internal_R_positive_count"].fillna(0).values > 0
        idxs = np.where(rp)[0]
        if len(idxs) == 0:
            continue
        erows.append({
            "cid": int(cid), "n_core": int(g["n_core"].iloc[0]) if not pd.isna(g["n_core"].iloc[0]) else -1,
            "n_rpos_events": int(len(idxs)),
            "frac_rpos": float(rp.mean()),
            "atom_change_rate_at_rpos": float(np.mean([
                g["rank_1_atom"].iloc[i] != g["rank_1_atom"].iloc[i - 1]
                for i in idxs if i > 0])) if any(i > 0 for i in idxs) else np.nan,
            "theta_mean_at_rpos": float(g["core_node_theta_resultant_length"].iloc[idxs].mean()),
            "theta_mean_overall": float(g["core_node_theta_resultant_length"].mean()),
        })
    eres = pd.DataFrame(erows)
    eres.to_parquet(OUT / "v1303b_obs_E_rpos_seed0.parquet", index=False)

    # ── 観察事実プリント（判定なし） ─────────────────────────────────────────
    print("=== v1303b 観察 (cid個別・n_core別・合成なし・判定なし) ===")
    print(f"対象 cid={len(res)} (min_points={MIN_POINTS}) | shuffle={N_SHUFFLE} seed={SEED}")
    print("\n--- 観察A: rank_1 再出現 (主指標は時間構造・dominant/entropyは補助) ---")
    for nc in sorted(res["n_core"].unique()):
        s = res[res["n_core"] == nc]
        print(f" n_core={nc} (cid={len(s)}): "
              f"mean_run_length med={s['mean_run_length'].median():.2f} "
              f"timeshuf_pctl med={s['mean_run_length__timeshuf_pctl'].median():.3f} "
              f"(>0.95 の cid={int((s['mean_run_length__timeshuf_pctl']>0.95).sum())}) | "
              f"dominant_frac med={s['dominant_atom_fraction'].median():.3f}")
    print("\n--- 観察B: θ 自己相関 (短期 lag だけで反復と呼ばない) ---")
    for nc in sorted(res["n_core"].unique()):
        s = res[res["n_core"] == nc]
        line = f" n_core={nc}:"
        for lag in LAGS:
            line += f" lag{lag} med={s[f'theta_autocorr_lag{lag}'].median():.3f}(pctl>0.95:{int((s[f'theta_autocorr_lag{lag}__timeshuf_pctl']>0.95).sum())})"
        print(line)
    print("\n--- 観察C: 同時変動 θ_jump@atomchange vs baseline ---")
    for nc in sorted(res["n_core"].unique()):
        s = res[res["n_core"] == nc]
        print(f" n_core={nc}: jump@change med={s['theta_jump_at_atomchange_med'].median():.4f} "
              f"baseline med={s['theta_jump_baseline_med'].median():.4f} "
              f"timeshuf_pctl med={s['theta_jump_at_atomchange_med__timeshuf_pctl'].median():.3f} "
              f"| atom_chg high_θ={s['atom_change_rate_high_theta'].median():.3f} low_θ={s['atom_change_rate_low_theta'].median():.3f}")
    print("\n--- 観察D: ghost 化前 vs mid-life (usable cid={}) ---".format(len(dres)))
    if len(dres):
        print(f" run_len: mid med={dres['run_len_mid'].median():.2f} -> pre_ghost med={dres['run_len_pre_ghost'].median():.2f}")
        print(f" theta_mean: mid med={dres['theta_mean_mid'].median():.3f} -> pre_ghost med={dres['theta_mean_pre_ghost'].median():.3f}")
        print(f" C_mean: mid med={dres['C_mean_mid'].median():.2f} -> pre_ghost med={dres['C_mean_pre_ghost'].median():.2f}")
        print(f" Q_mean: mid med={dres['Q_mean_mid'].median():.2f} -> pre_ghost med={dres['Q_mean_pre_ghost'].median():.2f}")
    print(f"\n--- 観察E (補助・別枠): R_positive を持つ cid={len(eres)} ---")
    if len(eres):
        print(f" n_rpos_events med={eres['n_rpos_events'].median():.0f} "
              f"atom_change_rate@rpos med={eres['atom_change_rate_at_rpos'].median():.3f} "
              f"θ@rpos med={eres['theta_mean_at_rpos'].median():.3f} vs overall med={eres['theta_mean_overall'].median():.3f}")
    print(f"\n出力: {OUT}/v1303b_obs_ABC_seed0.parquet (+D,+E)")


if __name__ == "__main__":
    main()
