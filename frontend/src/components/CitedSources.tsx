import type { CitedSources as CS } from "../api";

const CATS = ["own", "competitor", "social", "editorial"] as const;
type Cat = (typeof CATS)[number];

const CAT: Record<Cat, { label: string; color: string; desc: string }> = {
  own: { label: "Your site", color: "var(--accent)", desc: "content AI cites from you" },
  competitor: { label: "Competitors", color: "var(--warn)", desc: "rivals' own sites" },
  social: { label: "Social / UGC", color: "#9b8cff", desc: "Reddit, YouTube, forums" },
  editorial: { label: "Editorial / press", color: "var(--ink-faint)", desc: "reviews, publications" },
};

function favicon(domain: string) {
  return `https://www.google.com/s2/favicons?domain=${domain}&sz=32`;
}

export function CitedSources({ data }: { data: CS }) {
  if (data.total_citations === 0) {
    return <p className="text-sm text-ink-faint">No cited sources yet — re-run with a browsing assistant.</p>;
  }
  const total = data.total_citations;
  const ownedPct = Math.round(((data.by_category.own ?? 0) / total) * 100);
  const maxShare = Math.max(...data.sources.map((s) => s.share), 0.01);

  return (
    <div className="flex flex-col gap-5">
      {/* Hero: the owned-vs-borrowed story */}
      <div className="rounded-2xl border border-line bg-surface p-5">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-4xl font-bold tabular-nums" style={{ color: ownedPct ? "var(--good)" : "var(--crit)" }}>
              {ownedPct}%
            </div>
            <div className="mt-0.5 text-sm text-ink-soft">of AI's sources are your own site</div>
          </div>
          <div className="text-right text-sm text-ink-faint">
            <span className="font-mono text-2xl font-semibold text-ink">{total}</span> citations analyzed
          </div>
        </div>

        {/* Stacked proportion bar — where AI's trust actually goes */}
        <div className="mt-4 flex h-3.5 w-full overflow-hidden rounded-full">
          {CATS.map((c) => {
            const pct = ((data.by_category[c] ?? 0) / total) * 100;
            if (pct <= 0) return null;
            return <div key={c} className="bar-grow h-full" title={`${CAT[c].label}: ${Math.round(pct)}%`}
              style={{ width: `${pct}%`, background: CAT[c].color, opacity: c === "editorial" ? 0.5 : 1 }} />;
          })}
        </div>

        {ownedPct === 0 && (
          <p className="mt-3 text-sm text-crit">
            AI never cites <b>{data.your_domain}</b> — your visibility is entirely borrowed from third parties.
          </p>
        )}
      </div>

      {/* Category cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {CATS.map((c) => (
          <div key={c} className="rounded-xl border border-line bg-surface p-3.5 transition hover:-translate-y-0.5 hover:shadow-md">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-sm" style={{ background: CAT[c].color }} />
              <span className="text-2xl font-semibold tabular-nums text-ink">{data.by_category[c] ?? 0}</span>
            </div>
            <div className="mt-1 text-xs font-medium text-ink-soft">{CAT[c].label}</div>
            <div className="text-[11px] text-ink-faint">{CAT[c].desc}</div>
          </div>
        ))}
      </div>

      {/* Ranked domains AI trusts */}
      <div>
        <h4 className="mb-2 font-mono text-xs uppercase tracking-widest text-ink-faint">Who AI trusts most</h4>
        <div className="flex flex-col gap-1">
          {data.sources.map((s, i) => (
            <div key={s.domain}
              className="flex items-center gap-3 rounded-lg px-2 py-1.5 transition hover:bg-surface-2">
              <span className="w-5 shrink-0 text-right font-mono text-xs text-ink-faint">{i + 1}</span>
              <img src={favicon(s.domain)} alt="" width={16} height={16}
                className="shrink-0 rounded" onError={(e) => (e.currentTarget.style.visibility = "hidden")} />
              <div className={`w-40 shrink-0 truncate text-sm ${s.is_first_party ? "font-semibold text-accent" : "text-ink"}`}>
                {s.domain}
              </div>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-surface-2">
                <div className="bar-grow h-full rounded-full"
                  style={{ width: `${Math.max(4, (s.share / maxShare) * 100)}%`, background: CAT[s.category].color,
                    opacity: s.category === "editorial" ? 0.55 : 1 }} />
              </div>
              <span className="w-16 shrink-0 text-right font-mono text-[10px] uppercase" style={{ color: CAT[s.category].color }}>
                {s.category}
              </span>
              <span className="w-9 shrink-0 text-right font-mono text-xs text-ink-faint">{Math.round(s.share * 100)}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
