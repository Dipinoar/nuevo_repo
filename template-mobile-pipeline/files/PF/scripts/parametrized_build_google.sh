#!/bin/bash

set -eo pipefail

echo "============================================================"
echo "[INFO] SYSTEM MEMORY STATUS (before build)"
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

echo "EXPORTS completed"

# ====== Load build.env if exists ======
BUILD_ENV_PATH="${BUILD_ENV_PATH:-${CI_PROJECT_DIR:-.}/build.env}"
if [[ -f "${BUILD_ENV_PATH}" ]]; then
	echo "[INFO] Loading environment from ${BUILD_ENV_PATH}"
	set -a
	source "${BUILD_ENV_PATH}"
	set +a
else
	echo "[WARN] build.env not found at ${BUILD_ENV_PATH}. Relying on CI env variables."
fi

# ====== Inputs / Defaults ======
DEFAULT_SCRIPT_PATH="/home/jenkins/agent/workspace/cl-android-superapp/code/cl-android-superapp"
environmentParameter=""

# ====== Secrets / Keystore / DexGuard ======
export ANDROID_MAVEN_PULL_USER=${ANDROID_MAVEN_PULL_USER}
export ANDROID_MAVEN_PULL_USER_TOKEN=${ANDROID_MAVEN_PULL_USER_TOKEN}
export ANDROID_ARTIFACT_PULL_USER=${ANDROID_ARTIFACT_PULL_USER}
export ANDROID_ARTIFACT_PULL_USER_TOKEN=${ANDROID_ARTIFACT_PULL_USER_TOKEN}

export KEY_ALIAS=$1
export KEY_PASSWORD=$2
export KEY_STORE_PASSWORD=$3

export KEYSTORE_SOURCE="AWS Secrets Manager (via job 2.6 Retrieve Signing Keys)"
export DEXGUARD_LICENSE="${CI_PROJECT_DIR}/dexguard-license.txt"

# ====== Signing config per TARGET_BRANCH ======
case "${TARGET_BRANCH}" in
	production)
		export KEYSTORE_TYPE="RELEASE"
		export KEY_STORE_PATH="${CI_PROJECT_DIR}/release.keystore"
		;;
	quality)
		export KEYSTORE_TYPE="QUALITY"
		export QUALITY_KEY_STORE_PATH="${CI_PROJECT_DIR}/superAppHomologKey.keystore"
		export KEY_STORE_PATH="${QUALITY_KEY_STORE_PATH}"
		export KEY_ALIAS="${QUALITY_KEY_ALIAS}"
		export KEY_PASSWORD="${QUALITY_KEY_PASSWORD}"
		export KEY_STORE_PASSWORD="${QUALITY_KEY_STORE_PASSWORD}"
		;;
	*)
		export KEYSTORE_TYPE="DEBUG"
		export KEYSTORE_SOURCE="project (debug-keystore bundled in repo)"
		export KEY_STORE_PATH="${CI_PROJECT_DIR}/itau_debug.keystore"
		;;
esac

# ====== Signing validation ======
echo "============================================================"
echo "[SIGNING] Build target: ${TARGET_BRANCH}"
echo "[SIGNING] Keystore type: ${KEYSTORE_TYPE}"
echo "[SIGNING] Keystore source: ${KEYSTORE_SOURCE}"
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
echo "------------------------------------------------------------"
if [ ! -f "${KEY_STORE_PATH}" ]; then
	echo "[ERROR] Keystore NOT FOUND at: ${KEY_STORE_PATH}"
	echo "[ERROR] Release keystore must be retrieved from AWS Secrets Manager."
	echo "[ERROR] Ensure job '2.6 Retrieve Signing Keys' ran successfully"
	echo "[ERROR] and .prepare_release_keystore decoded RELEASE_KEYSTORE_B64."
	exit 1
fi
KEYSTORE_SIZE=$(du -h "${KEY_STORE_PATH}" | cut -f1)
echo "[SIGNING] Keystore FOUND: ${KEY_STORE_PATH} (${KEYSTORE_SIZE})"
echo "============================================================"

# ====== Working directory ======
ANDROID_PROJECT_PATH="${ANDROID_PROJECT_PATH:-$DEFAULT_SCRIPT_PATH}"
cd "${ANDROID_PROJECT_PATH}"

# ====== Locate app/build.gradle ======
APP_GRADLE_FILE=""
if [[ -f "./app/build.gradle" ]]; then
	APP_GRADLE_FILE="./app/build.gradle"
	echo "[INFO] Found ${APP_GRADLE_FILE}"
else
	echo "[WARN] app/build.gradle not found. BuildType auto-detection disabled."
fi

# ====== Detect buildTypes ======
BUILD_TYPE_MODE="classic"
if [[ -n "${APP_GRADLE_FILE}" ]]; then
	if grep -Eq '^\s*development\s*\{' "${APP_GRADLE_FILE}" && \
		grep -Eq '^\s*quality\s*\{' "${APP_GRADLE_FILE}" && \
		grep -Eq '^\s*production\s*\{' "${APP_GRADLE_FILE}"; then
		BUILD_TYPE_MODE="env"
	fi
fi
echo "[INFO] BuildType mode detected: ${BUILD_TYPE_MODE}"

export ANDROID_SDK_ROOT=${ANDROID_SDK_ROOT:-/usr/lib/android-sdk}
export EXEMPT_RUT_STORE="99000001"

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

# ====== Java / Gradle ======
echo "Java / Gradle versions:"
java -version || true

USE_WRAPPER=false
if [[ -x "./gradlew" ]]; then
	USE_WRAPPER=true
	chmod +x ./gradlew
	./gradlew --version || true
