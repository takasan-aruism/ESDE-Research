#!/bin/bash
# ESDE Genesis → Ecology Directory Reorganization
# Run from: ~/esde/ESDE-Research/
# Preview first: bash reorganize_genesis.sh --dry-run

set -euo pipefail

DRY=false
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY=true
  echo "=== DRY RUN (no changes will be made) ==="
fi

run() {
  echo "  $*"
  if ! $DRY; then eval "$@"; fi
}

echo ""
echo "=========================================="
echo " ESDE Genesis Directory Reorganization"
echo "=========================================="
echo ""

# --------------------------------------------------
# 0. Clean __pycache__ everywhere
# --------------------------------------------------
echo "[0] Cleaning __pycache__..."
run "find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true"

# --------------------------------------------------
# 1. Create new structure
# --------------------------------------------------
echo ""
echo "[1] Creating directory structure..."
run "mkdir -p docs"
run "mkdir -p genesis/canon"
run "mkdir -p genesis/results/v14"
run "mkdir -p genesis/results/v15"
run "mkdir -p genesis/results/v16"
run "mkdir -p genesis/results/v17"
run "mkdir -p genesis/results/v18"
run "mkdir -p genesis/results/v18O"
run "mkdir -p genesis/results/v18O2"
run "mkdir -p genesis/results/v19"
run "mkdir -p genesis/results/v19g_canon"
run "mkdir -p genesis/results/v1000"
run "mkdir -p genesis/results/scale"
run "mkdir -p genesis/archive"
run "mkdir -p ecology"

# --------------------------------------------------
# 2. docs/ — project-wide documents
# --------------------------------------------------
echo ""
echo "[2] Moving docs..."
run "mv ESDE_Genesis_Milestone_Report.md docs/"
run "mv ESDE_Genesis_AI_governance_rules_v2.txt docs/"
run "mv esde_explainability_constitution.txt docs/"
run "mv 概念理解.txt docs/"
run "mv ESDE_Claude_N1000_Instruction.txt docs/"

# --------------------------------------------------
# 3. genesis/canon/ — canonical code from v19g_canon_deploy
# --------------------------------------------------
echo ""
echo "[3] Setting up genesis/canon/ (from v19g_canon_deploy)..."
for f in v19g_canon.py run_scale_test.py v1000_scale.py \
         genesis_state.py genesis_physics.py genesis_logger.py \
         chemistry.py realization.py autogrowth.py intrusion.py \
         IMPLEMENTATION_SUMMARY.txt OBSERVER_FREEZE_NOTE.txt; do
  run "cp v19g_canon_deploy/$f genesis/canon/"
done

# --------------------------------------------------
# 4. genesis/results/ — collect all outputs
# --------------------------------------------------
echo ""
echo "[4] Moving results..."

# v14–v17 (outputs inside deploy dirs)
run "mv v14_deploy/outputs_v14/*  genesis/results/v14/  2>/dev/null || true"
run "mv v15_deploy/outputs_v15/*  genesis/results/v15/  2>/dev/null || true"
run "mv v16_deploy/outputs_v16/*  genesis/results/v16/  2>/dev/null || true"
run "mv v17_deploy/outputs_v17/*  genesis/results/v17/  2>/dev/null || true"

# v18 variants
run "mv v18_deploy/outputs_v18/*       genesis/results/v18/    2>/dev/null || true"
run "mv v18_deploy_fixed/outputs_v18/* genesis/results/v18/    2>/dev/null || true"
run "mv v18O_deploy/outputs_v18O/*     genesis/results/v18O/   2>/dev/null || true"
run "mv v18O2_deploy/outputs_v18O2/*   genesis/results/v18O2/  2>/dev/null || true"

# v19 variants (from v18O2_deploy and v19cd_deploy)
run "cp -r v18O2_deploy/outputs_v19/*         genesis/results/v19/          2>/dev/null || true"
run "cp -r v18O2_deploy/outputs_v19_followup/* genesis/results/v19/         2>/dev/null || true"
run "cp -r v19cd_deploy/outputs_v19c/*        genesis/results/v19/v19c/     2>/dev/null || true"
run "cp -r v19cd_deploy/outputs_v19d/*        genesis/results/v19/v19d/     2>/dev/null || true"
run "cp -r v19cd_deploy/outputs_v19e/*        genesis/results/v19/v19e/     2>/dev/null || true"
run "cp -r v19cd_deploy/outputs_v19f/*        genesis/results/v19/v19f/     2>/dev/null || true"
run "cp -r v19cd_deploy/outputs_v19_final/*   genesis/results/v19/v19_final/ 2>/dev/null || true"

# v19g canonical + scale
run "cp -r v19g_canon_deploy/outputs_v19g_canon/* genesis/results/v19g_canon/ 2>/dev/null || true"
run "cp -r v19g_canon_deploy/outputs_v1000/*     genesis/results/v1000/       2>/dev/null || true"
run "cp -r v19g_canon_deploy/outputs_scale/*     genesis/results/scale/       2>/dev/null || true"

# v19g (standalone)
run "cp -r v19g_deploy/outputs_v19g/* genesis/results/v19/v19g/ 2>/dev/null || true"

# --------------------------------------------------
# 5. genesis/archive/ — move all deploy/version dirs
# --------------------------------------------------
echo ""
echo "[5] Moving version dirs to archive..."
for d in v0.3 v0.4 v0.5 v0.7 v0.9 v1.0 v1.1 v1.2 v1.3 \
         o4 o5 o6 o7 \
         v14_deploy v15_deploy v16_deploy v17_deploy \
         v18_deploy v18_deploy_fixed v18O_deploy v18O2_deploy \
         v19cd_deploy v19g_deploy v19g_canon_deploy; do
  if [ -d "$d" ]; then
    run "mv $d genesis/archive/"
  fi
done

# --------------------------------------------------
# 6. ecology/ — placeholder
# --------------------------------------------------
echo ""
echo "[6] Creating ecology README..."
if ! $DRY; then
cat > ecology/README.md << 'EOF'
# ESDE Ecology: Observer Interaction Physics

Phase following Genesis. Studies how multiple observers interact.

## Status
Not yet started. Awaiting Gemini design specification.

## Prerequisites
- Genesis canon code: `../genesis/canon/`
- Genesis results: `../genesis/results/`

## Planned Topics
- Multiple observer regions
- Observer competition / coexistence
- Observer merging / splitting
- Regional dominance patterns
EOF
fi
run "echo 'ecology/README.md created'"

# --------------------------------------------------
# 7. Summary
# --------------------------------------------------
echo ""
echo "=========================================="
echo " Done. New structure:"
echo "=========================================="
echo ""
if ! $DRY; then
  find . -maxdepth 3 -type d | head -50
  echo ""
  echo "Verify with: tree -L 2"
  echo ""
  echo "If satisfied, commit:"
  echo "  git add -A && git commit -m 'Reorganize: Genesis complete, prepare Ecology'"
fi
