import { useEffect, useState } from "react";
import {
  api,
  type Organization,
  type Recommendation,
  type TwinSummary,
  type VisibilityScore,
} from "./api";
import { ScoreBar } from "./components/ScoreBar";
import { RecommendationList } from "./components/RecommendationList";

export default function App() {
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [orgId, setOrgId] = useState<string>("");
  const [twin, setTwin] = useState<TwinSummary | null>(null);
  const [score, setScore] = useState<VisibilityScore | null>(null);
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listOrganizations().then((o) => {
      setOrgs(o);
      if (o[0]) setOrgId(o[0].organization_id);
    }).catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (!orgId) return;
    refresh(orgId);
  }, [orgId]);

  async function refresh(org: string) {
    setError(null);
    try {
      const [t, rc] = await Promise.all([
        api.twin(org).catch(() => null),
        api.recommendations(org).catch(() => []),
      ]);
      setTwin(t);
      setRecs(rc);
      setScore(await api.score(org).catch(() => null));
    } catch (e) {
      setError(String(e));
    }
  }

  async function act(label: string, fn: () => Promise<unknown>) {
    setBusy(label);
    setError(null);
    try {
      await fn();
      await refresh(orgId);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(null);
    }
  }

  const org = orgs.find((o) => o.organization_id === orgId);

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <header className="flex items-center justify-between border-b border-line pb-5">
        <div className="flex items-center gap-2">
          <span className="text-lg font-bold">
            market<span className="text-accent">G</span>
          </span>
          <span className="font-mono text-[11px] uppercase tracking-widest text-ink-faint">
            AI Visibility
          </span>
        </div>
        {orgs.length > 0 && (
          <select
            value={orgId}
            onChange={(e) => setOrgId(e.target.value)}
            className="rounded-lg border border-line bg-surface px-3 py-1.5 text-sm"
          >
            {orgs.map((o) => (
              <option key={o.organization_id} value={o.organization_id}>
                {o.name}
              </option>
            ))}
          </select>
        )}
      </header>

      {error && (
        <div className="mt-4 rounded-lg border border-crit/40 bg-crit/10 px-4 py-2 text-sm text-crit">
          {error}
        </div>
      )}

      {org && (
        <section className="mt-8">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">{org.name}</h1>
              <p className="text-sm text-ink-faint">{org.website}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <ActionButton busy={busy} label="Run visibility" onClick={() =>
                act("Run visibility", () => api.runVisibility(orgId))} />
              <ActionButton busy={busy} label="Generate recommendations" onClick={() =>
                act("Generate recommendations", () => api.generateRecommendations(orgId))} />
            </div>
          </div>

          <div className="mt-8 grid gap-6 md:grid-cols-2">
            <div className="rounded-2xl border border-line bg-surface p-6">
              <div className="flex items-baseline justify-between">
                <h2 className="font-mono text-xs uppercase tracking-widest text-ink-soft">
                  AI Visibility Score
                </h2>
                <span className="text-4xl font-bold tabular-nums">
                  {score?.overall ?? "—"}
                </span>
              </div>
              <div className="mt-5 flex flex-col gap-4">
                <ScoreBar label="Retrieval" score={score?.retrieval ?? null} />
                <ScoreBar label="Citation" score={score?.citation ?? null}
                  hint="external AI probe (unbranded questions)" />
                <ScoreBar label="Reasoning" score={score?.reasoning ?? null} />
                <ScoreBar label="Trust" score={score?.trust ?? null} />
                <ScoreBar label="Machine-readability" score={score?.machine_readability ?? null}
                  hint="crawlable + AI-open + structured" />
              </div>
            </div>

            <div className="rounded-2xl border border-line bg-surface p-6">
              <h2 className="font-mono text-xs uppercase tracking-widest text-ink-soft">
                Semantic Business Twin
              </h2>
              {twin ? (
                <>
                  <div className="mt-5 grid grid-cols-3 gap-4 text-center">
                    <Stat label="entities" value={twin.entities} />
                    <Stat label="relationships" value={twin.relationships} />
                    <Stat label="claims" value={twin.claims} />
                    <Stat label="evidence" value={twin.evidence} />
                    <Stat label="conflicts" value={twin.conflicts} />
                  </div>
                  <div className="mt-5 flex flex-wrap gap-1.5">
                    {twin.entities_by_type.map((e) => (
                      <span key={e.entity_type}
                        className="rounded bg-surface-2 px-2 py-0.5 font-mono text-[11px] text-ink-soft">
                        {e.entity_type} · {e.n}
                      </span>
                    ))}
                  </div>
                </>
              ) : (
                <p className="mt-4 text-sm text-ink-faint">No twin yet — crawl the site first.</p>
              )}
            </div>
          </div>

          <div className="mt-8">
            <h2 className="mb-4 font-mono text-xs uppercase tracking-widest text-ink-soft">
              Recommendations
            </h2>
            <RecommendationList items={recs} />
          </div>
        </section>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="text-2xl font-bold tabular-nums">{value}</div>
      <div className="font-mono text-[10px] uppercase tracking-wide text-ink-faint">{label}</div>
    </div>
  );
}

function ActionButton({
  label,
  busy,
  onClick,
}: {
  label: string;
  busy: string | null;
  onClick: () => void;
}) {
  const isBusy = busy === label;
  return (
    <button
      onClick={onClick}
      disabled={busy !== null}
      className="rounded-lg border border-accent/50 bg-accent/10 px-3 py-1.5 text-sm text-accent transition hover:bg-accent/20 disabled:opacity-40"
    >
      {isBusy ? "Working…" : label}
    </button>
  );
}
