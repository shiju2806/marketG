import { useState } from "react";
import type { ShareOfVoice } from "../api";

export function Leaderboard({ data, limit = 8 }: { data: ShareOfVoice[]; limit?: number }) {
  const [showAll, setShowAll] = useState(false);
  if (data.length === 0) return <p className="text-sm text-ink-faint">No data yet.</p>;
  const max = Math.max(...data.map((d) => d.mentions), 1);
  const rows = showAll ? data : data.slice(0, limit);

  return (
    <div className="flex flex-col gap-1.5">
      {rows.map((d, i) => (
        <div key={d.brand} className="flex items-center gap-3">
          <span className="w-5 shrink-0 text-right font-mono text-xs text-ink-faint">{i + 1}</span>
          <span className={`w-28 shrink-0 truncate text-sm ${d.is_you ? "font-semibold text-accent" : "text-ink-soft"}`}>
            {d.brand}
          </span>
          <div className="h-5 flex-1 overflow-hidden rounded bg-surface-2">
            <div className="h-full rounded"
              style={{
                width: `${Math.max(4, (d.mentions / max) * 100)}%`,
                background: d.is_you ? "var(--accent)" : "var(--ink-faint)",
                opacity: d.is_you ? 1 : 0.5,
              }} />
          </div>
          <span className="w-9 shrink-0 text-right font-mono text-xs text-ink-faint">
            {Math.round(d.share * 100)}%
          </span>
        </div>
      ))}
      {data.length > limit && (
        <button onClick={() => setShowAll(!showAll)} className="mt-1 self-start text-xs text-accent hover:underline">
          {showAll ? "Show fewer" : `Show all ${data.length}`}
        </button>
      )}
    </div>
  );
}
