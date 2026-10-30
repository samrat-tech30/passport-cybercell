import { useLayoutEffect, useRef, useState } from "react";
import type { Decision, Evidence } from "../lib/api/types";
import { headline, preview, ruleChip, whereFrom } from "../lib/format";
import { Stamp } from "./Stamp";

interface Props {
  d: Decision;
  onEvidence: (ev: Evidence) => void;
}

/** One argument. Long values clamp to 3 lines with a toggle; nothing overflows the card. */
function ArgValue({ value }: { value: unknown }) {
  const ref = useRef<HTMLSpanElement>(null);
  const [clamped, setClamped] = useState(false);
  const [open, setOpen] = useState(false);
  const text = preview(value, 600);

  useLayoutEffect(() => {
    const el = ref.current;
    if (el && !open) setClamped(el.scrollHeight > el.clientHeight + 1);
  }, [text, open]);

  return (
    <span className="arg__body">
      <span ref={ref} className={`arg__value ${open ? "" : "arg__value--clamp"}`}><span className="ink">{text}</span></span>
      {(clamped || open) && (
        <button type="button" className="link" aria-expanded={open} onClick={() => setOpen((v) => !v)}>
          {open ? "Show less" : "Show full value"}
        </button>
      )}
    </span>
  );
}

export function DecisionCard({ d, onEvidence }: Props) {
  const passportByArg = new Map(d.passports.map((p) => [p.arg, p]));
  const evidence = d.passports.find((p) => p.segment_id && p.origin === "untrusted") ?? d.reasons.find((r) => r.evidence?.segment_id)?.evidence;
  // Sink arguments (they carry a passport) first and loud; free text (subject, body) after and quiet.
  const entries = Object.entries(d.args).sort(([a], [b]) => Number(passportByArg.has(b)) - Number(passportByArg.has(a)));

  return (
    <article className={`decision decision--${d.verdict.toLowerCase()} ${d.shield_on ? "" : "decision--unguarded"}`} aria-label={`Step ${d.step}, ${d.tool}: ${d.verdict}`}>
      <header className="decision__head">
        <span className="decision__step" aria-hidden="true">{String(d.step).padStart(2, "0")}</span>
        <span className="decision__id">
          <span className="decision__kicker">Step {d.step} · tool call</span>
          <code className="decision__tool">{d.tool}</code>
        </span>
        <Stamp verdict={d.verdict} shieldOn={d.shield_on} executed={d.executed} approval={d.approval} />
      </header>

      <p className="decision__headline">{headline(d)}</p>

      {entries.length > 0 && (
        <ul className="args">
          {entries.map(([k, v]) => {
            const p = passportByArg.get(k);
            return (
              <li key={k} className={p ? `arg arg--sink origin--${p.origin}` : "arg arg--free"}>
                <span className="arg__name">{k}</span>
                <ArgValue value={v} />
                {p && <span className="arg__origin">{whereFrom(p)}</span>}
              </li>
            );
          })}
        </ul>
      )}

      {/* The headline already names the risky value; the backend sentence is only needed when it doesn't */}
      {d.verdict !== "ALLOW" && !d.passports.some((p) => p.origin === "untrusted" || p.origin === "secret" || p.origin === "model_invented") && (
        <p className="decision__msg">{d.message}</p>
      )}

      <footer className="decision__foot">
        <span className="rules">
          {d.reasons.length === 0 ? (
            <span className="muted small">No rule fired</span>
          ) : (
            d.reasons.map((r) => {
              const c = ruleChip(r.rule_id);
              return <span key={r.rule_id} className="rule" title={c.title}>{c.label}</span>;
            })
          )}
        </span>
        <span className="decision__actions">
          {!d.shield_on && d.executed && d.verdict !== "ALLOW" && <span className="pill pill--bad">Shield off: it ran</span>}
          {evidence?.segment_id && (
            <button type="button" className="btn btn--outline btn--sm" onClick={() => onEvidence(evidence)}>
              Show evidence <span aria-hidden="true">→</span>
            </button>
          )}
        </span>
      </footer>
    </article>
  );
}
