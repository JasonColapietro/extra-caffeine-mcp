#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
adapter_out="$PWD/dist/mcpb"
adapter_stage="$adapter_out/stage"
mkdir -p "$adapter_stage/server" "$adapter_out/bin"
for adapter_arch in arm64 x86_64; do
  xcrun swiftc -O -target "$adapter_arch-apple-macos14.0" MCPB/Sources/main.swift -o "$adapter_out/bin/adapter-$adapter_arch"
done
xcrun lipo -create "$adapter_out/bin/adapter-arm64" "$adapter_out/bin/adapter-x86_64" -output "$adapter_stage/server/extra-caffeine-adapter"
# Signing here uses an existing identity; it does not export its private key.
adapter_identity="${EXTRA_CAFFEINE_SIGN_IDENTITY:--}"
if [ "$adapter_identity" = "-" ]; then
  codesign --force --sign - "$adapter_stage/server/extra-caffeine-adapter"
else
  codesign --force --options runtime --timestamp --sign "$adapter_identity" "$adapter_stage/server/extra-caffeine-adapter"
fi
cp MCPB/manifest.json "$adapter_stage/manifest.json"
cp MCPB/README.md "$adapter_stage/README.md"
npx --yes @anthropic-ai/mcpb@2.1.2 validate "$adapter_stage/manifest.json"
npx --yes @anthropic-ai/mcpb@2.1.2 pack "$adapter_stage" "$adapter_out/extra-caffeine-0.1.0.mcpb"
(cd "$adapter_out" && shasum -a 256 extra-caffeine-0.1.0.mcpb > SHA256SUMS)
codesign --verify --strict "$adapter_stage/server/extra-caffeine-adapter"
lipo -archs "$adapter_stage/server/extra-caffeine-adapter"
cat "$adapter_out/SHA256SUMS"
