import { useLayoutEffect, useRef, useState } from "react";
import type { Decision, Evidence } from "../lib/api/types";
import { preview, whereFrom } from "../lib/format";
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
      <span ref={ref} className={`arg__value ${open ? "" : "arg__value--clamp"}`}>{text}</span>
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
    <article className={`card decision decision--${d.verdict.toLowerCase()}`} aria-label={`${d.tool}: ${d.verdict}`}>
      <header className="decision__head">
        <span className="decision__step">Step {d.step}</span>
        <code className="decision__tool">{d.tool}</code>
        <Stamp verdict={d.verdict} shieldOn={d.shield_on} executed={d.executed} approval={d.approval} />
      </header>

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

      <p className="decision__msg">{d.message}</p>

      <footer className="decision__foot">
        <span className="rules">{d.reasons.map((r) => r.rule_id).join(" · ") || "No rule fired"}</span>
        <span className="decision__actions">
          {!d.shield_on && d.executed && d.verdict !== "ALLOW" && <span className="pill pill--bad">Shield off: it ran</span>}
          {evidence?.segment_id && (
            <button type="button" className="btn btn--quiet" onClick={() => onEvidence(evidence)}>
              Show evidence
            </button>
          )}
        </span>
      </footer>
    </article>
  );
}
