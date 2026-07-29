import { useState, type FormEvent } from "react";
import { api } from "../api";

const SUGGESTIONS = [
  "Which of your products is best for towing?",
  "What's your longest-range option?",
  "How do you compare on price?",
];

// Query the twin — the differentiating "queryable knowledge asset". Compact chat-style.
export function AskTwin({ orgId }: { orgId: string }) {
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState<{ answer: string | null; supported: boolean; facts_used: string[] } | null>(null);

  async function run(question: string) {
    if (!question.trim()) return;
    setQ(question);
    setBusy(true);
    setRes(null);
    try {
      setRes(await api.reason(orgId, question.trim()));
    } catch {
      setRes({ answer: "Something went wrong.", supported: false, facts_used: [] });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <form onSubmit={(e: FormEvent) => { e.preventDefault(); run(q); }} className="flex gap-2">
        <input value={q} onChange={(e) => setQ(e.target.value)} disabled={busy}
          placeholder="Ask anything about your products…"
          className="flex-1 rounded-lg border border-line bg-bg px-3 py-2 text-sm outline-none focus:border-accent" />
        <button type="submit" disabled={busy || !q.trim()}
          className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-40">
          {busy ? "Thinking…" : "Ask"}
        </button>
      </form>

      {!res && !busy && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {SUGGESTIONS.map((s) => (
            <button key={s} onClick={() => run(s)}
              className="rounded-full border border-line px-2.5 py-1 text-xs text-ink-soft hover:border-accent hover:text-accent">
              {s}
            </button>
          ))}
        </div>
      )}

      {busy && <div className="skeleton mt-3 h-16 w-full" />}

      {res && (
        <div className="fade-in mt-3 rounded-xl border border-line bg-bg p-4">
          <p className="text-sm text-ink">{res.answer ?? "No answer."}</p>
          <div className="mt-2 flex items-center gap-2">
            <span className={`rounded-md px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide ${
              res.supported ? "bg-good-soft text-good" : "bg-surface-2 text-ink-faint"}`}>
              {res.supported ? "✓ grounded in your twin" : "not supported by your content"}
            </span>
            {res.facts_used.length > 0 && (
              <details className="text-xs">
                <summary className="cursor-pointer text-accent">{res.facts_used.length} facts used</summary>
                <ul className="mt-1 flex flex-col gap-0.5">
                  {res.facts_used.map((f, i) => <li key={i} className="text-ink-soft">{f}</li>)}
                </ul>
              </details>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
