import type { Recommendation } from "../api";

const impactTone: Record<string, string> = {
  high: "text-crit border-crit",
  medium: "text-warn border-warn",
  low: "text-ink-soft border-line",
};

export function RecommendationList({ items }: { items: Recommendation[] }) {
  if (items.length === 0) {
    return <p className="text-sm text-ink-faint">No recommendations yet — run an analysis first.</p>;
  }
  return (
    <div className="flex flex-col gap-2.5">
      {items.map((r) => (
        <div key={r.recommendation_id} className="rounded-xl border border-line p-4">
          <div className="flex items-start justify-between gap-3">
            <h4 className="text-sm font-medium text-ink">{r.title}</h4>
            <span
              className={`shrink-0 rounded-md border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide ${impactTone[r.expected_impact]}`}
            >
              {r.expected_impact}
            </span>
          </div>
          <p className="mt-1 text-sm text-ink-soft">{r.missing_detail}</p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {r.affects.map((a) => (
              <span key={a} className="rounded bg-surface-2 px-2 py-0.5 font-mono text-[10px] text-ink-faint">
                {a}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
