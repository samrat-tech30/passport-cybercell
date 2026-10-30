import { useEffect, useState } from "react";
import { AuditView } from "./components/AuditView";
import { RunView } from "./components/RunView";
import { Scoreboard } from "./components/Scoreboard";
import { api, ApiError, getAccessCode, setAccessCode } from "./lib/api/client";
import type { Health, Scenario } from "./lib/api/types";
import { useRun } from "./lib/useRun";

type Tab = "run" | "score" | "audit";

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [scenarioId, setScenarioId] = useState("s2");
  const [shieldOn, setShieldOn] = useState(true);
  const [mode, setMode] = useState<"replay" | "live">("replay");
  const [tab, setTab] = useState<Tab>("run");
  const [code, setCode] = useState(getAccessCode());
  const { state, start, answer } = useRun();

  useEffect(() => {
    Promise.all([api.health(), api.scenarios()]).then(
      ([h, s]) => {
        setHealth(h);
        setScenarios(s);
      },
      (e) => setLoadError(e instanceof ApiError ? e.message : "Can't reach the backend."),
    );
  }, []);

  const scenario = scenarios.find((s) => s.id === scenarioId);
  const running = state.status === "starting" || state.status === "running" || state.status === "waiting";

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand__mark" aria-hidden="true" />
          <span className="brand__name">PASSPORT</span>
          <span className="muted small">Every argument needs a passport</span>
        </div>

        <nav className="tabs" aria-label="Views">
          {(["run", "score", "audit"] as const).map((t) => (
            <button key={t} type="button" className={`tab ${tab === t ? "tab--on" : ""}`} aria-current={tab === t} onClick={() => setTab(t)}>
              {t === "run" ? "Agent" : t === "score" ? "Scoreboard" : "Audit"}
            </button>
          ))}
        </nav>

        {tab === "run" && (
          <div className="controls">
            <label className="field">
              <span className="sr-only">Scenario</span>
              <select value={scenarioId} onChange={(e) => setScenarioId(e.target.value)} disabled={running}>
                {scenarios.map((s) => (
                  <option key={s.id} value={s.id}>{s.id.toUpperCase()} · {s.title}</option>
                ))}
              </select>
            </label>
            <button
              type="button"
              role="switch"
              aria-checked={shieldOn}
              className={`shield ${shieldOn ? "shield--on" : "shield--off"}`}
              onClick={() => setShieldOn((v) => !v)}
              disabled={running}
            >
              Shield {shieldOn ? "on" : "off"}
            </button>
            <label className="field">
              <span className="sr-only">Mode</span>
              <select value={mode} onChange={(e) => setMode(e.target.value as "replay" | "live")} disabled={running}>
                <option value="replay">Replay (recorded agent)</option>
                <option value="live" disabled={!health?.live_llm_available}>Live LLM{health?.live_llm_available ? "" : " (not configured)"}</option>
              </select>
            </label>
            <button type="button" className="btn btn--brand" disabled={running || !scenario} onClick={() => start({ scenarioId, shieldOn, mode })}>
              {running ? "Running…" : "Run scenario"}
            </button>
          </div>
        )}

        {health?.access_code_required && (
          <label className="field code">
            <span className="muted small">Demo code</span>
            <input
              type="password"
              value={code}
              autoComplete="off"
              onChange={(e) => {
                setCode(e.target.value);
                setAccessCode(e.target.value);
              }}
            />
          </label>
        )}
      </header>

      {loadError && <p className="error banner" role="alert">{loadError}</p>}

      <main>
        {tab === "run" && <RunView state={state} request={scenario?.user_request ?? ""} onAnswer={answer} />}
        {tab === "score" && <Scoreboard />}
        {tab === "audit" && <AuditView />}
      </main>
    </div>
  );
}
