#!/bin/bash
# Submit the already signed helper. notarytool credentials stay in Keychain.
set -euo pipefail
cd "$(dirname "$0")/.."
profile="${1:?Usage: bash MCPB/notarize.sh KEYCHAIN_PROFILE}"
out="$PWD/dist/mcpb"
helper="$out/stage/server/extra-caffeine-adapter"
codesign --verify --strict "$helper"
codesign -dvvv "$helper" 2> "$out/signing.txt"
rg -q 'Authority=Developer ID Application: Chester Wong Consulting Ltd \(3GPMM2KM4R\)' "$out/signing.txt"
rg -q 'flags=.*runtime' "$out/signing.txt"
/usr/bin/ditto -c -k --keepParent "$helper" "$out/notarization.zip"
xcrun notarytool submit "$out/notarization.zip" --keychain-profile "$profile" --wait --output-format json > "$out/notarization.json"
python3 - "$out/notarization.json" <<'PY'
import json, sys
receipt = json.load(open(sys.argv[1]))
print(json.dumps(receipt, indent=2))
if receipt.get('status') != 'Accepted':
    raise SystemExit('Notarization not accepted; do not publish.')
PY
# A raw executable cannot carry a stapled ticket; use Apple's code requirement.
codesign --verify --strict --all-architectures -R=notarized --check-notarization --verbose=4 "$helper" 2> "$out/notarization-check.txt"
cat "$out/notarization-check.txt"
# Notarization does not change helper bytes. Never rebuild/re-sign after submission.
(cd "$out" && shasum -a 256 -c SHA256SUMS)
