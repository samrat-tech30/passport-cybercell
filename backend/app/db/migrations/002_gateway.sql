-- Gateway sessions (contracts/README.md "Gateway API"). One row per sessions row created by the
-- MCP gateway. sessions.mode keeps its 001 CHECK (rebuilding that table would cascade-delete
-- decisions), so the row is stored with mode 'live' and the API reports mode "gateway" when a
-- gateway_sessions row exists.
CREATE TABLE IF NOT EXISTS gateway_sessions (
    session_id  TEXT PRIMARY KEY REFERENCES sessions(id) ON DELETE CASCADE,
    agent_name  TEXT NOT NULL,
    client      TEXT NOT NULL
);
