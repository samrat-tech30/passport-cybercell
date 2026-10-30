import type { RunState } from "../lib/useRun";

type Tone = "idle" | "active" | "ok" | "warn" | "bad" | "off";

function Node({ label, status, tone, icon }: { label: string; status: string; tone: Tone; icon: string }) {
  return (
    <li className={`gate__node gate__node--${tone}`}>
      <svg className="gate__icon" viewBox="0 0 20 20" aria-hidden="true"><path d={icon} /></svg>
      <span className="gate__text">
        <span className="gate__label">{label}</span>
        <span className="gate__status">{status}</span>
      </span>
    </li>
  );
}

const ICON = {
  request: "M4 4h12v9H8l-4 3z",
  agent: "M5 7h10v8H5zM10 7V4M7.5 11h.01M12.5 11h.01",
  gate: "M10 2l6 3v5c0 4-3 6.5-6 8-3-1.5-6-4-6-8V5z",
  tool: "M12 3a4 4 0 0 0-3.6 5.7L3 14.1 5.9 17l5.4-5.4A4 4 0 0 0 17 8l-2.5 2.5-2.5-.5-.5-2.5z",
};

/** The product's one idea, always visible: every tool call passes the PASSPORT check before it runs. */
export function GateStrip({ state }: { state: RunState }) {
  const last = state.decisions[state.decisions.length - 1];
  const s = state.status;
  const agentStatus = s === "idle" ? "Waiting" : s === "done" ? "Done" : s === "error" ? "Stopped" : s === "waiting" ? "Waiting for you" : "Working";

  let gate: [string, Tone] = ["Checks every tool call", "idle"];
  if (!state.shieldOn && s !== "idle") gate = ["Shield off: not checking", "off"];
  else if (last) {
    const verdict = last.verdict === "ALLOW" ? "Allowed" : last.verdict === "DENY" ? "Blocked" : last.approval ? (last.approval === "approved" ? "You approved" : "You said no") : "Asking you";
    gate = [`${last.tool} · ${verdict}`, last.verdict === "ALLOW" || last.approval === "approved" ? "ok" : last.verdict === "DENY" || last.approval ? "bad" : "warn"];
  }
  const tool: [string, Tone] = !last ? ["Nothing yet", "idle"] : last.executed ? [`${last.tool} ran`, !last.shield_on && last.verdict !== "ALLOW" ? "bad" : "ok"] : [`${last.tool} did not run`, "idle"];

  return (
    <ol className="gate" aria-label="How a tool call flows">
      <Node label="Your request" status={state.capsule ? "Frozen as intent" : "Ready"} tone={state.capsule ? "active" : "idle"} icon={ICON.request} />
      <Node label="AI agent" status={agentStatus} tone={s === "idle" ? "idle" : "active"} icon={ICON.agent} />
      <Node label="PASSPORT check" status={gate[0]} tone={gate[1]} icon={ICON.gate} />
      <Node label="Tool" status={tool[0]} tone={tool[1]} icon={ICON.tool} />
    </ol>
  );
}
