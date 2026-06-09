#!/usr/bin/env bash
# =============================================================================
# Guardsquare Build (Unified)
#
# Usage:
#   bash guardsquare_build.sh <type> <environment>
#
# Arguments:
#   type:        instrumented | protected
#   environment: quality | production
#
# Required env vars:
#   RELEASE_PATH, CI_PROJECT_DIR, PIPELINE_API_REPO_URL, PIPELINE_BRANCH,
#   TOKEN_GITLAB, GUARDSQUARE_ENV
#
# Optional env vars (signing):
#   DEXGUARD_LICENSE_B64, QUALITY_KEYSTORE_B64, RELEASE_KEYSTORE_B64,
#   QUALITY_KEY_STORE_PATH, KEY_STORE_PATH
#
# Optional env vars (DexGuard Maven):
#   MAVEN_USER_DEXGUARD, DEXGUARD_MAVEN_PASSWORD, MAVEN_PASSWORD_DEXGUARD
# =============================================================================
set -Eeo pipefail
trap 'echo "[ERROR] Command failed: $BASH_COMMAND (exitcode=$?)" >&2' ERR

BUILD_TYPE="${1:?Usage: guardsquare_build.sh <instrumented|protected> <quality|production>}"
ENVIRONMENT="${2:?Usage: guardsquare_build.sh <instrumented|protected> <quality|production>}"

case "${BUILD_TYPE}" in
  instrumented|protected) ;;
  *) echo "[ERROR] Invalid type: ${BUILD_TYPE}"; exit 1 ;;
esac

case "${ENVIRONMENT}" in
  quality)    GRADLE_FLAG="-PuseQuality" ;;
  production) GRADLE_FLAG="-PuseProduction" ;;
  *) echo "[ERROR] Invalid environment: ${ENVIRONMENT}"; exit 1 ;;
esac

echo "============================================================"
echo "[INFO] Guardsquare Build"
echo "[INFO]   Type:        ${BUILD_TYPE}"
echo "[INFO]   Environment: ${ENVIRONMENT}"
echo "[INFO]   Gradle flag: ${GRADLE_FLAG}"
echo "============================================================"

# ====== Android SDK detection ======
SDK_PATH="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}"
if [ -z "${SDK_PATH}" ] || [ ! -d "${SDK_PATH}" ]; then
  for candidate in /opt/android-sdk /usr/lib/android-sdk /usr/local/android-sdk; do
    if [ -d "${candidate}" ]; then SDK_PATH="${candidate}"; break; fi
  done
fi
if [ -z "${SDK_PATH}" ] || [ ! -d "${SDK_PATH}" ]; then
  echo "[ERROR] Android SDK not found"; exit 1
fi
export ANDROID_HOME="${SDK_PATH}" ANDROID_SDK_ROOT="${SDK_PATH}"
printf "sdk.dir=%s\n" "${SDK_PATH}" > local.properties
echo "[INFO] SDK: ${SDK_PATH}"

# ====== DexGuard credentials ======
if [[ -n "${MAVEN_USER_DEXGUARD:-}" ]]; then
  export ORG_GRADLE_PROJECT_MAVEN_USER_DEXGUARD="${MAVEN_USER_DEXGUARD}"
  export ORG_GRADLE_PROJECT_DEXGUARD_USERNAME="${MAVEN_USER_DEXGUARD}"
fi
if [[ -n "${DEXGUARD_MAVEN_PASSWORD:-}" ]]; then
  export ORG_GRADLE_PROJECT_MAVEN_PASSWORD_DEXGUARD="${DEXGUARD_MAVEN_PASSWORD}"
  export ORG_GRADLE_PROJECT_DEXGUARD_PASSWORD="${DEXGUARD_MAVEN_PASSWORD}"
fi

# ====== SSH agent for Guardsquare registry ======
if ! command -v ssh-agent >/dev/null 2>&1; then
  apt-get update && apt-get install -y --no-install-recommends openssh-client
fi
curl -fL -o guardsquare_ssh_setup.py \
  "${PIPELINE_API_REPO_URL}/files%2FPF%2Fscripts%2Fguardsquare_ssh_setup.py/raw?ref=${PIPELINE_BRANCH}" \
  --header "Authorization: Bearer $TOKEN_GITLAB"
