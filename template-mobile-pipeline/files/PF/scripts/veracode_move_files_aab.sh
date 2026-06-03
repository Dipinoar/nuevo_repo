#!/bin/bash

VERACODE_EXPR_PREFIX=app
VERACODE_EXPR_SUFFIX=latest
VERACODE_DIR="${VERACODE_DIR_NAME}"
PROJECT_DIR="${CI_PROJECT_DIR}"

echo "Find built AAB artifacts (excluding protected)"
androidPath=$(find "${RELEASE_PATH:-${CI_PROJECT_DIR}}" -name "*.aab" ! -name "*protected*")

echo "androidPath: ${androidPath}"
echo "VERACODE_DIR: ${VERACODE_DIR}"
echo "PROJECT_DIR: ${PROJECT_DIR}"

if [[ -z ${androidPath} ]]; then
	echo "No AAB artifacts found, skipping"
	exit 1
else
	gms_aab_name="${VERACODE_EXPR_PREFIX}_gms_${VERACODE_EXPR_SUFFIX}"

	mkdir -p "${PROJECT_DIR}/${VERACODE_DIR}"
	for i in $androidPath; do
		dest_path="."
		filename=$(echo "${i##*/}")
		[[ $i =~ ^.*gms.*$ ]] && echo "CI_ARTIFACT_ANDROID_GMS_AAB=${filename}" >> "${PROJECT_DIR}/build.env" && dest_path="${CI_PROJECT_DIR}/${VERACODE_DIR}/${gms_aab_name}.aab"
		echo "Moving ${i} to '${dest_path}'"
		mv $i $dest_path
	done
fi
