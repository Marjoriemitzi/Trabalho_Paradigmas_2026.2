#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

PLAYWRIGHT_VERSION=$(node -p "require('@playwright/test/package.json').version")

docker run --rm --init --ipc=host \
  -v "$PWD:/work" \
  -v /work/node_modules \
  -w /work \
  "mcr.microsoft.com/playwright:v${PLAYWRIGHT_VERSION}-noble" \
  bash -lc "npm ci && npm test"