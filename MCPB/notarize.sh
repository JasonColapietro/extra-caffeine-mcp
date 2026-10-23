#!/bin/bash
# Submit the already signed helper. notarytool credentials stay in Keychain.
set -euo pipefail
cd "$(dirname "$0")/.."
profile="${1:?Usage: bash MCPB/notarize.sh KEYCHAIN_PROFILE}"
out="$PWD/dist/mcpb"
helper="$out/stage/server/extra-caffeine-adapter"
codesign --verify --strict "$helper"
codesign -dv "$helper" 2>&1 | rg 'Authority=Developer ID Application: Chester Wong Consulting Ltd|flags=.*runtime'
/usr/bin/ditto -c -k --keepParent "$helper" "$out/notarization.zip"
xcrun notarytool submit "$out/notarization.zip" --keychain-profile "$profile" --wait --output-format json > "$out/notarization.json"
python3 - "$out/notarization.json" <<'PY'
import json, sys
receipt = json.load(open(sys.argv[1]))
print(json.dumps(receipt, indent=2))
if receipt.get('status') != 'Accepted':
    raise SystemExit('Notarization not accepted; do not publish.')
PY
# A raw executable cannot carry a stapled ticket. Verify Apple's online ticket.
spctl --assess --type execute --verbose=4 "$helper" 2> "$out/gatekeeper.txt"
cat "$out/gatekeeper.txt"
# Notarization does not change helper bytes. Never rebuild/re-sign after submission.
(cd "$out" && shasum -a 256 -c SHA256SUMS)
