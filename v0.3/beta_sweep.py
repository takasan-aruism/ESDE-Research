"""
ESDE Genesis v0.3 — Beta Sweep
"""
import numpy as np
import matplotlib.pyplot as plt
import time

from genesis_state import GenesisState
from genesis_physics import GenesisPhysics, PhysicsParams
from genesis_logger import GenesisLogger

N_NODES = 200; C_MAX = 1.0; INJECTION_STEPS = 300; QUIET_STEPS = 400
INJECT_INTERVAL = 3; SEED = 42
BETAS = [0.0, 0.1, 0.5, 1.0, 2.0]

def run_one(beta, verbose=True):
    state = GenesisState(n_nodes=N_NODES, c_max=C_MAX, seed=SEED)
    params = PhysicsParams(exclusion_enabled=True, resonance_enabled=(beta > 0), beta=beta)
    physics = GenesisPhysics(params)
    logger = GenesisLogger()
    t0 = time.time()

    for step in range(INJECTION_STEPS):
        if step % INJECT_INTERVAL == 0:
            physics.inject(state)
        cd = physics.step(state)
        if cd is not None:
            logger.observe_loops(cd)
        logger.observe(state)

    quiet_start = state.step
    for step in range(QUIET_STEPS):
        cd = physics.step(state)
        if cd is not None:
            logger.observe_loops(cd)
        logger.observe(state)

    kpis = logger.compute_kpis(quiet_start)
    elapsed = time.time() - t0
    if verbose:
        print(f"  beta={beta:<4}  L_HL={kpis['link_half_life']:>4}  "
              f"RM_HL={kpis['resonant_mass_half_life']:>4}  "
              f"E_HL={kpis['energy_half_life']:>4}  "
              f"Crystals={kpis['crystal_count']}  ({elapsed:.1f}s)")
    return logger, kpis

def main():
    print("=" * 60)
    print("  Genesis v0.3 — Beta Sweep")
    print("=" * 60)

    loggers = {}; kpis_all = {}
    for beta in BETAS:
        lgr, kpis = run_one(beta)
        loggers[f"beta={beta}"] = lgr
        kpis_all[f"beta={beta}"] = kpis

    colors = plt.cm.viridis(np.linspace(0.2, 0.9, len(BETAS)))
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle("Genesis v0.3 — Beta Sweep", fontsize=14, fontweight="bold")

    metrics = [("active_links", "Active Links"), ("resonant_mass", "Resonant Mass"),
               ("resonant_links", "Resonant Links"), ("total_energy", "Total Energy"),
               ("entropy", "Entropy")]

    for idx, (mk, mt) in enumerate(metrics):
        row, col = divmod(idx, 3)
        ax = axes[row][col]
        for i, beta in enumerate(BETAS):
            ts = loggers[f"beta={beta}"].get_timeseries()
            ax.plot(ts["step"], ts[mk], label=f"β={beta}", color=colors[i], linewidth=1.5)
        ax.axvline(x=INJECTION_STEPS, color="gray", linestyle="--", alpha=0.4)
        ax.set_title(mt, fontsize=10); ax.grid(True, alpha=0.15)
        if idx == 0: ax.legend(fontsize=7)

    ax_bar = axes[1][2]
    x = np.arange(len(BETAS))
    lhls = [kpis_all[f"beta={b}"]["link_half_life"] for b in BETAS]
    rmhls = [kpis_all[f"beta={b}"]["resonant_mass_half_life"] for b in BETAS]
    w = 0.35
    b1 = ax_bar.bar(x - w/2, lhls, w, label="Link HL", color="#2ecc71", alpha=0.85)
    b2 = ax_bar.bar(x + w/2, rmhls, w, label="RM HL", color="#9b59b6", alpha=0.85)
    ax_bar.set_xticks(x); ax_bar.set_xticklabels([f"{b}" for b in BETAS])
    ax_bar.set_xlabel("Beta"); ax_bar.set_title("Half-Lives vs Beta", fontsize=10)
    ax_bar.legend(fontsize=8); ax_bar.grid(True, axis="y", alpha=0.2)
    for bar, v in zip(b1, lhls):
        ax_bar.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1, str(v), ha="center", fontsize=8)
    for bar, v in zip(b2, rmhls):
        ax_bar.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1, str(v), ha="center", fontsize=8)

    plt.tight_layout()
    plt.savefig("genesis_v03_beta_sweep.png", dpi=150, bbox_inches="tight")
    print(f"\n  Plot: genesis_v03_beta_sweep.png")
    print(f"\n  +--------+--------+--------+--------+")
    print(f"  | Beta   | L_HL   | RM_HL  | E_HL   |")
    print(f"  +--------+--------+--------+--------+")
    for beta in BETAS:
        k = kpis_all[f"beta={beta}"]
        print(f"  | {beta:<6} | {k['link_half_life']:>5}  | {k['resonant_mass_half_life']:>5}  | {k['energy_half_life']:>5}  |")
    print(f"  +--------+--------+--------+--------+")

if __name__ == "__main__":
    main()
