import type { CitedSources as CS } from "../api";

export function CitedSources({ data }: { data: CS }) {
  if (data.total_citations === 0) {
    return <p className="text-sm text-ink-faint">No cited sources yet — re-run with a browsing assistant.</p>;
  }
  const max = Math.max(...data.sources.map((s) => s.share), 0.01);

  return (
    <div>
      {/* Headline callout: is your own site in AI's sources at all? */}
      <div
        className={`mb-4 rounded-xl border px-4 py-3 text-sm ${
          data.your_domain_cited ? "border-good bg-good-soft text-good" : "border-crit bg-crit-soft text-crit"
        }`}
      >
        {data.your_domain_cited ? (
          <>Your own site (<b>{data.your_domain}</b>) is among the sources AI cites.</>
        ) : (
          <>
            AI cited <b>{data.total_citations}</b> sources about your market —{" "}
            <b>none were {data.your_domain}</b>. Your own site is invisible to AI.
          </>
        )}
      </div>

      <div className="flex flex-col gap-1.5">
        {data.sources.map((s) => (
          <div key={s.domain} className="flex items-center gap-3">
            <div className={`w-40 shrink-0 truncate text-sm ${s.is_first_party ? "font-semibold text-accent" : "text-ink-soft"}`}>
              {s.domain}
            </div>
            <div className="h-5 flex-1 overflow-hidden rounded bg-surface-2">
              <div
                className={`h-full rounded ${s.is_first_party ? "bg-accent" : "bg-ink-faint"}`}
                style={{ width: `${Math.max(6, (s.share / max) * 100)}%`, opacity: s.is_first_party ? 1 : 0.5 }}
              />
            </div>
            <div className="w-10 shrink-0 text-right font-mono text-xs text-ink-faint">
              {Math.round(s.share * 100)}%
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
