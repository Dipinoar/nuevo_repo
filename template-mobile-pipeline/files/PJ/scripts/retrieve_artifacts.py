from enumerables import ArtifactSourceType
from environment import Artifact

import os, re, requests, posixpath, argparse

from utils import Gitlab

ENV_PREFIX="PIPELINE_ARTIFACT_"
GITLAB_PATH=os.getenv("CI_SERVER_URL", "http://gitlab.itauchile.cl")
TOKEN_GITLAB=os.getenv("TOKEN_GITLAB")
MAVEN_LIBRARY_DIR=os.getenv("MAVEN_LIBRARY_DIR")

class EnvArtifact(Artifact):
	def __init__(self, dict):
		super().__init__(None, "", None)
		if dict is not None:
			for key, value in dict.items():
				if 'type' in key:
					self.source_type = ArtifactSourceType.to_enum(value)
				else:
					setattr(self, key, value)

def environment_variables_to_dict(variables):
	artifacts={}

	for key in variables:
		res = re.search(rf"^{ENV_PREFIX}([a-zA-Z]+)(\d)$", key)
		if res:
			arg = res.group(1)
			idx = res.group(2)
			val = variables[key]
			artifact = artifacts.get(idx)

			if artifact is None:
				artifact = {}
			artifact.update({arg.lower(): val})
			artifacts.update({idx: artifact})

	return dict(sorted(artifacts.items()))

def download_artifact(args, artifact: EnvArtifact):
	if artifact.source_type == ArtifactSourceType.JFROG:
		print(f"[WARN] JFROG source type is deprecated and will be ignored. Skipping artifact.")
		return
	if artifact.source_type == ArtifactSourceType.GITLAB_MAVEN:
		gl = Gitlab(GITLAB_PATH, TOKEN_GITLAB)
		if artifact.package is None or artifact.package == "":
			raise ValueError(f"download_artifact: package cannot be empty for gitlab-maven type")
		if artifact.version is None or artifact.version == "":
			raise ValueError(f"download_artifact: version cannot be empty for gitlab-maven type")

		project, package_list = gl.get_package_list(artifact.package, artifact.version, artifact.source)

		if len(package_list) > 0:
			for package in package_list:
				if package.name == artifact.package:
					package_dir = f"{MAVEN_LIBRARY_DIR}/{package.name}/{package.version}"
					gl.download_files_from_package(project, package, package_dir)
		else:
			raise ValueError(f"No package definition found using {artifact}.")
	elif artifact.source_type == ArtifactSourceType.GITLAB_GENERIC:
		print("Not implemented yet")
	elif artifact.source_type == ArtifactSourceType.GITLAB_FILE:
		if artifact.target is None or artifact.target == "":
			raise ValueError(f"download_artifact: target cannot be empty for gitlab-file type")
		if artifact.path is None or artifact.path == "":
			raise ValueError(f"download_artifact: path cannot be empty for gitlab-file type")
		if artifact.branch is None or artifact.branch == "":
			raise ValueError(f"download_artifact: branch cannot be empty for gitlab-file type")

		gl = Gitlab(GITLAB_PATH, TOKEN_GITLAB)
		gl.get_project_raw_file(artifact.source, artifact.path, artifact.branch, artifact.target)

if __name__ == "__main__":
	# -- Parsing Arguments --
	parser = argparse.ArgumentParser(description="Download Artifact")
	parser.add_argument("-d", "--dir", dest="directory", help="Local directory executing script")
	args = parser.parse_args()

	artifact_dict = environment_variables_to_dict(os.environ)
	for key in artifact_dict:
		artifact = EnvArtifact(artifact_dict[key])
		download_artifact(args, artifact)
