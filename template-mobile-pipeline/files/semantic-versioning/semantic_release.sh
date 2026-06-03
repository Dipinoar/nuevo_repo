#!/bin/bash
set -Eeo pipefail

echo "[INFO] Instalando Semantic Release y plugins..."
npm install -g semantic-release@24.2.9 \
	@semantic-release/gitlab@13.3.0 \
	@semantic-release/changelog@6.0.3 \
	@semantic-release/git@10.0.1 \
	@semantic-release/gitlab-config@14.0.1 \
	semantic-release-yaml@1.1.3 \
	@semantic-release/exec@7.1.0
