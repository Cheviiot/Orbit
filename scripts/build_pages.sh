#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

: "${ORBIT_GPG_KEY_ID:?ORBIT_GPG_KEY_ID is required}"

REPO_TITLE="${ORBIT_REPO_TITLE:-Orbit}"
REMOTE_NAME="${ORBIT_REMOTE_NAME:-orbit}"
REPO_FILE="${ORBIT_REPO_FILE:-orbit.flatpakrepo}"
COLLECTION_ID="${ORBIT_COLLECTION_ID:-io.github.Cheviiot.Orbit}"

if [[ -n "${ORBIT_BASE_URL:-}" ]]; then
  BASE_URL="${ORBIT_BASE_URL%/}"
elif [[ -n "${GITHUB_REPOSITORY:-}" ]]; then
  owner="${GITHUB_REPOSITORY_OWNER:-${GITHUB_REPOSITORY%%/*}}"
  repo_name="${GITHUB_REPOSITORY#*/}"
  BASE_URL="https://${owner}.github.io/${repo_name}"
else
  BASE_URL="https://cheviiot.github.io/Orbit"
fi

rm -rf dist repo public
mkdir -p dist/bundles repo public
ostree --repo=repo init --mode=archive-z2

python3 tools/orbit_tools.py sync-bundles \
  --config packages/generalsx.json \
  --output-dir dist/bundles \
  --metadata dist/generalsx-release.json

mapfile -t bundles < <(find dist/bundles -maxdepth 1 -type f -name '*.flatpak' | sort)
if [[ "${#bundles[@]}" -eq 0 ]]; then
  echo "No Flatpak bundles were downloaded" >&2
  exit 1
fi

for bundle in "${bundles[@]}"; do
  flatpak build-import-bundle \
    --no-update-summary \
    --gpg-sign="${ORBIT_GPG_KEY_ID}" \
    repo \
    "${bundle}"
done

gpg --batch --export "${ORBIT_GPG_KEY_ID}" > dist/orbit.gpg
base64 --wrap=0 < dist/orbit.gpg > dist/orbit.gpg.base64

flatpak build-update-repo \
  --gpg-sign="${ORBIT_GPG_KEY_ID}" \
  --gpg-import=dist/orbit.gpg \
  --title="${REPO_TITLE}" \
  --comment="Личный Flatpak-репозиторий" \
  --description="Личный Flatpak-репозиторий с выбранными приложениями." \
  --homepage="${BASE_URL}/" \
  --collection-id="${COLLECTION_ID}" \
  --deploy-sideload-collection-id \
  --generate-static-deltas \
  --prune \
  repo

cp -a repo public/repo
touch public/.nojekyll

python3 tools/orbit_tools.py render-flatpakrepo \
  --title="${REPO_TITLE}" \
  --url="${BASE_URL}/repo/" \
  --homepage="${BASE_URL}/" \
  --comment="Личный Flatpak-репозиторий" \
  --description="Личный Flatpak-репозиторий с выбранными приложениями." \
  --gpg-key-file dist/orbit.gpg.base64 \
  --output "public/${REPO_FILE}"

python3 tools/orbit_tools.py render-index \
  --title="${REPO_TITLE}" \
  --base-url="${BASE_URL}" \
  --repo-file="${REPO_FILE}" \
  --remote-name="${REMOTE_NAME}" \
  --metadata dist/generalsx-release.json \
  --output public/index.html
