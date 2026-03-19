#!/usr/bin/env python3
"""
Label 空間抽出 — v7.3 engine を 200 window 走らせて
最終状態の label node ID と grid 座標を出力する。

USAGE: python extract_label_positions.py --seed 42 --windows 200
"""
import sys, math, json, argparse
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_PIPELINE_DIR = _SCRIPT_DIR.parent
_SEMANTIC_DIR = _PIPELINE_DIR.parent
_V4_PIPELINE = _SEMANTIC_DIR / "v4_pipeline"
_V43_DIR = _V4_PIPELINE / "v43"
_V41_DIR = _V4_PIPELINE / "v41"
_REPO_ROOT = _SEMANTIC_DIR.parent.parent
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_SCRIPT_DIR), str(_PIPELINE_DIR), str(_V43_DIR),
          str(_V41_DIR), str(_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from esde_v73_engine import V73Engine, V73EncapsulationParams, V73_WINDOW

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--windows", type=int, default=200)
    args = parser.parse_args()

    N = 5000
    side = int(math.ceil(math.sqrt(N)))

    print(f"Running v7.3 seed={args.seed} windows={args.windows}...")
    engine = V73Engine(seed=args.seed,
                       encap_params=V73EncapsulationParams())
    engine.run_injection()
    for w in range(args.windows):
        engine.step_window()
        if (w+1) % 50 == 0:
            print(f"  w{w+1}: links={len(engine.state.alive_l)} "
                  f"labels={len(engine.virtual.labels)}")

    # Extract
    result = {"seed": args.seed, "windows": args.windows,
              "grid_side": side, "labels": []}

    for lid, label in sorted(engine.virtual.labels.items(),
                              key=lambda x: x[1]["share"], reverse=True):
        nodes = sorted(label["nodes"])
        coords = [(n, n // side, n % side) for n in nodes]
        # Neighbors on substrate for each node
        node_links = {}
        for n in nodes:
            links_at_n = []
            for lk in engine.state.alive_l:
                if n in lk:
                    other = lk[0] if lk[1] == n else lk[1]
                    r = engine.state.R.get(lk, 0.0)
                    s = engine.state.S.get(lk, 0.0)
                    links_at_n.append({"other": other, "R": round(r,3),
                                       "S": round(s,3)})
            node_links[n] = links_at_n

        result["labels"].append({
            "id": lid,
            "share": round(label["share"], 6),
            "phase_sig": round(label["phase_sig"], 4),
            "born": label["born"],
            "nodes": [{"id": n, "row": r, "col": c}
                      for n, r, c in coords],
            "node_links": {str(n): links for n, links in node_links.items()},
        })

    # Inter-label distances (BFS on substrate)
    all_label_nodes = {}
    for lb in result["labels"]:
        for nd in lb["nodes"]:
            all_label_nodes[nd["id"]] = lb["id"]

    # Pairwise min distance between labels
    from collections import deque
    substrate = engine.substrate
    distances = {}
    label_ids = [lb["id"] for lb in result["labels"]]
    for i, lid1 in enumerate(label_ids):
        nodes1 = [nd["id"] for nd in result["labels"][i]["nodes"]]
        for j, lid2 in enumerate(label_ids):
            if j <= i:
                continue
            nodes2 = set(nd["id"] for nd in result["labels"][j]["nodes"])
            # BFS from nodes1, find min distance to any node in nodes2
            visited = {}
            queue = deque()
            for n in nodes1:
                queue.append((n, 0))
                visited[n] = 0
            min_dist = 999
            while queue and min_dist > 0:
                n, d = queue.popleft()
                if n in nodes2:
                    min_dist = min(min_dist, d)
                    continue
                if d >= min_dist:
                    continue
                for nb in substrate.get(n, []):
                    if nb not in visited or visited[nb] > d + 1:
                        visited[nb] = d + 1
                        queue.append((nb, d + 1))
            distances[f"{lid1}-{lid2}"] = min_dist

    result["inter_label_distances"] = distances

    # Output
    out_path = _SCRIPT_DIR / f"label_positions_seed{args.seed}.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved: {out_path}")

    # Print summary
    print(f"\n{'='*60}")
    print(f"LABEL SPATIAL SUMMARY")
    print(f"{'='*60}\n")
    for lb in result["labels"]:
        coords = [(nd["row"], nd["col"]) for nd in lb["nodes"]]
        mean_r = sum(r for r,c in coords) / len(coords)
        mean_c = sum(c for r,c in coords) / len(coords)
        print(f"  Label#{lb['id']:>4}: share={lb['share']:.3f} "
              f"center=({mean_r:.0f},{mean_c:.0f}) "
              f"nodes={[(r,c) for r,c in coords]}")

    print(f"\nInter-label distances (substrate hops):")
    for pair, dist in sorted(distances.items()):
        print(f"  {pair}: {dist} hops")

if __name__ == "__main__":
    main()
