import argparse
import xml.etree.ElementTree as ET

from dotenv import set_key
from pathlib import Path

from utils import Utils

def obtener_nombre_proyecto(pom_path):
	pom_output = {}
	try:
		tree = ET.parse(pom_path)
		root = tree.getroot()

		ns = {'xmlns': 'http://maven.apache.org/POM/4.0.0'}
		pom_output.update({'groupId': root.find('xmlns:groupId', ns).text})
		pom_output.update({'artifactId': root.find('xmlns:artifactId', ns).text})
		pom_output.update({'version': root.find('xmlns:version', ns).text})
		pom_output.update({'name': root.find('xmlns:name', ns).text})

		return pom_output
	except FileNotFoundError:
		print(f"Error: Cannot find file pom file on path {pom_path}")
	except ET.ParseError:
		print(f"Error: Cannot analyze pom structure. Check the file.")
	return None

def get_url_name(pom_data:dict, include_version:bool=False):
	prefix = f"{pom_data.get('groupId').replace('.', '/')}/{pom_data.get('artifactId')}"
	if include_version:
		return f"{prefix}/{pom_data.get('version')}"
	return prefix

if __name__ == "__main__":
	# Initialize parser
	parser = argparse.ArgumentParser()

	# Adding optional argument
	parser.add_argument("-p", "--pom_path", help = "POM path location")
	parser.add_argument("-o", "--output", help = "Output file name")
	parser.add_argument("-i", "--index", default="", help = "Set index for output")

	# Read arguments from command line
	args = parser.parse_args()
	nombre_proyecto = obtener_nombre_proyecto(args.pom_path)
	if nombre_proyecto:
		print(nombre_proyecto)
		print(nombre_proyecto.get("name"))
	else:
		nombre_proyecto=""

	# Save as build.env
	env_file_path = Path(args.output)
	env_file_path.touch(mode=0o600, exist_ok=True)

	set_key(dotenv_path=env_file_path, key_to_set=f"OUTPUT_APP_NAME{args.output}", value_to_set=nombre_proyecto.get("artifactId"))
	set_key(dotenv_path=env_file_path, key_to_set=f"POM_GROUP_ID{args.output}", value_to_set=nombre_proyecto.get("groupId"))
	set_key(dotenv_path=env_file_path, key_to_set=f"POM_ARTIFACT_ID{args.output}", value_to_set=nombre_proyecto.get("artifactId"))
	set_key(dotenv_path=env_file_path, key_to_set=f"POM_NAME{args.output}", value_to_set=nombre_proyecto.get("name"))
	set_key(dotenv_path=env_file_path, key_to_set=f"POM_VERSION{args.output}", value_to_set=nombre_proyecto.get("version"))
	set_key(dotenv_path=env_file_path, key_to_set=f"POM_RELEASE_PATH{args.output}", value_to_set=nombre_proyecto.get("name"))
	set_key(dotenv_path=env_file_path, key_to_set=f"ARTIFACT_URL{args.output}", value_to_set=get_url_name(nombre_proyecto))
	set_key(dotenv_path=env_file_path, key_to_set=f"ARTIFACT_URL_WITH_VERSION{args.output}", value_to_set=get_url_name(nombre_proyecto, True))

	# Clear .env file to skip simple quotes.
	Utils.clear_env_file(str(env_file_path))