import gitlab, os, re

import base64, argparse

import urllib.parse
import boto3

import json, subprocess

from dotenv import set_key
from pathlib import Path

class Gitlab:
	def __init__(self, url, token):
		# Connect to GitLab
		self.gl = gitlab.Gitlab(url, private_token=token)

	def get_group_by_project_id(self, project_id):
		try:
			project = self.gl.projects.get(project_id)
			group_id = str(project.namespace['id'])
			group = self.gl.groups.get(group_id)
			return group
		except gitlab.exceptions.GitlabGetError as e:
			print(f"Error getting the group by project: {e}")
			exit(1)

	def get_package_list(self, package_name, package_version, package_repository):
		try:
			project = None
			if package_repository:
				project = self.gl.projects.get(package_repository)

			package_res = None
			if package_name:
				package_res = project.packages.list(package_version=package_version, package_name=package_name)
			else:
				package_res = project.packages.list(package_version=package_version)

			return project, package_res
		except gitlab.exceptions.GitlabGetError as e:
			print(f"Error getting package files: {e}")
			exit(1)

	def get_project_raw_file(self, source_repository, path, branch, target):
		try:
			project = self.gl.projects.get(source_repository)

			Path(os.path.dirname(target)).mkdir(parents=True, exist_ok=True)

			with open(target, 'wb') as f:
				project.files.raw(file_path=path, ref=branch, streamed=True, action=f.write)
		except gitlab.exceptions.GitlabGetError as e:
			print(f"Error getting raw file: {e}")
			exit(1)

	def download_files_from_package(self, project, package, output_folder):
		if output_folder and output_folder != "":
			for pkg in package.package_files.list():
				if package.package_type == 'maven':
					# maven_package_url=urllib.parse.quote_plus(f"")
					path=f"/projects/{project.id}/packages/maven/{package.name}/{package.version}/{pkg.file_name}"
					response = self.gl.http_request(
						verb="GET",
						path=path)
					file = response.content
					Utils.write_binary_file(f"{output_folder}/{pkg.file_name}", file)
				elif package.package_type == 'generic':
					file = project.generic_packages.download(
						package_name=package.name,
						package_version=package.version,
						file_name=pkg.file_name
					)

					Utils.write_binary_file(f"{output_folder}/{pkg.file_name}", file)
				else:
					print("Package is not a 'maven' or 'generic' type.")
		else:
			print("No output folder defined.")

	def post_comment(self, project_id, merge_request_id, message):
		if self.gl == None:
			raise Exception("API not connected. Use connect() to initialize connection.")

		# Get the project object
		project = self.gl.projects.get(project_id)

		# Get the merge request
		merge_request = project.mergerequests.get(merge_request_id)

		# Add the message
		mr_note = merge_request.notes.create({'body': message})

class AWS:
	def extract_type_region_account_id_from_arn(arn):
		match = re.search(r"arn:aws:(.+):(.*):(\d+):.+", arn)

		if match:
			arn_type = match.group(1)
			arn_region = match.group(2)
			arn_account_id = match.group(3)

			return arn_type, arn_region, arn_account_id
		else:
			return None, None, None

	def read_arn_secret(secret_arn, role_arn, decode_base64 = False, json_key = ""):
		# client = boto3.client("secretsmanager")

		_, _, arn_account_id = AWS.extract_type_region_account_id_from_arn(secret_arn)

		session = boto3.Session()
		sts_client = session.client('sts')
		if arn_account_id is not None:
			response = sts_client.assume_role(
				RoleArn=f"arn:aws:iam::{arn_account_id}:role/itau-sts-terraform",
				RoleSessionName='AssumeRoleSession'
			)
		else:
			response = sts_client.assume_role(
				RoleArn=role_arn,
				RoleSessionName='AssumeRoleSession'
			)
		credentials = response['Credentials']
		assumed_session = boto3.Session(
			aws_access_key_id=credentials['AccessKeyId'],
			aws_secret_access_key=credentials['SecretAccessKey'],
			aws_session_token=credentials['SessionToken']
		)
		assumed_secretsmanager_client = assumed_session.client('secretsmanager')

		try:
			response = assumed_secretsmanager_client.get_secret_value(SecretId=secret_arn)
		except Exception as e:
			print(f"Errr retrieving secret: {e}")
			raise

		is_binary = True
		if 'SecretString' in response:
			secret = response['SecretString']

			if json_key != "":
				json_value = Utils.get_json_value(secret, json_key)
				if json_value is not None:
					secret = json_value

			if decode_base64:
				secret = Utils.clean_header_footer_base64(secret)
				decoded = Utils.decode_base64(secret)

			if decode_base64 and decoded is not None:
				return decoded, True
			else:
				is_binary = False
		else:
			secret = response['SecretBinary'].decode('utf-8')

		return secret, is_binary

