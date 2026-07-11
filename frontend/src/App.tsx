import { useEffect, useState } from "react";
import {
  api,
  type Organization,
  type ProbeReport,
  type Recommendation,
  type VisibilityScore,
} from "./api";
import { ShareOfVoice } from "./components/ShareOfVoice";
import { QuestionList } from "./components/QuestionList";
import { RecommendationList } from "./components/RecommendationList";

export default function App() {
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [orgId, setOrgId] = useState<string>("");
  const [probe, setProbe] = useState<ProbeReport | null>(null);
  const [score, setScore] = useState<VisibilityScore | null>(null);
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listOrganizations()
      .then((o) => { setOrgs(o); if (o[0]) setOrgId(o[0].organization_id); })
      .catch((e) => setError(String(e)));
  }, []);

  useEffect(() => { if (orgId) refresh(orgId); }, [orgId]);

  async function refresh(org: string) {
    setError(null);
    const [p, r] = await Promise.all([
      api.probeLatest(org).catch(() => null),
      api.recommendations(org).catch(() => []),
    ]);
    setProbe(p);
    setRecs(r);
    setScore(await api.score(org).catch(() => null));
  }

  async function act(label: string, fn: () => Promise<unknown>) {
    setBusy(label); setError(null);
    try { await fn(); await refresh(orgId); }
    catch (e) { setError(String(e)); }
    finally { setBusy(null); }
  }

  const org = orgs.find((o) => o.organization_id === orgId);
  const you = org?.name ?? "you";
  const sov = probe?.share_of_voice ?? [];
  const youShare = sov.find((s) => s.is_you);
  const mentionRate = youShare ? Math.round(youShare.share * 100) : null;
  const ahead = sov.filter((s) => !s.is_you && s.mentions > (youShare?.mentions ?? 0));

  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      <header className="flex items-center justify-between border-b border-line pb-5">
        <div className="flex items-center gap-2">
          <span className="text-lg font-bold">market<span className="text-accent">G</span></span>
          <span className="font-mono text-[11px] uppercase tracking-widest text-ink-faint">
            AI Visibility
          </span>
        </div>
        {orgs.length > 0 && (
          <select value={orgId} onChange={(e) => setOrgId(e.target.value)}
            className="rounded-lg border border-line bg-surface px-3 py-1.5 text-sm">
            {orgs.map((o) => <option key={o.organization_id} value={o.organization_id}>{o.name}</option>)}
          </select>
        )}
      </header>

      {error && (
        <div className="mt-4 rounded-lg border border-crit/40 bg-crit/10 px-4 py-2 text-sm text-crit">{error}</div>
      )}

      {org && (
        <>
          <section className="mt-8 flex flex-wrap items-end justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">{org.name}</h1>
              <p className="text-sm text-ink-faint">{org.website}</p>
            </div>
            <div className="flex gap-2">
              <ActionButton busy={busy} label="Run AI analysis" onClick={() =>
                act("Run AI analysis", () => api.runProbe(orgId))} />
              <ActionButton busy={busy} label="Recommendations" onClick={() =>
                act("Recommendations", () => api.generateRecommendations(orgId))} />
            </div>
          </section>

          {/* HERO: what AI actually says */}
          <section className="mt-8 rounded-2xl border border-line bg-surface p-6">
            <h2 className="font-mono text-xs uppercase tracking-widest text-ink-soft">
              When buyers ask AI about your market
            </h2>
            {mentionRate === null ? (
              <p className="mt-4 text-sm text-ink-faint">
                Run the analysis — we ask real AI assistants your category's buyer questions and
                show whether they name you, and who they name instead.
              </p>
            ) : (
              <>
                <p className="mt-3 text-2xl font-semibold leading-snug">
                  AI names <span className="text-accent">{org.name}</span> in{" "}
                  <span className="tabular-nums">{mentionRate}%</span> of category questions
                  {ahead.length > 0 && (
                    <> — but names{" "}
                      <span className="text-warn">{ahead.map((a) => a.brand).join(", ")}</span> more often
                    </>
                  )}.
                </p>
                <div className="mt-6">
                  <h3 className="mb-3 font-mono text-[11px] uppercase tracking-widest text-ink-faint">
                    Share of voice in AI answers
                  </h3>
                  <ShareOfVoice data={sov} />
                </div>
              </>
            )}
          </section>

          {/* Per-question AI answers */}
          {probe && probe.questions.length > 0 && (
            <section className="mt-8">
              <h2 className="mb-4 font-mono text-xs uppercase tracking-widest text-ink-soft">
                What AI said, question by question
              </h2>
              <QuestionList items={probe.questions} you={you} />
            </section>
          )}

          {/* Recommendations */}
          <section className="mt-8">
            <h2 className="mb-4 font-mono text-xs uppercase tracking-widest text-ink-soft">
              How to improve
            </h2>
            <RecommendationList items={recs} />
          </section>

          {/* Diagnostics (secondary) */}
          {score && (
            <section className="mt-10 border-t border-line pt-5">
              <h2 className="mb-3 font-mono text-[11px] uppercase tracking-widest text-ink-faint">
                Diagnostics — why (internal engine)
              </h2>
              <div className="flex flex-wrap gap-x-6 gap-y-1 font-mono text-xs text-ink-soft">
                <Diag label="Citation" v={score.citation} />
                <Diag label="Retrieval" v={score.retrieval} />
                <Diag label="Reasoning" v={score.reasoning} />
                <Diag label="Trust" v={score.trust} />
                <Diag label="Machine-readability" v={score.machine_readability} />
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}

function Diag({ label, v }: { label: string; v: number | null }) {
  return (
    <span>
      {label} <span className="text-ink">{v ?? "—"}</span>
    </span>
  );
}

function ActionButton({ label, busy, onClick }: { label: string; busy: string | null; onClick: () => void }) {
  const isBusy = busy === label;
  return (
    <button onClick={onClick} disabled={busy !== null}
      className="rounded-lg border border-accent/50 bg-accent/10 px-3 py-1.5 text-sm text-accent transition hover:bg-accent/20 disabled:opacity-40">
      {isBusy ? "Working…" : label}
    </button>
  );
}
