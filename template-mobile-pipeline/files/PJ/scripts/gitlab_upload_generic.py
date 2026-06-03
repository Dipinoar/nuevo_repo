import xml.etree.ElementTree as ET
import os
import requests
import argparse
import mimetypes

def upload_file(file_path, api_url, auth_type, token):
	try:
		# Get content-type of the file
		mimetypes.init()
		content_type = mimetypes.guess_type(file_path)[0]
		if content_type is None:
			content_type = "application/octet-stream"  # Default value

		# Upload the file to the API
		headers = {
			'Content-Type': content_type,
			f"{auth_type}": f"{token}"
		}

		with open(file_path, 'rb') as f:
			data = f.read()

		response = requests.put(api_url, headers=headers, data=data)

		# Verify the API response
		response.raise_for_status()
		print(f"File {os.path.basename(file_path)} uploaded successfully to {api_url}")

	except requests.exceptions.RequestException as e:
		print(f"Error uploading file {os.path.basename(file_path)} to API: {e}")


def upload_artifact(path, api_url, package_name, package_version, auth_type, token):
	try:
		# Validate the existence of the package file
		if not os.path.exists(path):
			raise FileNotFoundError(f"Package file not found: {path}")

		file_name = os.path.basename(path)

		upload_path = f"{package_name}/{package_version}"
		package_upload_path = f"{api_url}/{upload_path}/{file_name}"

		# Upload the package file
		package_path = path
		print(f"[INFO!] Uploading {package_path}")
		upload_file(package_path, package_upload_path, auth_type, token)
	except FileNotFoundError as e:
		print(e)


if __name__ == "__main__":
	# Set up the argument parser
	parser = argparse.ArgumentParser(description="Upload a generic app")
	parser.add_argument("-p", "--path", help="Path to the binary file")
	parser.add_argument("-u", "--api_url", help="Base API URL to upload the files")
	parser.add_argument("-v", "--version", help="Package Version")
	parser.add_argument("-n", "--name", help="Package Name")
	parser.add_argument("-a", "--auth_type", help="Authentication Type for the HTTP header")
	parser.add_argument("-t", "--token", help="Authentication token for the HTTP header")

	# Parse the arguments
	args = parser.parse_args()

	# Call the function with the parsed arguments
	print("[INFO!] Call upload function")
	upload_artifact(args.path, args.api_url, args.name, args.version, args.auth_type, args.token)