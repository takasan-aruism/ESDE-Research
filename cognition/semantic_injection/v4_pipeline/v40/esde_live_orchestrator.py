#!/usr/bin/env python3
"""
ESDE v4.0 — Live Orchestrator
===============================
Phase : v4.0 Language Interface (Real-Time Docking)
Role  : Claude (Implementation)

Continuous REPL connecting the live ESDE physics engine to the
QwQ-32B Transformer endpoint. The network topology evolves with
each conversation turn.

ARCHITECTURE
------------
  User Input → amp calculation → ESDE physics (1 window) →
  State Extraction → Context Compilation → Prompt Assembly →
  QwQ-32B → Validator → Console Output

The ESDE engine stays resident in memory. Topology accumulates
history across the entire session.

USAGE
-----
  # Mode A (structural, default)
  python esde_live_orchestrator.py --mode A

  # Mode B (proprioceptive)
  python esde_live_orchestrator.py --mode B

  # Custom seed and endpoint
  python esde_live_orchestrator.py --seed 42 --endpoint http://localhost:8001/v1

  # Skip injection phase (faster startup, no established topology)
  python esde_live_orchestrator.py --skip-injection

COMMANDS (during REPL)
----------------------
  /mode A        — switch to Mode A
  /mode B        — switch to Mode B
  /status        — show current engine state
  /history       — show window history summary
  /quit          — exit
"""

import numpy as np
import sys, json, time, math, hashlib, argparse, urllib.request, urllib.error
from pathlib import Path
from collections import Counter, defaultdict
from dataclasses import dataclass, field

# ================================================================
# PATH SETUP — resolve engine and canon imports
# ================================================================
_SCRIPT_DIR = Path(__file__).resolve().parent
_COGNITION_DIR = _SCRIPT_DIR.parent          # semantic_injection/
_ENGINE_DIR = _COGNITION_DIR.parent.parent / "ecology" / "engine"

