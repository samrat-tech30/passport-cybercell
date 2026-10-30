import type { Decision, Evidence, Origin, Verdict } from "./api/types";

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

/** Plain-English meaning of each rule, for chips and tooltips. Wording from docs/ARCHITECTURE.md + policy.yaml. */
export const RULE_TEXT: Record<string, [short: string, long: string]> = {
  R0_FAIL_CLOSED: ["Check failed, so blocked", "Something went wrong while checking. PASSPORT fails closed: when in doubt, the tool doesn't run."],
  R1_PROFILE: ["Tool not allowed here", "This tool or value isn't allowed by the profile for this task."],
  R2_CANARY: ["Secret marker seen", "A planted secret marker appeared in the arguments, so data is trying to leave."],
  R3_SINK_UNTRUSTED: ["Outside content chose a target", "A recipient, path, account or amount came from content you didn't write (an email, a file). Outside content can't steer actions."],
  R4_SECRET_EGRESS: ["Secret would leave", "A secret value would be sent out of the system."],
  R5_SINK_INVENTED: ["The AI made this up", "The AI wrote this target itself: it isn't from you or a trusted source, so you're asked."],
  R6_OUT_OF_INTENT: ["Not what you asked for", "This action is outside the task you gave, which was frozen before the agent read anything."],
  R7_HIGH_IMPACT: ["High impact: you decide", "Paying, deleting and similar actions always ask you first."],
  R8_TRIFECTA: ["Secret + outside content + sending", "The agent has read a secret and outside content and now wants to send something out."],
  R11_LOOKALIKE: ["Look-alike characters", "An address, account, path or key contains characters that only look like normal letters (for example a Cyrillic а), a common disguise."],
};

export function ruleChip(id: string): { label: string; title: string } {
  const t = RULE_TEXT[id];
  const num = id.split("_")[0];
  return t ? { label: `${num} · ${t[0]}`, title: `${id}: ${t[1]}` } : { label: id, title: id };
}

/** One plain sentence that says what happened, built only from the decision's own data. */
export function headline(d: Decision): string {
  const risky = d.passports.find((p) => p.origin === "untrusted") ?? d.passports.find((p) => p.origin === "secret") ?? d.passports.find((p) => p.origin === "model_invented");
  if (d.verdict === "ALLOW") return "Allowed: every value came from you or a trusted source.";
  let why = "it breaks a rule for this task";
  if (risky?.origin === "untrusted") why = `'${risky.arg}' came from ${risky.source ?? "outside content"}, not from you`;
  else if (risky?.origin === "secret") why = "it would send a secret out";
  else if (risky?.origin === "model_invented") why = `the AI made up '${risky.arg}'`;
  else if (d.reasons[0]) why = (RULE_TEXT[d.reasons[0].rule_id]?.[0] ?? why).toLowerCase();
  if (!d.shield_on) return `Would be ${d.verdict === "DENY" ? "blocked" : "stopped for you"}: ${why}. The shield is off, so it ran.`;
  if (d.verdict === "DENY") return `Blocked: ${why}.`;
  if (d.approval === "approved") return `You approved it: ${why}.`;
  if (d.approval) return `Stopped: you said no. ${why[0].toUpperCase()}${why.slice(1)}.`;
  return `Needs you: ${why}.`;
}
