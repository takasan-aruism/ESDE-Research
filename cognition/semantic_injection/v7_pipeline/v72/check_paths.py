#!/usr/bin/env python3
"""Path diagnostic — run from v72/ directory"""
from pathlib import Path
import sys

_SCRIPT_DIR = Path(__file__).resolve().parent
_PIPELINE_DIR = _SCRIPT_DIR.parent
_SEMANTIC_DIR = _PIPELINE_DIR.parent
_V4_PIPELINE = _SEMANTIC_DIR / "v4_pipeline"
_V43_DIR = _V4_PIPELINE / "v43"
_V41_DIR = _V4_PIPELINE / "v41"
_REPO_ROOT = _SEMANTIC_DIR.parent.parent
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

print(f"_SCRIPT_DIR:   {_SCRIPT_DIR}")
print(f"_PIPELINE_DIR: {_PIPELINE_DIR}")
print(f"_SEMANTIC_DIR: {_SEMANTIC_DIR}")
print(f"_V4_PIPELINE:  {_V4_PIPELINE}")
print(f"_V43_DIR:      {_V43_DIR}  exists={_V43_DIR.exists()}")
print(f"_V41_DIR:      {_V41_DIR}  exists={_V41_DIR.exists()}")
print(f"_REPO_ROOT:    {_REPO_ROOT}  exists={_REPO_ROOT.exists()}")
print(f"_ENGINE_DIR:   {_ENGINE_DIR}  exists={_ENGINE_DIR.exists()}")

# Check for engine_accel
import glob
ea = list(glob.glob(str(_ENGINE_DIR / "engine_accel*")))
print(f"\nengine_accel files: {ea}")
ea2 = list(glob.glob(str(_REPO_ROOT / "**" / "engine_accel*"), recursive=True))
print(f"All engine_accel in repo: {ea2[:5]}")
