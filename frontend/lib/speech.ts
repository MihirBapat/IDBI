// Voice I/O helpers. TTS tries the backend /tts (neural voice) and falls back to
// the browser SpeechSynthesis API on 503/error — audio must never block the UI.
// The browser fallback is deliberately *expressive*: it hand-picks the most
// natural voice on the device and speaks sentence-by-sentence with varied
// pitch/rate (questions rise, exclamations lift, numbers slow down) so Saarthi
// sounds human rather than flat/monotone.
// STT uses the Web Speech API (Chrome). Both are optional enhancements.

import { API } from "./api";

/** Race a promise against a max duration so speech never blocks forever. */
function withTimeout(p: Promise<void>, ms: number): Promise<void> {
  return new Promise<void>((resolve) => {
    let done = false;
    const finish = () => {
      if (!done) {
        done = true;
        resolve();
      }
    };
    const t = setTimeout(finish, ms);
    p.then(() => {
      clearTimeout(t);
      finish();
    }).catch(() => {
      clearTimeout(t);
      finish();
    });
  });
}

/** Speak text; resolves when playback ends, on error, or after a safety cap. */
export async function speak(
  text: string,
  opts: { onStart?: () => void; onEnd?: () => void } = {},
): Promise<void> {
  const body = speechBody(text);
  const cap = Math.min(20000, Math.max(3500, body.length * 70)); // safety ceiling
  opts.onStart?.();

  // 1) Try neural TTS from the backend.
  try {
    const res = await fetch(`${API}/tts?text=${encodeURIComponent(body)}`);
    if (res.ok) {
      const url = URL.createObjectURL(await res.blob());
      await withTimeout(
        new Promise<void>((resolve) => {
          const audio = new Audio(url);
          audio.onended = () => {
            URL.revokeObjectURL(url);
            resolve();
          };
          audio.onerror = () => resolve();
          audio.play().catch(() => resolve());
        }),
        cap,
      );
      opts.onEnd?.();
      return;
    }
  } catch {
    /* fall through to browser speech */
  }

  // 2) Expressive browser SpeechSynthesis fallback (some browsers never fire
  //    onend → the timeout guarantees resolution).
  if (typeof window !== "undefined" && "speechSynthesis" in window) {
    await withTimeout(speakExpressive(body), cap);
  }
  opts.onEnd?.();
}

