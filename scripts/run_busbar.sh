#!/usr/bin/env bash
set -euo pipefail

# ------------------------------
# CONFIG
# ------------------------------
REPO_NAME="tectonic-rhythm"
HOME_DIR="${HOME}"
REPO_DIR="${HOME_DIR}/${REPO_NAME}"

OUT_DIR="out"
FINAL_MP4="out/final.mp4"

STAMP="$(date -u +'%Y-%m-%dT%H%M%SZ')"
COMMIT_MSG="Render seismic soundtrack ${STAMP}"

# ------------------------------
# LOCATE REPO
# ------------------------------
echo "🔍 Locating repository: ${REPO_NAME}"

if [[ ! -d "${REPO_DIR}/.git" ]]; then
  echo "❌ ERROR: Git repo not found at ${REPO_DIR}"
  echo "   Did you clone it?"
  exit 1
fi

cd "${REPO_DIR}"
echo "📁 In repo: $(pwd)"
echo "🔗 Remote:"
git remote -v

# ------------------------------
# SYNC WITH GITHUB
# ------------------------------
echo "⬇️  Syncing with origin/main"
git fetch origin
git checkout main
git reset --hard origin/main

# ------------------------------
# PYTHON ENV
# ------------------------------
if [[ ! -d "venv" ]]; then
  echo "🐍 Creating Python venv"
  python3 -m venv venv
fi

echo "🐍 Activating venv"
# shellcheck disable=SC1091
source venv/bin/activate
python -m pip install --upgrade pip >/dev/null

if [[ -f "requirements.txt" ]]; then
  pip install -r requirements.txt
elif [[ -f "pyproject.toml" ]]; then
  pip install -e .
else
  pip install requests pandas numpy scipy matplotlib geopandas shapely pyproj
fi

# ------------------------------
# SYSTEM CHECKS
# ------------------------------
echo "🎥 Checking ffmpeg"
command -v ffmpeg >/dev/null || { echo "❌ ffmpeg not found"; exit 1; }

# ------------------------------
# CLEAN OUTPUTS
# ------------------------------
echo "🧹 Cleaning outputs"
rm -rf out/frames
rm -f out/audio.wav out/video.mp4
mkdir -p out/frames

# ------------------------------
# RUN PIPELINE
# ------------------------------
echo "🚀 Running seismic render pipeline"
python -u scripts/run_pipeline.py

if [[ ! -f "${FINAL_MP4}" ]]; then
  echo "❌ ERROR: ${FINAL_MP4} not produced"
  exit 1
fi

ls -lh "${FINAL_MP4}"

# ------------------------------
# COMMIT & PUSH RESULT
# ------------------------------
echo "📦 Committing final artifact"

git add "${FINAL_MP4}"

if git diff --cached --quiet; then
  echo "ℹ️  No changes to commit"
  exit 0
fi

git commit -m "${COMMIT_MSG}"
git push origin main

echo "✅ Done. ${FINAL_MP4} pushed to GitHub."