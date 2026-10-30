import type { Verdict } from "../lib/api/types";
import { STAMP } from "../lib/format";

/** The signature element: a passport-control stamp that lands on every decision. */
export function Stamp({ verdict, shieldOn, executed }: { verdict: Verdict; shieldOn: boolean; executed: boolean }) {
  if (!shieldOn && verdict !== "ALLOW") {
    return (
      <span className="stamp stamp--ghost" title={executed ? "The shield was off, so this ran anyway" : undefined}>
        Would {verdict === "DENY" ? "deny" : "ask"}
      </span>
    );
  }
  const tone = verdict === "ALLOW" ? "ok" : verdict === "DENY" ? "bad" : "warn";
  return <span className={`stamp stamp--${tone}`}>{STAMP[verdict]}</span>;
}
