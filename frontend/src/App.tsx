import { useEffect, useState, type FormEvent } from "react";
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
import { Section } from "./components/Section";

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
    const [p, r] = await Promise.all([
      api.probeLatest(org).catch(() => null),
      api.recommendations(org).catch(() => []),
    ]);
    setProbe(p);
    setRecs(r);
    setScore(await api.score(org).catch(() => null));
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
  const youShare = sov.find((s) => s.is_you);
  const mentionRate = youShare ? Math.round(youShare.share * 100) : null;
  const leaders = sov.filter((s) => !s.is_you && s.mentions > (youShare?.mentions ?? 0)).slice(0, 4);

  // "Why": how many distinct questions named you.
  const questions = probe?.questions ?? [];
  const byQ = new Map<string, boolean>();
  for (const q of questions) byQ.set(q.question, (byQ.get(q.question) ?? false) || q.organization_mentioned);
  const totalQ = byQ.size;
  const namedIn = [...byQ.values()].filter(Boolean).length;

  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-3xl px-5 py-8">
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
              className="rounded-lg border border-line bg-surface px-2.5 py-1.5 text-sm" title="Toggle theme">
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
            className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition hover:opacity-90 disabled:opacity-40">
            {analyzing ? "Analyzing…" : "Analyze"}
          </button>
          {analyzing && (
            <div className="w-full text-xs text-accent">
              <span className="inline-block animate-pulse">●</span> {analyzing} — this takes a minute or two…
            </div>
          )}
        </form>

        {!org && !analyzing && (
          <p className="mt-10 text-center text-sm text-ink-faint">
            Enter a company and website to see how it shows up when buyers research its market.
          </p>
        )}

        {org && (
          <>
            <div className="mt-6 flex flex-wrap items-end justify-between gap-3">
              <div>
                <h1 className="text-2xl font-bold tracking-tight">{org.name}</h1>
                <p className="text-sm text-ink-faint">{org.website}</p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => act("rerun", () => api.runProbe(orgId))} disabled={busy !== null}
                  className="rounded-lg border border-line bg-surface px-3 py-1.5 text-sm text-ink-soft hover:border-accent disabled:opacity-40">
                  {busy === "rerun" ? "Working…" : "Re-run"}
                </button>
                <button onClick={() => act("recs", () => api.generateRecommendations(orgId))} disabled={busy !== null}
                  className="rounded-lg border border-line bg-surface px-3 py-1.5 text-sm text-ink-soft hover:border-accent disabled:opacity-40">
                  {busy === "recs" ? "Working…" : "Refresh tips"}
                </button>
              </div>
            </div>

            {/* Headline */}
            <div className="mt-5 rounded-2xl border border-line bg-surface p-6">
              {mentionRate === null ? (
                <p className="text-sm text-ink-faint">
                  Re-run to see how often assistants name {org.name} when buyers research this market.
                </p>
              ) : (
                <>
                  <p className="text-xl font-semibold leading-snug">
                    <span className="text-accent">{org.name}</span> shows up in{" "}
                    <span className="tabular-nums">{mentionRate}%</span> of buyer questions
                    {leaders.length > 0 && (
                      <> — <span className="text-warn">{leaders.map((l) => l.brand).join(", ")}</span> show up more often</>
                    )}.
                  </p>
                  <p className="mt-2 text-sm text-ink-soft">
                    Named in <b className="text-ink">{namedIn}</b> of {totalQ} buyer questions.
                    {probe?.run && probe.run.earned_owned !== null && (
                      <> {" "}Of the sources cited,{" "}
                        <span className={probe.run.earned_owned > 0 ? "text-good" : "text-crit"}>
                          {Math.round(probe.run.earned_owned * 100)}% are your own site
                        </span>
                        {probe.run.earned_owned === 0 && " — your visibility is entirely borrowed"}.
                      </>
                    )}
                  </p>
                </>
              )}
            </div>

            <Section title="Share of voice" subtitle="Which brands get named in the buyer questions">
              <ShareOfVoice data={sov} />
            </Section>

            <Section
              title="Question by question"
              subtitle="What ChatGPT and Perplexity actually answered"
              defaultOpen={false}
              right={<span className="font-mono text-xs text-ink-faint">{totalQ}</span>}
            >
              <QuestionList items={questions} you={you} />
            </Section>

            <Section title="How to improve" defaultOpen={false}
              right={<span className="font-mono text-xs text-ink-faint">{recs.length}</span>}>
              <RecommendationList items={recs} />
            </Section>

            {score && (
              <div className="mt-6 flex flex-wrap gap-x-5 gap-y-1 px-1 font-mono text-xs text-ink-faint">
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
      </div>
    </div>
  );
}

function Diag({ label, v }: { label: string; v: number | null }) {
  return <span>{label} <span className="text-ink-soft">{v ?? "—"}</span></span>;
}
