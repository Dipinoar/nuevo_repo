#!/bin/bash

set -Eeo pipefail
trap 'echo "[ERROR] $BASH_COMMAND (exit=$?)" >&2' ERR

echo "============================================================"
echo "[INFO] DEPLOY PROD AAB TO GOOGLE PLAY"
echo "[INFO] PRODUCTION_PACKAGE: ${PRODUCTION_PACKAGE:-NOT SET}"
echo "[INFO] INTERNAL_TRACK: ${INTERNAL_TRACK:-NOT SET}"
echo "[INFO] GOOGLE_PLAY_DRY_RUN: ${GOOGLE_PLAY_DRY_RUN:-false}"
echo "[INFO] RELEASE_PATH: ${RELEASE_PATH:-NOT SET}"
echo "============================================================"

# ====== Validar variables requeridas ======
if [ -z "${PRODUCTION_PACKAGE:-}" ]; then
	echo "[ERROR] PRODUCTION_PACKAGE is not set. Configure this CI/CD variable."
	exit 1
fi

if [ -z "${INTERNAL_TRACK:-}" ]; then
	echo "[ERROR] INTERNAL_TRACK is not set. Configure this CI/CD variable."
	exit 1
fi

if [ -z "${GOOGLE_PLAY_CREDENTIALS:-}" ]; then
	echo "[ERROR] GOOGLE_PLAY_CREDENTIALS is not set. Ensure .decode_google_play_credentials ran."
	exit 1
fi

if [ ! -f "${GOOGLE_PLAY_CREDENTIALS}" ]; then
	echo "[ERROR] Google Play credentials file not found at: ${GOOGLE_PLAY_CREDENTIALS}"
	exit 1
fi

# ====== Localizar AAB de PROD (protected) ======
echo "[INFO] Locating PROD AAB (protected) in ${RELEASE_PATH}"
AAB_FILE=$(find "${RELEASE_PATH}" -name "*gms*production*protected*.aab" -type f | head -1)

if [ -z "${AAB_FILE}" ]; then
	echo "[ERROR] No production AAB (protected) found in ${RELEASE_PATH}"
	echo "[INFO] Available files:"
	ls -lhR "${RELEASE_PATH}" || true
	exit 1
fi

echo "============================================================"
echo "[INFO] ARTIFACT DETAILS"
echo "[INFO] File: $(basename "${AAB_FILE}")"
echo "[INFO] Path: ${AAB_FILE}"
echo "[INFO] Size: $(du -h "${AAB_FILE}" | cut -f1)"
echo "[INFO] MD5:  $(md5sum "${AAB_FILE}" | cut -d' ' -f1)"
echo "============================================================"

# ====== Deploy a Google Play ======
cd "${CI_PROJECT_DIR}"

if [ "${GOOGLE_PLAY_DRY_RUN:-false}" == "true" ]; then
	echo "[INFO] DRY RUN enabled - validating only, no upload to Google Play"
	fastlane supply \
		--aab "${AAB_FILE}" \
		--package_name "${PRODUCTION_PACKAGE}" \
		--track "${INTERNAL_TRACK}" \
		--json_key "${GOOGLE_PLAY_CREDENTIALS}" \
		--skip_upload_metadata \
		--skip_upload_changelogs \
		--skip_upload_images \
		--skip_upload_screenshots \
		--validate_only
	echo "[INFO] Dry run completed - AAB is valid for Google Play"
else
	echo "[INFO] Uploading PROD AAB to Google Play (track: ${INTERNAL_TRACK})"
	fastlane supply \
		--aab "${AAB_FILE}" \
		--package_name "${PRODUCTION_PACKAGE}" \
		--track "${INTERNAL_TRACK}" \
		--json_key "${GOOGLE_PLAY_CREDENTIALS}" \
		--skip_upload_metadata \
		--skip_upload_changelogs \
		--skip_upload_images \
		--skip_upload_screenshots
	echo "[INFO] Successfully uploaded PROD AAB to Google Play (track: ${INTERNAL_TRACK})"
fi

echo "============================================================"
echo "[INFO] deploy_prod_aab_google_play.sh finished OK"
echo "============================================================"
