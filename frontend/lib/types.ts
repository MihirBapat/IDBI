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
  source?: "gemini" | "template";
}

export interface SpendItem {
  category: string;
  monthly_paise: number;
  monthly_display: string;
  txn_count: number;
}

export interface RecentTxn {
  date: string;
  category: string;
  type: "CREDIT" | "DEBIT";
  amount_display: string;
  narration: string;
}

export interface Financials {
  name: string;
  age: number;
  risk_capacity: string;
  balance_paise: number;
  balance_display: string;
  monthly_income_display: string;
  savings_ratio_pct: number;
  sip_discipline_pct: number;
  idle_cash_display: string;
  equity_holding_display: string;
  insurance_gap_display: string;
  spend_leaks: { category: string; monthly_display: string }[];
  spending: SpendItem[];
  holdings: {
    fixed_deposits: {
      name: string;
      principal_display: string;
      rate_display: string;
      maturity_display: string;
    }[];
    mutual_funds: {
      scheme: string;
      current_display: string;
      cost_display: string;
      sip: boolean;
    }[];
  };
  recent: RecentTxn[];
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
