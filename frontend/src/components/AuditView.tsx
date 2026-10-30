import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "../lib/api/client";
import type { AuditRow, AuditVerify } from "../lib/api/types";

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
          <h1 className="display">Tamper-evident audit log</h1>
          <p className="muted">Each row stores the hash of the row before it. Edit any row and the chain breaks there.</p>
        </div>
        <button type="button" className="btn btn--brand" onClick={load}>Verify chain</button>
      </header>
      {error && <p className="error" role="alert">{error}</p>}
      {verify && (
        <p className={`pill ${verify.ok ? "pill--ok" : "pill--bad"}`} role="status">
          {verify.ok ? `Chain intact · ${verify.rows} rows · head ${verify.head.slice(0, 12)}` : `Chain broken at row #${verify.broken_at}`}
        </p>
      )}
      <table className="table">
        <thead>
          <tr><th>#</th><th>Time</th><th>Kind</th><th>Detail</th><th>Hash</th></tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.seq}>
              <td className="num">{r.seq}</td>
              <td className="num">{new Date(r.ts * 1000).toLocaleTimeString()}</td>
              <td>{r.kind}</td>
              <td className="mono small">
                {r.kind === "decision"
                  ? `${String(r.payload.tool)} → ${String(r.payload.verdict)} (${String(r.payload.rule_id)})`
                  : JSON.stringify(r.payload).slice(0, 80)}
              </td>
              <td className="mono small">{r.hash.slice(0, 12)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
