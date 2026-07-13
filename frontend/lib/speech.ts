// Voice I/O helpers. TTS tries the backend /tts (neural voice) and falls back to
// the browser SpeechSynthesis API on 503/error — audio must never block the UI.
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

  // 2) Browser SpeechSynthesis fallback (some browsers never fire onend →
  //    the timeout guarantees resolution).
  if (typeof window !== "undefined" && "speechSynthesis" in window) {
    await withTimeout(
      new Promise<void>((resolve) => {
        const u = new SpeechSynthesisUtterance(body);
        u.lang = "en-IN";
        u.rate = 1.0;
        u.onend = () => resolve();
        u.onerror = () => resolve();
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(u);
      }),
      cap,
    );
  }
  opts.onEnd?.();
}

export function stopSpeaking(): void {
  if (typeof window !== "undefined" && "speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
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
