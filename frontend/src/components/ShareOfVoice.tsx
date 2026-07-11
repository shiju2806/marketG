import type { ShareOfVoice as SOV } from "../api";

export function ShareOfVoice({ data }: { data: SOV[] }) {
  if (data.length === 0) {
    return <p className="text-sm text-ink-faint">Run the analysis to see who AI names in your market.</p>;
  }
  const max = Math.max(...data.map((d) => d.mentions), 1);
  return (
    <div className="flex flex-col gap-2.5">
      {data.map((d) => (
        <div key={d.brand} className="flex items-center gap-3">
          <div className={`w-28 shrink-0 truncate text-sm ${d.is_you ? "font-semibold text-accent" : "text-ink-soft"}`}>
            {d.brand}
            {d.is_you && <span className="ml-1 text-[10px] uppercase tracking-wide text-accent">you</span>}
          </div>
          <div className="h-6 flex-1 overflow-hidden rounded bg-surface-2">
            <div
              className={`flex h-full items-center justify-end rounded pr-2 font-mono text-[11px] ${
                d.is_you ? "bg-accent text-bg" : "bg-ink-faint/40 text-ink"
              }`}
              style={{ width: `${Math.max(8, (d.mentions / max) * 100)}%` }}
            >
              {Math.round(d.share * 100)}%
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
