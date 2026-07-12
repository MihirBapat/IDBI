// Shared API types — mirror the backend pydantic contracts (Part 3).

export interface ConsentSummary {
  persona_id: string;
  holder_name: string;
  purpose: string;
  fi_types: string[];
  status: string;
  expiry: string;
}

export interface ReasoningTrace {
  strategy_id: string;
  source_principle: string;
  inputs_used: Record<string, unknown>;
  math_steps: string[];
  engine_ver: string;
  shelf_sha: string;
  strategy_sha: string;
  refusal_reason: string | null;
}

export interface Recommendation {
  rec_id: string;
  action: string;
  product_ref: string | null;
  amount_paise: number | null;
  allocation: Record<string, number>;
  strategy_id: string;
  title: string;
  money_figures: Record<string, number>;
  pct_figures: Record<string, number>;
  year_figures: Record<string, number>;
  numeric_claims: string[];
  reasoning_trace: ReasoningTrace;
  status: "PASS" | "SOFTEN" | "VETO";
}

export interface ChatResponse {
  intent: string;
  spoken_text: string;
  transcript?: string;
  recommendations: Recommendation[];
  reasoning_trace: ReasoningTrace | null;
  disclosure: string;
  narration_hash: string;
  future_self_url?: string;
}

export interface ProjectionLine {
  text: string;
  numeric_claims: string[];
}

export interface ProjectionScript {
  persona_id: string;
  take_advice: boolean;
  horizon_years: number;
  corpus_paise: number;
  lines: ProjectionLine[];
  numeric_claims: string[];
  reasoning_trace: ReasoningTrace;
}

export interface AuditRow {
  id: number;
  persona_id: string;
  ts: string;
  intent: string;
  strategy_id: string | null;
  engine_ver: string | null;
  shelf_sha: string | null;
  strategy_sha: string | null;
  narration_hash: string;
  suitability_outcome: string | null;
  advisory_mode: string;
}
