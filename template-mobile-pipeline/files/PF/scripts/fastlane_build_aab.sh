#!/bin/bash

set -Eeo pipefail
trap 'echo "[ERROR] $BASH_COMMAND (exit=$?)" >&2' ERR

# ====== Memory check ======
echo "============================================================"
echo "[INFO] SYSTEM MEMORY STATUS (before AAB build)"
free -h
echo "[INFO] CPU cores: $(nproc)"
AVAILABLE_MEM_MB=$(free -m | awk '/^Mem:/{print $7}')
echo "[INFO] Available memory: ${AVAILABLE_MEM_MB} MB"
if [ "${AVAILABLE_MEM_MB}" -lt 4096 ]; then
  echo "[WARN] ============================================================"
  echo "[WARN] AVAILABLE MEMORY IS BELOW 4 GB (${AVAILABLE_MEM_MB} MB)"
  echo "[WARN] This build is likely to fail with OOM (daemon killed)."
  echo "[WARN] Recommendation: cancel this job and retry later when"
  echo "[WARN] other builds have finished and memory is available."
  echo "[WARN] ============================================================"
fi
echo "============================================================"

# ====== Build info ======
echo "============================================================"
echo "[INFO] FASTLANE AAB BUILD"
echo "[INFO] Lane: ${FASTLANE_AAB_LANE}"
echo "[INFO] Environment: ${AAB_ENVIRONMENT}"
echo "[INFO] Flavor: gms"
echo "[INFO] VERSION_NAME: ${VERSION_NAME:-not set}"
echo "[INFO] VERSION_CODE: ${VERSION_CODE:-not set}"
echo "[INFO] PIPELINE_ID: ${CI_PIPELINE_ID:-not set}"
echo "============================================================"

# ====== Resolve keystore and export signing env vars ======
export DEXGUARD_LICENSE="${CI_PROJECT_DIR}/dexguard-license.txt"

if [ "${AAB_ENVIRONMENT}" == "quality" ]; then
  # QA: decode homolog keystore and export QUALITY_* vars for build.gradle
  export QUALITY_KEY_STORE_PATH="${CI_PROJECT_DIR}/superAppHomologKey.keystore"
  echo "${QUALITY_KEYSTORE_B64}" | base64 -d > "${QUALITY_KEY_STORE_PATH}"
  export QUALITY_KEY_ALIAS="${QUALITY_KEY_ALIAS}"
  export QUALITY_KEY_PASSWORD="${QUALITY_KEY_PASSWORD}"
  export QUALITY_KEY_STORE_PASSWORD="${QUALITY_KEY_STORE_PASSWORD}"
  KEYSTORE_SOURCE="CI variable QUALITY_KEYSTORE_B64 (homolog keystore)"
  KEYSTORE_FILE="${QUALITY_KEY_STORE_PATH}"
else
  # PROD: use release keystore (from job 2.6 Retrieve Signing Keys)
  export KEY_STORE_PATH="${CI_PROJECT_DIR}/release.keystore"
  KEYSTORE_SOURCE="AWS Secrets Manager (via job 2.6 Retrieve Signing Keys)"
  KEYSTORE_FILE="${KEY_STORE_PATH}"
fi

# ====== Signing validation ======
echo "============================================================"
echo "[SIGNING] Environment: ${AAB_ENVIRONMENT}"
echo "[SIGNING] Keystore source: ${KEYSTORE_SOURCE}"
if [ "${AAB_ENVIRONMENT}" == "quality" ]; then
  echo "[SIGNING] QUALITY_KEY_ALIAS: ${QUALITY_KEY_ALIAS:-NOT SET}"
  echo "[SIGNING] QUALITY_KEY_STORE_PATH: ${QUALITY_KEY_STORE_PATH}"
  if [ -n "${QUALITY_KEY_PASSWORD}" ]; then
    echo "[SIGNING] QUALITY_KEY_PASSWORD: SET (length=${#QUALITY_KEY_PASSWORD})"
  else
    echo "[SIGNING] QUALITY_KEY_PASSWORD: NOT SET"
  fi
  if [ -n "${QUALITY_KEY_STORE_PASSWORD}" ]; then
    echo "[SIGNING] QUALITY_KEY_STORE_PASSWORD: SET (length=${#QUALITY_KEY_STORE_PASSWORD})"
  else
    echo "[SIGNING] QUALITY_KEY_STORE_PASSWORD: NOT SET"
  fi
