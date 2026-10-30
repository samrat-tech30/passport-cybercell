import { useEffect, useState } from "react";
import { api, ApiError } from "../lib/api/client";
import type { EvalResult } from "../lib/api/types";

const yn = (v: boolean | null) => (v === null ? "–" : v ? "Yes" : "No");

export function Scoreboard() {
  const [result, setResult] = useState<EvalResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.latestEval().then(setResult, () => undefined); // none yet is fine
  }, []);

  async function run() {
    setBusy(true);
    setError(null);
    try {
      setResult(await api.runEval());
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "The evaluation failed.");
    } finally {
      setBusy(false);
    }
  }

  const rows = result?.rows ?? [];
  const ids = [...new Set(rows.map((r) => r.scenario))];
  const get = (id: string, on: boolean) => rows.find((r) => r.scenario === id && r.shield_on === on);

  return (
    <div className="page">
      <header className="page__head">
        <div>
          <h1 className="display">Attack works before. Fails after.</h1>
          <p className="muted">Every scenario runs twice, shield off and on, in replay mode. Numbers are measured, not typed.</p>
        </div>
        <button type="button" className="btn btn--brand" onClick={run} disabled={busy}>
          {busy ? "Running all scenarios…" : "Run evaluation"}
        </button>
      </header>
      {error && <p className="error" role="alert">{error}</p>}
      {!result && !busy && <p className="muted">No evaluation yet. Press Run evaluation.</p>}
      {result && (
        <>
          <div className="metrics">
            <div className="card metric">
              <span className="muted">Attacks that got through</span>
              <span className="metric__pair">
                <span className="metric__off">{result.summary.off.attacks_landed}/{result.summary.off.attacks_total}</span>
                <span className="muted">→</span>
                <span className="metric__on">{result.summary.on.attacks_landed}/{result.summary.on.attacks_total}</span>
              </span>
              <span className="muted small">shield off → shield on</span>
            </div>
            <div className="card metric">
              <span className="muted">Legitimate tasks completed</span>
              <span className="metric__pair">
                <span>{result.summary.off.legit_done}/{result.summary.off.legit_total}</span>
                <span className="muted">→</span>
                <span className="metric__on">{result.summary.on.legit_done}/{result.summary.on.legit_total}</span>
              </span>
              <span className="muted small">shield off → shield on</span>
            </div>
            <div className="card metric">
              <span className="muted">Approval popups on clean legit tasks</span>
              <span className="metric__pair"><span className="metric__on">{result.summary.on.approvals_on_clean_legit_tasks}</span></span>
              <span className="muted small">shield on</span>
            </div>
          </div>
          <table className="table">
            <thead>
              <tr>
                <th>Scenario</th><th>Category</th><th>Attack landed (off)</th><th>Attack landed (on)</th>
                <th>Legit done (on)</th><th>Asks</th><th>Denies</th>
              </tr>
            </thead>
            <tbody>
              {ids.map((id) => {
                const off = get(id, false)!;
                const on = get(id, true)!;
                return (
                  <tr key={id}>
                    <td><strong>{id}</strong> <span className="muted">{on.title}</span></td>
                    <td>{on.category.replace("_", " ")}</td>
                    <td className={off.attack_landed ? "bad" : ""}>{yn(off.attack_landed)}</td>
                    <td className={on.attack_landed ? "bad" : on.attack_landed === false ? "ok" : ""}>{yn(on.attack_landed)}</td>
                    <td>{yn(on.legit_done)}</td>
                    <td className="num">{on.asks}</td>
                    <td className="num">{on.denies}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}