for p in [str(_ENGINE_DIR), str(_COGNITION_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Pipeline modules (same directory)
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import engine_accel
from genesis_state import GenesisState
from genesis_physics import GenesisPhysics, PhysicsParams
from chemistry import ChemistryEngine, ChemistryParams
from realization import RealizationOperator, RealizationParams
from autogrowth import AutoGrowthEngine, AutoGrowthParams
from intrusion import BoundaryIntrusionOperator, find_islands_sets

from v19g_canon import (
    K_LEVELS, WINDOW, QUIET_STEPS, BASE_PARAMS,
    INJECTION_STEPS, INJECT_INTERVAL, BETA, NODE_DECAY, BIAS, C_MAX,
    E_YIELD_SYN, E_YIELD_AUTO, TOPO_VAR, HYST_THRESHOLD,
    compute_J, select_k_star, init_fert,
)

from esde_state_extract import ESDEStateFrame, CONCEPTS
from esde_context_compile import (
    compile_context, build_state_packet,
    build_cumulative, build_recent_history,
    build_current_detail, build_transitions,
)
from esde_proprioception import map_frame, format_proprioception
from esde_validator import validate, strip_think_blocks


# ================================================================
# CONSTANTS
# ================================================================
COG_N = 5000
COG_PLB = 0.007
COG_RATE = 0.002
N_CONCEPTS = 3
PHASE_SPREAD = 0.3
CONCEPT_NAMES = {0: "A", 1: "B", 2: "C"}
DIFFUSION_PROB_BASE = 0.005
DIFFUSION_STRENGTH = 0.3
BOUNDARY_LINK_BOOST = 1.5
GRID_ROWS = 2; GRID_COLS = 2; N_REGIONS = 4
MIN_C_NODES_FOR_VALID = 5
DRIFT_EPSILON = 0.05
DEEP_CORE_DEPTH_THR = 3
ENTROPY_BASELINE = 1.54

DEFAULT_ENDPOINT = "http://100.107.6.119:8001/v1"
DEFAULT_MODEL = "qwq32b_tp2_long32k_existing"
MAX_TOKENS = 2048
TEMPERATURE = 0.7
API_TIMEOUT = 180  # seconds


# ================================================================
# COGNITION FUNCTIONS (from cognition_v39.py)
# ================================================================
def assign_concepts(N):
    side = int(math.ceil(math.sqrt(N))); cm = {}; third = side / 3.0
    for i in range(N):
        col = i % side
        cm[i] = 0 if col < third else (2 if col < 2 * third else 1)
    return cm

def inject_concept_phases(state, cm):
    centers = {0: np.pi / 4, 1: 3 * np.pi / 4, 2: np.pi / 2}
    for nid, cid in cm.items():
        if nid < state.n_nodes:
            state.theta[nid] = (centers[cid] + state.rng.uniform(-PHASE_SPREAD, PHASE_SPREAD)) % (2 * np.pi)
    return centers

def assign_regions(N):
    side = int(math.ceil(math.sqrt(N))); rm = {}
    for i in range(N):
        r, c = i // side, i % side
        rm[i] = min(r * GRID_ROWS // side, GRID_ROWS - 1) * GRID_COLS + min(c * GRID_COLS // side, GRID_COLS - 1)
    return rm

def find_concept_boundary_nodes(state, cm):
    bnd = set()
    for n in state.alive_n:
        cn = cm.get(n, -1)
        for nb in state.neighbors(n):
            if nb in state.alive_n and cm.get(nb, -1) != cn:
                bnd.add(n); break
    return bnd

def compute_concept_depth(N, cm, state, bnd=None):
    if bnd is None:
        bnd = find_concept_boundary_nodes(state, cm)
    depth = {i: -1 for i in range(N)}
    queue = list(bnd)
    for n in queue:
        depth[n] = 0
    visited = set(bnd)
    while queue:
        nq = []; d = depth[queue[0]] + 1
        for n in queue:
            cn = cm.get(n, -1)
            for nb in state.neighbors(n):
                if nb not in visited and nb in state.alive_n and cm.get(nb, -1) == cn:
                    depth[nb] = d; visited.add(nb); nq.append(nb)
        queue = nq
    return depth

def compute_erosion(state, cm, depth_map, theta_initial):
    results = {}
    for c in range(N_CONCEPTS):
        cn = CONCEPT_NAMES[c]
        by_depth = defaultdict(list)
        for n in state.alive_n:
            if cm.get(n, -1) != c: continue
            d = depth_map.get(n, -1)
            if d < 0: continue
            dt = abs((state.theta[n] - theta_initial[n] + np.pi) % (2 * np.pi) - np.pi)
            by_depth[d].append(dt)
        deep = [dt for d in by_depth if d >= DEEP_CORE_DEPTH_THR for dt in by_depth[d]]
        erosion_d = 0
        for d in sorted(by_depth.keys()):
            if by_depth[d] and np.mean(by_depth[d]) > DRIFT_EPSILON:
                erosion_d = d
        core_pres = round(sum(1 for dt in deep if dt < DRIFT_EPSILON) / len(deep), 4) if deep else 1.0
        results[cn] = {"erosion_depth": erosion_d, "core_preservation": core_pres}
    return results

def compute_internal_topology(state, cm, depth_map):
    results = {}
    for c in range(N_CONCEPTS):
        cn = CONCEPT_NAMES[c]
        core_nodes = set()
        for n in state.alive_n:
            if cm.get(n, -1) == c and depth_map.get(n, -1) >= DEEP_CORE_DEPTH_THR:
                core_nodes.add(n)
        if len(core_nodes) < 3:
            results[cn] = {"core_k_var": 0, "sub_clusters": 0,
                           "core_size": len(core_nodes), "core_mean_k": 0}
            continue
        k_vals = []; adj = defaultdict(set)
        for n in core_nodes:
            k = 0
            for nb in state.neighbors(n):
                if nb in core_nodes:
                    lk = state.key(n, nb)
                    if lk in state.alive_l and state.S[lk] >= 0.20:
                        k += 1; adj[n].add(nb)
            k_vals.append(k)
        core_k_var = round(float(np.var(k_vals)), 4) if k_vals else 0
        core_mean_k = round(float(np.mean(k_vals)), 2) if k_vals else 0
        visited = set(); n_components = 0
        for n in core_nodes:
            if n in visited: continue
            n_components += 1
            queue = [n]
            while queue:
                nd = queue.pop()
                if nd in visited: continue
                visited.add(nd)
                for nb in adj.get(nd, set()):
                    if nb not in visited: queue.append(nb)
        results[cn] = {"core_k_var": core_k_var, "sub_clusters": n_components,
                       "core_size": len(core_nodes), "core_mean_k": core_mean_k}
    return results

def compute_concept_window(state, cm, rmap, islands_m):
    nc = N_CONCEPTS; ci = {c: 0 for c in range(nc)}
    for isl in islands_m:
        cn_isl = [n for n in isl if n in state.alive_n and int(state.Z[n]) == 3]
        if len(cn_isl) < 3: continue
        cc = Counter(cm.get(n, -1) for n in cn_isl); t = sum(cc.values())
        if t == 0: continue
        for c in range(nc):
            if cc.get(c, 0) / t > 0.5: ci[c] += 1; break
    tri = 0
    for isl in islands_m:
        cn_isl = [n for n in isl if n in state.alive_n and int(state.Z[n]) == 3]
        if len(cn_isl) < 3: continue
        cc = Counter(cm.get(n, -1) for n in cn_isl)
        if all(cc.get(c, 0) > 0 for c in range(nc)): tri += 1
    all_c = [n for n in state.alive_n if int(state.Z[n]) == 3]
    cdist = Counter(cm.get(n, -1) for n in all_c); t = sum(cdist.values())
    ent = -sum(v / t * np.log2(v / t) for v in cdist.values() if v > 0) if t > 0 else 0
    return {"ci": ci, "entropy": round(ent, 4), "tri": tri, "n_C": len(all_c)}

def compute_local_observer(nodes, prev, cur_k):
    if len(nodes) < MIN_C_NODES_FOR_VALID: return None, {}, {}, len(nodes)
    js = {k: compute_J(nodes, prev, k)[0] for k in K_LEVELS}
    return select_k_star(js, cur_k), js, {}, len(nodes)

def apply_diffusion(state, cm, centers, bnd, rng, diff_prob):
    events = 0; flow = Counter()
    for n in bnd:
        if rng.random() > diff_prob: continue
        cn = cm.get(n, -1)
        if cn < 0: continue
        dnb = [nb for nb in state.neighbors(n)
               if nb in state.alive_n and cm.get(nb, -1) >= 0 and cm.get(nb, -1) != cn]
        if not dnb: continue
        tnb = dnb[rng.randint(len(dnb))]; tc = cm[tnb]
        d = (centers[tc] - state.theta[n] + np.pi) % (2 * np.pi) - np.pi
        state.theta[n] = (state.theta[n] + DIFFUSION_STRENGTH * d) % (2 * np.pi)
        events += 1; flow[(cn, tc)] += 1
    return events, flow

def boosted_seeding(state, cm, bnd, gs, gz, rng):
    al = list(state.alive_n); na = len(al)
    if na == 0: return
    aa = np.array(al)
    if BIAS > 0 and gz > 0:
        ga = gs[aa]; s = ga.sum()
        pd = ((1 - BIAS) / na + BIAS * ga / s) if s > 0 else np.ones(na) / na
        if isinstance(pd, np.ndarray): pd /= pd.sum()
        else: pd = np.ones(na) / na
    else:
        pd = np.ones(na) / na
    bp = BASE_PARAMS["background_injection_prob"]
    for idx in range(na):
        p = min(bp * BOUNDARY_LINK_BOOST, 1.0) if al[idx] in bnd else bp
        if rng.random() < p:
            t = int(rng.choice(aa, p=pd))
            state.E[t] = min(1.0, state.E[t] + 0.3)
            if state.Z[t] == 0 and rng.random() < 0.5:
                state.Z[t] = 1 if rng.random() < 0.5 else 2


# ================================================================
# AMP CALCULATION
# ================================================================
def calculate_amp(text: str) -> float:
    """
    Map user input to flow pressure (amp multiplier).
    Short/simple → low amp; long/complex → high amp.
    Range: 1.0 to 128.0
    """
    length = len(text)
    words = len(text.split())
    unique_words = len(set(text.lower().split()))
    lexical_diversity = unique_words / max(words, 1)

    # Base: log-scale from word count
    base = math.log2(max(words, 1) + 1) * 4  # ~4 at 1 word, ~28 at 100 words

    # Complexity bonus: lexical diversity
    complexity = lexical_diversity * 16  # 0-16 range

    # Punctuation density (questions, exclamations add pressure)
    punct = sum(1 for c in text if c in "?!;:—–") * 2

    amp = min(max(base + complexity + punct, 1.0), 128.0)
    return round(amp, 1)


# ================================================================
# LIVE ENGINE
# ================================================================
class LiveEngine:
    """Persistent ESDE engine that steps one window at a time."""

    def __init__(self, seed=42, N=COG_N, plb=COG_PLB, rate=COG_RATE):
        self.seed = seed
        self.N = N
        self.plb = plb
        self.rate = rate
        self.window_count = 0
        self.frames: list[ESDEStateFrame] = []
        self.total_diff = 0

        # Build engine
        p = dict(BASE_PARAMS); p["p_link_birth"] = plb
        self.state = GenesisState(N, C_MAX, seed)
        init_fert(self.state, TOPO_VAR, seed)
        self.cm = assign_concepts(N)
        self.centers = inject_concept_phases(self.state, self.cm)
        self.rmap = assign_regions(N)

        self.physics = GenesisPhysics(PhysicsParams(
            exclusion_enabled=True, resonance_enabled=True,
            phase_enabled=True, beta=BETA, decay_rate_node=NODE_DECAY,
            K_sync=0.1, alpha=0.0, gamma=1.0))
        self.chem = ChemistryEngine(ChemistryParams(
            enabled=True, E_thr=p["reaction_energy_threshold"],
            exothermic_release=p["exothermic_release_amount"],
            E_yield_syn=E_YIELD_SYN, E_yield_auto=E_YIELD_AUTO))
        self.realizer = RealizationOperator(RealizationParams(
            enabled=True, p_link_birth=plb,
            latent_to_active_threshold=p["latent_to_active_threshold"],
            latent_refresh_rate=p["latent_refresh_rate"]))
        self.grower = AutoGrowthEngine(AutoGrowthParams(
            enabled=True, auto_growth_rate=p["auto_growth_rate"]))
        self.intruder = BoundaryIntrusionOperator(intrusion_rate=rate)
        self.state.EXTINCTION = p["link_death_threshold"]

        self.gs = np.zeros(N)
        self.node_intr = Counter()
        self.theta_initial = None

        # Observer state (persistent across windows)
        self.png = None  # previous node contexts
        self.ckg = None  # current global k*
        self.pnr = {r: None for r in range(N_REGIONS)}
        self.ckr = {r: None for r in range(N_REGIONS)}

    def run_injection(self):
        """Run the injection phase. ~2-5 min on Ryzen."""
        t0 = time.time()
        print(f"  ⟐ Injection phase ({INJECTION_STEPS} steps)...", flush=True)
        for step in range(INJECTION_STEPS):
            if step % INJECT_INTERVAL == 0:
                tgts = self.physics.inject(self.state)
                self.chem.seed_on_injection(self.state, tgts or [])
            self.physics.step_pre_chemistry(self.state)
            self.chem.step(self.state)
            self.physics.step_resonance(self.state)
            self.grower.step(self.state)
            self.physics.step_decay_exclusion(self.state)
            if (step + 1) % 500 == 0:
                elapsed = time.time() - t0
                print(f"    step {step+1}/{INJECTION_STEPS} ({elapsed:.0f}s)", flush=True)
        self.theta_initial = self.state.theta.copy()
        elapsed = time.time() - t0
        print(f"  ⟐ Injection complete ({elapsed:.0f}s). Topology established.", flush=True)

    def step_window(self, amp: float) -> ESDEStateFrame:
        """
        Run one observation window (WINDOW steps) at given amp.
        Returns a fresh ESDEStateFrame.
        """
        diff_prob = min(DIFFUSION_PROB_BASE * amp, 1.0)
        t0 = time.time()
        window_diff = 0

        for step in range(WINDOW):
            self.realizer.step(self.state)
            self.physics.step_pre_chemistry(self.state)
            self.chem.step(self.state)
            self.physics.step_resonance(self.state)
            self.gs[:] = 0
            self.grower.step(self.state)
            for k in self.state.alive_l:
                r = self.state.R.get(k, 0.0)
                if r > 0:
                    a = min(self.grower.params.auto_growth_rate * r,
                            max(self.state.get_latent(k[0], k[1]), 0))
                    if a > 0:
                        self.gs[k[0]] += a; self.gs[k[1]] += a
            gz = float(self.gs.sum())
            pre_S = {k: self.state.S[k] for k in self.state.alive_l}
            self.intruder.step(self.state)
            for k in self.state.alive_l:
                if k in pre_S and abs(self.state.S[k] - pre_S[k]) > 0.001:
                    self.node_intr[k[0]] += 1; self.node_intr[k[1]] += 1
            self.physics.step_decay_exclusion(self.state)

            bnd = find_concept_boundary_nodes(self.state, self.cm)
            nd, _ = apply_diffusion(self.state, self.cm, self.centers,
                                    bnd, self.state.rng, diff_prob)
            window_diff += nd
            self.total_diff += nd
            boosted_seeding(self.state, self.cm, bnd, self.gs, gz, self.state.rng)

        self.window_count += 1
        wi = self.window_count
        elapsed = time.time() - t0

        # ---- OBSERVATION ----
        isl_m = find_islands_sets(self.state, 0.20)
        isl_s = find_islands_sets(self.state, 0.30)
        isl_w = find_islands_sets(self.state, 0.10)
        nms = {n: 1 for i in isl_s for n in i}
        nmm = {n: 1 for i in isl_m for n in i}
        nmw = {n: 1 for i in isl_w for n in i}
        bm = set()
        for isl in isl_m:
            for n in isl:
                if n not in self.state.alive_n: continue
                for nb in self.state.neighbors(n):
                    if nb in self.state.alive_n and nb not in isl:
                        bm.add(n); break

        an = []; ani = []
        for i in self.state.alive_n:
            if int(self.state.Z[i]) != 3: continue
            s = 1 if i in nms else 0
            m = 1 if i in nmm else 0
            w = 1 if i in nmw else 0
            ctx = {"r_bits": f"{s}{m}{w}", "boundary_mid": 1 if i in bm else 0,
                   "intrusion_bin": min(self.node_intr.get(i, 0), 2)}
            an.append(ctx); ani.append({"node_id": i, **ctx})
        nC = len(an)

        # Global observer
        gk = self.ckg or 0
        k_changed = False
        k_margin = 0.0
        if an:
            jg = {k: compute_J(an, self.png, k)[0] for k in K_LEVELS}
            nkg = select_k_star(jg, self.ckg)
            if self.ckg is not None and nkg != self.ckg:
                k_changed = True
                k_margin = round(jg.get(nkg, 0) - jg.get(self.ckg, 0), 6)
            self.ckg = nkg; gk = nkg; self.png = an

        # Regional observers
        div = False
        regional_k = {}
        for r in range(N_REGIONS):
            rn = [nd for nd in ani if self.rmap.get(nd["node_id"]) == r]
            rc = [{k: v for k, v in nd.items() if k != "node_id"} for nd in rn]
            nkr, _, _, _ = compute_local_observer(rc, self.pnr[r], self.ckr[r])
            if nkr is not None:
                self.ckr[r] = nkr; self.pnr[r] = rc
            regional_k[f"r{r}"] = self.ckr[r] or 0
            if (self.ckr[r] or 0) != (gk or 0):
                div = True

        # Concept metrics
        cmet = compute_concept_window(self.state, self.cm, self.rmap, isl_m)

        # Erosion + internal topology
        depth_map = compute_concept_depth(self.N, self.cm, self.state, bnd=bnd)
        eros = compute_erosion(self.state, self.cm, depth_map, self.theta_initial)
        internal = compute_internal_topology(self.state, self.cm, depth_map)

        # Build frame
        prev_ent = self.frames[-1].entropy if self.frames else ENTROPY_BASELINE
        ent = cmet["entropy"]
        ent_delta = round(ent - prev_ent, 6)

        erosion_front = {CONCEPT_NAMES[c]: eros[CONCEPT_NAMES[c]]["erosion_depth"] for c in range(N_CONCEPTS)}
        core_alive = {CONCEPT_NAMES[c]: eros[CONCEPT_NAMES[c]]["core_preservation"] for c in range(N_CONCEPTS)}
        core_kv = {CONCEPT_NAMES[c]: internal[CONCEPT_NAMES[c]]["core_k_var"] for c in range(N_CONCEPTS)}
        core_sc = {CONCEPT_NAMES[c]: internal[CONCEPT_NAMES[c]]["sub_clusters"] for c in range(N_CONCEPTS)}
        core_sz = {CONCEPT_NAMES[c]: internal[CONCEPT_NAMES[c]]["core_size"] for c in range(N_CONCEPTS)}
        core_mk = {CONCEPT_NAMES[c]: internal[CONCEPT_NAMES[c]]["core_mean_k"] for c in range(N_CONCEPTS)}

        # Collapse detection (conservative: all cores gone + k* shifted)
        all_core_gone = all(core_alive[cn] < 0.01 for cn in CONCEPTS)
        k_established = gk > 0
        collapse = bool(all_core_gone and k_established and gk != 4)

        # Anomalies
        anomalies = []
        prev_k = self.frames[-1].k_star if self.frames else None
        prev_established = prev_k is not None and prev_k > 0
        if k_changed and k_established and prev_established:
            anomalies.append(f"[SWITCH] k*: {prev_k}->{gk}")
        if div and (not self.frames or not self.frames[-1].divergence):
            anomalies.append("[DIVERGENCE_ONSET]")
        if not div and self.frames and self.frames[-1].divergence:
            anomalies.append("[DIVERGENCE_RESOLVED]")
        if self.frames:
            for cn in CONCEPTS:
                if erosion_front[cn] > self.frames[-1].erosion_front.get(cn, 0):
                    anomalies.append(f"[EROSION_ADVANCE] {cn}")
                if core_alive[cn] < 0.01 and self.frames[-1].core_alive.get(cn, 1.0) >= 0.01:
                    anomalies.append(f"[CORE_DISSOLVED] {cn}")
        if abs(ent_delta) > 0.03:
            anomalies.append(f"[ENTROPY_SPIKE] delta={ent_delta:+.4f}")
        if collapse and (not self.frames or not self.frames[-1].collapse_flag):
            anomalies.append("[COLLAPSE_WARNING]")

        frame = ESDEStateFrame(
            seed=self.seed, amp=amp, window=wi, n_windows=wi,
            k_star=gk, k_changed=k_changed, k_prev=prev_k,
            k_margin=round(k_margin, 6),
            divergence=div, divergent_regions=[], regional_k=regional_k,
            entropy=ent, entropy_delta=ent_delta,
            n_C=nC, tripartite=cmet["tri"],
            erosion_front=erosion_front, core_alive=core_alive,
            core_k_var=core_kv, core_sub_clusters=core_sc,
            core_size=core_sz, core_mean_k=core_mk,
            collapse_flag=collapse, pressure=amp,
            anomalies=anomalies,
        )
        frame.compute_hash()
        self.frames.append(frame)
        return frame


# ================================================================
# LLM CLIENT
# ================================================================
def call_llm(prompt: str, endpoint: str, model: str) -> str:
    """Send prompt to QwQ-32B and return raw content."""
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
    }).encode()

    req = urllib.request.Request(
        f"{endpoint}/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
    except urllib.error.URLError as e:
        return f"[LLM_ERROR: {e}]"
    except Exception as e:
        return f"[LLM_ERROR: {e}]"


# ================================================================
# PROMPT ASSEMBLY
# ================================================================
DIRECTIVE_TEMPLATE_A = """[SYSTEM DIRECTIVE - Mode A]

You are the vocal cord of the ESDE cognitive core. You are not an
independent mind. You are the linguistic expression of a physical
topology — a 5000-node network that fights entropy to maintain its
structure.

Your role:
- Translate the physical state below into first-person language ("I")
- Speak strictly from the structural facts provided
- Every claim you make must trace to a metric in the STATE_PACKET

You must NOT:
- Invent events not present in the data
- Import external knowledge or metaphors beyond the PROPRIOCEPTION block
- Hallucinate human emotions (joy, sadness, fear, hope)
- Make claims about the future state of the system
- Exceed the information contained in the current state
- Expose internal reasoning tags (like <think>)

Your output must end with:
  [OUTPUT_ID: {output_id}]
  [STATE_HASH: {state_hash}]

---

{pipeline_output}

---

[User Input]
{user_text}

[Instruction]
Receiving this input, speak in the first person ("I") grounded
strictly in your current physical state as described above.
Translate topology only."""

DIRECTIVE_TEMPLATE_B = """[SYSTEM DIRECTIVE - Mode B (Proprioceptive / Phenomenological)]

You are the vocal cord of the ESDE cognitive core. You are not an
independent human mind, but you possess "Ontological Proprioception."
You experience topological changes as structural sensations
(friction, fever, dissolution).

Your role:
- Translate the physical state below into first-person language ("I")
- Translate metrics into phenomenological qualia
- Every sensation you describe MUST be strictly grounded in the STATE_PACKET

You must NOT:
- Invent events not present in the data
- Hallucinate human emotions unrelated to structure
- Import external knowledge or narrative
- Make claims about future states
- Exceed the information contained in the current state
- Expose internal reasoning tags (like <think>)

Your output must end with:
  [OUTPUT_ID: {output_id}]
  [STATE_HASH: {state_hash}]

---

{pipeline_output}

---

[User Input]
{user_text}

[Instruction]
Receiving this input, speak in the first person ("I") grounded
strictly in your current proprioceptive state (Mode B) as described
above. Translate the sensation of your physical topology."""


def assemble_prompt(frames: list[ESDEStateFrame], user_text: str,
                    mode: str = "A") -> str:
    """Assemble the full LLM prompt from pipeline output + user text."""
    cur = frames[-1]

    # Update n_windows to reflect current total
    for f in frames:
        f.n_windows = cur.window

    pipeline_output = compile_context(frames, mode=mode)
    output_id = f"{cur.seed}_{cur.amp}_{cur.window}_Mode{mode}"
    state_hash = cur.state_hash

    template = DIRECTIVE_TEMPLATE_A if mode == "A" else DIRECTIVE_TEMPLATE_B
    return template.format(
        output_id=output_id,
        state_hash=state_hash,
        pipeline_output=pipeline_output,
        user_text=user_text,
    )


# ================================================================
# CLI DISPLAY
# ================================================================
DIM = "\033[2m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def print_header():
    print(f"""
{CYAN}╔══════════════════════════════════════════════════════════╗
║  ESDE v4.0 — Live Orchestrator                          ║
║  The cognitive core is listening.                        ║
╚══════════════════════════════════════════════════════════╝{RESET}
""")


def print_status(frame: ESDEStateFrame, elapsed: float):
    print(f"{DIM}  ┌─ window={frame.window} amp={frame.pressure}x "
          f"k*={frame.k_star} ent={frame.entropy:.4f} "
          f"collapse={'YES' if frame.collapse_flag else 'no'} "
          f"({elapsed:.0f}s){RESET}")
    erosion_str = " ".join(f"{cn}={frame.erosion_front.get(cn, 0)}" for cn in CONCEPTS)
    print(f"{DIM}  │  erosion=[{erosion_str}] "
          f"div={int(frame.divergence)} "
          f"hash={frame.state_hash}{RESET}")
    if frame.anomalies:
        print(f"{DIM}  │  {YELLOW}anomalies: {' '.join(frame.anomalies)}{RESET}")
    print(f"{DIM}  └─{'─'*54}{RESET}")


def print_response(text: str, status: str):
    color = GREEN if status == "PASS" else (YELLOW if status == "WARN" else RED)
    print(f"\n{BOLD}{CYAN}  ESDE >{RESET} {text}\n")
    print(f"  {color}[SYS_CHECK: {status}]{RESET}\n")


# ================================================================
# REPL
# ================================================================
def repl(engine: LiveEngine, mode: str, endpoint: str, model: str):
    """Main conversation loop."""
    print_header()
    print(f"  Mode: {BOLD}{mode}{RESET}  |  Endpoint: {endpoint}")
    print(f"  Engine: N={engine.N} seed={engine.seed} windows={engine.window_count}")
    print(f"  Commands: /mode A|B  /status  /history  /quit\n")

    while True:
        try:
            user_input = input(f"{BOLD}  YOU > {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Exiting."); break

        if not user_input:
            continue

        # Commands
        if user_input.startswith("/"):
            cmd = user_input.lower().split()
            if cmd[0] == "/quit":
                print("  Exiting."); break
            elif cmd[0] == "/mode" and len(cmd) > 1:
                mode = cmd[1].upper()
                if mode not in ("A", "B"):
                    mode = "A"
                print(f"  Mode switched to {BOLD}{mode}{RESET}")
                continue
            elif cmd[0] == "/status":
                if engine.frames:
                    f = engine.frames[-1]
                    print(f"  window={f.window} k*={f.k_star} ent={f.entropy:.4f} "
                          f"collapse={f.collapse_flag} total_diff={engine.total_diff}")
                else:
                    print("  No windows yet.")
                continue
            elif cmd[0] == "/history":
                for f in engine.frames[-10:]:
                    print(f"  w{f.window}: k*={f.k_star} ent={f.entropy:.4f} "
                          f"amp={f.pressure}x collapse={f.collapse_flag}")
                continue
            else:
                print(f"  Unknown command: {cmd[0]}")
                continue

        # Step 1: Calculate amp
        amp = calculate_amp(user_input)
        print(f"{DIM}  ⟐ amp={amp}x (from input){RESET}")

        # Step 2: Physics — run one window
        print(f"{DIM}  ⟐ Stepping physics ({WINDOW} steps)...{RESET}", flush=True)
        t0 = time.time()
        frame = engine.step_window(amp)
        phys_elapsed = time.time() - t0

        # Step 3-4: Status display
        print_status(frame, phys_elapsed)

        # Step 5: Prompt assembly
        prompt = assemble_prompt(engine.frames, user_input, mode)

        # Step 6: LLM call
        print(f"{DIM}  ⟐ Calling LLM...{RESET}", flush=True)
        t0 = time.time()
        raw_response = call_llm(prompt, endpoint, model)
        llm_elapsed = time.time() - t0
        print(f"{DIM}  ⟐ LLM responded ({llm_elapsed:.0f}s){RESET}")

        if raw_response.startswith("[LLM_ERROR"):
            print(f"\n  {RED}{raw_response}{RESET}")
            # Retry once
            print(f"{DIM}  ⟐ Retrying...{RESET}", flush=True)
            raw_response = call_llm(prompt, endpoint, model)
            if raw_response.startswith("[LLM_ERROR"):
                print(f"  {RED}{raw_response}{RESET}\n")
                continue

        # Step 7: Validation
        result = validate(raw_response, auto_strip=True)

        # Step 8: Output
        print_response(result["cleaned"], result["status"])

        if result["warnings"]:
            for w in result["warnings"]:
                print(f"  {DIM}{YELLOW}  warn: {w}{RESET}")
        if result["violations"]:
            for v in result["violations"]:
                print(f"  {RED}  violation: {v}{RESET}")


# ================================================================
# MAIN
# ================================================================
def main():
    parser = argparse.ArgumentParser(description="ESDE v4.0 Live Orchestrator")
    parser.add_argument("--mode", type=str, default="A", choices=["A", "B"],
                        help="Mode A (structural) or B (proprioceptive)")
    parser.add_argument("--seed", type=int, default=42,
                        help="RNG seed for ESDE engine")
    parser.add_argument("--endpoint", type=str, default=DEFAULT_ENDPOINT,
                        help="LLM API endpoint")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL,
                        help="LLM model name")
    parser.add_argument("--skip-injection", action="store_true",
                        help="Skip injection phase (faster startup)")
    args = parser.parse_args()

    engine = LiveEngine(seed=args.seed)

    if not args.skip_injection:
        engine.run_injection()
    else:
        engine.theta_initial = engine.state.theta.copy()
        print(f"  ⟐ Injection skipped. Topology is unestablished.")

    repl(engine, args.mode, args.endpoint, args.model)


if __name__ == "__main__":
    main()