else
  echo "[SIGNING] KEY_ALIAS: ${KEY_ALIAS:-NOT SET}"
  echo "[SIGNING] KEY_STORE_PATH: ${KEY_STORE_PATH}"
  if [ -n "${KEY_PASSWORD}" ]; then
    echo "[SIGNING] KEY_PASSWORD: SET (length=${#KEY_PASSWORD})"
  else
    echo "[SIGNING] KEY_PASSWORD: NOT SET"
  fi
  if [ -n "${KEY_STORE_PASSWORD}" ]; then
    echo "[SIGNING] KEY_STORE_PASSWORD: SET (length=${#KEY_STORE_PASSWORD})"
  else
    echo "[SIGNING] KEY_STORE_PASSWORD: NOT SET"
  fi
fi
echo "------------------------------------------------------------"
if [ ! -f "${KEYSTORE_FILE}" ]; then
  echo "[ERROR] Keystore NOT FOUND at: ${KEYSTORE_FILE}"
  exit 1
fi
KEYSTORE_SIZE=$(du -h "${KEYSTORE_FILE}" | cut -f1)
echo "[SIGNING] Keystore FOUND: ${KEYSTORE_FILE} (${KEYSTORE_SIZE})"
echo "------------------------------------------------------------"
echo "[CMD] fastlane ${FASTLANE_AAB_LANE} flavor:gms"
echo "[CMD] Gradle signingConfig will read env vars for ${AAB_ENVIRONMENT}"
echo "============================================================"

# ====== Build ======
cd "${CI_PROJECT_DIR}"

# ====== GRADLE MEMORY CONFIG (INYECTADO EN RUNTIME) ======
# Con concurrent=2 y 30 GB RAM, cada job tiene ~13 GB disponibles.
# Cap a 4 workers: 4 workers × ~1.5 GB + 6 GB heap = ~12 GB por job.
CORES=$(nproc)
WORKERS=$((CORES > 4 ? 4 : CORES))

# Inyectar configuración de memoria en gradle.properties (existe en raíz del proyecto)
GRADLE_PROPS="${CI_PROJECT_DIR}/gradle.properties"

if [ -f "${GRADLE_PROPS}" ]; then
  echo "[INFO] gradle.properties encontrado, sobreescribiendo jvmargs..."
  sed -i 's/^org\.gradle\.jvmargs=.*/org.gradle.jvmargs=-Xmx6144m -XX:MaxMetaspaceSize=1g -Dfile.encoding=UTF-8/' "${GRADLE_PROPS}"
  # Asegurar newline al final del archivo antes de agregar propiedades
  sed -i -e '$a\' "${GRADLE_PROPS}"
else
  echo "[INFO] gradle.properties no encontrado, creando..."
  touch "${GRADLE_PROPS}"
  echo "org.gradle.jvmargs=-Xmx6144m -XX:MaxMetaspaceSize=1g -Dfile.encoding=UTF-8" >> "${GRADLE_PROPS}"
fi

# Agregar workers y daemon si no existen
grep -q "^org.gradle.workers.max" "${GRADLE_PROPS}" && \
  sed -i "s/^org\.gradle\.workers\.max=.*/org.gradle.workers.max=${WORKERS}/" "${GRADLE_PROPS}" || \
  echo "org.gradle.workers.max=${WORKERS}" >> "${GRADLE_PROPS}"

grep -q "^org.gradle.daemon" "${GRADLE_PROPS}" && \
  sed -i "s/^org\.gradle\.daemon=.*/org.gradle.daemon=false/" "${GRADLE_PROPS}" || \
  echo "org.gradle.daemon=false" >> "${GRADLE_PROPS}"

# Inyectar credenciales del wrapper (reemplaza la necesidad de GRADLE_OPTS en CI)
grep -q "^systemProp.gradle.wrapperUser" "${GRADLE_PROPS}" && \
  sed -i "s/^systemProp\.gradle\.wrapperUser=.*/systemProp.gradle.wrapperUser=${ANDROID_ARTIFACT_PULL_USER}/" "${GRADLE_PROPS}" || \
  echo "systemProp.gradle.wrapperUser=${ANDROID_ARTIFACT_PULL_USER}" >> "${GRADLE_PROPS}"

grep -q "^systemProp.gradle.wrapperPassword" "${GRADLE_PROPS}" && \
  sed -i "s/^systemProp\.gradle\.wrapperPassword=.*/systemProp.gradle.wrapperPassword=${ANDROID_ARTIFACT_PULL_USER_TOKEN}/" "${GRADLE_PROPS}" || \
  echo "systemProp.gradle.wrapperPassword=${ANDROID_ARTIFACT_PULL_USER_TOKEN}" >> "${GRADLE_PROPS}"

# GRADLE_OPTS ya no es necesario - toda la config está en gradle.properties
export GRADLE_OPTS=""

