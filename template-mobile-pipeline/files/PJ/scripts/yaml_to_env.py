import yaml, argparse, json, types, os

from dotenv import set_key
from pathlib import Path

from enumerables import ProjectOS, ProjectType, VariableType, ArtifactSourceType, JavaJDKType, ProjectEnvironmentType
from environment import Project, ProjectEnvironment, Variable, Artifact, CI, Publish, Secret, SecretEnvironment, Scan, Instrumented

from utils import Utils

ENV_FILE_NAME="build.env"

def load_yaml(path=None, data=None):
    loader = yaml.SafeLoader

    if path:
        with open(path) as load_data:
            return yaml.load(load_data, Loader=loader)
    elif data:
        return yaml.load(data, Loader=loader)
    else:
        raise ValueError("YAMLParseError: Set a file or data to parse.")

def parse_yaml(env):
    def load_object(dct):
        return types.SimpleNamespace(**dct)

    if env["ci"]:
        print("File contains CI Root.")
        ci = json.loads(json.dumps(env["ci"]), object_hook=load_object)

        # ci.project
        if ci.project is None or isinstance(ci.project, str):
            raise ValueError("YAMLParseError: No project structure was defined properly in environment YAML")

        # ci.project.os
        if ci.project.os is None or not isinstance(ci.project.os, str):
            raise ValueError("YAMLParseError: No project.os value was defined properly in environment YAML")

        # ci.project.type
        if ci.project.type is None or not isinstance(ci.project.type, str):
            raise ValueError("YAMLParseError: No project.type value was defined properly in environment YAML")

        project = Project(ProjectOS.to_enum(ci.project.os), ProjectType.to_enum(ci.project.type))

        # ci.project.environment
        if 'environments' not in ci.project.__dict__ or ci.project.environments is None:
            raise ValueError("YAMLParseError: No project.environments value was defined properly in environment YAML")

        for key in vars(ci.project.environments):
            environment = ci.project.environments.__dict__[key]

            projectEnvironment = ProjectEnvironment(build_array=[], test_array=[], publish=None)

            # ci.project.environment.<env>.test
            if 'test' in environment.__dict__ and environment.test is None:
                raise ValueError("YAMLParseError: No project.environment.test value was defined properly in environment YAML")
            else:
                test = environment.test
                if not isinstance(test[0], list):
                    test = [environment.test]
                if not Utils.validate_command(environment.test):
                    raise ValueError("YAMLParseError: A project.environment.test array element contains special characters that are not supported.")
                else:
                    projectEnvironment.add_test(project.os, environment.test)

            # ci.project.environment.<env>.build
            if 'build' not in environment.__dict__ or environment.build is None:
                raise ValueError("YAMLParseError: No project..environment.build value was defined properly in environment YAML")
            else:
                build = environment.build
                if not isinstance(build[0], list):
                    build = [environment.build]
                if not Utils.validate_command(environment.build):
                    raise ValueError("YAMLParseError: A project.environment.build array element contains special characters that are not supported.")
                else:
                    projectEnvironment.add_build(project.os, environment.build)

            # ci.project.environment.<env>.publish
            if project.os == ProjectOS.ANDROID:
                if 'publish' not in environment.__dict__ or getattr(environment, 'publish') is None:
                    raise ValueError("YAMLParseError: No project.publish structure was defined properly in environment YAML")
                if environment.publish.output is None:
                    publish = Publish(output=Publish.DEFAULT_PUBLISH_ANDROID_EXT)
                elif not isinstance(environment.publish.output, str):
                    raise ValueError("YAMLParseError: No project.publish.output value was defined properly in environment YAML")
                else:
                    publish = Publish(output=environment.publish.output)

                # command precedence over release for compatibility. command if release not defined.
                if 'command' not in environment.publish.__dict__ and 'release' in environment.publish.__dict__:
                    if not Utils.validate_command(environment.publish.release):
                        raise ValueError(f"YAMLParseError: A {key}.publish.release array element contains special characters that are not supported.")
                    print(f"[WARN!] {key}.publish.release is deprecated. Change it to {key}.publish.command")
                    publish.add_command(project.os, environment.publish.release)
                else:
                    if not Utils.validate_command(environment.publish.command):
                        raise ValueError(f"YAMLParseError: A {key}.publish.command array element contains special characters that are not supported.")
                    publish.add_command(project.os, environment.publish.command)
                if 'scan' in environment.publish.__dict__ :
                    print(f"[WARN!] project.publish.scan unused. Use project.scan structure instead.")
                if 'pomgen' in environment.publish.__dict__ :
                    publish.add_pomgen(project.os, environment.publish.pomgen)
                else:
                    print(f"[INFO!] project.publish.pomgen not found for {key}. Skipping definition.")
                if 'jarsigner' in environment.publish.__dict__ :
                    publish.add_jarsigner(project.os, environment.publish.jarsigner)
                else:
                    publish.add_jarsigner(project.os, None)
                    print(f"[INFO!] project.publish.jarsigner not found for {key}. Skipping definition.")
                publish.add_profile(project.os, None)
                publish.add_certificate(project.os, None)
                if 'folder-ref' in environment.publish.__dict__ :
                    ref = getattr(environment.publish, 'folder-ref')
                    publish.add_folder_ref(project.os, ref)
                else:
                    publish.add_folder_ref(project.os, None)
                    print(f"[INFO!] project.publish.folder-ref not found for {key}. Setting default value.")
                projectEnvironment.publish = publish
            if project.os == ProjectOS.IOS:
                if 'publish' not in environment.__dict__ or getattr(environment, 'publish') is None:
                    raise ValueError("YAMLParseError: No project.publish structure was defined properly in environment YAML")
                if environment.publish.output is None:
                    publish = Publish(output=Publish.DEFAULT_PUBLISH_IOS_EXT)
                elif not isinstance(environment.publish.output, str):
                    raise ValueError("YAMLParseError: No project.publish.output value was defined properly in environment YAML")
                else:
                    publish = Publish(output=environment.publish.output)

                # command precedence and over release for compatibility.
                if 'command' not in environment.publish.__dict__ and 'release' in environment.publish.__dict__:
                    print(f"[WARN!] {key}.publish.release is deprecated. Change it to {key}.publish.command")
                    if not Utils.validate_command(environment.publish.release):
                        raise ValueError(f"YAMLParseError: A {key}.publish.release array element contains special characters that are not supported.")
                    publish.add_command(project.os, environment.publish.release)
                else:
                    if not Utils.validate_command(environment.publish.command):
                        raise ValueError(f"YAMLParseError: A {key}.publish.command array element contains special characters that are not supported.")
                    publish.add_command(project.os, environment.publish.command)
                publish.add_profile(project.os, environment.publish.profile)
                publish.add_certificate(project.os, environment.publish.certificate)
                publish.add_jarsigner(project.os, None)
                publish.add_folder_ref(project.os, None)
                projectEnvironment.publish = publish

            # ci.project.environment.<env>.scan
            # as default, scan is a mirror of publish, it will only update
            # when a reference is set.
            projectEnvironment.scan = Scan.cast(publish)
            if 'scan' in environment.__dict__:
                if 'output' in environment.scan.__dict__ and isinstance(environment.scan.output, str):
                    projectEnvironment.scan.output = environment.scan.output
                if 'command' in environment.scan.__dict__:
                    if not Utils.validate_command(environment.scan.command):
                        raise ValueError(f"YAMLParseError: A {key}.scan.command array element contains special characters that are not supported.")
                    projectEnvironment.scan.add_command(project.os, environment.scan.command)
                if project.os == ProjectOS.ANDROID and 'pomgen' in environment.scan.__dict__ :
                    projectEnvironment.scan.add_pomgen(project.os, environment.scan.pomgen)
                if project.os == ProjectOS.ANDROID and 'jarsigner' in environment.scan.__dict__ :
                    projectEnvironment.scan.add_jarsigner(project.os, environment.scan.jarsigner)
                if project.os == ProjectOS.ANDROID and 'folder-ref' in environment.scan.__dict__ :
                    ref = getattr(environment.scan, 'folder-ref')
                    projectEnvironment.scan.add_folder_ref(project.os, ref)
                if project.os == ProjectOS.IOS and 'profile' in environment.scan.__dict__ :
                    projectEnvironment.scan.add_profile(project.os, environment.scan.profile)
                if project.os == ProjectOS.IOS and 'certificate' in environment.scan.__dict__ :
                    projectEnvironment.scan.add_certificate(project.os, environment.scan.certificate)

            # ci.project.environment.<env>.instrumented
            # as default, instrumented is a mirror of publish, and deactivated if not present
            # it will only update when a reference is set.
            projectEnvironment.instrumented = Instrumented.cast(publish)
            if 'instrumented' in environment.__dict__:
                if 'output' in environment.instrumented.__dict__ and isinstance(environment.instrumented.output, str):
                    projectEnvironment.instrumented.output = environment.instrumented.output
                if 'command' in environment.instrumented.__dict__:
                    if not Utils.validate_command(environment.instrumented.command):
                        raise ValueError(f"YAMLParseError: A {key}.instrumented.command array element contains special characters that are not supported.")
                    projectEnvironment.instrumented.add_command(project.os, environment.instrumented.command)
                if project.os == ProjectOS.ANDROID and 'pomgen' in environment.instrumented.__dict__ :
                    projectEnvironment.instrumented.add_pomgen(project.os, environment.instrumented.pomgen)
                if project.os == ProjectOS.ANDROID and 'jarsigner' in environment.instrumented.__dict__ :
                    projectEnvironment.instrumented.add_jarsigner(project.os, environment.instrumented.jarsigner)
                if project.os == ProjectOS.ANDROID and 'folder-ref' in environment.instrumented.__dict__ :
                    ref = getattr(environment.instrumented, 'folder-ref')
                    projectEnvironment.instrumented.add_folder_ref(project.os, ref)
                if project.os == ProjectOS.IOS and 'profile' in environment.instrumented.__dict__ :
                    projectEnvironment.instrumented.add_profile(project.os, environment.instrumented.profile)
                if project.os == ProjectOS.IOS and 'certificate' in environment.instrumented.__dict__ :
                    projectEnvironment.instrumented.add_certificate(project.os, environment.instrumented.certificate)
            else:
                projectEnvironment.instrumented.enabled = False

            # Add projectEnvironment in project
            if key == ProjectEnvironmentType.DEVELOPMENT:
                project.developmentEnvironment = projectEnvironment
            if key == ProjectEnvironmentType.QUALITY:
                project.qualityEnvironment = projectEnvironment
            if key == ProjectEnvironmentType.PRODUCTION:
                project.productionEnvironment = projectEnvironment

        # ci.project.java-version
        if project.os == ProjectOS.ANDROID:
            if 'java-version' not in ci.project.__dict__ or getattr(ci.project, 'java-version') is None:
                project.add_java_version(JavaJDKType.TEMURIN_21)
            else:
                java_version = getattr(ci.project, 'java-version')
                project_java_version = JavaJDKType.to_enum(java_version)
                project.add_java_version(project_java_version)

        # ci.secrets
        secrets = {}
        if 'secrets' not in ci.__dict__ or ci.secrets is None:
            print("[INFO!] No secrets defined in environment YAML file.")
        else:
            for key in vars(ci.secrets):
                element = ci.secrets.__dict__[key]
                if element is None:
                    print(f"[WARN!] No value set for secret {key}. Ignoring.")
                elif isinstance(element, str):
                    secret_element = SecretEnvironment(value=element)
                    secret = Secret(secret_element, secret_element, secret_element)
                    secrets.update({key: secret})
                else:
                    secret = Secret()
                    def fill_secret_environment(data):
                        secret_env = SecretEnvironment()
                        if isinstance(data, str):
                            secret_env.value = data
                            return secret_env
                        if 'arn' in data.__dict__ and data.arn is not None:
                            secret_env.value = data.arn
                        if 'key' in data.__dict__ and data.key is not None:
                            secret_env.json_key = data.key
                        if 'target' in data.__dict__ and data.target is not None:
                            secret_env.target = data.target
                        if 'base64' in data.__dict__ and data.base64 is not None:
                            secret_env.encoded_base64 = data.base64
                        return secret_env

                    if ProjectEnvironmentType.DEVELOPMENT in element.__dict__:
                        secret.secret_development = fill_secret_environment(element.development)
                    if ProjectEnvironmentType.QUALITY in element.__dict__:
                        secret.secret_quality = fill_secret_environment(element.quality)
                    if ProjectEnvironmentType.PRODUCTION in element.__dict__:
                        secret.secret_production = fill_secret_environment(element.production)
                    secrets.update({key: secret})

        # ci.variables
        variables = {}
        if 'variables' not in ci.__dict__ or ci.variables is None:
            print("[INFO!] No variables defined in environment YAML file.")
        else:
            for key in vars(ci.variables):
                element = ci.variables.__dict__[key]

                if element is None:
                    print(f"[WARN!] No value set for variable {key}. Ignoring.")
                elif isinstance(element, str):
                    variables.update({key: Variable(VariableType.STRING, element)})
                else:
                    if 'type' not in element.__dict__:
                        variable_type = VariableType.STRING
                    else:
                        variable_type = VariableType.to_enum(element.type)

                    if  (
                            ('value' not in element.__dict__ or element.value is None) and 
                            variable_type is not VariableType.SECRET
                        ):
                        print(f"[WARN!] No value set for variable {key}. Ignoring.")
                    else:
                        if variable_type is VariableType.SECRET:
                            variable_value = element.value

                            if variable_value not in secrets.keys():
                                raise ValueError("YAMLParseError: Secret was defined in variables but it's not present in ci.secrets. Check documentation for details.")
                        elif variable_type is VariableType.PATH:
                            variable_value = Utils.get_file_path_from_cwd(element.value)
                            variable_type = VariableType.STRING
                        else:
                            variable_value = element.value
                        if 'environment' not in element.__dict__:
                            variables.update({key: Variable(variable_type, variable_value)})
                        else:
                            variable_environment = ProjectEnvironmentType.to_enum(element.environment)
                            variables.update({key: Variable(variable_type, variable_value, True, only_for=variable_environment)})
        # ci.artifacts
        artifacts = []
        if 'artifacts' not in ci.__dict__ or ci.artifacts is None:
            print("[INFO!] No artifacts defined in environment YAML file.")
        else:
            if not isinstance(ci.artifacts, list):
                raise ValueError("YAMLParseError: Artifact is not properly structured in environment YAML")
            for artifact in ci.artifacts:
                if 'type' not in artifact.__dict__ or artifact.type is None:
                    raise ValueError("YAMLParseError: No type value was defined properly for an artifact in environment YAML")
                source_type = ArtifactSourceType.to_enum(artifact.type)
                if 'source' not in artifact.__dict__ or artifact.type is None:
                    raise ValueError("YAMLParseError: No source value was defined properly for an artifact in environment YAML")
                if source_type == ArtifactSourceType.JFROG:
                    if 'target' not in artifact.__dict__ or artifact.type is None:
                        raise ValueError("YAMLParseError: No target value was defined properly for an artifact in environment YAML")
                    artifacts.append(Artifact(source_type, artifact.source, target=artifact.target))
                elif source_type == ArtifactSourceType.GITLAB_MAVEN:
                    if 'package' not in artifact.__dict__ or artifact.package is None:
                        raise ValueError("YAMLParseError: No package value was defined properly for an artifact in environment YAML")
                    if 'version' not in artifact.__dict__ or artifact.type is None:
                        raise ValueError("YAMLParseError: No version value was defined properly for an artifact in environment YAML")
                    artifacts.append(Artifact(source_type, artifact.source, package=artifact.package, version=artifact.version))
                elif source_type == ArtifactSourceType.GITLAB_FILE:
                    if 'target' not in artifact.__dict__ or artifact.type is None:
                        raise ValueError("YAMLParseError: No target value was defined properly for an artifact in environment YAML")
                    if 'path' not in artifact.__dict__ or artifact.path is None:
                        raise ValueError("YAMLParseError: No branch path was defined properly for an artifact in environment YAML")
                    if 'branch' not in artifact.__dict__ or artifact.branch is None:
                        raise ValueError("YAMLParseError: No branch value was defined properly for an artifact in environment YAML")
                    artifacts.append(Artifact(source_type, artifact.source, target=artifact.target, branch=artifact.branch, path=artifact.path))
                else:
                    ValueError(f"YAMLParseError: No process was defined properly for the artifact type {source_type} in environment YAML")
        return CI(project, variables, artifacts, secrets)

    else:
        raise ValueError("YAMLParseError: CI Root not found in environment YAML FIle.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YAML to ENV parser")
    parser.add_argument(
        "-f", "--file", action="store",
        dest="yaml_file",
        default="ci/environment.yaml",
        help="Path to yaml file"
    )
    parser.add_argument(
        "-e", "--environment",
        dest="environment",
        default="",
        help="Set environment"
    )

    # Read ci/environment.yaml file
    args = parser.parse_args()
    env = load_yaml(path=args.yaml_file)

    # Transform to object
    project_type = parse_yaml(env)

    # Get enviromnment variables defined.
    project_type.update_environment_variables()

    # Transform YAML object to key-val list
    environment_variables = project_type.to_environment_variables(args.environment)

    # Save as build.env
    env_file_path = Path(ENV_FILE_NAME)
    env_file_path.touch(mode=0o600, exist_ok=True)

    for env_key in environment_variables:
        env_val = environment_variables[env_key]
        set_key(dotenv_path=env_file_path, key_to_set=env_key, value_to_set=env_val)

    # Clear .env file to skip simple quotes.
    Utils.clear_env_file(str(env_file_path))