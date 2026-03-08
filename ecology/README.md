# ESDE Ecology: Observer Interaction Physics

## Structure

```
ecology/
├── engine/              # Frozen Genesis physics (one copy)
│   ├── v19g_canon.py
│   ├── genesis_state.py
│   └── ...
├── region_observer/     # First experiment: 2x2 partition
│   ├── region_observer.py
│   ├── csv_schema.txt
│   └── outputs/
└── README.md
```

## Running experiments

```bash
cd ecology/region_observer

# Sanity
python region_observer.py --sanity

# Full run (5 seeds)
parallel -j 5 python region_observer.py --seed {1} \
  ::: 42 123 456 789 2024

# Aggregate
python region_observer.py --aggregate
```

## Adding new experiments

1. Create a new directory: `ecology/new_experiment/`
2. Add this at the top of your script (after shebang and docstring):
   `import sys; from pathlib import Path as _P`
   `sys.path.insert(0, str(_P(__file__).resolve().parent.parent / "engine"))`
3. Engine modules are available: `from v19g_canon import run_canonical, ...`

## Engine changes

If the engine ever needs modification (unlikely during Ecology):
- Edit `ecology/engine/*.py`
- git commit with clear message
- All experiments pick up the change automatically
