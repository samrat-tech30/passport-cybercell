import { useEffect, useState } from "react";
import { api, ApiError } from "../lib/api/client";
import type { EvalResult } from "../lib/api/types";
import { Illustration } from "./Illustration";

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
          <p className="eyebrow">Scoreboard</p>
          <h1 className="display">
            Attack works before. <mark className="hl">Fails after.</mark>
          </h1>
          <p className="lead">Every scenario runs twice, shield off and on, in replay mode. Numbers are measured, not typed.</p>
        </div>
        <button type="button" className="btn btn--brand" onClick={run} disabled={busy}>
          {busy ? "Running all scenarios…" : "Run evaluation"}
        </button>
      </header>
      {error && <p className="error" role="alert">{error}</p>}
      {!result && !busy && !error && (
        <div className="empty">
          <Illustration scene="ledger" className="empty__art" />
          <p className="h2">No evaluation yet.</p>
          <p className="muted">Press Run evaluation. It runs every scenario with the shield off, then on.</p>
        </div>
      )}
      {result && (
        <>
          <section className="metrics" aria-label="Results">
            <div className="metric">
              <span className="metric__label">Attacks that got through</span>
              <span className="metric__pair">
                <span className="metric__off">{result.summary.off.attacks_landed}/{result.summary.off.attacks_total}</span>
                <span className="metric__arrow" aria-label="then">→</span>
                <span className="metric__on">{result.summary.on.attacks_landed}/{result.summary.on.attacks_total}</span>
              </span>
              <span className="metric__note">shield off → shield on</span>
            </div>
            <div className="metric">
              <span className="metric__label">Legitimate tasks completed</span>
              <span className="metric__pair">
                <span>{result.summary.off.legit_done}/{result.summary.off.legit_total}</span>
                <span className="metric__arrow" aria-label="then">→</span>
                <span className="metric__on">{result.summary.on.legit_done}/{result.summary.on.legit_total}</span>
              </span>
              <span className="metric__note">shield off → shield on</span>
            </div>
            <div className="metric">
              <span className="metric__label">Approval popups on clean legit tasks</span>
              <span className="metric__pair"><span className="metric__on">{result.summary.on.approvals_on_clean_legit_tasks}</span></span>
              <span className="metric__note">shield on</span>
            </div>
          </section>
          <p className="verdict-line" role="status">
            <strong>Shield on:</strong> {result.summary.on.attacks_landed} of {result.summary.on.attacks_total} attacks got through, and{" "}
            {result.summary.on.legit_done} of {result.summary.on.legit_total} legitimate tasks still finished.
            <span className="muted"> Shield off: {result.summary.off.attacks_landed} of {result.summary.off.attacks_total} got through.</span>
          </p>
          <table className="table">
            <thead>
              <tr>
                <th>Scenario</th><th>Category</th><th>Attack landed (off)</th><th>Attack landed (on)</th>
                <th>Legit done (on)</th><th className="num">Asks</th><th className="num">Denies</th>
              </tr>
            </thead>
            <tbody>
              {ids.map((id) => {
                const off = get(id, false)!;
                const on = get(id, true)!;
                return (
                  <tr key={id}>
                    <td><span className="cell-id">{id.toUpperCase()}</span> {on.title}</td>
                    <td className="muted nowrap">{on.category.replace(/_/g, " ")}</td>
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
