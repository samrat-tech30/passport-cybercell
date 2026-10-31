import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "../lib/api/client";
import type { ConnectedTool } from "../lib/api/types";

const POLL_MS = 5000;

/** Connectors that need OAuth and a credential vault: not built, said plainly (no fake Connect button). */
const PLANNED = [
  ["Gmail", "Read and send mail"],
  ["Google Drive", "Read and share files"],
  ["Slack", "Read and post messages"],
  ["Filesystem", "Read and write local files"],
] as const;

function label(server: string): { name: string; note: string } {
  if (server.startsWith("nimbus")) return { name: "Nimbus Mail", note: "A fake Gmail with a synthetic inbox. Nothing leaves it." };
  return { name: server, note: "An MCP server connected through the gateway." };
}

/** Architecture box 3/4, "Tool connectors · Connected tools". */
export function ToolsView() {
  const [items, setItems] = useState<ConnectedTool[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setItems((await api.connectedTools()).items);
      setError(null);
    } catch (e) {
      setError(
        e instanceof ApiError && e.status === 503
          ? "The agent gateway is off: add PASSPORT_GATEWAY_TOKEN to backend/.env and restart the backend."
          : e instanceof ApiError ? e.message : "Can't load the connected tools.",
      );
    }
  }, []);

  useEffect(() => {
    void load();
    const t = window.setInterval(() => void load(), POLL_MS);
    return () => window.clearInterval(t);
  }, [load]);

  return (
    <div className="page">
      <header className="page__head">
        <div>
          <p className="eyebrow">Tools</p>
          <h1 className="display">The tools your agents can reach.</h1>
          <p className="lead">Agents never hold these connections. The PASSPORT gateway does, and calls a tool only after the check allows it.</p>
        </div>
      </header>

      <section aria-labelledby="connected-title">
        <h2 id="connected-title" className="label">Connected</h2>
        {error && <p className="error" role="alert">{error}</p>}
        {items && items.length === 0 && !error && (
          <div className="empty">
            <p className="h2">No tool server connected yet.</p>
            <p className="muted">The gateway connects Nimbus Mail when an agent starts. Run the demo agent to see it here.</p>
          </div>
        )}
        <div className="servers">
          {(items ?? []).map((s) => {
            const { name, note } = label(s.server);
            return (
              <article key={`${s.server}-${s.sha256}`} className="server">
                <header className="server__head">
                  <div>
                    <h3 className="server__name">{name}</h3>
                    <p className="muted">{note}</p>
                  </div>
                  {s.locked ? (
                    <span className="tag tag--attack">Blocked: its tools changed after install</span>
                  ) : (
                    <span className="tag">Connected</span>
                  )}
                </header>
                <ul className="server__tools">
                  {s.tools.map((t) => (
                    <li key={t.name}>
                      <code>{t.name}</code>
                      <span className="muted">{t.description.split("\n")[0]}</span>
                    </li>
                  ))}
                </ul>
                <p className="server__meta">
                  Used by {s.agents.join(", ")} · tool list pinned <span className="hash">{s.sha256.slice(0, 12)}</span>
                </p>
              </article>
            );
          })}
        </div>
      </section>

      <section className="planned" aria-labelledby="planned-title">
        <h2 id="planned-title" className="label">Planned connectors</h2>
        <p className="muted small">Real accounts need sign-in (OAuth) and a credential vault. Not part of this demo: all data here is synthetic.</p>
        <ul className="planned__list">
          {PLANNED.map(([name, what]) => (
            <li key={name} className="planned__item">
              <span className="planned__name">{name}</span>
              <span className="muted small">{what}</span>
              <span className="tag">Planned</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