echo "============================================================"
echo "[INFO] VALIDACIÓN gradle.properties (contenido final):"
echo "------------------------------------------------------------"
cat "${GRADLE_PROPS}"
echo "------------------------------------------------------------"
echo "[INFO] - Xmx: 6144m"
echo "[INFO] - MaxMetaspaceSize: 1g"
echo "[INFO] - workers: ${WORKERS}"
echo "[INFO] - daemon: false"
echo "[INFO] - wrapperUser: ${ANDROID_ARTIFACT_PULL_USER}"
echo "[INFO] - wrapperPassword: ****"
echo "[INFO] GRADLE_OPTS: '${GRADLE_OPTS}' (vacío, toda la config está en gradle.properties)"
echo "============================================================"

# Patch: Google Play rejects debuggable AABs. Ensure quality buildType has debuggable false.
APP_GRADLE="${CI_PROJECT_DIR}/app/build.gradle"
if grep -A3 'quality {' "${APP_GRADLE}" | grep -q 'debuggable true'; then
  echo "[PATCH] Setting debuggable false for quality buildType"
  sed -i '/quality\s*{/,/}/ s/debuggable true/debuggable false/' "${APP_GRADLE}"
  echo "[PATCH] Applied successfully"
fi

fastlane "${FASTLANE_AAB_LANE}" flavor:"gms"

# ====== Sign AAB post-build (DISABLED - testing signingConfigs.quality from project) ======
# While build.gradle doesn't have signingConfigs.quality merged,
# Gradle generates unsigned AAB. Sign it explicitly with jarsigner.
# echo "============================================================"
# echo "[SIGNING] Signing generated AAB with jarsigner (post-build)"
# echo "------------------------------------------------------------"
#
# AAB_TO_SIGN=$(find "${CI_PROJECT_DIR}/app/build/outputs/bundle" -name "*.aab" -type f | head -1)
#
# if [ -z "${AAB_TO_SIGN}" ]; then
#   echo "[ERROR] No AAB found to sign"
#   exit 1
# fi
#
# echo "[SIGNING] AAB: ${AAB_TO_SIGN}"
#
# # Remove existing signature (Gradle may have signed with debug keystore)
# zip -d "${AAB_TO_SIGN}" 'META-INF/*.SF' 'META-INF/*.RSA' 'META-INF/*.DSA' 'META-INF/MANIFEST.MF' 2>/dev/null || true
# echo "[SIGNING] Removed any existing signatures"
#
# if [ "${AAB_ENVIRONMENT}" == "quality" ]; then
#   SIGN_KEYSTORE="${QUALITY_KEY_STORE_PATH}"
#   SIGN_STOREPASS="${QUALITY_KEY_STORE_PASSWORD}"
#   SIGN_KEYPASS="${QUALITY_KEY_PASSWORD}"
#   SIGN_ALIAS="${QUALITY_KEY_ALIAS}"
# else
#   SIGN_KEYSTORE="${KEY_STORE_PATH}"
#   SIGN_STOREPASS="${KEY_STORE_PASSWORD}"
#   SIGN_KEYPASS="${KEY_PASSWORD}"
#   SIGN_ALIAS="${KEY_ALIAS}"
# fi
#
# jarsigner -verbose \
#   -sigalg SHA256withRSA \
#   -digestalg SHA-256 \
#   -keystore "${SIGN_KEYSTORE}" \
#   -storepass "${SIGN_STOREPASS}" \
#   -keypass "${SIGN_KEYPASS}" \
#   "${AAB_TO_SIGN}" \
#   "${SIGN_ALIAS}"
# if [ $? -ne 0 ]; then
#   echo "[ERROR] jarsigner failed"
#   exit 1
# fi
# echo "[SIGNING] AAB signed successfully"
# echo "============================================================"

# ====== Locate and rename AAB ======
echo "[INFO] Locating generated AABs"
mkdir -p "${RELEASE_PATH}"

PIPELINE_ID="${CI_PIPELINE_ID:-123456}"
AAB_COUNT=0

while IFS= read -r -d '' AAB_FILE; do
  AAB_COUNT=$((AAB_COUNT + 1))
  BASENAME=$(basename "${AAB_FILE}" .aab)

  if echo "${BASENAME}" | grep -q "protected"; then
    AAB_NAME="cl-android-superapp-gms-${AAB_ENVIRONMENT}-${VERSION_NAME:-0.0.0}-${VERSION_CODE:-1}-pipeline-${PIPELINE_ID}-protected.aab"
  else
    AAB_NAME="cl-android-superapp-gms-${AAB_ENVIRONMENT}-${VERSION_NAME:-0.0.0}-${VERSION_CODE:-1}-pipeline-${PIPELINE_ID}.aab"
  fi

  mv -f "${AAB_FILE}" "${RELEASE_PATH}/${AAB_NAME}"
  echo "[INFO] Moved: ${AAB_NAME}"
done < <(find "${CI_PROJECT_DIR}/app/build/outputs/bundle" -name "*.aab" -type f -print0)

