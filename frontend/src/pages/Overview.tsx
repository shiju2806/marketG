import { Link } from "react-router-dom";
import { api } from "../api";
import { useAsync } from "../state";
import { TrendChart } from "../components/TrendChart";
import { DiagnosisCard } from "../components/DiagnosisCard";
import { Leaderboard } from "../components/Leaderboard";
import { PageTitle, Card, Loading, ErrorMsg } from "./parts";

function Kpi({ value, label, tone = "ink", to }: { value: string; label: string; tone?: string; to?: string }) {
  const toneClass = { ink: "text-ink", good: "text-good", warn: "text-warn", crit: "text-crit", accent: "text-accent" }[tone] ?? "text-ink";
  const body = (
    <div className="rounded-2xl border border-line bg-surface px-5 py-4 transition hover:border-accent">
      <div className={`text-3xl font-semibold tabular-nums tracking-tight ${toneClass}`}>{value}</div>
      <div className="mt-1 text-xs text-ink-faint">{label}</div>
    </div>
  );
  return to ? <Link to={to}>{body}</Link> : body;
}

export function Overview() {
  const { data, loading, error } = useAsync(api.overview);
  if (loading) return <Loading />;
  if (error) return <ErrorMsg error={error} />;
  if (!data) return null;

  const sov = data.share_of_voice;
  const rate = data.your_share;
  const owned = data.earned_owned;

  return (
    <div>
      <PageTitle title="Overview" subtitle="How AI sees you when buyers research your market" />

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Kpi value={data.score?.overall != null ? `${data.score.overall}` : "—"} label="AI visibility"
          tone={(data.score?.overall ?? 0) >= 60 ? "good" : (data.score?.overall ?? 0) >= 40 ? "warn" : "crit"} />
        <Kpi value={rate != null ? `${rate}%` : "—"} label="Share of voice"
          tone={(rate ?? 0) >= 40 ? "good" : (rate ?? 0) >= 15 ? "warn" : "crit"} to="/competitors" />
        <Kpi value={data.rank ? `#${data.rank}` : "—"} label={`of ${data.brand_count} brands`} to="/competitors" />
        <Kpi value={owned == null ? "—" : `${Math.round(owned * 100)}%`} label="Owned sources"
          tone={owned === 0 ? "crit" : "good"} to="/sources" />
      </div>

      {data.diagnosis && (
        <div className="mt-5">
          <DiagnosisCard data={{ status: data.diagnosis.status, diagnosis: {
            status: data.diagnosis.status as never, headline: data.diagnosis.headline, detail: "",
            pages_attempted: 0, pages_read: 0, pages_blocked: 0, ai_allowed_in_robots: true, has_structured_data: false,
          } }} />
        </div>
      )}

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <Card title="Visibility over time">
          <TrendChart data={{ points: data.trend }} />
        </Card>
        <Card title="Top competitors"><Leaderboard data={sov} limit={6} /></Card>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Kpi value={`${data.counts.gaps}`} label="Content gaps" tone={data.counts.gaps ? "crit" : "good"} to="/opportunities" />
        <Kpi value={`${data.counts.winning}`} label="Categories won" tone="good" to="/opportunities" />
        <Kpi value={`${data.counts.recommendations}`} label="Recommendations" to="/opportunities" />
        <Kpi value={`${data.counts.conflicts}`} label="Contradictions" tone={data.counts.conflicts ? "warn" : "ink"} to="/twin" />
      </div>
    </div>
  );
}
