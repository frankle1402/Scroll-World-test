#!/usr/bin/env bash
set -euo pipefail
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
base64 --decode \
  "$HERE/seedance-minimal-test-480p.mp4.b64" \
  > "$HERE/seedance-minimal-test-480p.mp4"
printf 'Restored %s\n' "$HERE/seedance-minimal-test-480p.mp4"
sha256sum "$HERE/seedance-minimal-test-480p.mp4"
