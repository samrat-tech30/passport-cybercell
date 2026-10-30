Stretch (only after code freeze is safe): an MCP gateway so MCP clients (Claude Desktop, Cursor, VS Code) can be protected.

Use verify-before-use: read the installed `fastmcp` docs (standalone package; proxy + middleware APIs change between versions) before writing code. Plan first, wait for my OK.

Shape: a new folder `integrations/mcp_gateway/` (separate from backend/app so the core stays clean). A FastMCP server that exposes our fake tools, and middleware that, on every tool call, calls the backend's `POST /v1/decide` with the tool, args, and the text of previous tool outputs in this MCP session as `context` (trust "untrusted"). DENY → return an MCP error with the reason; REQUIRE_APPROVAL → error "needs approval in the PASSPORT UI" (keep it simple); ALLOW → forward. Label every tool output as untrusted context for later calls. Add an example Claude Desktop config in `integrations/mcp_gateway/README.md`. Test with a small MCP client script. Record in DECISIONS.md what worked.
