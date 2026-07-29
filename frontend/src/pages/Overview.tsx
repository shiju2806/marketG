import { Link } from "react-router-dom";
import { api } from "../api";
import { useAsync } from "../state";
import { TrendChart } from "../components/TrendChart";
import { Leaderboard } from "../components/Leaderboard";
import { ScoreRing, Skeleton } from "../components/ScoreRing";
import { PageTitle, Card, ErrorMsg } from "./parts";

const statusStyle: Record<string, { border: string; bg: string; text: string; icon: string; note: string }> = {
  readable: { border: "border-good", bg: "bg-good-soft", text: "text-good", icon: "✓",
    note: "AI assistants can read and cite your site." },
  blocked: { border: "border-crit", bg: "bg-crit-soft", text: "text-crit", icon: "✕",
    note: "AI can't read your site — it describes you from third parties instead." },
  thin: { border: "border-warn", bg: "bg-warn-soft", text: "text-warn", icon: "!",
    note: "Your pages render for humans but expose little for AI to extract." },
  unreachable: { border: "border-crit", bg: "bg-crit-soft", text: "text-crit", icon: "✕",
    note: "We couldn't reach your site." },
};

function KpiCard({ value, label, tone = "ink", to, sub }: {
  value: string; label: string; tone?: string; to?: string; sub?: string;
}) {
  const toneClass = { ink: "text-ink", good: "text-good", warn: "text-warn", crit: "text-crit", accent: "text-accent" }[tone] ?? "text-ink";
  const body = (
    <div className="group h-full rounded-2xl border border-line bg-surface px-5 py-4 transition hover:-translate-y-0.5 hover:border-accent hover:shadow-lg">
      <div className={`text-3xl font-semibold tabular-nums tracking-tight ${toneClass}`}>{value}</div>
      <div className="mt-1 text-xs text-ink-faint">{label}</div>
      {sub && <div className="mt-1.5 text-[11px] text-ink-faint">{sub}</div>}
    </div>
  );
  return to ? <Link to={to} className="block">{body}</Link> : body;
}

export function Overview() {
  const { data, loading, error } = useAsync(api.overview);

  if (error) return <ErrorMsg error={error} />;
  if (loading || !data) {
    return (
      <div>
        <PageTitle title="Overview" subtitle="How AI sees you when buyers research your market" />
        <div className="grid gap-4 lg:grid-cols-3">
          <Skeleton className="h-32 lg:col-span-1" />
          <Skeleton className="h-32" /><Skeleton className="h-32" />
        </div>
        <Skeleton className="mt-4 h-40" />
      </div>
    );
  }

  const s = statusStyle[data.diagnosis?.status ?? ""] ?? null;
  const rate = data.your_share, owned = data.earned_owned;

  return (
    <div className="fade-in">
      <PageTitle title="Overview" subtitle="How AI sees you when buyers research your market" />

      {/* Hero row: score ring + headline stats */}
      <div className="grid gap-4 lg:grid-cols-[auto_1fr]">
        <Card><ScoreRing value={data.score?.overall ?? null} label="AI visibility score" /></Card>
        <div className="grid grid-cols-3 gap-4">
          <KpiCard value={rate != null ? `${rate}%` : "—"} label="Share of voice"
            sub={data.rank ? `#${data.rank} of ${data.brand_count} brands` : undefined}
            tone={(rate ?? 0) >= 40 ? "good" : (rate ?? 0) >= 15 ? "warn" : "crit"} to="/competitors" />
          <KpiCard value={owned == null ? "—" : `${Math.round(owned * 100)}%`} label="Owned sources"
            sub={owned === 0 ? "AI never cites your site" : undefined}
            tone={owned === 0 ? "crit" : "good"} to="/sources" />
          <KpiCard value={`${data.counts.gaps}`} label="Content gaps"
            sub={data.counts.gaps ? "categories AI names rivals, not you" : "no gaps"}
            tone={data.counts.gaps ? "crit" : "good"} to="/opportunities" />
        </div>
      </div>

      {/* Plain-language site status */}
      {s && data.diagnosis && (
        <div className={`fade-in-2 mt-4 flex items-start gap-3 rounded-2xl border ${s.border} ${s.bg} p-4`}>
          <span className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border ${s.border} ${s.text} text-sm font-bold`}>{s.icon}</span>
          <div>
            <div className={`text-sm font-semibold ${s.text}`}>{data.diagnosis.headline}</div>
            <div className="mt-0.5 text-sm text-ink-soft">{s.note}</div>
          </div>
        </div>
      )}

      <div className="fade-in-3 mt-4 grid gap-4 lg:grid-cols-2">
        <Card title="Visibility over time"><TrendChart data={{ points: data.trend }} /></Card>
        <Card title="Top competitors">
          <Leaderboard data={data.share_of_voice} limit={6} />
          <Link to="/competitors" className="mt-3 inline-block text-xs text-accent hover:underline">See all competitors →</Link>
        </Card>
      </div>
    </div>
  );
}
