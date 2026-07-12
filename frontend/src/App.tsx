import { useEffect, useState, type FormEvent } from "react";
import {
  api,
  type CompetitiveSummary,
  type CrawlDiagnosis,
  type Organization,
  type ProbeReport,
  type Recommendation,
  type VisibilityScore,
} from "./api";
import { DiagnosisCard } from "./components/DiagnosisCard";
import { ShareOfVoice } from "./components/ShareOfVoice";
import { QuestionList } from "./components/QuestionList";
import { RecommendationList } from "./components/RecommendationList";
import { Section } from "./components/Section";
import { StatCard } from "./components/StatCard";

type Theme = "light" | "dark";

function initialTheme(): Theme {
  const saved = localStorage.getItem("theme");
  if (saved === "light" || saved === "dark") return saved;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export default function App() {
  const [theme, setTheme] = useState<Theme>(initialTheme);
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [orgId, setOrgId] = useState("");
  const [probe, setProbe] = useState<ProbeReport | null>(null);
  const [score, setScore] = useState<VisibilityScore | null>(null);
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [insight, setInsight] = useState<CompetitiveSummary | null>(null);
  const [diag, setDiag] = useState<CrawlDiagnosis | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ name: "", website: "" });
  const [analyzing, setAnalyzing] = useState<string | null>(null);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("theme", theme);
  }, [theme]);

  useEffect(() => {
    api.listOrganizations().then(setOrgs).catch((e) => setError(String(e)));
  }, []);

  useEffect(() => { if (orgId) refresh(orgId); }, [orgId]);

  async function refresh(org: string) {
    setError(null);
    setInsight(null);
    const [p, r, dg] = await Promise.all([
      api.probeLatest(org).catch(() => null),
      api.recommendations(org).catch(() => []),
      api.crawlDiagnosis(org).catch(() => null),
    ]);
    setProbe(p);
    setRecs(r);
    setDiag(dg);
    setScore(await api.score(org).catch(() => null));
    api.competitiveSummary(org).then(setInsight).catch(() => setInsight(null));
  }

  async function analyzeWebsite(e: FormEvent) {
    e.preventDefault();
    if (!form.name || !form.website) return;
    setError(null);
    try {
      const { job_id, organization_id } = await api.analyze(form);
      setAnalyzing("starting…");
      const poll = async (): Promise<void> => {
        const s = await api.analyzeStatus(job_id);
        setAnalyzing(s.stage ?? s.status);
        if (s.status === "done") {
          setAnalyzing(null);
          setForm({ name: "", website: "" });
          setOrgs(await api.listOrganizations());
          setOrgId(organization_id);
          return;
        }
        if (s.status === "failed") { setAnalyzing(null); setError(s.error ?? "analysis failed"); return; }
        setTimeout(poll, 2500);
      };
      setTimeout(poll, 2500);
    } catch (err) { setAnalyzing(null); setError(String(err)); }
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
  const youIdx = sov.findIndex((s) => s.is_you);
  const youShare = youIdx >= 0 ? sov[youIdx] : undefined;
  const mentionRate = youShare ? Math.round(youShare.share * 100) : null;
  const rank = youIdx >= 0 ? youIdx + 1 : null;
  const owned = probe?.run?.earned_owned ?? null;

  const questions = probe?.questions ?? [];
  const byQ = new Map<string, boolean>();
  for (const q of questions) byQ.set(q.question, (byQ.get(q.question) ?? false) || q.organization_mentioned);
  const totalQ = byQ.size;
  const namedIn = [...byQ.values()].filter(Boolean).length;

  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-4xl px-5 py-8">
        {/* Nav */}
        <header className="flex items-center justify-between">
          <span className="text-lg font-bold tracking-tight">
            market<span className="text-accent">G</span>
          </span>
          <div className="flex items-center gap-2">
            {orgs.length > 0 && (
              <select value={orgId} onChange={(e) => setOrgId(e.target.value)}
                className="rounded-lg border border-line bg-surface px-2.5 py-1.5 text-sm text-ink-soft">
                <option value="">Past reports…</option>
                {orgs.map((o) => <option key={o.organization_id} value={o.organization_id}>{o.name}</option>)}
              </select>
            )}
            <button onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="h-8 w-8 rounded-lg border border-line bg-surface text-sm" title="Toggle theme">
              {theme === "dark" ? "☀" : "☾"}
            </button>
          </div>
        </header>

        {error && (
          <div className="mt-4 rounded-lg border border-crit bg-crit-soft px-4 py-2 text-sm text-crit">{error}</div>
        )}

        {/* Onboarding */}
        <form onSubmit={analyzeWebsite}
          className="mt-6 flex flex-wrap items-end gap-3 rounded-2xl border border-line bg-surface p-4">
          <div className="flex min-w-[120px] flex-1 flex-col gap-1">
            <label className="text-xs text-ink-faint">Company</label>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Rivian" disabled={analyzing !== null}
              className="rounded-lg border border-line bg-bg px-3 py-2 text-sm outline-none focus:border-accent" />
          </div>
          <div className="flex min-w-[160px] flex-[2] flex-col gap-1">
            <label className="text-xs text-ink-faint">Website</label>
            <input value={form.website} onChange={(e) => setForm({ ...form, website: e.target.value })}
              placeholder="rivian.com" disabled={analyzing !== null}
              className="rounded-lg border border-line bg-bg px-3 py-2 text-sm outline-none focus:border-accent" />
          </div>
          <button type="submit" disabled={analyzing !== null || !form.name || !form.website}
            className="rounded-lg bg-accent px-5 py-2 text-sm font-medium text-white transition hover:opacity-90 disabled:opacity-40">
            {analyzing ? "Analyzing…" : "Analyze"}
          </button>
          {analyzing && (
            <div className="w-full text-xs text-accent">
              <span className="inline-block animate-pulse">●</span> {analyzing} — this takes a minute or two…
            </div>
          )}
        </form>

        {!org && !analyzing && (
          <p className="mt-12 text-center text-sm text-ink-faint">
            Enter a company and website to see how it shows up when buyers research its market.
          </p>
        )}

        {org && (
          <>
            {/* Report header */}
            <div className="mt-8 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h1 className="text-2xl font-bold capitalize tracking-tight">{org.name}</h1>
                <a href={org.website ?? undefined} target="_blank" rel="noreferrer"
                  className="text-sm text-ink-faint hover:text-accent">{org.website}</a>
              </div>
              <button onClick={() => act("rerun", () => api.runProbe(orgId))} disabled={busy !== null}
                className="rounded-lg border border-line bg-surface px-3 py-1.5 text-sm text-ink-soft hover:border-accent disabled:opacity-40">
                {busy === "rerun" ? "Working…" : "↻ Re-run"}
              </button>
            </div>

            {/* Opening finding: what happened when AI tried to read the site */}
            {diag?.diagnosis && (
              <div className="mt-5">
                <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-ink-faint">
                  When AI visited your site
                </h3>
                <DiagnosisCard data={diag} />
              </div>
            )}

            {mentionRate !== null && (
              <>
                {/* Headline */}
                <p className="mt-5 text-xl font-semibold leading-snug">
                  When buyers research this market, AI names <span className="capitalize text-accent">{org.name}</span>{" "}
                  in <span className="tabular-nums">{mentionRate}%</span> of questions
                  {rank && rank > 3 && <> — it ranks <span className="tabular-nums">#{rank}</span> of {sov.length} brands</>}.
                </p>

                {/* KPI row */}
                <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <StatCard value={`${mentionRate}%`} label="Share of voice"
                    tone={mentionRate >= 40 ? "good" : mentionRate >= 15 ? "warn" : "crit"} />
                  <StatCard value={rank ? `#${rank}` : "—"} label={`of ${sov.length} brands`} />
                  <StatCard value={`${namedIn}/${totalQ}`} label="Categories won"
                    tone={namedIn === 0 ? "crit" : "ink"} />
                  <StatCard value={owned === null ? "—" : `${Math.round(owned * 100)}%`} label="Owned sources"
                    tone={owned === 0 ? "crit" : "good"} />
                </div>

                {/* Why competitors win — prominent */}
                <div className="mt-6 rounded-2xl border border-accent bg-accent-soft p-5">
                  <h2 className="text-sm font-semibold text-accent">Why competitors win</h2>
                  <p className="mt-2 text-sm leading-relaxed text-ink">
                    {insight?.summary ?? "Analyzing what leading brands do better…"}
                  </p>
                  {insight && insight.actions.length > 0 && (
                    <div className="mt-4">
                      <h3 className="text-xs font-medium uppercase tracking-wide text-ink-faint">Do this</h3>
                      <ol className="mt-2 flex flex-col gap-1.5">
                        {insight.actions.map((a, i) => (
                          <li key={i} className="flex gap-2 text-sm text-ink">
                            <span className="font-mono text-accent">{i + 1}.</span>
                            <span>{a.replace(/^\d+\.\s*/, "")}</span>
                          </li>
                        ))}
                      </ol>
                    </div>
                  )}
                </div>

                {/* Standings */}
                <Section title="Competitive standings" subtitle="Which brands AI names when buyers research this market">
                  <ShareOfVoice data={sov} />
                </Section>

                {/* Fix per category */}
                <Section title="Where you're losing" subtitle="Categories where AI names rivals but not you" defaultOpen
                  right={<span className="font-mono text-xs text-ink-faint">{recs.filter(r => r.missing_type === "citation").length}</span>}>
                  <RecommendationList items={recs} />
                </Section>

                {/* Detail */}
                <Section title="What AI actually said" subtitle="Every buyer question, both assistants"
                  defaultOpen={false} right={<span className="font-mono text-xs text-ink-faint">{totalQ}</span>}>
                  <QuestionList items={questions} you={you} />
                </Section>

                {score && (
                  <div className="mt-6 flex flex-wrap gap-x-5 gap-y-1 px-1 font-mono text-[11px] text-ink-faint">
                    <span>Diagnostics:</span>
                    <Diag label="visibility" v={score.citation} />
                    <Diag label="retrieval" v={score.retrieval} />
                    <Diag label="reasoning" v={score.reasoning} />
                    <Diag label="trust" v={score.trust} />
                    <Diag label="readability" v={score.machine_readability} />
                  </div>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function Diag({ label, v }: { label: string; v: number | null }) {
  return <span>{label} <span className="text-ink-soft">{v ?? "—"}</span></span>;
}
