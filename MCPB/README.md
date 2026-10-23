# Extra Caffeine MCPB adapter

This macOS-only binary adapter connects a local MCPB-compatible client to the user's separately installed **Extra Caffeine 1.2+** app. Requires macOS 14+, Intel or Apple silicon. The app is a separate paid purchase; it is not bundled or unlocked by this package.

Install the app from https://extracaffeine.chesterwong.com/ or the Mac App Store. Open it, enable **AI assistants**, then install the adapter in a client supporting MCPB binary extensions. Select that installed `.app` in the adapter's `app_path` setting. Both editions are supported; select the same edition you have open. For clients without MCPB, use the app's **Copy MCP settings** instead. Setup: https://extracaffeine.chesterwong.com/agent-setup.md.

The adapter checks the app's bundle, minimum version and vendor signature, then replaces itself with the installed executable running `--mcp`. It does not launch the GUI, purchase/install the app, enable control, change preferences, open network listeners or duplicate the MCP protocol. Stdin/stdout/stderr, exit status and process lifetime pass directly to the app's MCP process. Closed-app/disabled-access state is reported by the app as tool errors; tool discovery alone does not mean control is available. No extra tool prefix or client version compatibility is assumed.

Ask the user before starting or scheduling. Read status before/after mutations and reconcile timeouts before retrying. The app must stay open; schedules cannot wake a sleeping Mac. Closing the lid or manual/system safety sleep can still interrupt work. Cloud-only tasks may not need protection. A registry listing does not install or authorize anything.

## Build and validate

From the project root, run `bash MCPB/build.sh`. It compiles a universal binary and uses the official MCPB validator/packer. Set `EXTRA_CAFFEINE_SIGN_IDENTITY` to an existing Developer ID Application identity to sign the helper for distribution; default signing is ad hoc for local testing only. No private key is copied/exported. Output is under `dist/mcpb/`. Run `python3 MCPB/tests/test_adapter.py` after building.

The helper's Apple code signature and an optional MCPB archive signature are different. Local packaging success does not establish notarization, clean-Mac Gatekeeper acceptance, GUI installation compatibility or Registry listing. Keep the final artifact immutable after computing its hash. Public hosting, namespace authentication and Registry metadata/publication are separate release steps.
