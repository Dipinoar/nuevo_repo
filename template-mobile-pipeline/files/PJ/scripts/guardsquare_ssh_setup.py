#!/usr/bin/env python3
import os
import subprocess
import sys

def run(cmd, env=None):
	print(f"[DEBUG] Running: {' '.join(cmd)}")
	try:
		result = subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
		if result.stdout.strip():
			print(result.stdout.strip())
		return result.stdout.strip()
	except subprocess.CalledProcessError as e:
		print(f"[ERROR] Command failed: {e.stderr.strip()}")
		sys.exit(1)

print("[INFO] Starting Guardsquare SSH setup...")

key_path = os.getenv("SSH_GUARDSQUARE_KEY")  # File variable path
passphrase = os.getenv("SSH_GUARDSQUARE_PASS", "")

if not key_path or not os.path.isfile(key_path):
	print(f"[ERROR] SSH key file not found at {key_path}.")
	sys.exit(1)

print(f"[INFO] Using SSH key at: {key_path}")
os.chmod(key_path, 0o600)

# Validar que el socket existe
ssh_sock = os.getenv("SSH_AUTH_SOCK")
ssh_pid = os.getenv("SSH_AGENT_PID")
if not ssh_sock or not os.path.exists(ssh_sock):
	print("[ERROR] SSH_AUTH_SOCK is missing or invalid. ssh-agent may not be running.")
	sys.exit(1)

env = os.environ.copy()

if passphrase:
	print(f"[INFO] Key is encrypted. Using passphrase (length: {len(passphrase)}).")
	askpass_script = "./askpass.sh"
	with open(askpass_script, "w") as f:
		f.write("#!/bin/sh\n")
		f.write("echo \"$SSH_GUARDSQUARE_PASS\"\n")
	os.chmod(askpass_script, 0o700)
	env["SSH_ASKPASS_REQUIRE"] = "force"
	env["SSH_ASKPASS"] = askpass_script
	env["DISPLAY"] = ":9999"
	run(["setsid", "ssh-add", key_path], env=env)
else:
	print("[INFO] Adding key without passphrase...")
	run(["ssh-add", key_path], env=env)

print("[INFO] Verifying loaded keys...")
run(["ssh-add", "-l"], env=env)

print("[INFO] SSH agent ready for Guardsquare CLI.")