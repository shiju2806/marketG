import { useState } from "react";
import type { ProbeQuestion } from "../api";

export function QuestionList({ items, you }: { items: ProbeQuestion[]; you: string }) {
  if (items.length === 0) {
    return <p className="text-sm text-ink-faint">No AI answers yet — run the analysis.</p>;
  }
  return (
    <div className="flex flex-col gap-3">
      {items.map((q, i) => (
        <QuestionCard key={i} q={q} you={you} />
      ))}
    </div>
  );
}

function QuestionCard({ q, you }: { q: ProbeQuestion; you: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-xl border border-line bg-surface p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <span className="font-mono text-[10px] uppercase tracking-wide text-ink-faint">{q.model}</span>
          <h4 className="mt-0.5 font-medium text-ink">{q.question}</h4>
        </div>
        <span
          className={`shrink-0 rounded-md px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide ${
            q.organization_mentioned ? "bg-good/15 text-good" : "bg-crit/15 text-crit"
          }`}
        >
          {q.organization_mentioned ? `names ${you}` : `no ${you}`}
        </span>
      </div>

      {q.competitor_mentions.length > 0 && (
        <div className="mt-2 flex flex-wrap items-center gap-1.5">
          <span className="text-[11px] text-ink-faint">AI named:</span>
          {q.competitor_mentions.map((c) => (
            <span key={c} className="rounded bg-surface-2 px-2 py-0.5 font-mono text-[10px] text-ink-soft">
              {c}
            </span>
          ))}
        </div>
      )}

      <button
        onClick={() => setOpen(!open)}
        className="mt-2 font-mono text-[11px] text-accent hover:underline"
      >
        {open ? "hide" : "show"} AI answer
      </button>
      {open && <p className="mt-2 border-t border-line pt-2 text-sm text-ink-soft">{q.answer}</p>}
    </div>
  );
}
