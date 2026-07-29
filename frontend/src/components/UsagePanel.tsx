import type { UsageReport } from "../api";

export function UsagePanel({ data }: { data: UsageReport }) {
  return (
    <div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <div className="rounded-xl border border-line bg-surface px-4 py-3.5">
          <div className="text-2xl font-semibold tabular-nums">${data.total_cost_usd.toFixed(4)}</div>
          <div className="mt-0.5 text-xs text-ink-faint">Total spend</div>
        </div>
        <div className="rounded-xl border border-line bg-surface px-4 py-3.5">
          <div className="text-2xl font-semibold tabular-nums">{data.total_tokens.toLocaleString()}</div>
          <div className="mt-0.5 text-xs text-ink-faint">Tokens</div>
        </div>
        <div className="rounded-xl border border-line bg-surface px-4 py-3.5">
          <div className="text-2xl font-semibold tabular-nums">
            {data.budget_usd ? `$${data.budget_usd}` : "—"}
          </div>
          <div className="mt-0.5 text-xs text-ink-faint">Budget cap</div>
        </div>
      </div>

      <div className="mt-5 overflow-x-auto">
        <table className="w-full min-w-[520px] text-sm">
          <thead>
            <tr className="border-b border-line text-left font-mono text-[10px] uppercase tracking-wide text-ink-faint">
              <th className="py-2">When</th><th>Company</th><th className="text-right">Cost</th>
              <th className="text-right">Tokens</th><th className="text-right">Pages</th><th className="text-right">Skipped</th>
            </tr>
          </thead>
          <tbody>
            {data.runs.map((r, i) => (
              <tr key={i} className="border-b border-line/60">
                <td className="py-2 text-ink-soft">{new Date(r.at).toLocaleString()}</td>
                <td className="text-ink">{r.organization ?? "—"}</td>
                <td className="text-right font-mono tabular-nums">${Number(r.cost_usd).toFixed(4)}</td>
                <td className="text-right font-mono tabular-nums text-ink-soft">{Number(r.tokens).toLocaleString()}</td>
                <td className="text-right font-mono tabular-nums text-ink-soft">{r.pages}</td>
                <td className="text-right font-mono tabular-nums text-good">{r.pages_skipped || ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {data.runs.length === 0 && <p className="py-4 text-sm text-ink-faint">No runs yet.</p>}
      </div>
    </div>
  );
}