eval "$(ssh-agent -s)"
SSH_AUTH_SOCK="$SSH_AUTH_SOCK" SSH_AGENT_PID="$SSH_AGENT_PID" python3 guardsquare_ssh_setup.py
echo "[INFO] SSH agent ready"

# ====== Prepare keystore ======
mkdir -p "${RELEASE_PATH}"

if [[ -n "${DEXGUARD_LICENSE_B64:-}" ]]; then
  echo "${DEXGUARD_LICENSE_B64}" | base64 -d > "${CI_PROJECT_DIR}/dexguard-license.txt"
fi

if [[ "${ENVIRONMENT}" == "quality" ]]; then
  if [[ -n "${QUALITY_KEYSTORE_B64:-}" ]]; then
    echo "[INFO] Preparing quality keystore"
    echo "${QUALITY_KEYSTORE_B64}" | base64 -d > "${CI_PROJECT_DIR}/superAppHomologKey.keystore"
    export QUALITY_KEY_STORE_PATH="${CI_PROJECT_DIR}/superAppHomologKey.keystore"
  fi
elif [[ "${ENVIRONMENT}" == "production" ]]; then
  if [[ -n "${RELEASE_KEYSTORE_B64:-}" ]]; then
    echo "[INFO] Preparing release keystore"
    echo "${RELEASE_KEYSTORE_B64}" | base64 -d > "${CI_PROJECT_DIR}/release.keystore"
    export KEY_STORE_PATH="${CI_PROJECT_DIR}/release.keystore"
  fi
fi

# ====== Execute Gradle tasks ======
GRADLE_ARGS=("${GRADLE_FLAG}" "--no-daemon" "--build-cache")

if [[ "${BUILD_TYPE}" == "instrumented" ]]; then
  OUTPUT_EXT="apk"
  echo "[STEP] Building instrumented GMS/HMS APKs..."
  ./gradlew :app:guardsquareInstrumentGmsApk :app:guardsquareInstrumentHmsApk "${GRADLE_ARGS[@]}"

elif [[ "${BUILD_TYPE}" == "protected" ]]; then
  OUTPUT_EXT="aab"
  echo "[STEP] Building protected GMS/HMS Bundles..."
  ./gradlew :app:guardsquareProtectGMSBundle :app:guardsquareProtectHMSBundle "${GRADLE_ARGS[@]}"
fi

# ====== Collect artifacts ======
echo "[STEP] Collecting *.${OUTPUT_EXT} artifacts..."
find . -type f -name "*.${OUTPUT_EXT}" -not -path "*/.gradle/*" -exec mv {} "${RELEASE_PATH}/" \;

echo "============================================================"
echo "[INFO] Artifacts in ${RELEASE_PATH}:"
ls -lh "${RELEASE_PATH}/" || true
echo "============================================================"

# ====== Rename artifacts ======
ENVIRONMENT_LOWER="${ENVIRONMENT,,}"
for file in "${RELEASE_PATH}"/*; do
  [ -f "$file" ] || continue
  filename=$(basename "$file")
  extension="${filename##*.}"

  if [[ "$filename" == *gms* || "$filename" == *Gms* ]]; then TECH="gms"
  elif [[ "$filename" == *hms* || "$filename" == *Hms* ]]; then TECH="hms"
  else continue; fi

  TYPE_SUFFIX=""
  [[ "${BUILD_TYPE}" == "instrumented" ]] && TYPE_SUFFIX="-instrumented"
  [[ "${BUILD_TYPE}" == "protected" ]] && TYPE_SUFFIX="-protected"

  NEW_NAME="${CI_PROJECT_NAME}-${TECH}${TYPE_SUFFIX}-${ENVIRONMENT_LOWER}-${APP_VERSION}-${VERSION_CODE}-pipeline-${CI_PIPELINE_ID}.${extension}"
  mv "$file" "${RELEASE_PATH}/${NEW_NAME}"
  echo "[INFO] $filename → $NEW_NAME"
done

echo "guardsquare_build.sh finished OK"
