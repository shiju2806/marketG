import type { Recommendation } from "../api";

const impactTone: Record<string, string> = {
  high: "text-crit border-crit/40",
  medium: "text-warn border-warn/40",
  low: "text-ink-soft border-line",
};

export function RecommendationList({ items }: { items: Recommendation[] }) {
  if (items.length === 0) {
    return <p className="text-sm text-ink-faint">No recommendations yet — run a visibility + probe pass, then generate.</p>;
  }
  return (
    <div className="flex flex-col gap-3">
      {items.map((r) => (
        <div key={r.recommendation_id} className="rounded-xl border border-line bg-surface p-4">
          <div className="flex items-start justify-between gap-3">
            <h4 className="font-medium text-ink">{r.title}</h4>
            <span
              className={`shrink-0 rounded-md border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide ${impactTone[r.expected_impact]}`}
            >
              {r.expected_impact}
            </span>
          </div>
          <p className="mt-1 text-sm text-ink-soft">{r.missing_detail}</p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {r.affects.map((a) => (
              <span key={a} className="rounded bg-surface-2 px-2 py-0.5 font-mono text-[10px] text-accent">
                {a}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
