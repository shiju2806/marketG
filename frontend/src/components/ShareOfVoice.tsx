import { useState } from "react";
import type { ShareOfVoice as SOV } from "../api";

export function ShareOfVoice({ data }: { data: SOV[] }) {
  const [showAll, setShowAll] = useState(false);
  if (data.length === 0) {
    return <p className="text-sm text-ink-faint">Run an analysis to see who gets named in your market.</p>;
  }
  const max = Math.max(...data.map((d) => d.mentions), 1);
  const visible = showAll ? data : data.slice(0, 8);

  return (
    <div className="flex flex-col gap-2">
      {visible.map((d) => (
        <div key={d.brand} className="flex items-center gap-3">
          <div className={`w-24 shrink-0 truncate text-sm ${d.is_you ? "font-semibold text-accent" : "text-ink-soft"}`}>
            {d.brand}
          </div>
          <div className="h-6 flex-1 overflow-hidden rounded bg-surface-2">
            <div
              className={`flex h-full items-center justify-end rounded pr-2 font-mono text-[11px] ${
                d.is_you ? "bg-accent text-white" : "bg-ink-faint text-white"
              }`}
              style={{ width: `${Math.max(9, (d.mentions / max) * 100)}%`, opacity: d.is_you ? 1 : 0.55 }}
            >
              {Math.round(d.share * 100)}%
            </div>
          </div>
        </div>
      ))}
      {data.length > 8 && (
        <button
          onClick={() => setShowAll(!showAll)}
          className="mt-1 self-start text-xs text-accent hover:underline"
        >
          {showAll ? "Show fewer" : `Show all ${data.length}`}
        </button>
      )}
    </div>
  );
}
