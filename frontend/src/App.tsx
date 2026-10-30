import { useCallback, useEffect, useState } from "react";
import { AuditView } from "./components/AuditView";
import { Illustration } from "./components/Illustration";
import { RunView } from "./components/RunView";
import { Scoreboard } from "./components/Scoreboard";
import { api, ApiError, getAccessCode, setAccessCode } from "./lib/api/client";
import type { Health, Scenario } from "./lib/api/types";
import { useRun } from "./lib/useRun";

type Tab = "run" | "score" | "audit";
const TABS: { id: Tab; label: string }[] = [
  { id: "run", label: "Agent" },
  { id: "score", label: "Scoreboard" },
  { id: "audit", label: "Audit" },
];

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [scenarioId, setScenarioId] = useState("s2");
  const [shieldOn, setShieldOn] = useState(true);
  const [mode, setMode] = useState<"replay" | "live">("replay");
  const [tab, setTab] = useState<Tab>("run");
  const [code, setCode] = useState(getAccessCode());
  const { state, start, answer } = useRun();

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([api.health(), api.scenarios()]).then(
      ([h, s]) => {
        setHealth(h);
        setScenarios(s);
        setLoadError(null);
        setLoading(false);
      },
      (e) => {
        setLoadError(e instanceof ApiError ? e.message : "Can't reach the backend.");
        setLoading(false);
      },
    );
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const scenario = scenarios.find((s) => s.id === scenarioId);
  const runMode = health?.live_llm_available ? mode : "replay"; // never start live on a server without it
  const running = state.status === "starting" || state.status === "running" || state.status === "waiting";
  const canRun = !running && Boolean(scenario) && !loadError;
  const run = () => {
    if (canRun) start({ scenarioId, shieldOn, mode: runMode });
  };

  const controls = (
    <form
      className="controls"
      onSubmit={(e) => {
        e.preventDefault();
        run();
      }}
      onKeyDown={(e) => {
        // Browsers only submit on Enter from text inputs; make Enter on a select run too.
        if (e.key === "Enter" && e.target instanceof HTMLSelectElement) {
          e.preventDefault();
          run();
        }
      }}
    >
      <label className="field">
        <span className="field__label">Scenario</span>
        <select value={scenarioId} onChange={(e) => setScenarioId(e.target.value)} disabled={running || scenarios.length === 0}>
          {scenarios.length === 0 && <option value={scenarioId}>{loading ? "Loading scenarios…" : "No scenarios"}</option>}
          {scenarios.map((s) => (
            <option key={s.id} value={s.id}>{s.id.toUpperCase()} · {s.title}</option>
          ))}
        </select>
      </label>
      <div className="controls__row">
        <button
          type="button"
          role="switch"
          aria-checked={shieldOn}
          className={`switch ${shieldOn ? "switch--on" : ""}`}
          onClick={() => setShieldOn((v) => !v)}
          disabled={running}
        >
          <span className="switch__track" aria-hidden="true"><span className="switch__knob" /></span>
          Shield {shieldOn ? "on" : "off"}
        </button>
        <label className="field field--mode">
          <span className="sr-only">Mode</span>
          <select value={runMode} onChange={(e) => setMode(e.target.value as "replay" | "live")} disabled={running}>
            <option value="replay">Replay</option>
            {health?.live_llm_available && <option value="live">Live LLM</option>}
          </select>
        </label>
      </div>
      <button type="submit" className="btn btn--brand btn--block" disabled={!canRun}>
        {running ? "Running…" : "Run scenario"}
      </button>
    </form>
  );

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <svg className="brand__mark" viewBox="0 0 20 20" aria-hidden="true">
            <circle cx="10" cy="10" r="8.5" />
            <path d="M1.5 10h17M10 1.5c2.6 2.4 2.6 14.6 0 17M10 1.5c-2.6 2.4-2.6 14.6 0 17" />
          </svg>
          <span className="brand__name">Passport</span>
          <span className="brand__tag">Every argument needs a passport</span>
        </div>

        <nav className="tabs" aria-label="Views">
          {TABS.map((t) => (
            <button key={t.id} type="button" className={`tab ${tab === t.id ? "tab--on" : ""}`} aria-current={tab === t.id ? "page" : undefined} onClick={() => setTab(t.id)}>
              {t.label}
            </button>
          ))}
        </nav>

        {health?.access_code_required && (
          <label className="field field--code">
            <span className="field__label">Demo code</span>
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

      <main>
        {loadError ? (
          <section className="offline" role="alert">
            <Illustration scene="unplugged" className="offline__art" />
            <h1 className="display">Waiting for the backend.</h1>
            <p className="muted">{loadError} Start it with <code>make backend</code>, then try again.</p>
            <button type="button" className="btn btn--brand" onClick={load} disabled={loading}>
              {loading ? "Trying…" : "Retry"}
            </button>
          </section>
        ) : (
          <>
            {tab === "run" && (
              <RunView
                state={state}
                scenario={scenario}
                controls={controls}
                onAnswer={answer}
                onRetry={run}
                canRun={canRun}
                scenarios={scenarios}
                scenarioId={scenarioId}
                onPick={setScenarioId}
              />
            )}
            {tab === "score" && <Scoreboard />}
            {tab === "audit" && <AuditView />}
          </>
        )}
      </main>
    </div>
  );
}
