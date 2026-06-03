from environment import JarSignerConfig
from utils import Utils

import argparse
import subprocess

JARSIGNER_KEY = "PIPELINE_PROJECT_PUBLISH_JARSIGNER"

def execute_jarsigner(jarsigner: JarSignerConfig, apk_path:str):
	cmd = ["jarsigner"]
	if jarsigner.keypass != "": cmd.extend(["-keypass", jarsigner.keypass])
	if jarsigner.keystore != "": cmd.extend(["-keystore", jarsigner.keystore])
	if jarsigner.storepass != "": cmd.extend(["-storepass", jarsigner.storepass])
	if jarsigner.storetype != "": cmd.extend(["-storetype", jarsigner.storetype])
	cmd.append(apk_path)
	if jarsigner.alias != "": cmd.append(jarsigner.alias)

	try:
		subprocess.run(cmd, check=True)
		print(f"[INFO!] {apk_path} signed successfully")
	except Exception as e:
		print(f"[ERROR!] Error signing package")
		exit(1)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Sign the android package")
	parser.add_argument("path", help="Package file path")

	args = parser.parse_args()

	path = Utils.get_file_path_from_cwd(args.path)

	environment = Utils.get_env_value("ENVIRONMENT")
	environment_suffix = Utils.get_env_value("ENVIRONMENT_SUFFIX")

	if not environment:
		print("No value provided in the ENVIRONMENT variable.")
		exit(1)

	if not environment_suffix:
		print("No value provided in the ENVIRONMENT_SUFFIX variable.")
		exit(1)

	enabled = Utils.get_env_value(f"{JARSIGNER_KEY}_ENABLED{environment_suffix}")

	print(enabled)
	if Utils.str2bool(enabled):
		jarsigner = JarSignerConfig()
		jarsigner.enabled = enabled
		jarsigner.alias = Utils.get_env_value(f"{JARSIGNER_KEY}_ALIAS{environment_suffix}")
		jarsigner.keypass = Utils.get_env_value(f"{JARSIGNER_KEY}_KEYPASS{environment_suffix}")
		jarsigner.keystore = Utils.get_env_value(f"{JARSIGNER_KEY}_KEYSTORE{environment_suffix}")
		jarsigner.storepass = Utils.get_env_value(f"{JARSIGNER_KEY}_STOREPASS{environment_suffix}")
		jarsigner.storetype = Utils.get_env_value(f"{JARSIGNER_KEY}_STORETYPE{environment_suffix}")

		if jarsigner.keystore != "":
			jarsigner.keystore = Utils.get_file_path_from_cwd(jarsigner.keystore)

		execute_jarsigner(jarsigner, path)
	else:
		print("[WARN!] No Jarsigner configured in your ci/config.yaml file. Ignoring signing by Jarsineer.")