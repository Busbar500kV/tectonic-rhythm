#!/usr/bin/env bash
set -euo pipefail

# ==============================
# scripts/run_busbar.sh
# Runs the pipeline on busbar, commits out/final.mp4, pushes to GitHub.
# Works regardless of where you launch it from.
# ==============================

# Resolve repo root from this script location (no hardcoded ~/repo-name assumptions)
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

OUT_DIR="${REPO_DIR}/out"
FRAMES_DIR="${OUT_DIR}/frames"
AUDIO="${OUT_DIR}/audio.wav"
VIDEO="${OUT_DIR}/video.mp4"
FINAL="${OUT_DIR}/final.mp4"

STAMP="$(date -u +'%Y-%m-%dT%H%M%SZ')"
COMMIT_MSG="Render output ${STAMP}"

echo "[run_busbar] Repo dir: ${REPO_DIR}"
cd "${REPO_DIR}"

# Ensure we're in a git repo
if [[ ! -d ".git" ]]; then
  echo "ERROR: ${REPO_DIR} is not a git repository (missing .git)"
  exit 1
fi

echo "[run_busbar] Remote:"
git remote -v || true

# Sync with GitHub
echo "[run_busbar] Fetch + reset to origin/main"
git fetch origin
git checkout main
git reset --hard origin/main

# Python venv
if [[ ! -d "venv" ]]; then
  echo "[run_busbar] Creating venv/"
  python3 -m venv venv
fi

echo "[run_busbar] Activating venv"
# shellcheck disable=SC1091
source venv/bin/activate

python -m pip install --upgrade pip >/dev/null

# Install deps
if [[ -f "requirements.txt" ]]; then
  echo "[run_busbar] Installing requirements.txt"
  pip install -r requirements.txt
elif [[ -f "pyproject.toml" ]]; then
  echo "[run_busbar] Installing from pyproject.toml"
  pip install -e .
else
  echo "[run_busbar] Installing minimal deps (no requirements.txt / pyproject.toml found)"
  pip install requests pandas numpy scipy matplotlib geopandas shapely pyproj
fi

# System checks
echo "[run_busbar] Checking ffmpeg"
command -v ffmpeg >/dev/null 2>&1 || { echo "ERROR: ffmpeg not found"; exit 1; }

# Clean outputs (frames are huge)
echo "[run_busbar] Cleaning outputs"
mkdir -p "${OUT_DIR}"
rm -f "${AUDIO}" "${VIDEO}" "${FINAL}"
rm -rf "${FRAMES_DIR}"
mkdir -p "${FRAMES_DIR}"

# Run pipeline (make src importable)
echo "[run_busbar] Running pipeline"
export PYTHONPATH="${REPO_DIR}/src:${PYTHONPATH:-}"
python -u scripts/run_pipeline.py

# Validate output
if [[ ! -f "${FINAL}" ]]; then
  echo "ERROR: ${FINAL} was not created."
  exit 1
fi

echo "[run_busbar] Final artifact:"
ls -lh "${FINAL}"

# Warn if big (GitHub may reject large files)
FILE_MB=$(du -m "${FINAL}" | awk '{print $1}')
if [[ "${FILE_MB}" -gt 90 ]]; then
  echo "WARNING: final.mp4 is ${FILE_MB} MB. GitHub may reject large pushes."
  echo "Tip: reduce duration_s and/or fps in scripts/run_pipeline.py"
fi

# Commit + push final.mp4 only
echo "[run_busbar] Git add + commit + push"
git add "out/final.mp4"

if git diff --cached --quiet; then
  echo "[run_busbar] No changes to commit."
  exit 0
fi

git commit -m "${COMMIT_MSG}"
git push origin main

echo "[run_busbar] Done. Pushed out/final.mp4"