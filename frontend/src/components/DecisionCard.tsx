import type { Decision, Evidence } from "../lib/api/types";
import { preview, whereFrom } from "../lib/format";
import { Stamp } from "./Stamp";

interface Props {
  d: Decision;
  onEvidence: (ev: Evidence) => void;
}

export function DecisionCard({ d, onEvidence }: Props) {
  const passportByArg = new Map(d.passports.map((p) => [p.arg, p]));
  const evidence = d.passports.find((p) => p.segment_id && p.origin === "untrusted") ?? d.reasons.find((r) => r.evidence?.segment_id)?.evidence;

  return (
    <article className={`card decision decision--${d.verdict.toLowerCase()}`} aria-label={`${d.tool}: ${d.verdict}`}>
      <header className="decision__head">
        <span className="decision__step">Step {d.step}</span>
        <code className="decision__tool">{d.tool}</code>
        <Stamp verdict={d.verdict} shieldOn={d.shield_on} executed={d.executed} />
      </header>

      {Object.keys(d.args).length > 0 && (
        <ul className="args">
          {Object.entries(d.args).map(([k, v]) => {
            const p = passportByArg.get(k);
            return (
              <li key={k} className={`arg ${p ? `origin--${p.origin}` : ""}`}>
                <span className="arg__name">{k}</span>
                <span className="arg__value">{preview(v)}</span>
                {p && <span className="arg__origin">{whereFrom(p)}</span>}
              </li>
            );
          })}
        </ul>
      )}

      <p className="decision__msg">{d.message}</p>

      <footer className="decision__foot">
        <span className="rules">{d.reasons.map((r) => r.rule_id).join(" · ") || "No rule fired"}</span>
        {!d.shield_on && d.executed && d.verdict !== "ALLOW" && <span className="pill pill--bad">Shield off: it ran</span>}
        {d.approval && <span className="pill">You {d.approval === "approved" ? "approved" : d.approval === "rejected" ? "rejected" : "didn't answer"}</span>}
        {evidence?.segment_id && (
          <button type="button" className="btn btn--quiet" onClick={() => onEvidence(evidence)}>
            Show evidence
          </button>
        )}
      </footer>
    </article>
  );
}
