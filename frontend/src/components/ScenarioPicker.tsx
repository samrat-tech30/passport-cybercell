import type { KeyboardEvent } from "react";
import type { Scenario } from "../lib/api/types";

interface Props {
  scenarios: Scenario[];
  value: string;
  onChange: (id: string) => void;
}

/** Scenarios as a ruled list and a radio group: arrow keys move, the selected row is the one that runs. */
export function ScenarioPicker({ scenarios, value, onChange }: Props) {
  function onKey(e: KeyboardEvent<HTMLDivElement>) {
    const step = e.key === "ArrowRight" || e.key === "ArrowDown" ? 1 : e.key === "ArrowLeft" || e.key === "ArrowUp" ? -1 : 0;
    if (!step) return;
    e.preventDefault();
    const i = scenarios.findIndex((s) => s.id === value);
    const next = scenarios[(i + step + scenarios.length) % scenarios.length];
    onChange(next.id);
    (e.currentTarget.querySelector(`[data-id="${next.id}"]`) as HTMLElement | null)?.focus();
  }

  return (
    <div className="picker" role="radiogroup" aria-label="Scenario" onKeyDown={onKey}>
      {scenarios.map((s) => (
        <button
          key={s.id}
          type="button"
          role="radio"
          data-id={s.id}
          aria-checked={s.id === value}
          tabIndex={s.id === value ? 0 : -1}
          className={`pick ${s.id === value ? "pick--on" : ""}`}
          onClick={() => onChange(s.id)}
        >
          <span className="pick__radio" aria-hidden="true" />
          <span className="pick__id">{s.id.toUpperCase()}</span>
          <span className="pick__body">
            <span className="pick__title">{s.title}</span>
            <span className="pick__cat">{s.category.replace(/_/g, " ")}</span>
          </span>
          <span className={`tag ${s.is_attack ? "tag--attack" : ""}`}>{s.is_attack ? "Attack" : "Normal task"}</span>
        </button>
      ))}
    </div>
  );
}
