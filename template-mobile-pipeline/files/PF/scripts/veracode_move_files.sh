#!/bin/bash

VERACODE_EXPR_PREFIX=app
VERACODE_EXPR_SUFFIX=latest
VERACODE_DIR="${VERACODE_DIR_NAME}"
PROJECT_DIR="${CI_PROJECT_DIR}"

echo "Find built APK artifacts (quality or production only, excluding development and protected)"
androidPath=$(find "${RELEASE_PATH:-${CI_PROJECT_DIR}}" -name "*.apk" ! -name "*protected*" ! -name "*development*")

echo "androidPath: ${androidPath}"
echo "VERACODE_DIR: ${VERACODE_DIR}"
echo "PROJECT_DIR: ${PROJECT_DIR}"

if [[ -z ${androidPath} ]]; then
	echo "No APK artifacts found, skipping"
	exit 1
else
	gms_apk_name="${VERACODE_EXPR_PREFIX}_gms_${VERACODE_EXPR_SUFFIX}"
	hms_apk_name="${VERACODE_EXPR_PREFIX}_hms_${VERACODE_EXPR_SUFFIX}"

	mkdir -p "${PROJECT_DIR}/${VERACODE_DIR}"
	for i in $androidPath; do
		dest_path="."
		filename=$(echo "${i##*/}")
		[[ $i =~ ^.*gms.*$ ]] && echo "CI_ARTIFACT_ANDROID_GMS_APK=${filename}" >> "${PROJECT_DIR}/build.env" && dest_path="${CI_PROJECT_DIR}/${VERACODE_DIR}/${gms_apk_name}.apk"
		[[ $i =~ ^.*hms.*$ ]] && echo "CI_ARTIFACT_ANDROID_HMS_APK=${filename}" >> "${PROJECT_DIR}/build.env" && dest_path="${CI_PROJECT_DIR}/${VERACODE_DIR}/${hms_apk_name}.apk"
		echo "Moving ${i} to '${dest_path}'"
		mv $i $dest_path
	done
fi
