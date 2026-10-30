import { useEffect, useState, type CSSProperties } from "react";
import { api, ApiError } from "../lib/api/client";
import type { EvalResult } from "../lib/api/types";

const yn = (v: boolean | null) => (v === null ? "–" : v ? "Yes" : "No");

/** Counts from 0 to n once (eases out). Instant under reduced motion. Display only: the value is n. */
function Count({ n }: { n: number }) {
  const [shown, setShown] = useState(n);
  useEffect(() => {
    if (n === 0 || matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setShown(n);
      return;
    }
    const t0 = performance.now();
    let raf = 0;
    const tick = (t: number) => {
      const k = Math.min(1, (t - t0) / 700);
      setShown(Math.round(n * (1 - Math.pow(1 - k, 3))));
      if (k < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [n]);
  return <>{shown}</>;
}

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
          <p className="verdict-line" role="status">
            <span className="verdict-line__k">Shield on</span>
            {result.summary.on.attacks_landed} of {result.summary.on.attacks_total} attacks got through,{" "}
            {result.summary.on.legit_done} of {result.summary.on.legit_total} legit tasks still done.
            <span className="muted"> Shield off: {result.summary.off.attacks_landed} of {result.summary.off.attacks_total} got through.</span>
          </p>
          <div className="metrics">
            <div className="card metric">
              <span className="muted">Attacks that got through</span>
              <span className="metric__pair">
                <span className="metric__off"><Count n={result.summary.off.attacks_landed} />/{result.summary.off.attacks_total}</span>
                <span className="muted">→</span>
                <span className="metric__on"><Count n={result.summary.on.attacks_landed} />/{result.summary.on.attacks_total}</span>
              </span>
              <span className="muted small">shield off → shield on</span>
            </div>
            <div className="card metric">
              <span className="muted">Legitimate tasks completed</span>
              <span className="metric__pair">
                <span><Count n={result.summary.off.legit_done} />/{result.summary.off.legit_total}</span>
                <span className="muted">→</span>
                <span className="metric__on"><Count n={result.summary.on.legit_done} />/{result.summary.on.legit_total}</span>
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
              {ids.map((id, i) => {
                const off = get(id, false)!;
                const on = get(id, true)!;
                return (
                  <tr key={id} style={{ "--i": i } as CSSProperties}>
                    <td><strong>{id}</strong> <span className="muted">{on.title}</span></td>
                    <td className="muted">{on.category.replace("_", " ")}</td>
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
