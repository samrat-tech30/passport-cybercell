import type { Evidence, Origin, Verdict } from "./api/types";

export const ORIGIN_LABEL: Record<Origin, string> = {
  user: "From you",
  trusted: "Trusted registry",
  untrusted: "Outside content",
  secret: "Secret",
  model_invented: "Written by the AI",
  constant: "Constant",
};

export function whereFrom(ev: Evidence): string {
  const disguise = ev.disguised && (ev.origin === "untrusted" || ev.origin === "secret") ? " (written in disguise)" : "";
  if (ev.origin === "untrusted" && ev.source) return `${ev.line ? `${ev.source}, line ${ev.line}` : ev.source}${disguise}`;
  return `${ORIGIN_LABEL[ev.origin]}${disguise}`;
}

export const STAMP: Record<Verdict, string> = { ALLOW: "Allowed", REQUIRE_APPROVAL: "Needs you", DENY: "Denied" };

export function preview(v: unknown, max = 90): string {
  const s = typeof v === "string" ? v : JSON.stringify(v);
  return s.length > max ? `${s.slice(0, max)}…` : s;
}

/** Text an email client would not show (white, 1px). We reveal it on purpose. */
export function looksHidden(line: string): boolean {
  return /color:\s*#?(?:fff(?:fff)?|white)\b|font-size:\s*[01]px|display:\s*none/i.test(line);
}
