import type { Origin } from "../lib/api/types";
import { ORIGIN_LABEL } from "../lib/format";

const SHOWN: Origin[] = ["user", "trusted", "untrusted", "secret", "model_invented"];

/** One line that says what each origin colour means, in words. Swatches match the argument rows. */
export function Legend() {
  return (
    <div className="legend" aria-label="Where a value came from">
      <span className="legend__lead">Where each value came from</span>
      <ul className="legend__list">
        {SHOWN.map((o) => (
          <li key={o} className={`legend__item origin--${o}`}>
            <span className="legend__swatch" aria-hidden="true" />
            {ORIGIN_LABEL[o]}
          </li>
        ))}
      </ul>
    </div>
  );
}
