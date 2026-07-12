import type { Delta, DeltaCategory } from "../api";

const cellStyle: Record<string, string> = {
  winning: "border-good bg-good-soft",
  hidden: "border-crit bg-crit-soft",
  missing: "border-crit bg-crit-soft",
  borrowed: "border-warn bg-warn-soft",
};

const cellLabel: Record<string, { title: string; sub: string }> = {
  winning: { title: "Winning", sub: "you have content · AI names you" },
  hidden: { title: "Hidden", sub: "you have content · AI can't see it" },
  missing: { title: "Missing", sub: "no content · AI names rivals" },
  borrowed: { title: "Borrowed", sub: "no content · AI knows you 2nd-hand" },
};

function Cell({ q, cats }: { q: string; cats: DeltaCategory[] }) {
  const label = cellLabel[q];
  return (
    <div className={`rounded-xl border p-3 ${cellStyle[q]}`}>
      <div className="flex items-baseline justify-between">
        <span className="text-sm font-semibold text-ink">{label.title}</span>
        <span className="font-mono text-lg font-bold tabular-nums text-ink">{cats.length}</span>
      </div>
      <div className="mt-0.5 text-[11px] text-ink-faint">{label.sub}</div>
      <ul className="mt-2 flex flex-col gap-1">
        {cats.slice(0, 4).map((c, i) => (
          <li key={i} className="truncate text-xs text-ink-soft">{c.question}</li>
        ))}
        {cats.length > 4 && <li className="text-xs text-ink-faint">+{cats.length - 4} more</li>}
      </ul>
    </div>
  );
}

export function GapMatrix({ data }: { data: Delta }) {
  if (!data.twin_readable) {
    return (
      <p className="text-sm text-ink-faint">
        We couldn't read your site, so we can't map your content against what AI is asked.
        Fix crawlability first (see the top of the report).
      </p>
    );
  }
  const by = (q: string) => data.categories.filter((c) => c.quadrant === q);
  return (
    <div>
      <div className="mb-2 grid grid-cols-[80px_1fr_1fr] gap-2 font-mono text-[10px] uppercase tracking-wide text-ink-faint">
        <span />
        <span className="text-center">AI names you</span>
        <span className="text-center">AI doesn't</span>
      </div>
      <div className="grid grid-cols-[80px_1fr_1fr] gap-2">
        <div className="flex items-center font-mono text-[10px] uppercase tracking-wide text-ink-faint">You have content</div>
        <Cell q="winning" cats={by("winning")} />
        <Cell q="hidden" cats={by("hidden")} />
        <div className="flex items-center font-mono text-[10px] uppercase tracking-wide text-ink-faint">No content</div>
        <Cell q="borrowed" cats={by("borrowed")} />
        <Cell q="missing" cats={by("missing")} />
      </div>
    </div>
  );
}