export function stopSpeaking(): void {
  if (typeof window !== "undefined" && "speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
}

// --------------------------------------------------------------------------- //
// Expressive browser speech
// --------------------------------------------------------------------------- //

let _voice: SpeechSynthesisVoice | null | undefined;

/** getVoices() is async on first load; wait (briefly) for it to populate. */
function loadVoices(): Promise<SpeechSynthesisVoice[]> {
  const synth = window.speechSynthesis;
  const now = synth.getVoices();
  if (now.length) return Promise.resolve(now);
  return new Promise((resolve) => {
    const t = setTimeout(() => resolve(synth.getVoices()), 800);
    synth.onvoiceschanged = () => {
      clearTimeout(t);
      resolve(synth.getVoices());
    };
  });
}

/** Rank the installed voices and cache the most natural-sounding one. */
async function pickVoice(): Promise<SpeechSynthesisVoice | null> {
  if (_voice !== undefined) return _voice;
  const voices = await loadVoices();
  const score = (v: SpeechSynthesisVoice): number => {
    const n = v.name.toLowerCase();
    const l = v.lang.toLowerCase();
    let s = 0;
    if (l === "en-in") s += 40;
    else if (l.startsWith("en")) s += 15;
    if (/natural|neural/.test(n)) s += 30; // modern high-quality voices
    if (n.includes("google")) s += 20; // Google voices sound notably human
    if (/microsoft/.test(n)) s += 6;
    if (/neerja|swara|aria|jenny|sonia|priya|kavya|female/.test(n)) s += 8;
    if (v.localService === false) s += 4; // network voices tend to be richer
    return s;
  };
  const en = voices.filter((v) => v.lang.toLowerCase().startsWith("en"));
  const pool = (en.length ? en : voices).slice().sort((a, b) => score(b) - score(a));
  _voice = pool[0] ?? null;
  return _voice;
}

/** Pitch/rate for one sentence — the source of the "emotion". */
function prosody(sentence: string): { rate: number; pitch: number } {
  const s = sentence.trim();
  let rate = 0.97; // a touch slower than default reads as warmer, more human
  let pitch = 1.06;
  if (/\?\s*$/.test(s)) {
    pitch = 1.16; // questions rise at the end
    rate = 1.0;
  } else if (/!\s*$/.test(s)) {
    pitch = 1.22; // exclamations lift and quicken
    rate = 1.06;
  }
  if (/[₹%]|\d/.test(s)) rate = Math.min(rate, 0.9); // let money/figures land
  pitch += (Math.random() - 0.5) * 0.06; // subtle variation between sentences
  return { rate, pitch: Math.max(0.9, Math.min(1.4, pitch)) };
}

/** Break a narration into speakable, prosody-tagged clauses. */
function phrase(body: string): Array<{ text: string; rate: number; pitch: number }> {
  const sentences = body.match(/[^.!?]+[.!?]*/g) ?? [body];
  const out: string[] = [];
  for (const raw of sentences) {
    const t = raw.trim();
    if (!t) continue;
    // Long sentences get broken on commas so Saarthi "breathes" mid-thought.
    if (t.length > 140 && t.includes(", ")) {
      let buf = "";
      for (const clause of t.split(", ")) {
        buf = buf ? `${buf}, ${clause}` : clause;
        if (buf.length > 90) {
          out.push(buf);
          buf = "";
        }
      }
      if (buf) out.push(buf);
    } else {
      out.push(t);
    }
  }
  return out.map((text) => ({ text, ...prosody(text) }));
}

/** Speak a narration with per-sentence emotion; resolves when the last ends. */
function speakExpressive(body: string): Promise<void> {
  const synth = window.speechSynthesis;
  synth.cancel();
  return pickVoice().then(
    (voice) =>
      new Promise<void>((resolve) => {
        const chunks = phrase(body);
        if (!chunks.length) {
          resolve();
          return;
        }
        // Chrome pauses long queued speech after ~15s; nudge it to keep going.
        const keepAlive = setInterval(() => synth.resume(), 5000);
        const finish = () => {
          clearInterval(keepAlive);
          resolve();
        };
        chunks.forEach((chunk, i) => {
          const u = new SpeechSynthesisUtterance(chunk.text);
          u.lang = voice?.lang ?? "en-IN";
          if (voice) u.voice = voice;
          u.rate = chunk.rate;
          u.pitch = chunk.pitch;
          u.volume = 1;
          if (i === chunks.length - 1) {
            u.onend = finish;
            u.onerror = finish;
          }
          synth.speak(u);
        });
      }),
  );
}

/** Drop the SEBI disclosure (after the blank line) so it isn't read aloud. */
function speechBody(text: string): string {
  return text.split("\n\n")[0].trim();
}

/** True if the browser exposes speech recognition (Chrome/Edge). */
export function sttSupported(): boolean {
  if (typeof window === "undefined") return false;
  const w = window as unknown as Record<string, unknown>;
  return Boolean(w.SpeechRecognition || w.webkitSpeechRecognition);
}

/** One-shot listen; calls onResult with the final transcript. Returns a stopper. */
export function listen(
  onResult: (text: string) => void,
  onEnd?: () => void,
): () => void {
  const w = window as unknown as Record<string, unknown>;
  const Ctor = (w.SpeechRecognition || w.webkitSpeechRecognition) as
    | (new () => {
        lang: string;
        interimResults: boolean;
        maxAlternatives: number;
        onresult: (e: unknown) => void;
        onend: () => void;
        start: () => void;
        stop: () => void;
      })
    | undefined;
  if (!Ctor) {
    onEnd?.();
    return () => {};
  }
  const rec = new Ctor();
  rec.lang = "en-IN";
  rec.interimResults = false;
  rec.maxAlternatives = 1;
  rec.onresult = (e: unknown) => {
    const ev = e as { results: Array<Array<{ transcript: string }>> };
    onResult(ev.results[0][0].transcript);
  };
  rec.onend = () => onEnd?.();
  rec.start();
  return () => rec.stop();
}
