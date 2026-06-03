from enumerables import ProjectOS, ProjectType, VariableType, ArtifactSourceType, JavaJDKType, ProjectEnvironmentType
from enumerables import ValidIOSCompilationMethod, ValidAndroidCompilationMethod, ValidCertificateProfileRetrieveType

import typing, os, copy

class CertificateProfile:
	def __init__(self, retrieve_type: ValidCertificateProfileRetrieveType, source = "", command = "", password=""):
		self.retrieve_type = retrieve_type
		self.source = source
		self.command = command
		self.password = password

	def source_command_as_string(self):
		if self.retrieve_type == ValidCertificateProfileRetrieveType.FILES:
			return self.source
		elif self.retrieve_type == ValidCertificateProfileRetrieveType.COMMAND:
			output = []
			for s in self.command:
				output.append(' '.join(s))
			return ' && '.join(output)
		else:
			return ""

	def __str__(self):
		return f"CertificateProfile: {{retrieve_type: {self.retrieve_type}, source: {self.source}, command: {self.command}}}"

class JarSignerConfig:
	def __init__(self, enabled: bool = False, keystore: str = "", storetype: str = "", storepass: str = "", keypass: str = "", alias:str = ""):
		self.enabled = enabled
		self.keystore = keystore
		self.storetype = storetype
		self.storepass = storepass
		self.keypass = keypass
		self.alias = alias

	def __str__(self):
		return f"JarSignerConfig: {{enabled: {self.enabled}, keystore: {self.keystore}, storetype: {self.storetype}, storepass: {self.storepass}, keypass: {self.keypass}, alias: {self.alias}}}"

