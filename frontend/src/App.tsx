import { useCallback, useEffect, useState, type CSSProperties } from "react";
import { AuditView } from "./components/AuditView";
import { Legend } from "./components/Legend";
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
  const tabIndex = TABS.findIndex((t) => t.id === tab);

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <svg className="brand__mark" viewBox="0 0 20 20" aria-hidden="true">
            <circle cx="10" cy="10" r="8.5" />
            <circle cx="10" cy="10" r="5" />
            <path d="M1.5 10h17M10 1.5c2.6 2.4 2.6 14.6 0 17M10 1.5c-2.6 2.4-2.6 14.6 0 17" />
          </svg>
          <span className="brand__name">Passport</span>
          <span className="brand__tag">Every argument needs a passport</span>
        </div>

        <nav className="tabs" aria-label="Views" style={{ "--tab-i": tabIndex } as CSSProperties}>
          <span className="tabs__ink" aria-hidden="true" />
          {TABS.map((t) => (
            <button key={t.id} type="button" className={`tab ${tab === t.id ? "tab--on" : ""}`} aria-current={tab === t.id ? "page" : undefined} onClick={() => setTab(t.id)}>
              {t.label}
            </button>
          ))}
        </nav>

        {tab === "run" && (
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
            <label className="field field--scenario">
              <span className="sr-only">Scenario</span>
              <select value={scenarioId} onChange={(e) => setScenarioId(e.target.value)} disabled={running || scenarios.length === 0 || Boolean(loadError)}>
                {scenarios.length === 0 && <option value={scenarioId}>{loading ? "Loading scenarios…" : "No scenarios"}</option>}
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
              disabled={running || Boolean(loadError)}
            >
              <span className="shield__track" aria-hidden="true"><span className="shield__knob" /></span>
              Shield {shieldOn ? "on" : "off"}
            </button>
            <label className="field field--mode">
              <span className="sr-only">Mode</span>
              <select value={runMode} onChange={(e) => setMode(e.target.value as "replay" | "live")} disabled={running || Boolean(loadError)}>
                <option value="replay">Replay</option>
                {health?.live_llm_available && <option value="live">Live LLM</option>}
              </select>
            </label>
            <button type="submit" className="btn btn--brand" disabled={!canRun}>
              {running ? "Running…" : "Run scenario"}
            </button>
          </form>
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

      {loadError && (
        <div className="banner" role="alert">
          <span className="banner__dot" aria-hidden="true" />
          <div className="banner__text">
            <strong>Backend not reachable.</strong> <span className="muted">{loadError}</span>
          </div>
          <button type="button" className="btn btn--quiet" onClick={load} disabled={loading}>
            {loading ? "Trying…" : "Retry"}
          </button>
        </div>
      )}

      {tab === "run" && <Legend />}

      <main>
        {tab === "run" && <RunView state={state} request={scenario?.user_request ?? ""} onAnswer={answer} onRetry={run} canRun={canRun} offline={Boolean(loadError)} />}
        {tab === "score" && <Scoreboard />}
        {tab === "audit" && <AuditView />}
      </main>
    </div>
  );
}
