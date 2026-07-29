import type { CitedSources as CS } from "../api";

const CAT_LABEL: Record<string, string> = {
  own: "Your site", competitor: "Competitors", social: "Social / UGC", editorial: "Editorial / press",
};
const CAT_TONE: Record<string, string> = {
  own: "text-good", competitor: "text-warn", social: "text-accent", editorial: "text-ink-soft",
};

export function CitedSources({ data }: { data: CS }) {
  if (data.total_citations === 0) {
    return <p className="text-sm text-ink-faint">No cited sources yet — re-run with a browsing assistant.</p>;
  }
  const max = Math.max(...data.sources.map((s) => s.share), 0.01);
  const cats = ["own", "competitor", "social", "editorial"] as const;

  return (
    <div>
      {/* Headline: is your own site in AI's sources at all? */}
      <div className={`mb-4 rounded-xl border px-4 py-3 text-sm ${
        data.your_domain_cited ? "border-good bg-good-soft text-good" : "border-crit bg-crit-soft text-crit"}`}>
        {data.your_domain_cited ? (
          <>Your own site (<b>{data.your_domain}</b>) is among the sources AI cites.</>
        ) : (
          <>AI cited <b>{data.total_citations}</b> sources about your market — <b>none were {data.your_domain}</b>.
            Your own site is invisible to AI.</>
        )}
      </div>

      {/* Category breakdown */}
      <div className="mb-5 grid grid-cols-2 gap-2 sm:grid-cols-4">
        {cats.map((c) => (
          <div key={c} className="rounded-xl border border-line bg-surface px-3 py-2.5">
            <div className={`text-xl font-semibold tabular-nums ${CAT_TONE[c]}`}>{data.by_category[c] ?? 0}</div>
            <div className="text-[11px] text-ink-faint">{CAT_LABEL[c]}</div>
          </div>
        ))}
      </div>

      {/* Ranked domains */}
      <div className="flex flex-col gap-1.5">
        {data.sources.map((s) => (
          <div key={s.domain} className="flex items-center gap-3">
            <div className={`w-44 shrink-0 truncate text-sm ${s.is_first_party ? "font-semibold text-accent" : "text-ink-soft"}`}>
              {s.domain}
            </div>
            <div className="h-5 flex-1 overflow-hidden rounded bg-surface-2">
              <div className={`h-full rounded ${s.is_first_party ? "bg-accent" : "bg-ink-faint"}`}
                style={{ width: `${Math.max(6, (s.share / max) * 100)}%`, opacity: s.is_first_party ? 1 : 0.5 }} />
            </div>
            <span className={`w-20 shrink-0 text-right font-mono text-[10px] uppercase ${CAT_TONE[s.category]}`}>
              {s.category}
            </span>
            <span className="w-9 shrink-0 text-right font-mono text-xs text-ink-faint">{Math.round(s.share * 100)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
