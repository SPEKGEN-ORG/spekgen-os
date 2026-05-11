---
name: Claude Code MCP — type:stdio field required for stdio servers
description: Adding an MCP entry to ~/.claude.json without "type": "stdio" causes Claude Code to silently skip launching it (no log entries, server never starts).
type: feedback
originSessionId: 57841043-f116-44ae-a90e-75d6ba3b1741
---
**Discovered 2026-04-29 installing shadcn-ui-mcp-server.**

When adding a new MCP server to `~/.claude.json` under `mcpServers`, the `"type"` field is **required** even though many docs/examples omit it. Without it, Claude Code silently skips launching the server — zero log entries, no error, the entry just doesn't activate.

## Wrong (silently fails)

```json
"shadcn": {
  "command": "npx",
  "args": ["-y", "@jpisnice/shadcn-ui-mcp-server", "--framework", "react"]
}
```

## Right

```json
"shadcn": {
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@jpisnice/shadcn-ui-mcp-server", "--framework", "react"]
}
```

## Diagnostic technique used

1. Run the npx command manually in a terminal — confirms package itself works (server prints "Server started successfully - Mode: stdio").
2. Check `~/Library/Logs/Claude/claude.ai-web.log` for any mention of the server name. If ZERO mentions → Claude Code never even attempted to launch it → config issue.
3. Compare against a working MCP entry (e.g. `ghl`) — diff for missing fields.

## How to apply

Always include `"type": "stdio"` when adding new local MCP servers to `~/.claude.json`. For SSE or HTTP MCP servers, use `"type": "sse"` or `"type": "http"` respectively.

## Related

- Working MCP example: `ghl` in `~/.claude.json` mcpServers
- shadcn-ui-mcp-server install location: `~/.claude.json` user-scope (not project-scope)
- After config edit: must Cmd+Q Claude Code completely and re-open — file watcher does NOT pick up `mcpServers` changes mid-session.

## Second gotcha: nvm-managed node not in Claude Code PATH

Even with `"type": "stdio"` set, an MCP server using `"command": "npx"` can silently fail because Claude Code's launcher does NOT inherit nvm's PATH. `npx` lives at `~/.nvm/versions/node/vX.Y.Z/bin/npx` — invisible to Claude Code's spawned process.

**Working pattern (used by ghl which IS managed via Homebrew):**
```json
"command": "/opt/homebrew/bin/uv"
```
Absolute path. Always resolves.

**Fix for nvm-managed node MCP servers:**
1. `npm install -g <package>` to materialize the JS file at a stable absolute path.
2. Use the absolute node binary + absolute script path:
   ```json
   "command": "/Users/<you>/.nvm/versions/node/<ver>/bin/node",
   "args": ["/Users/<you>/.nvm/versions/node/<ver>/lib/node_modules/<scope>/<pkg>/build/index.js", ...]
   ```
3. This bypasses npx, PATH lookup, and the `#!/usr/bin/env node` shebang resolution entirely.

If you ever rebuild node via nvm to a new version, all MCP server configs using absolute nvm paths will break. Update them or symlink.
