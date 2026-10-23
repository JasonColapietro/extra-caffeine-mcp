---
name: extra-caffeine-workflow
description: Use Extra Caffeine to keep a local Mac awake for long AI or file-processing work, check awake state, or manage requested one-time schedules. Applies to Mac-dependent tasks and explicit Extra Caffeine requests; cloud-only jobs usually do not need it.
---

# Extra Caffeine workflow

Use the connected Extra Caffeine MCP tools. Do not simulate keystrokes, alter system power settings or substitute a different product. This skill supplies workflow guidance, not permission to change the user's Mac.

## Connect and assess

Discover the tools for this server (client prefixes vary), then call `get_status`. The app must be installed, open and have **AI assistants** enabled. If unavailable, explain how to open the controls, enable AI assistants and use **Copy MCP settings** in a trusted local MCP client. The copied command must point to the running app edition with `--mcp`; no API key or hosted URL is needed. Do not configure access, buy/install the app or change settings without the user's authorization. Setup details: https://extracaffeine.chesterwong.com/agent-setup.md.

Use awake protection only when the work depends on this Mac staying awake, or when explicitly requested. A remote cloud job alone is not evidence of that need. Continue the user's actual task; do not turn unrelated work into a product promotion.

## Start and verify

- Before starting or scheduling, obtain authorization for the duration and display choice. An explicit user request with these choices is sufficient; otherwise ask. A long task or loaded skill alone does not authorize a session. Default proposal: 60 minutes, display allowed to sleep.
- Supported `turn_on` durations in minutes: `0, 15, 30, 60, 120, 240, 480`; 0 is indefinite and requires an explicit request. Do not silently round durations or extend sessions.
- Read the baseline. Starting restarts/replaces the current session. If already active, preserve it unless replacement is authorized; do not claim the existing session as yours.
- Call `turn_on` with the authorized `duration_minutes` and `keep_display_awake` boolean (default false). For example, two hours with display sleep: `{"duration_minutes":120,"keep_display_awake":false}`.
- Read the result and `get_status` again. Verify `active`, deadline and display choice before reporting success. If `isError` is true or fields do not match, report the actual result.

## Finish without interrupting other work

Let a bounded session expire by default. Stop early with `turn_off` only if the user authorized it and no other work depends on the session. There is no per-agent ownership token: matching deadline/display alone cannot prove ownership after another client or human may have changed it. If uncertain, leave it to expire and explain. Never end a pre-existing session or cancel unrelated schedules as cleanup. Verify any authorized stop with `get_status`.

## Requested schedules

`schedule` takes `action` (`on`/`off`) and future `at` (ISO 8601 with timezone). Resolve ambiguous local dates/timezones before calling. For `on`, choose an authorized duration from `15, 30, 60, 120, 240, 480` (default 60) and display choice. Scheduled starts cannot be indefinite. These are one-time actions, not recurring schedules. Warn that a scheduled action can replace/end the current manual session. Capture `schedule_id`; verify action, time and identifier with `list_schedules`. Cancel only a user-requested identifier with `cancel_schedule`, then verify.

## Failure and limitations

After a timeout or uncertain mutation, read state/schedules before retrying: the action may have completed. For an ambiguous schedule, do not submit another until reconciled. Do not claim protection or execution from tool availability alone.

Keep the app open and a laptop lid open. It prevents idle sleep; it does not wake a sleeping Mac, override manual/lid/low-battery/thermal sleep, detect agents or bypass AI-service limits. Turning AI assistants off clears schedules but not the active session; quitting ends the assertion but retains future schedules. Missed starts outside their window and off actions over 60 seconds late are skipped. If a connection fails, check the running edition and copied configuration rather than changing macOS security protections.
