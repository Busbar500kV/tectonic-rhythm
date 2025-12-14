#!/usr/bin/env bash
set -euo pipefail

# =========================================================
# Bulletproof end-to-end runner for busbar (Blink safe)
# =========================================================

REPO_NAME="tectonic-rhythm"
GITHUB_USER="Busbar500kV"
REPO_URL="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"

HOME_DIR="${HOME}"
REPO_DIR="${HOME_DIR}/${REPO_NAME}"

SCREEN_NAME="seismo_render"
LOG_DIR="${REPO_DIR}/out"
LOG_FILE="${LOG_DIR}/run.log"

STAMP="$(date -u +'%Y-%m-%dT%H%M%SZ')"
COMMIT_MSG="Automated render ${STAMP}"

# ---------------------------------------------------------
# Ensure screen exists
# ---------------------------------------------------------
if ! command -v screen >/dev/null 2>&1; then
  echo "[bootstrap] Installing screen"
  sudo apt-get update
  sudo apt-get install -y screen
fi

# ---------------------------------------------------------
# Clone repo if missing
# ---------------------------------------------------------
if [[ ! -d "${REPO_DIR}/.git" ]]; then
  echo "[bootstrap] Repo not found. Cloning..."
  cd "${HOME_DIR}"
  git clone "${REPO_URL}" "${REPO_DIR}"
else
  echo "[bootstrap] Repo found."
fi

# ---------------------------------------------------------
# Prepare log dir
# ---------------------------------------------------------
mkdir -p "${LOG_DIR}"

# ---------------------------------------------------------
# Kill existing screen session if stuck
# ---------------------------------------------------------
if screen -ls | grep -q "${SCREEN_NAME}"; then
  echo "[bootstrap] Existing screen '${SCREEN_NAME}' found. Killing it."
  screen -S "${SCREEN_NAME}" -X quit || true
fi

# ---------------------------------------------------------
# Start detached screen session
# ---------------------------------------------------------
echo "[bootstrap] Starting detached screen session: ${SCREEN_NAME}"

screen -dmS "${SCREEN_NAME}" bash -c "
  set -euo pipefail

  echo '=== Seismic render started at ${STAMP} ===' > '${LOG_FILE}'

  cd '${REPO_DIR}'
  echo '[screen] In repo:' \$(pwd) >> '${LOG_FILE}'

  git fetch origin >> '${LOG_FILE}' 2>&1
  git checkout main >> '${LOG_FILE}' 2>&1
  git reset --hard origin/main >> '${LOG_FILE}' 2>&1

  # Python venv
  if [[ ! -d venv ]]; then
    echo '[screen] Creating venv' >> '${LOG_FILE}'
    python3 -m venv venv >> '${LOG_FILE}' 2>&1
  fi

  source venv/bin/activate
  python -m pip install --upgrade pip >> '${LOG_FILE}' 2>&1

  if [[ -f requirements.txt ]]; then
    pip install -r requirements.txt >> '${LOG_FILE}' 2>&1
  elif [[ -f pyproject.toml ]]; then
    pip install -e . >> '${LOG_FILE}' 2>&1
  else
    pip install requests pandas numpy scipy matplotlib geopandas shapely pyproj >> '${LOG_FILE}' 2>&1
  fi

  command -v ffmpeg >/dev/null || { echo 'ffmpeg missing' >> '${LOG_FILE}'; exit 1; }

  # Clean outputs
  rm -rf out/frames
  rm -f out/audio.wav out/video.mp4 out/final.mp4
  mkdir -p out/frames

  # Run pipeline
  export PYTHONPATH='${REPO_DIR}/src'
  python -u scripts/run_pipeline.py >> '${LOG_FILE}' 2>&1

  if [[ ! -f out/final.mp4 ]]; then
    echo 'ERROR: final.mp4 not created' >> '${LOG_FILE}'
    exit 1
  fi

  git add out/final.mp4
  if ! git diff --cached --quiet; then
    git commit -m '${COMMIT_MSG}' >> '${LOG_FILE}' 2>&1
    git push origin main >> '${LOG_FILE}' 2>&1
  else
    echo '[screen] Nothing new to commit' >> '${LOG_FILE}'
  fi

  echo '=== Render completed successfully ===' >> '${LOG_FILE}'
"

# ---------------------------------------------------------
# Final message to user
# ---------------------------------------------------------
echo
echo "✅ Detached render started successfully."
echo
echo "Useful commands:"
echo "  View progress:   tail -f ${LOG_FILE}"
echo "  Reattach screen: screen -r ${SCREEN_NAME}"
echo "  List screens:    screen -ls"
echo
echo "You may safely disconnect Blink now."