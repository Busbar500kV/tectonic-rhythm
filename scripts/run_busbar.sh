#!/usr/bin/env bash
set -euo pipefail

# --- config you may tweak ---
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="out"
FRAMES_DIR="out/frames"
AUDIO="out/audio.wav"
VIDEO="out/video.mp4"
FINAL="out/final.mp4"

# Commit message tag
STAMP="$(date -u +'%Y-%m-%dT%H%M%SZ')"
COMMIT_MSG="Render output ${STAMP}"

echo "[run_busbar] Repo: ${REPO_DIR}"
cd "${REPO_DIR}"

# Ensure we're on main and up to date
echo "[run_busbar] Fetch + reset to origin/main"
git fetch origin
git checkout main
git reset --hard origin/main

# Optional: create venv if not present
if [[ ! -d "venv" ]]; then
  echo "[run_busbar] Creating venv/"
  python3 -m venv venv
fi

echo "[run_busbar] Activating venv"
# shellcheck disable=SC1091
source venv/bin/activate
python -m pip install --upgrade pip >/dev/null

# Install python deps
if [[ -f "requirements.txt" ]]; then
  echo "[run_busbar] Installing requirements.txt"
  pip install -r requirements.txt
elif [[ -f "pyproject.toml" ]]; then
  echo "[run_busbar] Installing from pyproject.toml"
  pip install -e .
else
  echo "[run_busbar] No requirements.txt or pyproject.toml found. Installing minimal deps."
  pip install requests pandas numpy scipy matplotlib geopandas shapely pyproj
fi

# Quick dependency sanity checks
echo "[run_busbar] Checking ffmpeg availability"
command -v ffmpeg >/dev/null 2>&1 || { echo "ERROR: ffmpeg not found"; exit 1; }

# Run pipeline
echo "[run_busbar] Cleaning old outputs (keeping directory)"
mkdir -p "${OUT_DIR}"
rm -f "${AUDIO}" "${VIDEO}" "${FINAL}"
# (frames can be huge; delete to avoid stale leftovers)
rm -rf "${FRAMES_DIR}"
mkdir -p "${FRAMES_DIR}"

echo "[run_busbar] Running pipeline"
python -u scripts/run_pipeline.py

# Confirm output exists
if [[ ! -f "${FINAL}" ]]; then
  echo "ERROR: ${FINAL} not produced."
  exit 1
fi

echo "[run_busbar] Output produced: ${FINAL}"
ls -lh "${FINAL}"

# Warn if file is large (GitHub can reject big pushes)
FILE_MB=$(du -m "${FINAL}" | awk '{print $1}')
if [[ "${FILE_MB}" -gt 90 ]]; then
  echo "WARNING: final.mp4 is ${FILE_MB} MB. GitHub may reject large files."
  echo "Consider reducing duration/fps or using Git LFS."
fi

# Commit and push ONLY the final artifact(s)
echo "[run_busbar] Git add outputs"
git add "${FINAL}" || true
# optionally also add audio/video (uncomment if you want them in repo)
# git add "${AUDIO}" "${VIDEO}" || true

# If nothing changed, don't fail
if git diff --cached --quiet; then
  echo "[run_busbar] No changes to commit."
  exit 0
fi

echo "[run_busbar] Commit + push"
git commit -m "${COMMIT_MSG}"
git push origin main

echo "[run_busbar] Done. Pushed ${FINAL}"