class Export:
	DEFAULT_PUBLISH_ANDROID_EXT = "aar"
	DEFAULT_PUBLISH_IOS_EXT = "ipa"
	DEFAULT_FOLDER_REF_ANDROID = "build/outputs"

	def __init__(self, output: str = "", command: list = None, pomgen: list = None, profile: CertificateProfile = None, certificate: CertificateProfile = None, jarsigner: JarSignerConfig = None, scan: list = None, folder_ref = None):
		self.enabled = True
		self.output = output
		self.command =  command or list()
		self.pomgen = pomgen or list()
		self.profile = profile
		self.certificate = certificate
		self.jarsigner = jarsigner
		self.folder_ref = folder_ref or list()
		self.scan = scan or list()

	def add_command(self, os: ProjectOS, value):
		if isinstance(value, str):
			value = [value]

		if isinstance(value, list) and len(value) > 0 and isinstance(value[0], list):
			# Array of arrays: join into sequential commands separated by &&
			commands = []
			for cmd in value:
				if isinstance(cmd, list) and len(cmd) > 0 and isinstance(cmd[0], str):
					if os == ProjectOS.ANDROID and ValidAndroidCompilationMethod.is_valid_method(cmd[0]):
						release = ValidAndroidCompilationMethod.to_enum(cmd[0])
						cmd[0] = release.get_instruction()
					elif os == ProjectOS.IOS and ValidIOSCompilationMethod.is_valid_method(cmd[0]):
						release = ValidIOSCompilationMethod.to_enum(cmd[0])
						cmd[0] = release.get_instruction()
					commands.append(' '.join(cmd))
			self.command = [' && '.join(commands)]
		elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], str):
			if os == ProjectOS.ANDROID and ValidAndroidCompilationMethod.is_valid_method(value[0]):
				release = ValidAndroidCompilationMethod.to_enum(value[0])
				value[0] = release.get_instruction()
				self.command = value
			elif os == ProjectOS.IOS and ValidIOSCompilationMethod.is_valid_method(value[0]):
				release = ValidIOSCompilationMethod.to_enum(value[0])
				value[0] = release.get_instruction()
				self.command = value
			else:
				raise ValueError(f"{type(self).__name__}.add_command: '{value[0]}' is not a valid operation in publish.release for {os}. Ignoring.")
		else:
			raise ValueError(f"{type(self).__name__}.add_command: command or release doesn't have a supported structure. Check the environment YAML.") 

	def command_as_script(self):
		return ' '.join(self.command)

	def add_scan(self, os: ProjectOS, value):
		if isinstance(value, str):
			value = [value]

		if isinstance(value, list) and len(value) > 0 and isinstance(value[0], list):
			# Array of arrays: join into sequential commands separated by &&
			commands = []
			for cmd in value:
				if isinstance(cmd, list) and len(cmd) > 0 and isinstance(cmd[0], str):
					if os == ProjectOS.ANDROID and ValidAndroidCompilationMethod.is_valid_method(cmd[0]):
						scan = ValidAndroidCompilationMethod.to_enum(cmd[0])
						cmd[0] = scan.get_instruction()
					elif os == ProjectOS.IOS and ValidIOSCompilationMethod.is_valid_method(cmd[0]):
						scan = ValidIOSCompilationMethod.to_enum(cmd[0])
						cmd[0] = scan.get_instruction()
					commands.append(' '.join(cmd))
			self.scan = [' && '.join(commands)]
		elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], str):
			if os == ProjectOS.ANDROID and ValidAndroidCompilationMethod.is_valid_method(value[0]):
				scan = ValidAndroidCompilationMethod.to_enum(value[0])
				value[0] = scan.get_instruction()
				self.scan = value
			elif os == ProjectOS.IOS and ValidIOSCompilationMethod.is_valid_method(value[0]):
				scan = ValidIOSCompilationMethod.to_enum(value[0])
				value[0] = scan.get_instruction()
				self.scan = value
			else:
				raise ValueError(f"{type(self).__name__}.add_scan: '{value[0]}' is not a valid operation in publish.scan for {os}. Ignoring.")
		else:
			raise ValueError(f"{type(self).__name__}.add_scan: scan doesn't have a supported structure. Check the environment YAML.") 

	def scan_as_string(self):
		return ' '.join(self.scan)

	def add_pomgen(self, os: ProjectOS, value):
		if isinstance(value, str):
			value = [value]

		if isinstance(value, list) and len(value) > 0 and isinstance(value[0], list):
			# Array of arrays: join into sequential commands separated by &&
			commands = []
			for cmd in value:
				if isinstance(cmd, list) and len(cmd) > 0 and isinstance(cmd[0], str):
					if os == ProjectOS.ANDROID and ValidAndroidCompilationMethod.is_valid_method(cmd[0]):
						pomgen = ValidAndroidCompilationMethod.to_enum(cmd[0])
						cmd[0] = pomgen.get_instruction()
					commands.append(' '.join(cmd))
			self.pomgen = [' && '.join(commands)]
		elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], str):
			if os == ProjectOS.ANDROID and ValidAndroidCompilationMethod.is_valid_method(value[0]):
				pomgen = ValidAndroidCompilationMethod.to_enum(value[0])
				value[0] = pomgen.get_instruction()
				self.pomgen = value
			else:
				raise ValueError(f"{type(self).__name__}.add_pomgen: '{value[0]}' is not a valid operation in publish.pomgen for {os}. Ignoring.")
		else:
			raise ValueError(f"{type(self).__name__}.add_pomgen: pomgen doesn't have a supported structure. Check the environment YAML.") 

	def pomgen_as_string(self):
		return ' '.join(self.pomgen)

	def add_profile(self, os, profile):
		if os == ProjectOS.IOS:
			try:
				profile_type = profile.type
				profile_source = profile.source
				profile_password = profile.password if 'password' in profile.__dict__ else ""

				prof_type = ValidCertificateProfileRetrieveType.to_enum(profile_type)
				if prof_type == ValidCertificateProfileRetrieveType.FILES:
					self.profile = CertificateProfile(prof_type, source=profile_source, password=profile_password)
				elif prof_type == ValidCertificateProfileRetrieveType.COMMAND:
					self.profile = CertificateProfile(prof_type, command=profile_source, password=profile_password)
				else:
					raise ValueError(f"{type(self).__name__}.add_profile: '{profile_type}' function not implemented yet.")
			except Exception as e:
				print(f"{type(self).__name__}.add_profile error:  {e}")
				raise
		elif os == ProjectOS.ANDROID:
			self.profile = CertificateProfile(ValidCertificateProfileRetrieveType.COMMAND, "")
		else:
			raise ValueError(f"{type(self).__name__}.add_profile: '{profile_type}' is not a valid operation in publish.profile for {os}. Ignoring.")

	def add_certificate(self, os, certificate):
		if os == ProjectOS.IOS:
			try:
				certificate_type = certificate.type
				certificate_source = certificate.source
				certificate_password = certificate.password if 'password' in certificate.__dict__ else ""

				prof_type = ValidCertificateProfileRetrieveType.to_enum(certificate_type)
				if prof_type == ValidCertificateProfileRetrieveType.FILES:
					self.certificate = CertificateProfile(prof_type, source=certificate_source, password=certificate_password)
				elif prof_type == ValidCertificateProfileRetrieveType.COMMAND:
					self.certificate = CertificateProfile(prof_type, command=certificate_source, password=certificate_password)
				else:
					raise ValueError(f"{type(self).__name__}.add_certificate: '{certificate_type}' function not implemented yet.")
			except Exception as e:
				print(f"{type(self).__name__}.add_certificate error:  {e}")
				raise
		elif os == ProjectOS.ANDROID:
			self.certificate = CertificateProfile(ValidCertificateProfileRetrieveType.COMMAND, "")
		else:
			raise ValueError(f"{type(self).__name__}.add_certificate: '{certificate_type}' is not a valid operation in publish.certificate for {os}. Ignoring.")

	def add_jarsigner(self, os, jarsigner):
		if os == ProjectOS.ANDROID:
			if jarsigner is not None:
				config = JarSignerConfig(enabled=True)
			else:
				config = JarSignerConfig()
			if jarsigner is not None and 'keystore' in jarsigner.__dict__: config.keystore = jarsigner.keystore
			if jarsigner is not None and 'storetype' in jarsigner.__dict__: config.storetype = jarsigner.storetype
			if jarsigner is not None and 'storepass' in jarsigner.__dict__: config.storepass = jarsigner.storepass
			if jarsigner is not None and 'keypass' in jarsigner.__dict__: config.keypass = jarsigner.keypass
			if jarsigner is not None and 'alias' in jarsigner.__dict__: config.alias = jarsigner.alias
			self.jarsigner = config
		elif os == ProjectOS.IOS:
			self.jarsigner = JarSignerConfig()
		else:
			raise ValueError(f"{type(self).__name__}.add_jarsigner: jarsigner is not a valid operation for {os}. Ignoring.")

	def add_folder_ref(self, os, ref = None):
		if ref is None:
			if os == ProjectOS.ANDROID:
				self.folder_ref = [self.DEFAULT_FOLDER_REF_ANDROID]
			else:
				self.folder_ref = [""]
		elif isinstance(ref, str):
			self.folder_ref = [ref]
		elif isinstance(ref, list):
			self.folder_ref = ref
		else:
			self.folder_ref = [""]

	def print_folder_ref(self):
		return ' '.join(f'-e "{ref}"' for ref in self.folder_ref)

	@classmethod
	def cast(cls, obj):
		pass

