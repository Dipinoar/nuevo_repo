import argparse
import json
import sys
import urllib.request

def verify_packages(api_url, token, version):
    url = f"{api_url}/packages?per_page=20&sort=desc&order_by=created_at"
    req = urllib.request.Request(url, headers={"PRIVATE-TOKEN": token})

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"[ERROR] Failed to query Package Registry: {e}")
        sys.exit(1)

    if not isinstance(data, list):
        print("[WARN] Unexpected response from Package Registry")
        sys.exit(0)

    matched = [p for p in data if p.get("version") == version]

    if matched:
        print(f"[INFO] ✅ Found {len(matched)} package(s) for version {version}:")
        for p in matched:
            name = p.get("name", "?")
            ver = p.get("version", "?")
            pkg_type = p.get("package_type", "?")
            print(f"  - {name} v{ver} ({pkg_type})")
    else:
        print(f"[WARN] No packages found for version {version}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify artifacts in Package Registry")
    parser.add_argument("-u", "--url", required=True, help="Project API URL prefix")
    parser.add_argument("-t", "--token", required=True, help="GitLab private token")
    parser.add_argument("-v", "--version", required=True, help="Package version to verify")
    args = parser.parse_args()

    verify_packages(args.url, args.token, args.version)
