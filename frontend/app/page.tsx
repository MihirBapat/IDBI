"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import ConsentFlow from "@/components/ConsentFlow";
import FinancialPanel from "@/components/FinancialPanel";
import FutureSelfPanel from "@/components/FutureSelfPanel";
import GovernancePanel from "@/components/GovernancePanel";
import RecommendationCard from "@/components/RecommendationCard";
import SaarthiAvatar from "@/components/SaarthiAvatar";
import Streamed from "@/components/Streamed";
import {
  API,
  chat,
  futureSelf,
  getFinancials,
  revokeConsent,
  type ChatTurn,
} from "@/lib/api";
import type { PersonaCard } from "@/lib/personas";
import { listen, speak, stopSpeaking, sttSupported } from "@/lib/speech";
import type {
  ChatResponse,
  ConsentSummary,
  Financials,
  ProjectionScript,
  Recommendation,
  ReasoningTrace,
} from "@/lib/types";

interface Msg {
  role: "user" | "saarthi";
  text: string;
  recs?: Recommendation[];
  trace?: ReasoningTrace | null;
  source?: "gemini" | "template";
}

const SUGGESTIONS = [
  "How am I spending my money?",
  "What should I do with my savings?",
  "Am I saving enough?",
  "Show me my future self",
];

export default function Home() {
  const [persona, setPersona] = useState<PersonaCard | null>(null);
  const [, setConsent] = useState<ConsentSummary | null>(null);
  const [fin, setFin] = useState<Financials | null>(null);
  const [finLoading, setFinLoading] = useState(false);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [speaking, setSpeaking] = useState(false);
  const [listening, setListening] = useState(false);
  const [caption, setCaption] = useState("");
  const [busy, setBusy] = useState(false);
  const [aged, setAged] = useState(false);
  const [future, setFuture] = useState<ProjectionScript | null>(null);
  const [branch, setBranch] = useState<"good" | "bad">("good");
  const [govOpen, setGovOpen] = useState(false);
  const [advisoryMode, setAdvisoryMode] = useState("on");
  const [geminiOn, setGeminiOn] = useState(false);
  const stopListenRef = useRef<() => void>(() => {});
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch(`${API}/health`)
      .then((r) => r.json())
      .then((h) => {
        setAdvisoryMode(h.advisory_mode ?? "on");
        setGeminiOn(Boolean(h.gemini));
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, aged, future]);

  const bodyOf = (t: string) => t.split("\n\n")[0].trim();

  const say = useCallback(async (text: string) => {
    setCaption(text);
    setSpeaking(true);
    await speak(text, {});
    setSpeaking(false);
  }, []);

  const historyFor = (): ChatTurn[] =>
    messages.slice(-8).map((m) => ({ role: m.role, text: bodyOf(m.text) }));

  const onGranted = useCallback(
    async (p: PersonaCard, c: ConsentSummary) => {
      setPersona(p);
      setConsent(c);
      setFinLoading(true);
      getFinancials(p.id)
        .then(setFin)
        .catch(() => {})
        .finally(() => setFinLoading(false));
      setBusy(true);
      try {
        const r = await chat(p.id, "hello", []);
        setMessages([{ role: "saarthi", text: r.spoken_text, source: r.source }]);
        void say(bodyOf(r.spoken_text)); // speak in background; don't block input
      } finally {
        setBusy(false);
      }
    },
    [say],
  );

  const openFuture = useCallback(
    async (b: "good" | "bad") => {
      if (!persona) return;
      setBranch(b);
      setAged(true);
      setBusy(true);
      try {
        const script = await futureSelf(persona.id, b);
        setFuture(script);
        for (const line of script.lines) await say(line.text);
      } finally {
        setBusy(false);
      }
    },
    [persona, say],
  );

  const send = useCallback(
    async (text: string) => {
      if (!persona || !text.trim() || busy) return;
      const history = historyFor();
      setInput("");
      setMessages((m) => [...m, { role: "user", text }]);
      setBusy(true);
      try {
        const r: ChatResponse = await chat(persona.id, text, history);
        setMessages((m) => [
          ...m,
          {
            role: "saarthi",
            text: r.spoken_text,
            recs: r.recommendations,
            trace: r.reasoning_trace,
            source: r.source,
          },
        ]);
        if (r.intent === "FUTURE_SELF") {
          void openFuture("good");
        } else {
          setAged(false);
          setFuture(null);
          void say(bodyOf(r.spoken_text)); // speak in background
        }
      } catch {
        const err = "I couldn't reach the advisory service. Is the backend running on :8000?";
        setMessages((m) => [...m, { role: "saarthi", text: err }]);
        await say(err);
      } finally {
        setBusy(false);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [persona, busy, say],
  );

  const toggleMic = useCallback(() => {
    if (listening) {
      stopListenRef.current();
      setListening(false);
      return;
    }
    if (!sttSupported()) return;
    setListening(true);
    stopListenRef.current = listen(
      (text) => {
        setListening(false);
        send(text);
      },
      () => setListening(false),
    );
  }, [listening, send]);

  const switchCustomer = useCallback(async () => {
    stopSpeaking();
    if (persona) await revokeConsent(persona.id).catch(() => {});
    setPersona(null);
    setConsent(null);
    setFin(null);
    setMessages([]);
    setFuture(null);
    setAged(false);
    setCaption("");
    setGovOpen(false);
  }, [persona]);

  if (!persona) {
    return (
      <div className="app">
        <BrandBar advisoryMode={advisoryMode} geminiOn={geminiOn} />
        <ConsentFlow onGranted={onGranted} />
      </div>
    );
  }

  const lastSaarthi = (() => {
    for (let i = messages.length - 1; i >= 0; i--) if (messages[i].role === "saarthi") return i;
    return -1;
  })();

  return (
    <div className="gem-shell">
      <BrandBar
        advisoryMode={advisoryMode}
        geminiOn={geminiOn}
        persona={persona}
        onSwitch={switchCustomer}
        onGov={() => setGovOpen(true)}
      />

      <div className="gem-body">
        <section className="gem-chat">
          <div className="assistant-header">
            <SaarthiAvatar size={54} speaking={speaking} aged={aged} />
            <div className="assistant-id">
              <div className="assistant-name">
                Saarthi
                <span className="assistant-status">
                  {busy ? "thinking…" : speaking ? "speaking…" : aged ? "your future self" : "online"}
                </span>
              </div>
              <div className="assistant-caption">{caption || "Ask me anything about your money."}</div>
            </div>
          </div>

          <div className="thread">
            {messages.map((m, i) => (
              <div key={i} className={`turn ${m.role}`}>
                {m.role === "saarthi" && (
                  <div className="turn-spark">
                    <SaarthiAvatar size={30} aged={aged && i === lastSaarthi} />
                  </div>
                )}
                <div className="turn-body">
                  <div className="turn-text">
                    {m.role === "saarthi" && i === lastSaarthi ? (
                      <Streamed
                        text={bodyOf(m.text)}
                        onTick={() => endRef.current?.scrollIntoView()}
                      />
                    ) : m.role === "saarthi" ? (
                      bodyOf(m.text)
                    ) : (
                      m.text
                    )}
                  </div>
                  {m.source === "gemini" && (
                    <div className="turn-badge">✨ grounded in your data</div>
                  )}
                  {m.recs && m.recs.length > 0 && (
                    <div className="recs">
                      {m.recs.map((r) => (
                        <RecommendationCard
                          key={r.rec_id}
                          rec={r}
                          personaId={persona.id}
                          execDisabled={advisoryMode === "info_only"}
                        />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {aged && (
              <FutureSelfPanel
                script={future}
                branch={branch}
                onBranch={openFuture}
                onReplay={() => openFuture(branch)}
                busy={busy}
              />
            )}
            <div ref={endRef} />
          </div>

          <div className="composer-wrap">
            <div className="suggestions">
              {SUGGESTIONS.map((s) => (
                <button key={s} className="chip-btn" onClick={() => send(s)} disabled={busy}>
                  {s}
                </button>
              ))}
            </div>
            <div className="promptbar">
              <input
                value={input}
                placeholder="Message Saarthi…"
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && send(input)}
                disabled={busy}
              />
              {sttSupported() && (
                <button
                  className={`icon-btn ${listening ? "on" : ""}`}
                  onClick={toggleMic}
                  title="Speak (Chrome)"
                >
                  🎤
                </button>
              )}
              <button
                className="icon-btn send"
                onClick={() => send(input)}
                disabled={busy || !input.trim()}
                title="Send"
              >
                {busy ? <span className="spinner" /> : "➤"}
              </button>
            </div>
            <div className="disclosure-mini">
              Educational guidance on your consented data — not individual advice under SEBI IA
              Regulations. Every figure is computed by the engine, not the AI.
            </div>
          </div>
        </section>

        <FinancialPanel data={fin} loading={finLoading} />
      </div>

      {govOpen && (
        <div className="overlay" onClick={() => setGovOpen(false)}>
          <div onClick={(e) => e.stopPropagation()}>
            <GovernancePanel personaId={persona.id} onClose={() => setGovOpen(false)} />
          </div>
        </div>
      )}
    </div>
  );
}

function BrandBar({
  advisoryMode,
  geminiOn,
  persona,
  onSwitch,
  onGov,
}: {
  advisoryMode: string;
  geminiOn: boolean;
  persona?: PersonaCard;
  onSwitch?: () => void;
  onGov?: () => void;
}) {
  return (
    <div className="topbar">
      <div className="brand">
        <div className="brand-mark">🪔</div>
        <div>
          <h1>DhanSaarthi</h1>
          <div className="sub">IDBI · Avatar wealth advisor</div>
        </div>
      </div>
      <div className="topbar-right">
        <span className={`pill ${geminiOn ? "pill-live" : ""}`}>
          {geminiOn ? "✨ Gemini live" : "offline mode"}
        </span>
        {advisoryMode === "info_only" && <span className="pill">advisory paused</span>}
        {persona && (
          <span className="pill">
            {persona.name} · {persona.id}
          </span>
        )}
        {onGov && (
          <button className="btn btn-ghost" onClick={onGov}>
            🛡️ Governance
          </button>
        )}
        {onSwitch && (
          <button className="btn btn-ghost" onClick={onSwitch}>
            Switch
          </button>
        )}
      </div>
    </div>
  );
}
