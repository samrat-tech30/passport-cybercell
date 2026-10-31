import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "../lib/api/client";
import type { AuditRow, AuditVerify } from "../lib/api/types";
import { Illustration } from "./Illustration";

export function AuditView() {
  const [rows, setRows] = useState<AuditRow[]>([]);
  const [verify, setVerify] = useState<AuditVerify | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setError(null);
    Promise.all([api.audit(100), api.verifyAudit()]).then(
      ([a, v]) => {
        setRows(a.items);
        setVerify(v);
      },
      (e) => setError(e instanceof ApiError ? e.message : "Couldn't load the audit log."),
    );
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="page">
      <header className="page__head">
        <div>
          <p className="eyebrow">Audit</p>
          <h1 className="display">A log that shows if anyone edits it.</h1>
          <p className="lead">Each row stores the hash of the row before it. Change any row and the chain breaks from there.</p>
        </div>
        <button type="button" className="btn btn--brand" onClick={load}>Verify chain</button>
      </header>
      {error && <p className="error" role="alert">{error}</p>}
      {verify && (
        <p className={`chain ${verify.ok ? "chain--ok" : "chain--bad"}`} role="status">
          <span className="chain__state">{verify.ok ? "Chain intact" : `Chain broken at row ${verify.broken_at}`}</span>
          <span className="chain__meta">{verify.rows} rows</span>
          {verify.ok && <span className="chain__meta mono">head {verify.head.slice(0, 12)}</span>}
        </p>
      )}
      {rows.length === 0 && !error ? (
        <div className="empty">
          <Illustration scene="ledger" className="empty__art" />
          <p className="h2">Nothing logged yet.</p>
          <p className="muted">Connect an agent or run a scenario on the Demo tab. Every decision lands here.</p>
        </div>
      ) : (
        <table className="table">
          <thead>
            <tr><th className="num">#</th><th>Time</th><th>Kind</th><th>Detail</th><th>Hash</th></tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.seq}>
                <td className="num">{r.seq}</td>
                <td className="nowrap">{new Date(r.ts * 1000).toLocaleTimeString()}</td>
                <td>{r.kind}</td>
                <td className="mono">
                  {r.kind === "decision" || r.kind === "gateway_decide"
                    ? `${String(r.payload.tool)} → ${String(r.payload.verdict)} (${String(r.payload.rule_id)})`
                    : JSON.stringify(r.payload).slice(0, 80)}
                </td>
                <td className="mono muted">{r.hash.slice(0, 12)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
