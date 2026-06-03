from dotenv import set_key
from pathlib import Path

from utils import AWS, Utils
from environment import VariableType

ENV_FILE_NAME="secrets.env"

if __name__ == "__main__":
	role_arn = Utils.get_env_value("AWS_SECRET_ROLE_ARN")
	environment = Utils.get_env_value("ENVIRONMENT")
	environment_suffix = Utils.get_env_value("ENVIRONMENT_SUFFIX")

	if not role_arn:
		print("No role ARN provided in the ROLE_ARN environment variable.")
		exit(1)

	if not environment:
		print("No value provided in the ENVIRONMENT variable.")
		exit(1)

	if not environment_suffix:
		print("No value provided in the ENVIRONMENT_SUFFIX variable.")
		exit(1)

	# Read all environment variables and search by ${VAR}_TYPE
	env_vars = Utils.get_env_vars()

	# Filter all variables that are type: secret
	type_vars = [
		key for key, value in env_vars
			if key.endswith("_TYPE")
			and not key.startswith("PIPELINE")
			and value == VariableType.SECRET
	]

	for t in type_vars:
		# Retrieve all environment definitions for that secret
		# var_name = t.removesuffix("_TYPE")
		var_name = Utils.remove_suffix(t, "_TYPE")
		environment_var_name = [value for key, value in env_vars if key == f"{var_name}_NAME"]

		# Skip if it doesn't have a env var _NAME
		if len(environment_var_name) == 0:
			print(f"[WARN!] No '_NAME' environmenT varariable suffix has been found from environment variable set {var_name}.")
			continue

		environment_var_data = f"{environment_var_name[0]}"
		print(f"[INFO!] Retriving data from secret {environment_var_data}")

		environment_var_data_suffix = f"{environment_var_data}{environment_suffix}"

		if Utils.get_env_value(f"{environment_var_data_suffix}_VALUE") is not None:
			arn = Utils.get_env_value(f"{environment_var_data_suffix}_VALUE")
			base64 = Utils.str2bool(Utils.get_env_value(f"{environment_var_data_suffix}_BASE64"))
			target = Utils.get_env_value(f"{environment_var_data_suffix}_TARGET")
			the_key = Utils.get_env_value(f"{environment_var_data_suffix}_KEY")
		elif Utils.get_env_value(f"{environment_var_data}_VALUE") is not None:
			arn = Utils.get_env_value(f"{environment_var_data}_VALUE")
			base64 = Utils.str2bool(Utils.get_env_value(f"{environment_var_data}_BASE64"))
			target = bool(Utils.get_env_value(f"{environment_var_data}_TARGET"))
			the_key = Utils.get_env_value(f"{environment_var_data_suffix}_KEY")
		else:
			print(f"[WARN!] environment variable {var_name} defined incorrectly for secret retrieval.")
			continue

		secret_value, is_binary = AWS.read_arn_secret(arn, role_arn, base64, the_key)

		if is_binary:
			if target != "":
				print(f"[INFO!] Found secret as file, Saving in path {target}")
				Utils.write_binary_file(target, secret_value)
			else:
				print("[WARN!] Cannot save binary secret. No target was defined or it's empty.")
		else:
			print("[INFO!] Found secret as string, Saving in env file")
			# Save as build.env
			env_file_path = Path(ENV_FILE_NAME)
			env_file_path.touch(mode=0o600, exist_ok=True)

			set_key(dotenv_path=env_file_path, key_to_set=environment_var_data, value_to_set=secret_value)

			# Clear .env file to skip simple quotes.
			Utils.clear_env_file(str(env_file_path))
