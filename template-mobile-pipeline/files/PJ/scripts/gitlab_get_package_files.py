import argparse
import os

from dotenv import set_key
from pathlib import Path

from utils import Gitlab

# Initialize parser
parser = argparse.ArgumentParser()

# Adding optional argument
parser.add_argument("-u", "--url", help = "Gitlab instance URL")
parser.add_argument("-t", "--token", help = "Gitlab private token")
parser.add_argument("-o", "--output_folder", help = "Folder path to retrieve files")
parser.add_argument("-pkgn", "--package_name", help = "Gitlab Package Name")
parser.add_argument("-pkgv", "--package_version", help = "Gitlab Package Version")
parser.add_argument("-pkgp", "--package_project", help= "Gitlab Package from ProjectID")
parser.add_argument("-pkgr", "--package_repository", help= "Gitlab Package from Repository Name")

# Read arguments from command line
args = parser.parse_args()

# Accessing arguments
gitlab_url = args.url
gitlab_token = args.token
package_name = args.package_name
package_version = args.package_version
package_project = args.package_project
package_repository = args.package_repository
output_folder = args.output_folder

if not gitlab_url or not gitlab_token:
	print("Error: Missing arguments. Please provide GitLab URL and token.")
	exit(1)

# Connect to GitLab
gl = Gitlab(gitlab_url, gitlab_token)

project, package_list = gl.get_package_list(package_name, package_version, package_repository)

if len(package_list) > 0:
	result = package_list[0]
	gl.download_files_from_package(project, result, output_folder)
else:
	prnt=f"package_name='{package_name}', package_version='{package_version}', package_repository='{package_repository}'"
	print(f"No package definition found using {prnt}.")
	exit(1)