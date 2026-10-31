import { useEffect, useRef, useState } from "react";
import type { Decision } from "../lib/api/types";
import { preview, whereFrom } from "../lib/format";

interface Props {
  d: Decision;
  onAnswer: (approve: boolean) => void;
  /** epoch ms when the backend stops waiting (outside agents); shows a countdown */
  deadline?: number;
  /** who is asking, e.g. "Claude Desktop is waiting for your answer" */
  context?: string;
}

/** Shows only the risky values and where they came from. Reject has focus; Esc = reject. */
export function ApprovalDialog({ d, onAnswer, deadline, context }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const reject = useRef<HTMLButtonElement>(null);
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (deadline === undefined) return undefined;
    const t = window.setInterval(() => setNow(Date.now()), 250);
    return () => window.clearInterval(t);
  }, [deadline]);
  const left = deadline === undefined ? null : Math.max(0, Math.ceil((deadline - now) / 1000));
  const expired = left === 0;
  useEffect(() => {
    if (ref.current && !ref.current.open) ref.current.showModal();
    reject.current?.focus(); // showModal() focuses the first button (Approve); the safe choice must have focus
  }, []);
  const risky = d.reasons.filter((r) => r.verdict !== "ALLOW");

  return (
    <dialog
      ref={ref}
      className="dialog approval"
      aria-labelledby="approval-title"
      onCancel={(e) => {
        e.preventDefault();
        onAnswer(false);
      }}
    >
      <p className="eyebrow">{context ?? `Step ${d.step} needs you`}</p>
      <h2 id="approval-title" className="dialog__title">
        Allow <code>{d.tool}</code> to run?
      </h2>
      <ul className="args approval__list">
        {d.passports.map((p) => (
          <li key={p.arg} className={`arg arg--sink origin--${p.origin}`}>
            <span className="arg__name">{p.arg}</span>
            <span className="arg__body"><span className="arg__value"><span className="ink">{preview(p.value, 60)}</span></span></span>
            <span className="arg__origin">{whereFrom(p)}</span>
          </li>
        ))}
      </ul>
      {risky.length > 0 && (
        <div className="approval__why">
          <p className="label">Why you're being asked</p>
          <ul>
            {risky.map((r, i) => (
              <li key={i}>{r.message}</li>
            ))}
          </ul>
        </div>
      )}
      <div className="approval__actions">
        {left === null ? (
          <p className="muted small">No answer within 2 minutes counts as no.</p>
        ) : expired ? (
          <p className="error" role="alert">Timed out, so the call was refused.</p>
        ) : (
          <p className="muted small" aria-live="polite"><strong className="countdown">{left} s</strong> left. No answer counts as no.</p>
        )}
        <button type="button" className="btn btn--outline" disabled={expired} onClick={() => onAnswer(true)}>
          Approve
        </button>
        <button ref={reject} type="button" className="btn btn--ink" disabled={expired} onClick={() => onAnswer(false)}>
          Reject
        </button>
      </div>
    </dialog>
  );
}