class Utils:
	def run_cmd_masking_values(cmd, mask_data=[]):
		process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		result, error = process.communicate()
		result = result.decode("utf-8")
		error = error.decode("utf-8")

		for data in mask_data:
			result = result.replace(data, "[MASKED]")
			error = error.replace(data, "[MASKED]")

		return process, result, error

	def get_env_value(key):
		value = os.environ.get(key, "").strip("\n").strip("\r")

		if value.startswith("%") and value.endswith("%"):
			keyref = value.strip("%")
			valref = os.environ.get(keyref, "").strip("\n").strip("\r")
			if valref != "":
				value = valref
		return value

	def get_file_path_from_cwd(path:str):
		return os.path.normpath(os.path.join(os.getcwd(), path))

	def remove_suffix(input_string, suffix):
		if suffix and input_string.endswith(suffix):
			return input_string[:-len(suffix)]
		return input_string

	def get_env_vars():
		return os.environ.items()

	def clean_header_footer_base64(val):
		# Remove headers & footer lines (---- CERT OR PRIVAKE KEY ----) 
		val = val.replace("\n", " ")
		match = re.search(r"-+[\w ]+-+ (.*) -+[\w ]+-+", val)

		if match:
			return match.group(1).replace(" ", "")
		else:
			return val.replace(" ", "")

	def write_binary_file(path, file):
		os.makedirs(os.path.dirname(path), exist_ok=True)
		with open(path, "wb") as binary_file:
			# Write bytes to file
			binary_file.write(file)

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

	def get_json_value(json_string, key):
		try:
			data = json.loads(json_string)
			if key in data:
				return data[key]
			else:
				return None
		except json.JSONDecodeError:
			return None

	def fill_env_file(file_name, collection):
		# Save as build.env
		env_file_path = Path(file_name)
		env_file_path.touch(mode=0o600, exist_ok=True)

		for env_key in collection:
			env_val = collection[env_key]
			set_key(dotenv_path=env_file_path, key_to_set=env_key, value_to_set=env_val)

	def decode_base64(str):
		try:
			str = str.replace("\n", "").replace(" ", "")
			base64.standard_b64decode(str)
			print("[INFO!] Value of string is base64 encoded. Decoding.")
			decode = base64.standard_b64decode(str)
			print("[INFO!] Decoded")
			return decode
		except Exception:
			print("[WARN!] Value of string is not base64 encoded.")
			return None

	def decode_base64_cmd(string):
		try:
			print("[INFO!] Value of string is base64 encoded. Decoding.")
			string = string.replace("\n", "").replace(" ", "")
			echo = subprocess.Popen(("echo", string), stdout=subprocess.PIPE)
			result = subprocess.check_output(("base64", "--decode"), stdin=echo.stdout)
			echo.wait()

			return result
		except Exception:
			print("[WARN!] Value of string is not base64 encoded.")
			return None

	def str2bool(v):
		if isinstance(v, bool):
			return v
		if v is None or v == "":
			return False
		elif v.lower() in ('yes', 'true', 't', 'y', '1'):
			return True
		elif v.lower() in ('no', 'false', 'f', 'n', '0'):
			return False
		else:
			return argparse.ArgumentTypeError("Boolean value expected")

	def is_valid_command_parameter(value):
		# Validate is string is alphanumerical
		# and contains only these special characters: .:-_
		# Note:
		# && can be used as a hack to execute other commands.
		# The idea is to not allow that.
		pattern = r'^[a-zA-Z0-9\.\:\_\-]*$'
		return bool(re.match(pattern, value))

	def validate_command(lst):
		if not isinstance(lst, list):
			if not Utils.is_valid_command_parameter(lst):
				return False
			return True
		elif isinstance(lst, list) and not isinstance(lst[0], list):
			valid = True
			for value in lst[1:]:
				valid = valid and Utils.validate_command(value)
			return valid
		else:
			valid = True
			for value in lst:
				valid = valid and Utils.validate_command(value)
			return valid