else
	if [[ -f /etc/profile.d/gradle.sh ]]; then
		source /etc/profile.d/gradle.sh || true
	fi
	gradle -v | head -n 10 || true
fi

# ====== Resolve desired GMS Gradle task ======
DESIRED_TASK=""

case "${TARGET_BRANCH}" in
	development)
		[[ "${BUILD_TYPE_MODE}" == "env" ]] && DESIRED_TASK="assembleGmsDevelopment" || DESIRED_TASK="assembleGmsDebug"
		;;
	quality)
		[[ "${BUILD_TYPE_MODE}" == "env" ]] && DESIRED_TASK="assembleGmsQuality" || DESIRED_TASK="assembleGmsHomolog"
		;;
	production)
		[[ "${BUILD_TYPE_MODE}" == "env" ]] && DESIRED_TASK="assembleGmsProduction" || DESIRED_TASK="assembleGmsRelease"
		;;
	*)
		[[ "${BUILD_TYPE_MODE}" == "env" ]] && DESIRED_TASK="assembleGmsDevelopment" || DESIRED_TASK="assembleGmsDebug"
		;;
esac

echo "[INFO] Desired Gradle task: ${DESIRED_TASK}"

# ====== Validate GMS Gradle task ======
echo "[INFO] Resolving available assembleGms tasks from Gradle..."
AVAILABLE_TASKS=$(./gradlew tasks --all --quiet | grep -oE 'assembleGms[A-Za-z]+' | sort -u || true)

echo "[INFO] Available tasks:"
echo "${AVAILABLE_TASKS}"

if echo "${AVAILABLE_TASKS}" | grep -qx "${DESIRED_TASK}"; then
	environmentParameter="${DESIRED_TASK}"
	echo "[INFO] Using task: ${environmentParameter}"
else
	echo "[WARN] Task ${DESIRED_TASK} not found. Trying fallback..."

	case "${DESIRED_TASK}" in
		assembleGmsDevelopment) FALLBACK_TASK="assembleGmsDebug" ;;
		assembleGmsQuality) FALLBACK_TASK="assembleGmsHomolog" ;;
		assembleGmsProduction) FALLBACK_TASK="assembleGmsRelease" ;;
		assembleGmsDebug) FALLBACK_TASK="assembleGmsDevelopment" ;;
		assembleGmsHomolog) FALLBACK_TASK="assembleGmsQuality" ;;
		assembleGmsRelease) FALLBACK_TASK="assembleGmsProduction" ;;
		*) FALLBACK_TASK="" ;;
	esac

	if [[ -n "${FALLBACK_TASK}" ]] && echo "${AVAILABLE_TASKS}" | grep -qx "${FALLBACK_TASK}"; then
		environmentParameter="${FALLBACK_TASK}"
		echo "[INFO] Using fallback task: ${environmentParameter}"
	else
		echo "[ERROR] No valid assembleGms task found"
		exit 1
	fi
fi

# ====== Helper ======
run_and_check() {
	local task="$1"
	local out="build.txt"

	if [[ "${USE_WRAPPER}" == "true" ]]; then
		./gradlew clean "${task}" \
			-PmavenUser="${ANDROID_MAVEN_PULL_USER}" \
			-PmavenPassword="${ANDROID_MAVEN_PULL_USER_TOKEN}" \
			-PRELEASE_STORE_FILE="${KEY_STORE_PATH}" \
			-PRELEASE_STORE_PASSWORD="${KEY_STORE_PASSWORD}" \
			-PRELEASE_KEY_ALIAS="${KEY_ALIAS}" \
			-PRELEASE_KEY_PASSWORD="${KEY_PASSWORD}" \
			--no-daemon \
			--stacktrace \
			--console=plain \
			--warning-mode=summary \
			> "${out}" 2>&1
	else
		gradle clean "${task}" \
			-PmavenUser="${ANDROID_MAVEN_PULL_USER}" \
			-PmavenPassword="${ANDROID_MAVEN_PULL_USER_TOKEN}" \
			-PRELEASE_STORE_FILE="${KEY_STORE_PATH}" \
			-PRELEASE_STORE_PASSWORD="${KEY_STORE_PASSWORD}" \
			-PRELEASE_KEY_ALIAS="${KEY_ALIAS}" \
			-PRELEASE_KEY_PASSWORD="${KEY_PASSWORD}" \
			--no-daemon \
			--stacktrace \
			--console=plain \
			--warning-mode=summary \
			> "${out}" 2>&1
	fi

	if grep -q "BUILD SUCCESSFUL" "${out}"; then
		echo "----------------"
		echo "APKs have been built (${task})"
		echo "----------------"
		tail -n 120 "${out}"
	else
		echo "----------------"
		echo "Build has failed (${task})"
		echo "----------------"
		cat "${out}"
		exit 1
	fi
}

# ====== Build ======
echo "------------------------------------------------------------"
echo "[CMD] Full Gradle command (passwords masked):"
if [[ "${USE_WRAPPER}" == "true" ]]; then
	echo "[CMD] ./gradlew clean ${environmentParameter} -PmavenUser=${ANDROID_MAVEN_PULL_USER} -PmavenPassword=*** --no-daemon --stacktrace"
else
	echo "[CMD] gradle clean ${environmentParameter} -PmavenUser=${ANDROID_MAVEN_PULL_USER} -PmavenPassword=*** --no-daemon --stacktrace"
fi
echo "[CMD] Signing with: KEY_STORE_PATH=${KEY_STORE_PATH} KEY_ALIAS=${KEY_ALIAS}"
echo "------------------------------------------------------------"
run_and_check "${environmentParameter}"

echo "parametrized_build_google.sh finished OK"
