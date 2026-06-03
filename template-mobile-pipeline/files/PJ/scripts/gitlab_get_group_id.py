import argparse
import os

from dotenv import set_key
from pathlib import Path

from utils import Gitlab

# Initialize parser
parser = argparse.ArgumentParser()

# Adding optional argument
parser.add_argument("-u", "--url", help = "GitLab instance URL")
parser.add_argument("-t", "--token", help = "GitLab private token")
parser.add_argument("-p", "--project_id", help = "GitLab project ID", type=int)

# Read arguments from command line
args = parser.parse_args()

# Accessing arguments
gitlab_url = args.url
gitlab_token = args.token
project_id = args.project_id

if not gitlab_url or not gitlab_token or not project_id:
	print("Error: Missing arguments. Please provide GitLab URL, token, and project ID.")
	exit(1)

# Connect to GitLab
gl = Gitlab(gitlab_url, gitlab_token)

# Get the project object
group = gl.get_group_by_project_id(project_id)

# Get the group ID
group_id = group.id

print(f"{group_id}")