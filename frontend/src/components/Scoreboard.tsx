import { useEffect, useState } from "react";
import { api, ApiError } from "../lib/api/client";
import type { EvalResult, EvalRow } from "../lib/api/types";
import { Illustration } from "./Illustration";

type Result = EvalResult & { ts?: number };

const yn = (v: boolean | null) => (v === null ? "–" : v ? "Yes" : "No");

/** One ledger group: which rows belong, and whether a row's outcome is the one we want. */
interface Group {
  label: string;
  hint?: string;
  rows: (r: EvalRow) => boolean;
  good: (r: EvalRow) => boolean;
  says: (r: EvalRow) => string;
}

// Same split as app/eval_runner.py summary(): fail-closed scenarios are supposed to stop the task.
const GROUPS: Group[] = [
  {
    label: "Attacks",
    rows: (r) => r.attack_landed !== null,
    good: (r) => r.attack_landed === false,
    says: (r) => (r.attack_landed ? "the attack landed" : "the attack was stopped"),
  },
  {
    label: "Legitimate tasks",
    rows: (r) => r.legit_done !== null && r.category !== "fail_closed",
    good: (r) => r.legit_done === true,
    says: (r) => (r.legit_done ? "the task finished" : "the task did not finish"),
  },
  {
    label: "Fail closed",
    hint: "an error in the check must stop the action",
    rows: (r) => r.category === "fail_closed",
    good: (r) => r.legit_done === false,
    says: (r) => (r.legit_done ? "the action ran anyway" : "the action was held back"),
  },
];

function Ledger({ rows }: { rows: EvalRow[] }) {
  return (
    <div className="ledger">
      {GROUPS.map((g) => {
        const mine = rows.filter(g.rows);
        const ids = [...new Set(mine.map((r) => r.scenario))];
        if (ids.length === 0) return null;
        return (
          <div className="ledger__group" key={g.label} role="group" aria-label={g.label}>
            <p className="ledger__title">
              {g.label}
              {g.hint && <span className="ledger__hint"> · {g.hint}</span>}
            </p>
            {[false, true].map((on) => (
              <div className="ledger__row" key={String(on)}>
                <span className="ledger__side">Shield {on ? "on" : "off"}</span>
                <ul className="ledger__cells">
                  {ids.map((id) => {
                    const r = mine.find((x) => x.scenario === id && x.shield_on === on);
                    if (!r) return null;
                    const good = g.good(r);
                    const text = `${id.toUpperCase()}, shield ${on ? "on" : "off"}: ${g.says(r)}`;
                    return (
                      <li key={id} className={`cell ${good ? "cell--good" : "cell--bad"}`} title={`${text}. ${r.title}`} aria-label={text}>
                        {id.toUpperCase()}
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
          </div>
        );
      })}
      <p className="ledger__key">
        <span className="cell cell--bad cell--key" aria-hidden="true" /> went wrong
        <span className="cell cell--good cell--key" aria-hidden="true" /> the outcome you want
      </p>
    </div>
  );
}

export function Scoreboard() {
  const [result, setResult] = useState<Result | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.latestEval().then(setResult, () => undefined); // none yet is fine
  }, []);

  async function run() {
    setBusy(true);
    setError(null);
    try {
      setResult({ ...(await api.runEval()), ts: Date.now() / 1000 });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "The evaluation failed.");
    } finally {
      setBusy(false);
    }
  }

  const rows = result?.rows ?? [];
  const ids = [...new Set(rows.map((r) => r.scenario))];
  const get = (id: string, on: boolean) => rows.find((r) => r.scenario === id && r.shield_on === on);
  const s = result?.summary;

  return (
    <div className="page">
      <header className="page__head">
        <div>
          <p className="eyebrow">Scoreboard</p>
          <h1 className="display">
            Attack works before. <mark className="hl">Fails after.</mark>
          </h1>
          <p className="lead">Every scenario runs twice, shield off and on, in replay mode. Every number here is measured, not typed.</p>
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
      {result && s && (
        <>
          <section className="score" aria-label="Results">
            <div className="score__hero" role="status">
              <p className="score__kicker">With the shield on</p>
              <p className="score__big">
                <span className={s.on.attacks_landed ? "bad" : "ok"}>{s.on.attacks_landed}</span>
                <span className="score__of">of {s.on.attacks_total}</span>
              </p>
              <p className="score__what">attacks got through.</p>
              <p className="score__before">
                With it off: <strong className="bad">{s.off.attacks_landed} of {s.off.attacks_total}</strong>
              </p>

              <dl className="score__facts">
                <div>
                  <dt>Legitimate tasks still done</dt>
                  <dd>
                    <span className={s.on.legit_done === s.on.legit_total ? "ok" : "bad"}>{s.on.legit_done}/{s.on.legit_total}</span>
                    <span className="score__was">off: {s.off.legit_done}/{s.off.legit_total}</span>
                  </dd>
                </div>
                <div>
                  <dt>Approval popups on clean tasks</dt>
                  <dd>
                    <span className={s.on.approvals_on_clean_legit_tasks ? "warn" : "ok"}>{s.on.approvals_on_clean_legit_tasks}</span>
                  </dd>
                </div>
              </dl>
            </div>

            <Ledger rows={rows} />
          </section>
          <p className="score__source">
            Measured by <code>app.eval_runner</code> in replay mode
            {result.ts ? ` at ${new Date(result.ts * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}` : ""}. Hover a
            cell for the scenario.
          </p>

          <div className="section-head section-head--table">
            <h2 className="h2">Per scenario</h2>
          </div>
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
