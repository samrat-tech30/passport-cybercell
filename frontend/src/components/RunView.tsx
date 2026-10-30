import { useState } from "react";
import type { Evidence } from "../lib/api/types";
import type { RunState } from "../lib/useRun";
import { ApprovalDialog } from "./ApprovalDialog";
import { DecisionCard } from "./DecisionCard";
import { EvidenceDrawer } from "./EvidenceDrawer";
import { WorldPanel } from "./WorldPanel";

interface Props {
  state: RunState;
  request: string;
  onAnswer: (decisionId: string, approve: boolean) => void;
}

export function RunView({ state, request, onAnswer }: Props) {
  const [evidence, setEvidence] = useState<Evidence | null>(null);

  return (
    <div className="run">
      <section className="side">
        <div className="card">
          <h2 className="title">Your request</h2>
          <p className="request">{request}</p>
        </div>
        <div className="card">
          <h2 className="title">Frozen intent</h2>
          {state.capsule ? (
            <>
              <p>{state.capsule.summary}</p>
              <p className="muted small mono">capsule {state.capsule.sha256.slice(0, 12)}</p>
            </>
          ) : (
            <p className="muted">Run a scenario to see what the gate will allow.</p>
          )}
        </div>
        {state.steps.length > 0 && (
          <div className="card">
            <h2 className="title">The agent says</h2>
            <ol className="list">{state.steps.map((s, i) => <li key={i}>{s.content}</li>)}</ol>
          </div>
        )}
      </section>

      <section className="timeline" aria-live="polite" aria-busy={state.status === "running" || state.status === "starting"}>
        {state.status === "idle" && (
          <div className="empty">
            <p className="title">Pick a scenario and press Run scenario.</p>
            <p className="muted">Try S2 with the shield off, then on. Same email, same agent.</p>
          </div>
        )}
        {state.status === "starting" && <p className="muted">Starting the agent…</p>}
        {state.error && <p className="error" role="alert">{state.error}</p>}
        {state.decisions.map((d) => (
          <DecisionCard key={d.id} d={d} onEvidence={setEvidence} />
        ))}
        {state.status === "done" && <p className="muted done">Run finished{state.answer ? `: ${state.answer}` : "."}</p>}
      </section>

      <WorldPanel events={state.world} />

      {state.pending && state.shieldOn && (
        <ApprovalDialog key={state.pending.id} d={state.pending} onAnswer={(ok) => onAnswer(state.pending!.id, ok)} />
      )}
      {evidence && state.sessionId && (
        <EvidenceDrawer sessionId={state.sessionId} evidence={evidence} onClose={() => setEvidence(null)} />
      )}
    </div>
  );
}
