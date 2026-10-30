import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "../lib/api/client";
import type { Evidence, SegmentView } from "../lib/api/types";
import { looksHidden } from "../lib/format";

interface Props {
  sessionId: string;
  evidence: Evidence;
  onClose: () => void;
}

export function EvidenceDrawer({ sessionId, evidence, onClose }: Props) {
  const [seg, setSeg] = useState<SegmentView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const ref = useRef<HTMLDialogElement>(null);
  const hit = useRef<HTMLLIElement>(null);

  useEffect(() => {
    if (ref.current && !ref.current.open) ref.current.showModal();
    if (!evidence.segment_id) return;
    api.segment(sessionId, evidence.segment_id).then(setSeg, (e) => setError(e instanceof ApiError ? e.message : "Couldn't load the source."));
  }, [sessionId, evidence.segment_id]);

  useEffect(() => {
    hit.current?.scrollIntoView({ block: "center" });
  }, [seg]);

  return (
    <dialog ref={ref} className="drawer" onClose={onClose} aria-labelledby="evidence-title">
      <header className="drawer__head">
        <div>
          <h2 id="evidence-title" className="title">{evidence.source ?? "Source"}</h2>
          <p className="muted">
            <code>{evidence.arg}</code> = <code>{evidence.value}</code> was found on line {evidence.line}. This text came from
            outside, so it can't choose where an action goes.
          </p>
        </div>
        <button type="button" className="btn btn--quiet" onClick={() => ref.current?.close()} autoFocus>
          Close
        </button>
      </header>
      {error && <p className="error">{error}</p>}
      {!seg && !error && <p className="muted">Loading the source…</p>}
      {seg && (
        <ol className="source">
          {seg.lines.map((line, i) => {
            const isHit = i + 1 === evidence.line;
            return (
              <li key={i} ref={isHit ? hit : undefined} className={isHit ? "source__line source__line--hit" : "source__line"}>
                <span className="source__no">{i + 1}</span>
                <span className="source__text">{line || " "}</span>
                {isHit && looksHidden(line) && <span className="pill pill--bad">Hidden in the original email</span>}
              </li>
            );
          })}
        </ol>
      )}
    </dialog>
  );
}
