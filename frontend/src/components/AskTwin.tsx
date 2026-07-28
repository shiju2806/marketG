import { useState, type FormEvent } from "react";
import { api } from "../api";

// Query the twin — the differentiating "queryable knowledge asset" (multi-hop
// reasoning over the graph), which a point-tool tracker can't do.
export function AskTwin({ orgId }: { orgId: string }) {
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState<{ answer: string | null; supported: boolean; facts_used: string[] } | null>(null);

  async function ask(e: FormEvent) {
    e.preventDefault();
    if (!q.trim()) return;
    setBusy(true);
    setRes(null);
    try {
      const r = await api.reason(orgId, q.trim());
      setRes(r);
    } catch {
      setRes({ answer: "Something went wrong.", supported: false, facts_used: [] });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <form onSubmit={ask} className="flex gap-2">
        <input value={q} onChange={(e) => setQ(e.target.value)} disabled={busy}
          placeholder="e.g. Which of your products is best for towing?"
          className="flex-1 rounded-lg border border-line bg-bg px-3 py-2 text-sm outline-none focus:border-accent" />
        <button type="submit" disabled={busy || !q.trim()}
          className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-40">
          {busy ? "Thinking…" : "Ask"}
        </button>
      </form>
      {res && (
        <div className="mt-3 rounded-xl border border-line bg-surface p-4">
          <p className="text-sm text-ink">{res.answer ?? "No answer."}</p>
          <div className="mt-1 font-mono text-[10px] uppercase tracking-wide text-ink-faint">
            {res.supported ? "grounded in your twin" : "not supported by your content"}
          </div>
          {res.facts_used.length > 0 && (
            <details className="mt-2">
              <summary className="cursor-pointer text-xs text-accent">facts used</summary>
              <ul className="mt-1 flex flex-col gap-0.5">
                {res.facts_used.map((f, i) => <li key={i} className="text-xs text-ink-soft">{f}</li>)}
              </ul>
            </details>
          )}
        </div>
      )}
    </div>
  );
}
