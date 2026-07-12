import { useState } from "react";
import type { ProbeQuestion } from "../api";

// Group the per-model rows by question so each question shows once.
interface Grouped {
  question: string;
  mentioned: boolean;
  byModel: ProbeQuestion[];
  competitors: string[];
}

function group(items: ProbeQuestion[]): Grouped[] {
  const map = new Map<string, Grouped>();
  for (const it of items) {
    const g = map.get(it.question) ?? {
      question: it.question, mentioned: false, byModel: [], competitors: [],
    };
    g.byModel.push(it);
    g.mentioned = g.mentioned || it.organization_mentioned;
    for (const c of it.competitor_mentions) if (!g.competitors.includes(c)) g.competitors.push(c);
    map.set(it.question, g);
  }
  return [...map.values()];
}

export function QuestionList({ items, you }: { items: ProbeQuestion[]; you: string }) {
  const grouped = group(items);
  if (grouped.length === 0) return <p className="text-sm text-ink-faint">No answers yet.</p>;
  return (
    <div className="flex flex-col gap-2.5">
      {grouped.map((g, i) => <QuestionRow key={i} g={g} you={you} />)}
    </div>
  );
}

function QuestionRow({ g, you }: { g: Grouped; you: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-xl border border-line">
      <button onClick={() => setOpen(!open)} className="flex w-full items-center gap-3 px-4 py-3 text-left">
        <span
          className={`shrink-0 rounded-md px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide ${
            g.mentioned ? "bg-good-soft text-good" : "bg-crit-soft text-crit"
          }`}
        >
          {g.mentioned ? "appears" : "absent"}
        </span>
        <span className="flex-1 text-sm text-ink">{g.question}</span>
        {g.competitors.length > 0 && (
          <span className="hidden shrink-0 text-xs text-ink-faint sm:inline">
            {g.competitors.slice(0, 3).join(", ")}
            {g.competitors.length > 3 && ` +${g.competitors.length - 3}`}
          </span>
        )}
      </button>
      {open && (
        <div className="border-t border-line px-4 py-3">
          <div className="mb-2 text-xs text-ink-faint">
            Named: {g.competitors.join(", ") || "—"}
          </div>
          {g.byModel.map((m, j) => (
            <div key={j} className="mb-3 last:mb-0">
              <div className="font-mono text-[10px] uppercase tracking-wide text-ink-faint">
                {m.model} · {m.organization_mentioned ? `names ${you}` : `no ${you}`}
              </div>
              <p className="mt-1 text-sm text-ink-soft">{m.answer}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
