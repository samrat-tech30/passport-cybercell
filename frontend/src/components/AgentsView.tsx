import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "../lib/api/client";
import type { Decision, Evidence, GatewaySessionRow, Health } from "../lib/api/types";
import { useRun } from "../lib/useRun";
import { ApprovalDialog } from "./ApprovalDialog";
import { DecisionCard } from "./DecisionCard";
import { EvidenceDrawer } from "./EvidenceDrawer";

const POLL_MS = 3000;

const STEPS = [
  ["Your agent asks", "Claude Desktop, Cursor or any MCP agent wants to use a tool."],
  ["PASSPORT checks", "Every value must show where it came from. Text from emails can't steer an action."],
  ["The tool runs only if allowed", "Blocked calls never reach the tool. Risky ones wait for you."],
] as const;

/** An agent session opened in its own window: index.html#agent=ses_… */
function agentFromHash(): string | null {
  const m = /(?:^#|&)agent=(ses_[0-9a-f]{10})\b/.exec(window.location.hash);
  return m ? m[1] : null;
}

/** Architecture box 4, "Connected agents · Live decisions · Approval center". */
export function AgentsView({ health }: { health: Health | null }) {
  const [items, setItems] = useState<GatewaySessionRow[]>([]);
  const [listError, setListError] = useState<string | null>(null);
  const [disabled, setDisabled] = useState(false);
  const [selected, setSelected] = useState<string | null>(agentFromHash);
  const [pinned, setPinned] = useState(() => agentFromHash() !== null); // false = follow the newest agent
  const [elsewhere, setElsewhere] = useState<Decision | null>(null); // an approval from an agent not on screen
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const { state, attach, detach, answer } = useRun();
  const asked = useRef<string | null>(null);

  const poll = useCallback(async () => {
    try {
      const { items: next } = await api.gatewaySessions();
      setItems(next);
      setListError(null);
      setDisabled(false);
      const waiting = next.find((s) => s.status === "waiting_approval" && s.session_id !== selected);
      if (!waiting) {
        asked.current = null;
        setElsewhere(null);
      } else if (asked.current !== waiting.session_id) {
        asked.current = waiting.session_id;
        setElsewhere((await api.session(waiting.session_id)).pending_approvals[0] ?? null);
      }
    } catch (e) {
      if (e instanceof ApiError && e.status === 503) setDisabled(true);
      else setListError(e instanceof ApiError ? e.message : "Can't load the connected agents.");
    }
  }, [selected]);

  useEffect(() => {
    void poll();
    const t = window.setInterval(() => void poll(), POLL_MS);
    return () => window.clearInterval(t);
  }, [poll]);

  useEffect(() => {
    if (!pinned && items[0] && items[0].session_id !== selected) setSelected(items[0].session_id);
  }, [items, pinned, selected]);

  const current = items.find((s) => s.session_id === selected) ?? null;
  const currentShield = current?.shield_on;
  useEffect(() => {
    if (selected && currentShield !== undefined) void attach(selected, currentShield);
    return () => detach();
  }, [selected, currentShield, attach, detach]);

  const pending = state.pending ?? elsewhere;
  const asking = pending ? items.find((s) => s.session_id === pending.session_id) : undefined;
  const waitS = health?.gateway_approval_wait_s ?? 40;
  const decisions = [...state.decisions].reverse(); // newest first: a live monitor

  const onAnswer = async (ok: boolean) => {
    if (!pending) return;
    if (pending === elsewhere) setElsewhere(null);
    await answer(pending.id, ok);
  };

  return (
    <div className="page">
      <header className="page__head">
        <div>
          <p className="eyebrow">Agents</p>
          <h1 className="display">Every tool call, checked before it runs.</h1>
        </div>
      </header>

      <ol className="flow" aria-label="How it works">
        {STEPS.map(([title, text], i) => (
          <li key={title} className="flow__step">
            <span className="flow__n">{i + 1}</span>
            <span>
              <span className="flow__title">{title}</span>
              <span className="flow__text">{text}</span>
            </span>
          </li>
        ))}
      </ol>

      {disabled || health?.gateway_enabled === false ? (
        <div className="empty">
          <p className="h2">The agent gateway is off.</p>
          <p className="muted">
            Add <code>PASSPORT_GATEWAY_TOKEN</code> (24+ random characters) to <code>backend/.env</code> and restart the backend.
          </p>
        </div>
      ) : items.length === 0 ? (
        <div className="empty">
          <p className="h2">No agent connected yet.</p>
          <p className="muted">Run the demo agent, or connect Claude Desktop (integrations/README.md).</p>
          <pre className="cmd">PASSPORT_GATEWAY_TOKEN=… make fooled-agent</pre>
          {listError && <p className="error" role="alert">{listError}</p>}
        </div>
      ) : (
        <div className="agents">
          <section aria-labelledby="agents-title">
            <h2 id="agents-title" className="label">Connected agents</h2>
            <ul className="agents__list">
              {items.map((s) => (
                <li key={s.session_id}>
                  <button
                    type="button"
                    className={`agent ${s.session_id === selected ? "agent--on" : ""}`}
                    aria-current={s.session_id === selected}
                    onClick={() => {
                      setPinned(true);
                      setSelected(s.session_id);
                    }}
                  >
                    <span className="agent__top">
                      <span className="agent__name">{s.agent_name}</span>
                      {s.status === "waiting_approval" ? (
                        <span className="tag tag--attack">Needs you</span>
                      ) : (
                        <span className="tag">{s.shield_on ? "Protected" : "Watch only"}</span>
                      )}
                    </span>
                    <span className="agent__intent">{s.intent ?? "No task yet"}</span>
                    <span className="agent__counts">
                      {s.counts.ALLOW} allowed · {s.counts.REQUIRE_APPROVAL} asked ·{" "}
                      <span className={s.counts.DENY ? "bad" : ""}>{s.counts.DENY} blocked</span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
            {pinned && items.length > 1 && (
              <button type="button" className="link agents__follow" onClick={() => setPinned(false)}>Follow the newest agent</button>
            )}
          </section>

          <section className="agents__live" aria-live="polite" aria-label="Live decisions">
            {current && (
              <div className="hero agents__hero">
                <div className="hero__copy">
                  <p className="eyebrow">
                    {current.agent_name}
                    {current.client && <span className="muted">via {current.client}</span>}
                    <a className="link agents__open" href={`#agent=${current.session_id}`} target="_blank" rel="noopener noreferrer">
                      Open in new window
                    </a>
                  </p>
                  <p className="hero__request">{current.intent ?? "Waiting for the agent to say what the user asked."}</p>
                  {state.capsule && current.intent && <p className="hero__hint">{state.capsule.summary}</p>}
                  {!current.shield_on && (
                    <p className="hero__hint"><mark className="hl">Watch-only mode:</mark> calls are checked and shown, but nothing is blocked.</p>
                  )}
                </div>
              </div>
            )}
            {state.lastApproval?.result === "timeout" && (
              <p className="error" role="status">No answer in time, so the call was refused. The agent can ask again.</p>
            )}
            {current && decisions.length === 0 && <p className="muted">No tool calls yet.</p>}
            <div className="timeline">
              {decisions.map((d) => (
                <DecisionCard key={d.id} d={d} onEvidence={setEvidence} />
              ))}
            </div>
          </section>
        </div>
      )}

      {pending && (
        <ApprovalDialog
          key={pending.id}
          d={pending}
          deadline={pending.ts * 1000 + waitS * 1000}
          context={`${asking?.agent_name ?? "An agent"} is waiting for your answer`}
          onAnswer={(ok) => void onAnswer(ok)}
        />
      )}
      {evidence && state.sessionId && (
        <EvidenceDrawer sessionId={state.sessionId} evidence={evidence} onClose={() => setEvidence(null)} />
      )}
    </div>
  );
}
