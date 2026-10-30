import type { Origin } from "../lib/api/types";
import { ORIGIN_LABEL } from "../lib/format";

const SHOWN: Origin[] = ["user", "trusted", "untrusted", "secret", "model_invented"];

/** Says what each origin treatment means, drawn with the same treatment the argument values use. */
export function Legend() {
  return (
    <div className="legend" aria-label="Where a value came from">
      <span className="legend__lead">Where each value came from</span>
      <ul className="legend__list">
        {SHOWN.map((o) => (
          <li key={o} className={`origin--${o}`}>
            <span className="ink">{ORIGIN_LABEL[o]}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
