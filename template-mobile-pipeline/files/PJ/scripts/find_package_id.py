import argparse
import json
import sys
import urllib.request


def find_package_id(api_url, token, artifact_id, version):
    """Busca un paquete en Package Registry por nombre de artefacto y versión.
    Imprime el package_id si lo encuentra, nada si no existe."""
    url = f"{api_url}/packages?package_name={artifact_id}&per_page=100"
    req = urllib.request.Request(url, headers={"PRIVATE-TOKEN": token})

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"[WARN] Failed to query Package Registry: {e}", file=sys.stderr)
        return

    if not isinstance(data, list):
        return

    for pkg in data:
        pkg_name = pkg.get("name", "")
        pkg_version = pkg.get("version", "")
        if pkg_name.endswith(artifact_id) and pkg_version == version:
            print(pkg["id"])
            return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find package ID in GitLab Package Registry")
    parser.add_argument("-u", "--url", required=True, help="Project API URL prefix")
    parser.add_argument("-t", "--token", required=True, help="GitLab private token")
    parser.add_argument("-a", "--artifact", required=True, help="Artifact ID to search")
    parser.add_argument("-v", "--version", required=True, help="Package version to match")
    args = parser.parse_args()

    find_package_id(args.url, args.token, args.artifact, args.version)
