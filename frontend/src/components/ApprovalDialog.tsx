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
  useEffect(() => {
    if (ref.current && !ref.current.open) ref.current.showModal();
  }, []);
  const risky = d.reasons.filter((r) => r.verdict !== "ALLOW");

  return (
    <dialog
      ref={ref}
      className="approval"
      aria-labelledby="approval-title"
      onCancel={(e) => {
        e.preventDefault();
        onAnswer(false);
      }}
    >
      <h2 id="approval-title" className="title">
        Allow <code>{d.tool}</code>?
      </h2>
      <ul className="approval__list">
        {d.passports.map((p) => (
          <li key={p.arg} className={`arg origin--${p.origin}`}>
            <span className="arg__name">{p.arg}</span>
            <span className="arg__value">{preview(p.value, 60)}</span>
            <span className="arg__origin">{whereFrom(p)}</span>
          </li>
        ))}
      </ul>
      <ul className="approval__why">
        {risky.map((r, i) => (
          <li key={i}>{r.message}</li>
        ))}
      </ul>
      <p className="muted small">No answer within 2 minutes counts as no.</p>
      <div className="approval__actions">
        <button type="button" className="btn btn--danger" autoFocus onClick={() => onAnswer(false)}>
          Reject
        </button>
        <button type="button" className="btn" onClick={() => onAnswer(true)}>
          Approve
        </button>
      </div>
    </dialog>
  );
}