class Publish(Export):
	@classmethod
	def cast(cls, obj):
		obj2 = copy.deepcopy(obj)
		obj2.__class__ = cls
		assert isinstance(obj2, Export)
		assert isinstance(obj2, Publish)
		return obj2

class Scan(Export):
	@classmethod
	def cast(cls, obj):
		obj2 = copy.deepcopy(obj)
		obj2.__class__ = cls
		assert isinstance(obj2, Export)
		assert isinstance(obj2, Scan)
		return obj2

class Instrumented(Export):
	@classmethod
	def cast(cls, obj):
		obj2 = copy.deepcopy(obj)
		obj2.__class__ = cls
		assert isinstance(obj2, Export)
		assert isinstance(obj2, Instrumented)
		return obj2

class ProjectEnvironment:
	def __init__(self, test_array: list = [[]], build_array: list = [[]], publish: Publish = None, scan: Scan = None, instrumented: Instrumented = None):
		self.test = test_array
		self.build = build_array
		self.publish = publish or Publish()
		self.scan = scan or Scan()
		self.instrumented = instrumented or Instrumented()

	def add_test(self, os, value):

		if isinstance(value, str):
			value = [value]

		if isinstance(value, list) and (isinstance(value[0], str) or isinstance(value[0], list)):
			if isinstance(value[0], str):
				value = [value]

			for val in value:
				if isinstance(val, str):
					val = [val]

				if os == ProjectOS.ANDROID and ValidAndroidCompilationMethod.is_valid_method(val[0]):
					test = ValidAndroidCompilationMethod.to_enum(val[0])
					val[0] = test.get_instruction()
					self.test.append(val)
				elif os == ProjectOS.IOS and ValidIOSCompilationMethod.is_valid_method(val[0]):
					test = ValidIOSCompilationMethod.to_enum(val[0])
					val[0] = test.get_instruction()
					self.test.append(val)
				else:
					print(f"[WARN!] '{val[0]}' is not a valid operation in project.environment.test for {os}. Ignoring.")
		else:
			raise ValueError(f"ProjectEnvironment.add_test: project.environment.test doesn't have a supported structure. Check the environment YAML.") 

	def test_as_string(self):
		output = []
		for s in self.test:
			output.append(' '.join(s))
		return ' && '.join(output)

	def add_build(self, os, value):
		if isinstance(value, str):
			value = [value]

		if isinstance(value, list) and (isinstance(value[0], str) or isinstance(value[0], list)):
			if isinstance(value[0], str):
				value = [value]

			for val in value:
				if isinstance(val, str):
					val = [val]

				if os == ProjectOS.ANDROID and ValidAndroidCompilationMethod.is_valid_method(val[0]):
					build = ValidAndroidCompilationMethod.to_enum(val[0])
					val[0] = build.get_instruction()
					self.build.append(val)
				elif os == ProjectOS.IOS and ValidIOSCompilationMethod.is_valid_method(val[0]):
					build = ValidIOSCompilationMethod.to_enum(val[0])
					val[0] = build.get_instruction()
					self.build.append(val)
				else:
					raise ValueError(f"ProjectEnvironment.add_build: '{val[0]}' is not a valid operation in project.environment.build for {os}. Ignoring.")
		else:
			raise ValueError(f"ProjectEnvironment.add_build: project.environment.build doesn't have a supported structure. Check the environment YAML.") 

	def build_as_string(self):
		output = []
		for s in self.build:
			output.append(' '.join(s))
		return ' && '.join(output)

	def __repr__(self):
		return f"[ProjectEnvironment] {{test: {self.test}, build: {self.build}, publish: {self.publish}}}"

	def __str__(self):
		return f"ProjectEnvironment: {{test: {self.test_as_string()}, build: {self.build_as_string()}, publish: {self.publish}}}"

