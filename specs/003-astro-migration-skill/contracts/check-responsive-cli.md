# Contract: `astro-site/scripts/check-responsive.mjs`

Covers FR-005, FR-006.

The interface the skill (`SKILL.md`) uses to invoke the automated
overflow check — a plain Node CLI script, not a library import, so the
skill can invoke it as a shell command like any other verification step.

## Invocation

```sh
node astro-site/scripts/check-responsive.mjs <preview-base-url> <path> [<path> ...]
```

| Argument | Notes |
|----------|-------|
| `<preview-base-url>` | Base URL of the running `astro preview` server serving the real build output (research.md #2), e.g. `http://localhost:4321`. |
| `<path>` (one or more) | One or more page paths to check, e.g. `/branding/`. Each is checked independently at all five viewports. |

## Output

Prints one JSON object to stdout:

```json
{
  "results": {
    "/branding/": { "320": true, "375": true, "768": true, "1024": false, "1920": true }
  }
}
```

`results[path][viewport]` is `true` when that path has **no** horizontal
overflow at that viewport width (research.md #3), `false` when it does.
Viewport keys are exactly `"320"`, `"375"`, `"768"`, `"1024"`, `"1920"`
(FR-005) — always all five, for every requested path.

## Exit code

- `0` — the script ran successfully (regardless of whether individual
  pages passed or failed their overflow checks — that result is in the
  JSON output, not the exit code).
- Non-zero — the script itself failed (e.g. the preview server at
  `<preview-base-url>` is unreachable, or a requested path returned a
  non-2xx response). stderr carries a human-readable reason.

## Guarantees

- Every requested path is checked at all five specified viewport widths —
  never a subset (FR-005).
- The script makes no WordPress calls and has no MCP dependency — it only
  ever talks to the local `astro preview` server (research.md #6's "no
  WordPress HTTP client" constraint applies to the whole feature,
  including this script).
