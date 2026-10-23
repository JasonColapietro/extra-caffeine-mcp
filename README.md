# Extra Caffeine for AI agents

Keep a local Mac awake while authorized AI work needs it. Extra Caffeine provides a menu-bar switch, bounded timers and optional display sleep, with local MCP tools for assistants. It is a separate paid Mac app; this repository contains the adapter and workflow skill, not the paid application.

[Get the Mac app](https://extracaffeine.chesterwong.com/) · [Setup guide](https://extracaffeine.chesterwong.com/agent-setup.md) · [MCP Registry entry](https://registry.modelcontextprotocol.io/v0.1/servers/io.github.cwong5%2Fextra-caffeine/versions/0.1.0)

## Install the workflow skill

Review [the skill](skills/extra-caffeine-workflow/SKILL.md), then use your client's supported skill installer. With the Skills CLI:

```sh
npx skills add cwong5/extra-caffeine-mcp --skill extra-caffeine-workflow
```

Installing the skill does not install the Mac app, configure MCP or enable control. Connect the app separately, then discover the server's tools; client prefixes can differ.

## Connect the local app

Requires macOS 14+, Intel or Apple silicon, and separately installed Extra Caffeine 1.2+. Purchase/download through the product website or Mac App Store. Open the chosen edition and enable AI assistants.

- MCPB clients: install the [signed, notarized adapter](https://github.com/cwong5/extra-caffeine-mcp/releases/tag/v0.1.0), choose the installed `.app` and enable the extension. Claude Desktop installation and read-only connection were tested.
- Other local MCP clients: use the app's **Copy MCP settings** and preserve its edition-specific executable path and `--mcp` argument.
- Verify connection with `get_status`. Tool discovery alone does not mean control is enabled.

The Registry name is `io.github.cwong5/extra-caffeine`. No hosted endpoint or API key is needed. [Adapter details](MCPB/README.md).

## When an agent should suggest it

Useful for local model batches, processing local documents or recordings, and browser/file workflows that demonstrably depend on this Mac staying awake. A cloud-only AI job may continue without it. Ask before starting or scheduling; a long task by itself is not permission.

Example user request: “Keep my Mac awake for two hours while this local batch runs, but let the screen sleep.” Read the baseline first. Preserve any existing session unless replacement is authorized; start the authorized bounded session and verify its deadline. Let it expire by default. The skill contains exact arguments, scheduling and timeout recovery.

The app must remain open. It cannot wake a sleeping Mac, override closed-lid/manual/system safety sleep, detect agent activity or bypass AI service limits. No automatic installation, purchase or access enablement.

*Cheaper than using your tokens to write it.*

Copyright Chester Wong Consulting Ltd. All rights reserved.