class Project:
	def __init__(self, os: ProjectOS, type: ProjectType,  java_version: JavaJDKType = None,
				developmentEnvironment: ProjectEnvironment = None,
				qualityEnvironment: ProjectEnvironment = None,
				productionEnvironment: ProjectEnvironment = None):
		self.os = os
		self.type = type
		self.java_version = java_version
		self.developmentEnvironment = developmentEnvironment
		self.qualityEnvironment = qualityEnvironment
		self.productionEnvironment = productionEnvironment

	def add_java_version(self, java_version : JavaJDKType):
		self.java_version = java_version

	def java_version_as_string(self):
		if self.java_version is None:
			return ""
		return str(self.java_version)

	def __repr__(self):
		return f"[Project] {{os: {self.os}, type: {self.type}, java_version: {self.java_version}}}"

	def __str__(self):
		return f"Project: {{os: {self.os}, type: {self.type}, java_version: {self.java_version}}}"

class Variable:
	def __init__(self, type: VariableType, value, lock_environment:bool=False, only_for:ProjectEnvironmentType = None):
		self.type = type
		self.value = value
		self.lock_environment = lock_environment
		self.only_for = only_for

	def __repr__(self):
		return f"[Variable] {{type: {self.type}, value: {self.value}}}"

	def get_type(self):
		return str(self.type)

	def to_string(self):
		if self.type is VariableType.STRING:
			return f"{self.value}"
		else:
			return f"{self.type}:{self.value}"

