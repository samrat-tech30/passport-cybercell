import { useState } from "react";
import type { Evidence, Scenario } from "../lib/api/types";
import type { RunState } from "../lib/useRun";
import { ApprovalDialog } from "./ApprovalDialog";
import { DecisionCard } from "./DecisionCard";
import { EvidenceDrawer } from "./EvidenceDrawer";
import { GateStrip } from "./GateStrip";
import { ScenarioPicker } from "./ScenarioPicker";
import { WorldPanel } from "./WorldPanel";

interface Props {
  state: RunState;
  request: string;
  onAnswer: (decisionId: string, approve: boolean) => void;
  onRetry: () => void;
  canRun: boolean;
  offline: boolean;
  scenarios: Scenario[];
  scenarioId: string;
  onPick: (id: string) => void;
  shieldOn: boolean;
}

export function RunView({ state, request, onAnswer, onRetry, canRun, offline, scenarios, scenarioId, onPick, shieldOn }: Props) {
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const busy = state.status === "starting" || state.status === "running";
  const count = (v: string) => state.decisions.filter((d) => d.verdict === v).length;
  const rejected = state.decisions.filter((d) => d.approval && d.approval !== "approved");
  const phase = state.status === "idle" ? "idle" : state.status === "done" ? "done" : state.status === "error" ? "stopped" : "running";

  return (
    <div className={`run ${state.status === "idle" ? "run--idle" : ""}`}>
      <div className="run__gate">
        <GateStrip state={state} />
      </div>
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
          <div className="intro">
            {offline ? (
              <>
                <h1 className="display">Waiting for the backend.</h1>
                <p className="muted">Start it, then press Retry above.</p>
              </>
            ) : (
              <>
                <h1 className="display">See an AI agent get attacked, and stopped.</h1>
                <ol className="steps">
                  <li><strong>Pick a scenario.</strong> <span className="muted">Most hide an attack in an email or file.</span></li>
                  <li><strong>Run it.</strong> <span className="muted">Each tool call the agent makes is checked before it runs.</span></li>
                  <li><strong>See why.</strong> <span className="muted">Every value shows where it came from. Outside content can't steer actions.</span></li>
                </ol>
                <ScenarioPicker scenarios={scenarios} value={scenarioId} onChange={onPick} />
                <div className="intro__go">
                  <button type="button" className="btn btn--brand btn--lg" disabled={!canRun} onClick={onRetry}>
                    Run {scenarioId.toUpperCase()} with the shield {shieldOn ? "on" : "off"}
                  </button>
                  <span className="muted small">Tip: run S2 with the shield off first, then on.</span>
                </div>
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
