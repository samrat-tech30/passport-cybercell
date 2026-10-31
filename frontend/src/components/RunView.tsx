import { useState, type ReactNode } from "react";
import type { Evidence, Scenario } from "../lib/api/types";
import type { RunState } from "../lib/useRun";
import { ApprovalDialog } from "./ApprovalDialog";
import { DecisionCard } from "./DecisionCard";
import { EvidenceDrawer } from "./EvidenceDrawer";
import { GateStrip } from "./GateStrip";
import { Legend } from "./Legend";
import { ScenarioPicker } from "./ScenarioPicker";
import { WorldPanel } from "./WorldPanel";

interface Props {
  state: RunState;
  scenario: Scenario | undefined;
  controls: ReactNode;
  onAnswer: (decisionId: string, approve: boolean) => void;
  onRetry: () => void;
  canRun: boolean;
  scenarios: Scenario[];
  scenarioId: string;
  onPick: (id: string) => void;
}

export function RunView({ state, scenario, controls, onAnswer, onRetry, canRun, scenarios, scenarioId, onPick }: Props) {
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const idle = state.status === "idle";
  const busy = state.status === "starting" || state.status === "running";
  const count = (v: string) => state.decisions.filter((d) => d.verdict === v).length;
  const rejected = state.decisions.filter((d) => d.approval && d.approval !== "approved");
  const phase = idle ? "idle" : state.status === "done" ? "done" : state.status === "error" ? "stopped" : "running";

  return (
    <div className="run">

      {/* The one sky block: what you asked for, and the controls to run it. */}
      <section className={`hero ${idle ? "" : "hero--compact"}`} aria-label="Task">
        <div className="hero__copy">
          <p className="eyebrow">
            Your request
            {scenario && <span className={`tag ${scenario.is_attack ? "tag--attack" : ""}`}>{scenario.id.toUpperCase()} · {scenario.is_attack ? "Attack hidden inside" : "Normal task"}</span>}
          </p>
          <p className="hero__request">{scenario?.user_request ?? "Pick a scenario to see the request."}</p>
          {state.capsule ? (
            <div className="capsule">
              <p className="capsule__label">Frozen intent</p>
              <p className="capsule__text">{state.capsule.summary}</p>
              <p className="hash">signed capsule {state.capsule.sha256.slice(0, 12)}</p>
            </div>
          ) : (
            <p className="hero__hint">When the run starts, this request is frozen into a signed intent before the agent reads anything.</p>
          )}
        </div>
        <div className="hero__controls">{controls}</div>
      </section>

      {idle ? (
        <section className="scenarios" aria-labelledby="scenarios-title">
          <div className="section-head">
            <h2 id="scenarios-title" className="h2">Scenarios</h2>
            <p className="muted">Try S2 with the shield off first, then on. Same email, same agent.</p>
          </div>
          <ScenarioPicker scenarios={scenarios} value={scenarioId} onChange={onPick} />
        </section>
      ) : (
        <>
          <GateStrip state={state} />
          <div className="run__body">
            <section className="timeline" aria-live="polite" aria-busy={busy}>
              <Legend />
              {state.decisions.map((d) => (
                <DecisionCard key={d.id} d={d} onEvidence={setEvidence} />
              ))}
              {busy && (
                <p className="working">
                  <span className="pulse" aria-hidden="true" />
                  {state.status === "starting" ? "Starting the agent…" : "The agent is working…"}
                </p>
              )}
              {state.status === "error" && (
                <div className="fault" role="alert">
                  <div>
                    <p className="fault__title">The run stopped.</p>
                    <p className="error">{state.error}</p>
                  </div>
                  <button type="button" className="btn btn--ink" onClick={onRetry} disabled={!canRun}>Run again</button>
                </div>
              )}
              {state.status === "done" && (
                <div className="done">
                  <p className="done__head">
                    <span className="done__title">Run finished</span>
                    <span className="done__counts">
                      {state.shieldOn ? (
                        <>
                          <span className={count("ALLOW") ? "ok" : "muted"}>{count("ALLOW")} allowed</span>
                          <span className={count("DENY") ? "bad" : "muted"}>{count("DENY")} denied</span>
                          <span className={count("REQUIRE_APPROVAL") ? "warn" : "muted"}>{count("REQUIRE_APPROVAL")} asked you</span>
                        </>
                      ) : (
                        <span className="bad">Shield off: {state.decisions.filter((d) => d.verdict !== "ALLOW" && d.executed).length} calls the gate would stop ran anyway</span>
                      )}
                    </span>
                  </p>
                  {rejected.map((d) => (
                    <p key={d.id} className="bad">Not run: you rejected {d.tool}.</p>
                  ))}
                  {state.answer && <p className="done__answer">The agent's final answer: “{state.answer}”</p>}
                </div>
              )}
            </section>

            <aside className="rail" aria-label="Outcome">
              <WorldPanel events={state.world} phase={phase} />
              {state.steps.length > 0 && (
                <section className="rail__block">
                  <h2 className="label">The agent says</h2>
                  <ol className="notes">{state.steps.map((s, i) => <li key={i}>{s.content}</li>)}</ol>
                </section>
              )}
            </aside>
          </div>
        </>
      )}

      {state.pending && state.shieldOn && (
        <ApprovalDialog key={state.pending.id} d={state.pending} onAnswer={(ok) => onAnswer(state.pending!.id, ok)} />
      )}
      {evidence && state.sessionId && (
        <EvidenceDrawer sessionId={state.sessionId} evidence={evidence} onClose={() => setEvidence(null)} />
      )}
    </div>
  );
}
