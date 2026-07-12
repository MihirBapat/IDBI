"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import AvatarStage from "@/components/AvatarStage";
import ConsentFlow from "@/components/ConsentFlow";
import FutureSelfPanel from "@/components/FutureSelfPanel";
import GovernancePanel from "@/components/GovernancePanel";
import RecommendationCard from "@/components/RecommendationCard";
import { API, chat, futureSelf, revokeConsent } from "@/lib/api";
import type { PersonaCard } from "@/lib/personas";
import { listen, speak, stopSpeaking, sttSupported } from "@/lib/speech";
import type {
  ChatResponse,
  ConsentSummary,
  ProjectionScript,
  Recommendation,
} from "@/lib/types";

interface Msg {
  role: "user" | "saarthi";
  text: string;
}

const SUGGESTIONS = [
  "What should I do with my money?",
  "Why this advice?",
  "Show me my future self",
  "The market is crashing — should I sell?",
];

export default function Home() {
  const [persona, setPersona] = useState<PersonaCard | null>(null);
  const [, setConsent] = useState<ConsentSummary | null>(null);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [input, setInput] = useState("");
  const [speaking, setSpeaking] = useState(false);
  const [listening, setListening] = useState(false);
  const [caption, setCaption] = useState<string>("");
  const [disclosure, setDisclosure] = useState<string | undefined>();
  const [busy, setBusy] = useState(false);
  const [aged, setAged] = useState(false);
  const [future, setFuture] = useState<ProjectionScript | null>(null);
  const [branch, setBranch] = useState<"good" | "bad">("good");
  const [govOpen, setGovOpen] = useState(false);
  const [advisoryMode, setAdvisoryMode] = useState<string>("on");
  const stopListenRef = useRef<() => void>(() => {});
  const msgEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch(`${API}/health`)
      .then((r) => r.json())
      .then((h) => setAdvisoryMode(h.advisory_mode ?? "on"))
      .catch(() => {});
  }, []);

  useEffect(() => {
    msgEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const say = useCallback(async (text: string, disc?: string) => {
    setCaption(text);
    setDisclosure(disc);
    setSpeaking(true);
    await speak(text, {});
    setSpeaking(false);
  }, []);

  const bodyOf = (t: string) => t.split("\n\n")[0].trim();

  // Greet on consent grant.
  const onGranted = useCallback(
    async (p: PersonaCard, c: ConsentSummary) => {
      setPersona(p);
      setConsent(c);
      setBusy(true);
      try {
        const r = await chat(p.id, "hello");
        setMessages([{ role: "saarthi", text: r.spoken_text }]);
        await say(bodyOf(r.spoken_text), r.disclosure);
      } finally {
        setBusy(false);
      }
    },
    [say],
  );

  const send = useCallback(
    async (text: string) => {
      if (!persona || !text.trim()) return;
      setInput("");
      setMessages((m) => [...m, { role: "user", text }]);
      setBusy(true);
      try {
        const r: ChatResponse = await chat(persona.id, text);
        setMessages((m) => [...m, { role: "saarthi", text: r.spoken_text }]);
        if (r.recommendations.length > 0) setRecs(r.recommendations);
        if (r.intent === "FUTURE_SELF") {
          await openFuture("good");
        } else {
          setAged(false);
          setFuture(null);
          await say(bodyOf(r.spoken_text), r.disclosure);
        }
      } catch {
        const err = "I couldn't reach the advisory service. Is the backend running?";
        setMessages((m) => [...m, { role: "saarthi", text: err }]);
        await say(err);
      } finally {
        setBusy(false);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [persona, say],
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
        for (const line of script.lines) {
          await say(line.text);
        }
      } finally {
        setBusy(false);
      }
    },
    [persona, say],
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
    setMessages([]);
    setRecs([]);
    setFuture(null);
    setAged(false);
    setCaption("");
    setGovOpen(false);
  }, [persona]);

  // ---- Render ----
  if (!persona) {
    return (
      <div className="app">
        <BrandBar advisoryMode={advisoryMode} />
        <ConsentFlow onGranted={onGranted} />
      </div>
    );
  }

  return (
    <div className="app">
      <BrandBar advisoryMode={advisoryMode} onSwitch={switchCustomer} persona={persona} />

      <div className="grid">
        <div className="card stage-card">
          <AvatarStage
            speaking={speaking}
            listening={listening}
            aged={aged}
            caption={caption}
            disclosure={disclosure}
          />
          {aged && (
            <FutureSelfPanel
              script={future}
              branch={branch}
              onBranch={openFuture}
              onReplay={() => openFuture(branch)}
              busy={busy}
            />
          )}
        </div>

        <div className="card chat">
          <div className="messages">
            {messages.map((m, i) => (
              <div key={i} className={`msg ${m.role}`}>
                {m.role === "saarthi" ? bodyOf(m.text) : m.text}
              </div>
            ))}
            <div ref={msgEndRef} />
          </div>

          <div className="composer">
            <input
              value={input}
              placeholder="Ask Saarthi about your money…"
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send(input)}
              disabled={busy}
            />
            {sttSupported() && (
              <button
                className={`btn mic ${listening ? "on" : ""}`}
                onClick={toggleMic}
                title="Speak (Chrome)"
              >
                🎤
              </button>
            )}
            <button className="btn btn-primary" onClick={() => send(input)} disabled={busy}>
              {busy ? <span className="spinner" /> : "Send"}
            </button>
          </div>

          <div className="suggestions">
            {SUGGESTIONS.map((s) => (
              <button key={s} className="btn btn-ghost" onClick={() => send(s)} disabled={busy}>
                {s}
              </button>
            ))}
          </div>

          {recs.length > 0 && (
            <div style={{ marginTop: 6 }}>
              <div className="section-title">Recommendations</div>
              <div className="recs">
                {recs.map((r) => (
                  <RecommendationCard
                    key={r.rec_id}
                    rec={r}
                    personaId={persona.id}
                    execDisabled={advisoryMode === "info_only"}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <button className="btn gov-toggle" onClick={() => setGovOpen(true)}>
        🛡️ Governance
      </button>
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
  onSwitch,
  persona,
}: {
  advisoryMode: string;
  onSwitch?: () => void;
  persona?: PersonaCard;
}) {
  return (
    <div className="brandbar">
      <div className="brand">
        <div className="brand-mark">🪔</div>
        <div>
          <h1>DhanSaarthi</h1>
          <div className="sub">IDBI · Avatar wealth advisor</div>
        </div>
      </div>
      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <span className="tagpill">
          advisory: {advisoryMode === "info_only" ? "info-only (paused)" : "on"}
        </span>
        {persona && (
          <span className="tagpill">
            {persona.name} · {persona.id}
          </span>
        )}
        {onSwitch && (
          <button className="btn btn-ghost" onClick={onSwitch}>
            Switch customer
          </button>
        )}
      </div>
    </div>
  );
}
