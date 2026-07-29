import { api } from "../api";
import { useAsync } from "../state";
import { DonutChart } from "../components/DonutChart";
import { Leaderboard } from "../components/Leaderboard";
import { PageTitle, Card, Loading, ErrorMsg } from "./parts";

export function Competitors() {
  const probe = useAsync(api.probeLatest);
  const insight = useAsync(api.competitiveSummary);

  if (probe.loading) return <Loading />;
  if (probe.error) return <ErrorMsg error={probe.error} />;
  const sov = probe.data?.share_of_voice ?? [];

  return (
    <div>
      <PageTitle title="Competitors" subtitle="Which brands AI names when buyers research this market" />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Share of voice"><DonutChart data={sov} /></Card>
        <Card title="Leaderboard"><Leaderboard data={sov} limit={10} /></Card>
      </div>

      <Card title="Why competitors win" className="mt-4">
        <p className="text-sm leading-relaxed text-ink">
          {insight.data?.summary ?? "Analyzing what leading brands do better…"}
        </p>
        {insight.data && insight.data.actions.length > 0 && (
          <ol className="mt-4 flex flex-col gap-1.5">
            {insight.data.actions.map((a, i) => (
              <li key={i} className="flex gap-2 text-sm text-ink">
                <span className="font-mono text-accent">{i + 1}.</span>
                <span>{a.replace(/^\d+\.\s*/, "")}</span>
              </li>
            ))}
          </ol>
        )}
      </Card>
    </div>
  );
}