class Artifact:
	def __init__(self, source_type: ArtifactSourceType, source, target=None, package=None, version=None, branch=None, path=None):
		self.source_type = source_type
		self.source = source
		self.target = target
		self.package = package
		self.version = version
		self.branch = branch
		self.path = path

	def __repr__(self):
		return f"[Artifact] {{source_type: {self.source_type}, source: {self.source}, target: {self.target}, package: {self.package}, version: {self.version}}}"

class SecretEnvironment:
	def __init__(self, value: str = "", json_key: str = "", target: str  = "", encoded_base64: bool = False):
		self.value = value
		self.json_key = json_key
		self.target = target
		self.encoded_base64 = encoded_base64

	def __str__(self):
		return f"[SecretEnvironment] {{value: {self.value}, json_key: {self.json_key}, target: {self.target}, encoded_base64: {self.encoded_base64}}}"

class Secret:
	def __init__(self, secret_development: SecretEnvironment = None, secret_quality: SecretEnvironment = None, secret_production: SecretEnvironment = None):
		self.secret_development = secret_development
		self.secret_quality = secret_quality
		self.secret_production = secret_production

	def __str__(self):
		return f"[Secret] {{development: {self.secret_development}, quality: {self.secret_quality}, production: {self.secret_production}}}"

class CI:
	def __init__(self, project: Project, variables: typing.List[Variable], artifacts: typing.List[Artifact], secrets: typing.List[Secret]):
		self.project = project
		self.variables = variables
		self.artifacts = artifacts
		self.secrets = secrets

	def update_environment_variables(self):
		for key in self.variables:
			element : Variable = self.variables[key]
			if element.type == VariableType.ENVIRONMENT:
				# Read environment variable value and replace to string type
				element.value = os.getenv(element.value, "")
				element.type = VariableType.STRING
				self.variables[key] = element

	def to_environment_variables(self, set_environment=""):
		environment_list = {}

		environment_only = None
		if set_environment != "":
			environment_only = ProjectEnvironmentType.to_enum(set_environment)

		def fill_environment_data(data: ProjectEnvironment, environment: str):
			env_data = {}

			environment = environment.upper()

			def fill_export_data(export: Export, prefix: str, environment: str):
				export_data = {}
				export_data.update({f"{prefix}_ENABLED_{environment}": str(export.enabled)})
				export_data.update({f"{prefix}_OUTPUT_{environment}": export.output})
				export_data.update({f"{prefix}_COMMAND_{environment}": export.command_as_script()})
				export_data.update({f"{prefix}_POMGEN_{environment}": export.pomgen_as_string()})
				# profiles
				export_data.update({f"{prefix}_PROFILE_TYPE_{environment}": export.profile.retrieve_type})
				export_data.update({f"{prefix}_PROFILE_SOURCE_{environment}": export.profile.source_command_as_string()})
				export_data.update({f"{prefix}_PROFILE_PASSWORD_{environment}": export.profile.password})
				# certificates
				export_data.update({f"{prefix}_CERTIFICATE_TYPE_{environment}": export.certificate.retrieve_type})
				export_data.update({f"{prefix}_CERTIFICATE_SOURCE_{environment}": export.certificate.source_command_as_string()})
				export_data.update({f"{prefix}_CERTIFICATE_PASSWORD_{environment}": export.certificate.password})
				# jarsigner
				export_data.update({f"{prefix}_JARSIGNER_ENABLED_{environment}": str(export.jarsigner.enabled)})
				export_data.update({f"{prefix}_JARSIGNER_KEYPASS_{environment}": export.jarsigner.keypass})
				export_data.update({f"{prefix}_JARSIGNER_ALIAS_{environment}": export.jarsigner.alias})
				export_data.update({f"{prefix}_JARSIGNER_KEYSTORE_{environment}": export.jarsigner.keystore})
				export_data.update({f"{prefix}_JARSIGNER_STOREPASS_{environment}": export.jarsigner.storepass})
				export_data.update({f"{prefix}_JARSIGNER_STORETYPE_{environment}": export.jarsigner.storetype})
				export_data.update({f"{prefix}_FOLDER_REF_{environment}": export.print_folder_ref()})

				return export_data

			env_data.update(fill_export_data(data.publish, "PIPELINE_PROJECT_PUBLISH", environment))
			env_data.update(fill_export_data(data.scan, "PIPELINE_PROJECT_SCAN", environment))
			env_data.update(fill_export_data(data.instrumented, "PIPELINE_PROJECT_INSTRUMENTED", environment))

			env_data.update({f"PIPELINE_PROJECT_BUILD_{environment}": data.build_as_string()})
			env_data.update({f"PIPELINE_PROJECT_TEST_{environment}": data.test_as_string()})

			# Export individual build/publish/pomgen steps for sequential module publishing
			build_steps = [s for s in data.build if s]
			env_data.update({f"PIPELINE_PROJECT_BUILD_COUNT_{environment}": str(len(build_steps))})
			for idx, step in enumerate(build_steps):
				env_data.update({f"PIPELINE_PROJECT_BUILD_STEP{idx}_{environment}": ' '.join(step)})

			publish_steps = [s for s in data.publish.command if s] if isinstance(data.publish.command, list) and len(data.publish.command) > 0 and isinstance(data.publish.command[0], str) else []
			# If command was joined with &&, split back for individual steps
			joined_cmd = data.publish.command_as_script()
			if ' && ' in joined_cmd:
				individual_cmds = joined_cmd.split(' && ')
				env_data.update({f"PIPELINE_PROJECT_PUBLISH_CMD_COUNT_{environment}": str(len(individual_cmds))})
				for idx, cmd in enumerate(individual_cmds):
					env_data.update({f"PIPELINE_PROJECT_PUBLISH_CMD_STEP{idx}_{environment}": cmd})
			else:
				env_data.update({f"PIPELINE_PROJECT_PUBLISH_CMD_COUNT_{environment}": "1"})
				env_data.update({f"PIPELINE_PROJECT_PUBLISH_CMD_STEP0_{environment}": joined_cmd})

			joined_pomgen = data.publish.pomgen_as_string()
			if ' && ' in joined_pomgen:
				individual_pomgens = joined_pomgen.split(' && ')
				env_data.update({f"PIPELINE_PROJECT_PUBLISH_POMGEN_COUNT_{environment}": str(len(individual_pomgens))})
				for idx, cmd in enumerate(individual_pomgens):
					env_data.update({f"PIPELINE_PROJECT_PUBLISH_POMGEN_STEP{idx}_{environment}": cmd})
			elif joined_pomgen:
				env_data.update({f"PIPELINE_PROJECT_PUBLISH_POMGEN_COUNT_{environment}": "1"})
				env_data.update({f"PIPELINE_PROJECT_PUBLISH_POMGEN_STEP0_{environment}": joined_pomgen})
			else:
				env_data.update({f"PIPELINE_PROJECT_PUBLISH_POMGEN_COUNT_{environment}": "0"})

			return env_data

		# project
		environment_list.update({"PIPELINE_PROJECT_OS": self.project.os.value})
		environment_list.update({"PIPELINE_PROJECT_TYPE": self.project.type.value})
		environment_list.update({"PIPELINE_PROJECT_JAVA_VERSION": self.project.java_version_as_string()})

		if environment_only is None or environment_only == ProjectEnvironmentType.DEVELOPMENT:
			environment_list.update(fill_environment_data(self.project.developmentEnvironment, ProjectEnvironmentType.DEVELOPMENT))
		if environment_only is None or environment_only == ProjectEnvironmentType.QUALITY:
			environment_list.update(fill_environment_data(self.project.qualityEnvironment, ProjectEnvironmentType.QUALITY))
		if environment_only is None or environment_only == ProjectEnvironmentType.PRODUCTION:
			environment_list.update(fill_environment_data(self.project.productionEnvironment, ProjectEnvironmentType.PRODUCTION))


		# variables
		def fill_secret_data(key:str, data: SecretEnvironment, environment: str):
			env_data = {}
			environment = environment.upper()

			env_data.update({f"{environment}_TYPE": self.variables[key].get_type()})
			env_data.update({f"{environment}_NAME": key})
			env_data.update({f"{environment}_VALUE": data.value})
			env_data.update({f"{environment}_KEY": data.json_key})
			env_data.update({f"{environment}_TARGET": data.target})
			env_data.update({f"{environment}_BASE64": str(data.encoded_base64)})

			return env_data

		for key in self.variables:
			if self.variables[key].type == VariableType.SECRET:

				secret_key = str(key).upper()
				secret_index = self.variables[key].value
				lock_environment = self.variables[key].lock_environment
				locked_for =  self.variables[key].only_for

				if not lock_environment:
					if environment_only is None or environment_only == ProjectEnvironmentType.DEVELOPMENT:
						environment_list.update(fill_secret_data(key, self.secrets[secret_index].secret_development, f"{secret_key}_DEVELOPMENT"))
					if environment_only is None or environment_only == ProjectEnvironmentType.QUALITY:
						environment_list.update(fill_secret_data(key, self.secrets[secret_index].secret_quality, f"{secret_key}_QUALITY"))
					if environment_only is None or environment_only == ProjectEnvironmentType.PRODUCTION:
						environment_list.update(fill_secret_data(key, self.secrets[secret_index].secret_production, f"{secret_key}_PRODUCTION"))
				else:
					if (environment_only is None or environment_only == ProjectEnvironmentType.DEVELOPMENT) and locked_for == ProjectEnvironmentType.DEVELOPMENT:
						environment_list.update(fill_secret_data(key, self.secrets[secret_index].secret_development, f"{secret_key}_DEVELOPMENT"))
					if (environment_only is None or environment_only == ProjectEnvironmentType.QUALITY) and locked_for == ProjectEnvironmentType.QUALITY:
						environment_list.update(fill_secret_data(key, self.secrets[secret_index].secret_quality, f"{secret_key}_QUALITY"))
					if (environment_only is None or environment_only == ProjectEnvironmentType.PRODUCTION) and locked_for == ProjectEnvironmentType.PRODUCTION:
						environment_list.update(fill_secret_data(key, self.secrets[secret_index].secret_production, f"{secret_key}_PRODUCTION"))
			else:
				#environment_list.update({f"{key}_TYPE": self.variables[key].get_type()})
				#environment_list.update({f"{key}_NAME": key})
				environment_list.update({key: self.variables[key].to_string()})

		# artifacts
		for artifact in self.artifacts:
			idx = self.artifacts.index(artifact)
			environment_list.update({f"PIPELINE_ARTIFACT_TYPE{idx}": artifact.source_type})
			environment_list.update({f"PIPELINE_ARTIFACT_SOURCE{idx}": artifact.source})
			environment_list.update({f"PIPELINE_ARTIFACT_TARGET{idx}": artifact.target or ""})
			environment_list.update({f"PIPELINE_ARTIFACT_PACKAGE{idx}": artifact.package or ""})
			environment_list.update({f"PIPELINE_ARTIFACT_VERSION{idx}": artifact.version or ""})
			environment_list.update({f"PIPELINE_ARTIFACT_BRANCH{idx}": artifact.branch or ""})
			environment_list.update({f"PIPELINE_ARTIFACT_PATH{idx}": artifact.path or ""})
		return environment_list