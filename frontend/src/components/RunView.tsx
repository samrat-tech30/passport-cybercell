import { useState } from "react";
import type { Evidence } from "../lib/api/types";
import type { RunState } from "../lib/useRun";
import { ApprovalDialog } from "./ApprovalDialog";
import { DecisionCard } from "./DecisionCard";
import { EvidenceDrawer } from "./EvidenceDrawer";
import { IdleSeal } from "./IdleSeal";
import { WorldPanel } from "./WorldPanel";

interface Props {
  state: RunState;
  request: string;
  onAnswer: (decisionId: string, approve: boolean) => void;
  onRetry: () => void;
  canRun: boolean;
  offline: boolean;
}

export function RunView({ state, request, onAnswer, onRetry, canRun, offline }: Props) {
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const busy = state.status === "starting" || state.status === "running";
  const count = (v: string) => state.decisions.filter((d) => d.verdict === v).length;
  const rejected = state.decisions.filter((d) => d.approval && d.approval !== "approved");
  const phase = state.status === "idle" ? "idle" : state.status === "done" ? "done" : state.status === "error" ? "stopped" : "running";

  return (
    <div className="run">
      {/* Wide screens: a left column. Projector (< 1366px): a compact strip above the timeline. */}
      <section className="brief" aria-label="Task">
        <div className="card brief__item">
          <h2 className="label">Your request</h2>
          <p className={request ? "request" : "request muted"}>{request || "Not loaded."}</p>
        </div>
        <div className="card brief__item">
          <h2 className="label">Frozen intent</h2>
          {state.capsule ? (
            <>
              <p>{state.capsule.summary}</p>
              <p className="hash">capsule {state.capsule.sha256.slice(0, 12)}</p>
            </>
          ) : (
            <p className="muted">Frozen when the run starts.</p>
          )}
        </div>
        {state.steps.length > 0 && (
          <div className="card brief__item brief__steps">
            <h2 className="label">The agent says</h2>
            <ol className="list">{state.steps.map((s, i) => <li key={i}>{s.content}</li>)}</ol>
          </div>
        )}
      </section>

      <section className="timeline" aria-live="polite" aria-busy={busy}>
        {state.status === "idle" && (
          <div className="empty">
            <IdleSeal />
            {offline ? (
              <>
                <p className="title">Waiting for the backend.</p>
                <p className="muted">Start it, then press Retry.</p>
              </>
            ) : (
              <>
                <p className="title">Pick a scenario and press Run scenario.</p>
                <p className="muted">Try S2 with the shield off, then on. Same email, same agent.</p>
              </>
            )}
          </div>
        )}
        {state.decisions.map((d) => (
          <DecisionCard key={d.id} d={d} onEvidence={setEvidence} />
        ))}
        {busy && (
          <div className="card skeleton" aria-hidden="true">
            <span className="skeleton__bar skeleton__bar--short" />
            <span className="skeleton__bar" />
            <span className="skeleton__bar skeleton__bar--mid" />
          </div>
        )}
        {busy && <p className="sr-only">{state.status === "starting" ? "Starting the agent…" : "The agent is working…"}</p>}
        {state.status === "error" && (
          <div className="card fault" role="alert">
            <div>
              <p className="fault__title">The run stopped.</p>
              <p className="error">{state.error}</p>
            </div>
            <button type="button" className="btn" onClick={onRetry} disabled={!canRun}>Run again</button>
          </div>
        )}
        {state.status === "done" && (
          <div className="done">
            <span className="done__rule" aria-hidden="true" />
            <p className="done__head">
              <strong>Run finished</strong>
              <span className="done__counts">
                {state.shieldOn ? (
                  <>
                    <span className="ok">{count("ALLOW")} allowed</span> · <span className="bad">{count("DENY")} denied</span> ·{" "}
                    <span className="warn">{count("REQUIRE_APPROVAL")} asked</span>
                  </>
                ) : (
                  <span className="bad">Shield off: {state.decisions.filter((d) => d.verdict !== "ALLOW" && d.executed).length} calls the gate would stop ran anyway</span>
                )}
              </span>
            </p>
            {rejected.map((d) => (
              <p key={d.id} className="bad">Not run: you rejected {d.tool}.</p>
            ))}
            {state.answer && <p className="muted">Agent claimed: “{state.answer}”</p>}
          </div>
        )}
      </section>

      <WorldPanel events={state.world} phase={phase} />

      {state.pending && state.shieldOn && (
        <ApprovalDialog key={state.pending.id} d={state.pending} onAnswer={(ok) => onAnswer(state.pending!.id, ok)} />
      )}
      {evidence && state.sessionId && (
        <EvidenceDrawer sessionId={state.sessionId} evidence={evidence} onClose={() => setEvidence(null)} />
      )}
    </div>
  );
}
