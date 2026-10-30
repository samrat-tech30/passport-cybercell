import { useEffect, useRef } from "react";
import type { Decision } from "../lib/api/types";
import { preview, whereFrom } from "../lib/format";

interface Props {
  d: Decision;
  onAnswer: (approve: boolean) => void;
}

/** Shows only the risky values and where they came from. Reject has focus; Esc = reject. */
export function ApprovalDialog({ d, onAnswer }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const reject = useRef<HTMLButtonElement>(null);
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
      <p className="eyebrow">Step {d.step} needs you</p>
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
        <p className="muted small">No answer within 2 minutes counts as no.</p>
        <button type="button" className="btn btn--outline" onClick={() => onAnswer(true)}>
          Approve
        </button>
        <button ref={reject} type="button" className="btn btn--ink" onClick={() => onAnswer(false)}>
          Reject
        </button>
      </div>
    </dialog>
  );
}