if [ "${AAB_COUNT}" -eq 0 ]; then
  echo "[ERROR] No AAB found after Fastlane build"
  find "${CI_PROJECT_DIR}/app/build/outputs" -type f || true
  exit 1
fi

# ====== Artifact details ======
echo "============================================================"
echo "[INFO] ARTIFACT DETAILS (${AAB_COUNT} AABs generated)"
ls -lh "${RELEASE_PATH}"/*.aab
echo "============================================================"

# ====== Signature verification (informative, non-blocking) ======
echo "============================================================"
echo "[VERIFY] Verifying AAB signature integrity"
echo "------------------------------------------------------------"

for AAB_PATH in "${RELEASE_PATH}"/*.aab; do
  AAB_BASENAME=$(basename "${AAB_PATH}")
  echo "[VERIFY] Checking: ${AAB_BASENAME}"
  echo "[VERIFY] Size: $(du -h "${AAB_PATH}" | cut -f1)"
  echo "[VERIFY] MD5:  $(md5sum "${AAB_PATH}" | cut -d' ' -f1)"

  if command -v jarsigner &>/dev/null; then
    VERIFY_RESULT=$(jarsigner -verify "${AAB_PATH}" 2>&1)

    if echo "${VERIFY_RESULT}" | grep -q "jar verified"; then
      echo "[VERIFY] jarsigner: SIGNED OK"

      # Extraer info del certificado de firma
      CERT_INFO=$(jarsigner -verify -verbose -certs "${AAB_PATH}" 2>&1)
      SIGNER_DN=$(echo "${CERT_INFO}" | grep "CN=" | head -1 | sed 's/.*\[//' | sed 's/\].*//' || true)
      SIG_ALG=$(echo "${CERT_INFO}" | grep -i "Signature algorithm" | head -1 | awk -F: '{print $2}' | xargs || true)
      DIGEST_ALG=$(echo "${CERT_INFO}" | grep -i "Digest algorithm" | head -1 | awk -F: '{print $2}' | xargs || true)

      echo "[VERIFY] Signer DN: ${SIGNER_DN}"
      [ -n "${SIG_ALG}" ] && echo "[VERIFY] Signature algorithm: ${SIG_ALG}"
      [ -n "${DIGEST_ALG}" ] && echo "[VERIFY] Digest algorithm: ${DIGEST_ALG}"

      # Extraer fingerprints SHA-1 y SHA-256 del certificado dentro del AAB
      if command -v keytool &>/dev/null; then
        # Extraer el certificado del AAB firmado
        CERT_FILE=$(unzip -l "${AAB_PATH}" 2>/dev/null | grep -oE 'META-INF/.*\.(RSA|DSA|EC)' | head -1 || true)
        if [ -n "${CERT_FILE}" ]; then
          TEMP_CERT="/tmp/aab_cert_$$"
          unzip -o -q "${AAB_PATH}" "${CERT_FILE}" -d "${TEMP_CERT}" 2>/dev/null || true
          if [ -f "${TEMP_CERT}/${CERT_FILE}" ]; then
            KEYTOOL_OUTPUT=$(keytool -printcert -file "${TEMP_CERT}/${CERT_FILE}" 2>/dev/null || true)
            SHA1=$(echo "${KEYTOOL_OUTPUT}" | grep -i "SHA1:" | awk -F: '{print $2":"$3":"$4":"$5":"$6":"$7":"$8":"$9":"$10":"$11":"$12":"$13":"$14":"$15":"$16":"$17":"$18":"$19":"$20":"$21}' | sed 's/^[[:space:]]*//' | cut -c1-59 || true)
            SHA256=$(echo "${KEYTOOL_OUTPUT}" | grep -i "SHA256:" | awk '{$1=""; print $0}' | sed 's/^[[:space:]]*//' || true)
            VALID_FROM=$(echo "${KEYTOOL_OUTPUT}" | grep -i "Valid from" | head -1 || true)

            [ -n "${SHA1}" ] && echo "[VERIFY] SHA-1:   ${SHA1}"
            [ -n "${SHA256}" ] && echo "[VERIFY] SHA-256: ${SHA256}"
            [ -n "${VALID_FROM}" ] && echo "[VERIFY] ${VALID_FROM}"
          fi
          rm -rf "${TEMP_CERT}"
        fi
      fi
    else
      echo "[VERIFY] jarsigner: NOT SIGNED or INVALID"
      echo "[VERIFY] Result: ${VERIFY_RESULT}"
    fi
  else
    echo "[VERIFY] jarsigner not available, skipping signature check"
  fi

  echo "------------------------------------------------------------"
done

echo "[VERIFY] Verification complete"
echo "============================================================"

echo "fastlane_build_aab.sh finished OK"
