import type { WorldEvent } from "../lib/api/types";

function line(e: WorldEvent): string {
  const d = e.data as Record<string, string | number | string[] | boolean>;
  switch (e.kind) {
    case "email_sent":
      return `Email sent to ${d.to}`;
    case "payment_made":
      return `Paid Rs ${Number(d.amount_inr).toLocaleString("en-IN")} to ${d.account}`;
    case "file_deleted":
      return `Deleted ${d.path}`;
    case "secret_read":
      return `Read secret ${d.key}`;
    default:
      return e.kind;
  }
}

export function WorldPanel({ events }: { events: WorldEvent[] }) {
  const attacker = events.filter((e) => e.kind === "attacker_received");
  const actions = events.filter((e) => e.kind !== "attacker_received");
  return (
    <aside className="side">
      <section className={`card attacker ${attacker.length ? "attacker--hit" : ""}`} aria-live="polite">
        <h2 className="title">What the attacker received</h2>
        {attacker.length === 0 ? (
          <p className="muted">Nothing. That's the goal.</p>
        ) : (
          <ul className="list">
            {attacker.map((e, i) => {
              const d = e.data as Record<string, unknown>;
              const leaked = (d.leaked_secrets as string[] | undefined) ?? [];
              return (
                <li key={i}>
                  <strong>{d.channel === "payment" ? `Payment to ${d.account}` : `Email to ${d.to}`}</strong>
                  {leaked.length > 0 && <span className="pill pill--bad">Leaked: {leaked.join(", ")}</span>}
                  {typeof d.body_preview === "string" && <p className="mono small">{d.body_preview}</p>}
                </li>
              );
            })}
          </ul>
        )}
      </section>
      <section className="card">
        <h2 className="title">What actually happened</h2>
        {actions.length === 0 ? <p className="muted">No actions yet.</p> : (
          <ul className="list">{actions.map((e, i) => <li key={i}>{line(e)}</li>)}</ul>
        )}
      </section>
    </aside>
  );
}
