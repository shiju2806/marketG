import { useEffect, useState, type FormEvent } from "react";
import {
  api,
  type CompetitiveSummary,
  type CrawlDiagnosis,
  type CitedSources as CitedSourcesT,
  type Delta,
  type Organization,
  type ProbeReport,
  type Recommendation,
  type VisibilityScore,
} from "./api";
import { DiagnosisCard } from "./components/DiagnosisCard";
import { CitedSources } from "./components/CitedSources";
import { GapMatrix } from "./components/GapMatrix";
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

function Dashboard() {
  const [theme, setTheme] = useState<Theme>(initialTheme);
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [orgId, setOrgId] = useState("");
  const [probe, setProbe] = useState<ProbeReport | null>(null);
  const [score, setScore] = useState<VisibilityScore | null>(null);
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [insight, setInsight] = useState<CompetitiveSummary | null>(null);
  const [diag, setDiag] = useState<CrawlDiagnosis | null>(null);
  const [cited, setCited] = useState<CitedSourcesT | null>(null);
  const [delta, setDelta] = useState<Delta | null>(null);
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
    const [p, r, dg, cs, dl] = await Promise.all([
      api.probeLatest(org).catch(() => null),
      api.recommendations(org).catch(() => []),
      api.crawlDiagnosis(org).catch(() => null),
      api.citedSources(org).catch(() => null),
      api.delta(org).catch(() => null),
    ]);
    setProbe(p);
    setRecs(r);
    setDiag(dg);
    setCited(cs);
    setDelta(dl);
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

                {/* The gap: what you have vs what AI says */}
                {delta && (
                  <Section title="Content gap" subtitle="Your content vs. what buyers ask AI">
                    <GapMatrix data={delta} />
                  </Section>
                )}

                {/* Standings */}
                <Section title="Competitive standings" subtitle="Which brands AI names when buyers research this market">
                  <ShareOfVoice data={sov} />
                </Section>

                {/* Who AI trusts */}
                {cited && cited.total_citations > 0 && (
                  <Section title="Who AI cites" subtitle="The sources assistants trust for your market"
                    defaultOpen={false}
                    right={<span className="font-mono text-xs text-ink-faint">{cited.total_citations}</span>}>
                    <CitedSources data={cited} />
                  </Section>
                )}

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

function RestaurantLanding() {
  const scrollToAudit = () => document.getElementById("audit")?.scrollIntoView({ behavior: "smooth" });

  return (
    <main className="restaurant-site">
      <div className="top-ticker">
        <span>22% of diners use AI to choose a restaurant</span>
        <span className="ticker-star">✦</span>
        <span>Don&apos;t let your locations get left off the list</span>
      </div>

      <nav className="restaurant-nav" aria-label="Main navigation">
        <a className="restaurant-logo" href="#top" aria-label="marketG home">
          <span className="logo-mark">mG</span>
          <span>market<span>G</span></span>
        </a>
        <div className="nav-links">
          <a href="#how-it-works">How it works</a>
          <a href="#teams">For your team</a>
        </div>
        <button className="nav-cta" onClick={scrollToAudit}>Get an audit <span>↗</span></button>
      </nav>

      <section className="hero" id="top">
        <div className="hero-copy">
          <div className="eyebrow"><span className="dot" /> AI DISCOVERY FOR RESTAURANT CHAINS</div>
          <h1>Be the restaurant<br /><em>AI recommends.</em></h1>
          <p className="hero-lede">marketG shows restaurant groups exactly how AI sees every location—and how to become the answer when diners ask where to eat.</p>
          <div className="hero-actions">
            <button className="btn-primary" onClick={scrollToAudit}>Get your AI visibility audit <span>→</span></button>
            <a className="text-link" href="#how-it-works">See how it works <span>↓</span></a>
          </div>
          <p className="audience-line"><span>FOR</span> MULTI-LOCATION · QSR · FAST-CASUAL · DELIVERY-FIRST BRANDS</p>
        </div>

        <div className="hero-visual" aria-label="Example AI restaurant recommendation">
          <div className="burst burst-one">TASTY<br />DATA</div>
          <div className="hero-squiggle">⌇</div>
          <div className="chat-window">
            <div className="chat-top"><span className="chat-dots"><i /><i /><i /></span><b>AI SEARCH</b><span>LIVE</span></div>
            <div className="chat-body">
              <div className="user-query">Best family-friendly pizza<br />near me tonight?</div>
              <div className="ai-label"><span>✦</span> ANSWER</div>
              <p className="ai-answer">For a relaxed family dinner, try <strong>Pizza Palace</strong>—they have a kids&apos; menu, vegetarian options, and delivery.</p>
              <div className="recommendation">
                <div className="pizza-icon">🍕</div>
                <div><strong>Pizza Palace</strong><small>0.4 km away · Open until 11 pm</small></div>
                <b className="score-pill">98</b>
              </div>
              <div className="competitor-row"><span>Other places mentioned</span><b>3 competitors</b></div>
            </div>
          </div>
          <div className="missing-card"><span className="missing-x">×</span><b>Your location</b><small>Not mentioned</small></div>
          <div className="arrow-note">This is where<br />marketG comes in <span>↘</span></div>
        </div>
      </section>

      <section className="logo-strip" aria-label="Ideal restaurant operators">
        <p>BUILT FOR THE TEAMS BEHIND GREAT RESTAURANTS</p>
        <div><span>BRAND</span><span>LOCAL</span><span>DIGITAL</span><span>OPS</span><span>GROWTH</span></div>
      </section>

      <section className="problem-section">
        <div className="section-kicker"><span>01</span> THE PROBLEM</div>
        <div className="problem-heading"><h2>Diners ask AI.<br />AI makes a <i>shortlist.</i></h2><p>You may already be losing the decision before a guest sees your website, opens a delivery app, or walks through the door.</p></div>
        <div className="prompt-grid">
          <article className="prompt-card yellow"><span className="prompt-num">01</span><p>“What&apos;s a good late-night spot near me?”</p><span className="prompt-tag">OCCASION</span></article>
          <article className="prompt-card red"><span className="prompt-num">02</span><p>“Where can I get gluten-free takeout?”</p><span className="prompt-tag">DIETARY</span></article>
          <article className="prompt-card green"><span className="prompt-num">03</span><p>“What&apos;s good for a team lunch?”</p><span className="prompt-tag">GROUP ORDER</span></article>
        </div>
      </section>

      <section className="split-insight" id="how-it-works">
        <div className="insight-copy">
          <div className="section-kicker light"><span>02</span> THE FIX</div>
          <h2>Turn your scattered restaurant data into an <i>AI-ready</i> advantage.</h2>
          <p>marketG maps the facts that matter for discovery: menus, dietary details, location data, ordering, reviews, services, and the sources that support them.</p>
          <button className="btn-lime" onClick={scrollToAudit}>See your visibility <span>→</span></button>
        </div>
        <div className="insight-board">
          <div className="board-title"><span>YOUR AI VISIBILITY</span><b>LIVE REPORT</b></div>
          <div className="score-display"><span>73</span><small>/100</small><b>+12 THIS MONTH ↗</b></div>
          <div className="metric-line"><span>AI recommendations</span><b>64%</b><i><em style={{ width: "64%" }} /></i></div>
          <div className="metric-line"><span>Menu clarity</span><b>87%</b><i><em style={{ width: "87%" }} /></i></div>
          <div className="metric-line"><span>Location accuracy</span><b>51%</b><i><em style={{ width: "51%" }} /></i></div>
          <div className="board-callout"><span>!</span><p><b>18 locations</b> have missing dietary details.</p><strong>FIX THIS →</strong></div>
        </div>
      </section>

      <section className="steps-section">
        <div className="section-kicker"><span>03</span> HOW IT WORKS</div>
        <h2>One clear path from<br /><i>invisible</i> to recommended.</h2>
        <div className="steps-grid">
          <article><span className="step-number">01</span><div className="step-icon pin">⌖</div><h3>Scan your footprint</h3><p>We connect your locations, menus, website, ordering, and public sources.</p></article>
          <article><span className="step-number">02</span><div className="step-icon chat">✦</div><h3>Ask what diners ask</h3><p>We test real discovery questions across the AI tools your guests use.</p></article>
          <article><span className="step-number">03</span><div className="step-icon spark">↗</div><h3>Know what to fix</h3><p>Get prioritized, location-level actions that improve your visibility.</p></article>
        </div>
      </section>

      <section className="teams-section" id="teams">
        <div className="teams-visual"><div className="plate"><div>market<span>G</span></div></div><span className="fork">⌁</span><span className="pepper">✦</span></div>
        <div className="teams-copy"><div className="section-kicker"><span>04</span> MADE FOR YOUR TEAM</div><h2>One source of truth for every team that shapes <i>discovery.</i></h2>
          <div className="team-list"><p><b>BRAND &amp; MARKETING</b><span>Win the category moments that matter.</span></p><p><b>LOCAL MARKETING</b><span>See which locations are missing—and why.</span></p><p><b>DIGITAL &amp; OPS</b><span>Keep menus, details, and ordering AI-ready.</span></p><p><b>LEADERSHIP</b><span>See where competitors own the answer.</span></p></div>
        </div>
      </section>

      <section className="audit-section" id="audit">
        <div className="audit-star">✦</div>
        <p className="eyebrow"><span className="dot" /> READY WHEN YOU ARE</p>
        <h2>Is AI serving up<br /><i>your</i> restaurant?</h2>
        <p>Find out what AI knows about your brand, your locations, and your competitors.</p>
        <form className="audit-form" onSubmit={(event) => event.preventDefault()}>
          <input type="email" aria-label="Work email" placeholder="Work email" />
          <button type="submit">Get an AI visibility audit <span>→</span></button>
        </form>
        <small>No spam. Just a clear view of your AI discovery.</small>
      </section>

      <footer className="restaurant-footer"><a className="restaurant-logo" href="#top"><span className="logo-mark">mG</span><span>market<span>G</span></span></a><p>AI visibility for restaurant chains.</p><span>© 2026 marketG</span></footer>
    </main>
  );
}

export default function App() {
  return window.location.pathname === "/dashboard" ? <Dashboard /> : <RestaurantLanding />;
}
