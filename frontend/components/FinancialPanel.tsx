"use client";

import type { Financials } from "@/lib/types";

// The side panel: the customer's financial history, records & state — pulled
// live from GET /financials. Read-only mirror of their consented AA data.

const CATEGORY_LABEL: Record<string, string> = {
  FOOD_DELIVERY: "Food delivery",
  DINING: "Dining out",
  SHOPPING: "Shopping",
  GROCERIES: "Groceries",
  RENT: "Rent",
  EMI: "Home loan EMI",
  UTILITIES: "Utilities",
  SUBSCRIPTION: "Subscriptions",
  FUEL: "Fuel",
  EDUCATION: "Education",
  MEDICAL: "Medical",
  HOUSING: "Housing",
  INSURANCE_PREMIUM: "Insurance",
  UPI_P2P: "Transfers",
  INTEREST_CREDIT: "Interest",
  SALARY: "Salary",
};

function label(code: string): string {
  return CATEGORY_LABEL[code] ?? code.toLowerCase().replace(/_/g, " ");
}

export default function FinancialPanel({
  data,
  loading,
}: {
  data: Financials | null;
  loading: boolean;
}) {
  if (loading || !data) {
    return (
      <aside className="fin-panel">
        <div className="fin-loading">
          <span className="spinner" /> Loading financial snapshot…
        </div>
      </aside>
    );
  }

  const maxSpend = Math.max(...data.spending.map((s) => s.monthly_paise), 1);

  return (
    <aside className="fin-panel">
      <div className="fin-head">
        <div>
          <div className="fin-title">Financial snapshot</div>
          <div className="fin-sub">
            {data.name} · {data.age} yrs
          </div>
        </div>
        <span className={`risk-chip risk-${data.risk_capacity}`}>
          {data.risk_capacity} risk
        </span>
      </div>

      <div className="fin-balance">
        <span className="fin-balance-label">Savings balance</span>
        <span className="fin-balance-value">{data.balance_display}</span>
      </div>

      <div className="fin-tiles">
        <Tile k="Monthly income" v={data.monthly_income_display} />
        <Tile k="Savings rate" v={`${data.savings_ratio_pct}%`} />
        <Tile k="Idle cash" v={data.idle_cash_display} />
        <Tile k="Insurance gap" v={data.insurance_gap_display} />
      </div>

      <div className="fin-section-title">Where the money goes (monthly)</div>
      <div className="spend-list">
        {data.spending.slice(0, 7).map((s) => (
          <div className="spend-row" key={s.category}>
            <div className="spend-top">
              <span>{label(s.category)}</span>
              <span className="spend-amt">{s.monthly_display}</span>
            </div>
            <div className="spend-track">
              <div
                className="spend-fill"
                style={{ width: `${Math.round((s.monthly_paise / maxSpend) * 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {(data.holdings.fixed_deposits.length > 0 ||
        data.holdings.mutual_funds.length > 0) && (
        <>
          <div className="fin-section-title">Holdings</div>
          <div className="holdings">
            {data.holdings.fixed_deposits.map((h, i) => (
              <div className="holding" key={`fd${i}`}>
                <span>🏦 {h.name}</span>
                <span className="holding-v">
                  {h.principal_display} @ {h.rate_display}
                </span>
              </div>
            ))}
            {data.holdings.mutual_funds.map((h, i) => (
              <div className="holding" key={`mf${i}`}>
                <span>📈 {h.scheme.replace(/ - .*/, "")}</span>
                <span className="holding-v">
                  {h.current_display}
                  {h.sip ? " · SIP" : ""}
                </span>
              </div>
            ))}
          </div>
        </>
      )}

      <div className="fin-section-title">Recent activity</div>
      <div className="recent">
        {data.recent.slice(0, 7).map((t, i) => (
          <div className="recent-row" key={i}>
            <div className="recent-left">
              <span className="recent-cat">{label(t.category)}</span>
              <span className="recent-date">{t.date}</span>
            </div>
            <span className={`recent-amt ${t.type === "CREDIT" ? "cr" : "dr"}`}>
              {t.amount_display}
            </span>
          </div>
        ))}
      </div>

      <div className="fin-foot">Source: Account Aggregator · consented, read-only</div>
    </aside>
  );
}

function Tile({ k, v }: { k: string; v: string }) {
  return (
    <div className="fin-tile">
      <span className="fin-tile-k">{k}</span>
      <span className="fin-tile-v">{v}</span>
    </div>
  );
}
