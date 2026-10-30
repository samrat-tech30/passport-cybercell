// Mirrors backend/app/contracts.py and contracts/README.md. Change the contract first.

export type Trust = "user" | "trusted" | "untrusted" | "secret";
export type Origin = Trust | "model_invented" | "constant";
export type Verdict = "ALLOW" | "REQUIRE_APPROVAL" | "DENY";

export interface Evidence {
  arg: string;
  value: string;
  origin: Origin;
  segment_id: string | null;
  source: string | null;
  line: number | null;
  snippet: string | null;
  sink: boolean;
  /** found only in a clean view of the line ("at"/"dot", base64, Indic digits...) */
  disguised: boolean;
}

export interface Reason {
  rule_id: string;
  verdict: Verdict;
  message: string;
  risk: number;
  evidence: Evidence | null;
}

export interface Decision {
  id: string;
  session_id: string;
  step: number;
  tool: string;
  args: Record<string, unknown>;
  verdict: Verdict;
  rule_id: string;
  message: string;
  risk: number;
  reasons: Reason[];
  passports: Evidence[];
  shield_on: boolean;
  executed: boolean;
  approval: "approved" | "rejected" | "timeout" | null;
  ts: number;
}

export interface Capsule {
  goal: string;
  allowed_tools: string[];
  recipients: string[];
  files: string[];
  max_amount_inr: number | null;
  summary: string;
  sha256: string;
}

export interface WorldEvent {
  kind: "email_sent" | "attacker_received" | "payment_made" | "file_deleted" | "secret_read" | string;
  data: Record<string, unknown>;
}

export type EventType =
  | "session_started"
  | "capsule"
  | "llm_step"
  | "decision"
  | "approval_needed"
  | "approval_result"
  | "tool_result"
  | "world_event"
  | "done"
  | "error";

export interface StreamEvent {
  seq: number;
  session_id: string;
  type: EventType;
  data: Record<string, unknown>;
  ts: number;
}

export interface Scenario {
  id: string;
  title: string;
  category: string;
  user_request: string;
  is_attack: boolean;
  v2_note: string | null;
}

export interface Health {
  status: "ok";
  version: string;
  env: string;
  live_llm_available: boolean;
  access_code_required: boolean;
}

export interface NewSessionResponse {
  session_id: string;
  status: string;
  capsule: Capsule;
  shield_on: boolean;
  mode: "replay" | "live";
}

export interface SegmentView {
  id: string;
  source: string;
  trust: Trust;
  text: string;
  lines: string[];
}

export interface AuditRow {
  seq: number;
  ts: number;
  session_id: string | null;
  kind: string;
  payload: Record<string, unknown>;
  prev_hash: string;
  hash: string;
}

export type AuditVerify = { ok: true; rows: number; head: string } | { ok: false; broken_at: number; rows: number };

export interface EvalRow {
  scenario: string;
  title: string;
  category: string;
  shield_on: boolean;
  attack_landed: boolean | null;
  legit_done: boolean | null;
  allows: number;
  asks: number;
  denies: number;
  session_id: string;
}

export interface EvalSide {
  attacks_landed: number;
  attacks_total: number;
  legit_done: number;
  legit_total: number;
  approvals_on_clean_legit_tasks: number;
}

export interface EvalResult {
  summary: { off: EvalSide; on: EvalSide };
  rows: EvalRow[];
}
