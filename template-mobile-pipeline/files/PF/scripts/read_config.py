import os
import yaml
from dotenv import set_key, find_dotenv
import argparse

def load_env_vars(yaml_path, env_path):
	env_vars = {
		"gradle": "7.5",  # Valor por defecto para gradle
		"temurin": "11"   # Valor por defecto para temurin
	}

	ci_data = {}  # <-- agregado para evitar referencia antes de asignar

	try:
		with open(yaml_path, 'r') as archivo:
			data = yaml.safe_load(archivo)
			if data and "ci" in data:
				ci_data = data["ci"]
			if "gradle" in ci_data and ci_data["gradle"]:
				env_vars["gradle"] = str(ci_data["gradle"])
			if "temurin" in ci_data and ci_data["temurin"]:
				env_vars["temurin"] = str(ci_data["temurin"])
	except FileNotFoundError:
		print(f"YAML file not found: {yaml_path}")
	except Exception as e:
		print(f"Error reading YAML file: {e}")

	# Guardar las variables en el archivo .env
	if not env_path:
		env_path = ".env"  # Usar .env por defecto si no se especifica

	set_key(env_path, "GRADLE_VERSION", env_vars["gradle"])
	set_key(env_path, "TEMURIN_VERSION", env_vars["temurin"])

	# <-- agregado: exportar todas las variables bajo ci.variables
	try:
		variables = ci_data.get("variables", {})
		if isinstance(variables, dict):
			for k, v in variables.items():
				set_key(env_path, str(k), str(v))
		elif variables:
			print("Advertencia: 'ci.variables' no es un dict; se ignora.")
	except Exception as e:
		print(f"Error procesando 'ci.variables': {e}")

def clear_env_file(path):
	with open(path, 'r') as f:
		lines = f.readlines()

	with open(path, 'w') as f:
		for line in lines:
			if '=' in line:
				key, val = line.strip().split('=', 1)
				# Detect if value contain spaces or not.
				if ' ' not in val and (val.startswith("'") and val.endswith("'")):
					val = val.strip("'")
				f.write(f"{key}={val}\n")
			else:
				f.write(line)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Create environment variables (.env) from YAML config")
	parser.add_argument("-c", "--config", help="YAML path to load", default="config.yaml")
	parser.add_argument("-e", "--env", help=".env path to save", default=".env")
	args = parser.parse_args()

	load_env_vars(args.config, args.env)
	clear_env_file(args.env)
	print(f"Environment variables saved in file {args.env}")