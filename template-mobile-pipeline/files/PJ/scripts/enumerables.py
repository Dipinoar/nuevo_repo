import os

from enum import auto
from strenum import LowercaseStrEnum, StrEnum

class ProjectOS(LowercaseStrEnum):
	IOS=auto()
	ANDROID=auto()

	@classmethod
	def to_enum(cls, value):
		value = value.lower()
		if value in cls._value2member_map_:
			return ProjectOS(value)
		else:
			raise ValueError(f"ProjectOS: Cannot parse value of {value} to Enum")

class ProjectType(LowercaseStrEnum):
	APPLICATION=auto()
	LIBRARY=auto()

	@classmethod
	def to_enum(cls, value):
		value = value.lower()
		if value in cls._value2member_map_:
			return ProjectType(value)
		else:
			raise ValueError(f"ProjectType: Cannot parse value of {value} to Enum")

class ProjectEnvironmentType(LowercaseStrEnum):
	DEVELOPMENT=auto()
	QUALITY=auto()
	PRODUCTION=auto()

	@classmethod
	def to_enum(cls, value):
		value = value.lower()
		if value in cls._value2member_map_:
			return ProjectEnvironmentType(value)
		else:
			raise ValueError(f"ProjectEnvironmentType: Cannot parse value of {value} to Enum")

class ArtifactSourceType(StrEnum):
	JFROG=auto()
	GITLAB_MAVEN=auto()
	GITLAB_GENERIC=auto()
	GITLAB_FILE=auto()

	@classmethod
	def to_enum(cls, value):
		value = value.upper().replace("-", "_")

		if value in cls._value2member_map_:
			return ArtifactSourceType(value)
		else:
			raise ValueError(f"ArtifactSourceType: Cannot parse value of {value} to Enum")

	def __str__(self):
		return str(self.value).lower().replace("_", "-")

class VariableType(LowercaseStrEnum):
	STRING=auto()
	SECRET=auto()
	ENVIRONMENT=auto()
	PATH=auto()

	@classmethod
	def to_enum(cls, value):
		value = value.lower()
		if value in cls._value2member_map_:
			return VariableType(value)
		else:
			raise ValueError(f"VariableType: Cannot parse value of {value} to Enum")

class ValidAndroidCompilationMethod(LowercaseStrEnum):
	GRADLEW=auto()
	FASTLANE=auto()

	__MAVEN_LIBRARY_DIR__=os.getenv("MAVEN_LIBRARY_DIR") or "ci/maven"

	@classmethod
	def to_enum(cls, value):
		value = value.lower()
		if value in cls._value2member_map_:
			return ValidAndroidCompilationMethod(value)
		else:
			raise ValueError(f"ValidAndroidCompilationMethod: Cannot parse value of {value} to Enum")

	@classmethod
	def is_valid_method(cls, value):
		value = value.lower()
		if value in cls._value2member_map_:
			return True
		return False

	def get_instruction(self):
		if self == ValidAndroidCompilationMethod.GRADLEW:
			return f"./gradlew -g .gradle --no-daemon --no-parallel"
		elif self == ValidAndroidCompilationMethod.FASTLANE:
			return "fastlane"


class ValidIOSCompilationMethod(LowercaseStrEnum):
	MAKEFILE=auto()
	FASTLANE=auto()

	@classmethod
	def to_enum(cls, value):
		value = value.lower()
		if value in cls._value2member_map_:
			return ValidIOSCompilationMethod(value)
		else:
			raise ValueError(f"ValidIOSCompilationMethod: Cannot parse value of {value} to Enum")

	@classmethod
	def is_valid_method(cls, value):
		value = value.lower()
		if value in cls._value2member_map_:
			return True
		return False

	def get_instruction(self):
		if self == ValidIOSCompilationMethod.MAKEFILE:
			return "make"
		elif self == ValidIOSCompilationMethod.FASTLANE:
			return "fastlane"
		else:
			return self.__str__()

class ValidCertificateProfileRetrieveType(LowercaseStrEnum):
	FILES=auto()
	COMMAND=auto()

	@classmethod
	def to_enum(cls, value):
		value = value.lower()
		if value in cls._value2member_map_:
			return ValidCertificateProfileRetrieveType(value)
		else:
			raise ValueError(f"ValidCertificateProfileRetrieveType: Cannot parse value of {value} to Enum")

class EnvironmentType(LowercaseStrEnum):
	DEVELOPMENT=auto()
	QUALITY=auto()
	PRODUCTION=auto()

	@classmethod
	def to_enum(cls, value):
		value = value.lower()
		if value in cls._value2member_map_:
			return EnvironmentType(value)
		else:
			raise ValueError(f"EnvironmentType: Cannot parse value of {value} to Enum")

class JavaJDKType(StrEnum):
	TEMURIN_21=auto()
	JAVA_LATEST=auto()
	JAVA_21=auto()
	JAVA_17=auto()
	JAVA_11=auto()
	JAVA_8=auto()

	@classmethod
	def to_enum(cls, value):
		value = value.upper().replace("-", "_")

		if value in cls._value2member_map_:
			return JavaJDKType(value)
		else:
			raise ValueError(f"JavaJDKType: Cannot parse value of {value} to Enum")

	def __str__(self):
		return str(self.value).lower().replace("_", "-")