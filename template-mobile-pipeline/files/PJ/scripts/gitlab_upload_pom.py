import xml.etree.ElementTree as ET
import os
import requests
import argparse
import mimetypes

def check_package_exists(api_url, auth_type, token, groupId, artifactId, version):
	"""Check if a package version already exists in the registry."""
	try:
		# Use the packages API to search for existing package
		# api_url format: http://gitlab.../api/v4/projects/{id}/packages/maven
		# We need the project packages API: replace /packages/maven with /packages
		packages_api = api_url.rsplit('/packages/maven', 1)[0] + '/packages'
		search_name = f"{groupId.replace('.', '/')}/{artifactId}"

		params = {
			'package_name': search_name,
			'package_version': version,
			'package_type': 'maven'
		}
		headers = {f"{auth_type}": f"{token}"}

		response = requests.get(packages_api, headers=headers, params=params)
		if response.status_code == 200:
			packages = response.json()
			matching = [p for p in packages if p.get('version') == version and p.get('name') == search_name]
			if matching:
				return True, matching[0].get('id')
		return False, None
	except Exception as e:
		print(f"[WARN] Error checking package existence: {e}")
		return False, None

def delete_package(api_url, auth_type, token, package_id):
	"""Delete an existing package by ID."""
	try:
		packages_api = api_url.rsplit('/packages/maven', 1)[0] + f'/packages/{package_id}'
		headers = {f"{auth_type}": f"{token}"}
		response = requests.delete(packages_api, headers=headers)
		if response.status_code in [200, 204]:
			print(f"[INFO] Deleted existing package (ID: {package_id})")
			return True
		else:
			print(f"[WARN] Failed to delete package (ID: {package_id}): HTTP {response.status_code}")
			return False
	except Exception as e:
		print(f"[WARN] Error deleting package: {e}")
		return False

def upload_file(file_path, api_url, auth_type, token):
	try:
		mimetypes.init()
		content_type = mimetypes.guess_type(file_path)[0]
		if content_type is None:
			content_type = "application/octet-stream"

		headers = {
			'Content-Type': content_type,
			f"{auth_type}": f"{token}"
		}

		with open(file_path, 'rb') as f:
			data = f.read()

		response = requests.put(api_url, headers=headers, data=data)
		response.raise_for_status()
		print(f"File {os.path.basename(file_path)} uploaded successfully to {api_url}")

	except requests.exceptions.RequestException as e:
		print(f"Error uploading file {os.path.basename(file_path)} to API: {e}")


def upload_artifact(pom_path, api_url, auth_type, token, replace_existing=False):
	try:
		print(f"[INFO!] Reading info from {pom_path}")
		tree = ET.parse(pom_path)
		root = tree.getroot()

		groupId = root.find('{http://maven.apache.org/POM/4.0.0}groupId').text
		artifactId = root.find('{http://maven.apache.org/POM/4.0.0}artifactId').text
		version = root.find('{http://maven.apache.org/POM/4.0.0}version').text
		packaging = root.find('{http://maven.apache.org/POM/4.0.0}packaging').text

		# Check if package already exists
		exists, package_id = check_package_exists(api_url, auth_type, token, groupId, artifactId, version)
		if exists:
			if replace_existing:
				print(f"[INFO] Package {groupId}:{artifactId}:{version} already exists. Replacing...")
				delete_package(api_url, auth_type, token, package_id)
			else:
				print(f"[WARN] Package {groupId}:{artifactId}:{version} already exists. Overwriting files...")

		package_file = f"{os.path.splitext(os.path.basename(pom_path))[0]}.{packaging}"

		if not os.path.exists(os.path.join(os.path.dirname(pom_path), package_file)):
			raise FileNotFoundError(f"Package file not found: {package_file}")

		upload_path = f"{groupId.replace('.', '/')}/{artifactId}/{version}"
		pom_upload_path = f"{api_url}/{upload_path}/{artifactId}-{version}.pom"
		package_upload_path = f"{api_url}/{upload_path}/{artifactId}-{version}.{packaging}"

		print(f"[INFO!] Uploading {pom_path}")
		upload_file(pom_path, pom_upload_path, auth_type, token)

		package_path = os.path.join(os.path.dirname(pom_path), package_file)
		print(f"[INFO!] Uploading {package_path}")
		upload_file(package_path, package_upload_path, auth_type, token)

	except ET.ParseError:
		print(f"Error parsing POM file: {pom_path}")
	except FileNotFoundError as e:
		print(e)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Upload an artifact to an API")
	parser.add_argument("-p", "--pom_path", help="Path to the POM file")
	parser.add_argument("-u", "--api_url", help="Base API URL to upload the files")
	parser.add_argument("-a", "--auth_type", help="Authentication Type for the HTTP header")
	parser.add_argument("-t", "--token", help="Authentication token for the HTTP header")
	parser.add_argument("-r", "--replace", action="store_true", default=False,
		help="Delete existing package before uploading (default: overwrite files)")

	args = parser.parse_args()

	print("[INFO!] Call upload function")
	upload_artifact(args.pom_path, args.api_url, args.auth_type, args.token, replace_existing=args.replace)