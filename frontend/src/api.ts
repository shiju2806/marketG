// Thin API client for the marketG backend.
// Auth is a placeholder (X-Account-Id header) matching the backend's Sprint-1
// dependency; swaps to a Supabase JWT when auth is wired.

const BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";
const ACCOUNT = import.meta.env.VITE_ACCOUNT_ID ?? "00000000-0000-0000-0000-000000000001";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}/api/v1${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Account-Id": ACCOUNT,
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json() as Promise<T>;
}

export interface Organization {
  organization_id: string;
  name: string;
  website: string | null;
  vertical_pack_id: string;
}

export interface VisibilityScore {
  run_id: string;
  retrieval: number | null;
  reasoning: number | null;
  trust: number | null;
  machine_readability: number | null;
  citation: number | null;
  overall: number | null;
  question_count: number;
}

export interface CrawlDiagnosis {
  status: string | null;
  diagnosis: {
    status: "readable" | "blocked" | "thin" | "unreachable";
    headline: string;
    detail: string;
    pages_attempted: number;
    pages_read: number;
    pages_blocked: number;
    ai_allowed_in_robots: boolean;
    has_structured_data: boolean;
  } | null;
}

export interface TrendPoint {
  date: string;
  citation: number | null;
  your_share: number | null;
  targets: string[];
}

export interface VisibilityTrend {
  points: TrendPoint[];
}

export interface CitedSource {
  domain: string;
  count: number;
  share: number;
  is_first_party: boolean;
  category: "own" | "competitor" | "social" | "editorial";
}

export interface CitedSources {
  your_domain: string | null;
  your_domain_cited: boolean;
  total_citations: number;
  sources: CitedSource[];
  by_category: Partial<Record<"own" | "competitor" | "social" | "editorial", number>>;
}

export interface Overview {
  organization: { name: string; website: string | null };
  score: VisibilityScore | null;
  share_of_voice: ShareOfVoice[];
  your_share: number | null;
  rank: number | null;
  brand_count: number;
  earned_owned: number | null;
  trend: TrendPoint[];
  diagnosis: { status: string; headline: string } | null;
  counts: {
    gaps: number; hidden: number; missing: number; winning: number;
    recommendations: number; conflicts: number;
  };
}

export interface UsageReport {
  total_cost_usd: number;
  total_tokens: number;
  budget_usd: number | null;
  runs: {
    organization: string | null;
    cost_usd: number; tokens: number; pages: number; pages_skipped: number; at: string;
  }[];
}

export interface DeltaCategory {
  question: string;
  ai_mentions: boolean;
  competitors: string[];
  have_content: boolean | null;
  evidence: { heading?: string; url?: string; cos: number } | null;
  quadrant: "winning" | "hidden" | "missing" | "borrowed" | "unknown";
}

export interface Delta {
  crawl_status: string | null;
  twin_readable: boolean;
  categories: DeltaCategory[];
}

export interface CompetitiveSummary {
  summary: string | null;
  actions: string[];
  leaders: string[];
}

export interface Artifact {
  title: string;
  gap_type: string;
  body_markdown: string;
  body_html: string;
  schema_jsonld: Record<string, unknown>;
  notes: string;
}

export interface Recommendation {
  recommendation_id: string;
  title: string;
  missing_type: string;
  missing_detail: string;
  affects: string[];
  expected_impact: "high" | "medium" | "low";
}

export interface ShareOfVoice {
  brand: string;
  mentions: number;
  share: number;
  is_you: boolean;
}

export interface ProbeQuestion {
  question: string;
  model: string;
  organization_mentioned: boolean;
  competitor_mentions: string[];
  answer: string;
}

export interface ProbeReport {
  run: {
    probe_run_id: string;
    citation: number | null;
    earned_owned: number | null;
    targets: string[];
    created_at: string;
  } | null;
  share_of_voice: ShareOfVoice[];
  questions: ProbeQuestion[];
}

export const api = {
  listOrganizations: () => req<Organization[]>("/organizations"),
  analyze: (body: { name: string; website: string }) =>
    req<{ job_id: string; organization_id: string }>("/analyze", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  analyzeStatus: (jobId: string) =>
    req<{ status: string; stage: string | null; organization_id: string; error: string | null }>(
      `/analyze/${jobId}`
    ),
  createOrganization: (body: { name: string; website: string }) =>
    req<Organization>("/organizations", { method: "POST", body: JSON.stringify(body) }),
  score: (org: string) => req<VisibilityScore>(`/visibility-score?organization_id=${org}`),
  runVisibility: (org: string) =>
    req<{ run_id: string }>(`/visibility/run?organization_id=${org}`, { method: "POST" }),
  crawlDiagnosis: (org: string) => req<CrawlDiagnosis>(`/crawl-diagnosis?organization_id=${org}`),
  citedSources: (org: string) => req<CitedSources>(`/cited-sources?organization_id=${org}`),
  delta: (org: string) => req<Delta>(`/delta?organization_id=${org}`),
  probeLatest: (org: string) => req<ProbeReport>(`/probe/latest?organization_id=${org}`),
  trend: (org: string) => req<VisibilityTrend>(`/visibility-trend?organization_id=${org}`),
  conflicts: (org: string) =>
    req<{ conflict_id: string; description: string }[]>(`/conflicts?organization_id=${org}`),
  reason: (org: string, question: string) =>
    req<{ question: string; answer: string | null; supported: boolean; facts_used: string[] }>(
      `/reason?organization_id=${org}`, { method: "POST", body: JSON.stringify({ question }) }
    ),
  runProbe: (org: string) =>
    req<{ citation: number }>(`/probe?organization_id=${org}`, { method: "POST" }),
  competitiveSummary: (org: string) =>
    req<CompetitiveSummary>(`/competitive-summary?organization_id=${org}`),
  recommendations: (org: string) => req<Recommendation[]>(`/recommendations?organization_id=${org}`),
  remediate: (recommendationId: string) =>
    req<{ remediation_id: string; artifact: Artifact }>(
      `/remediate?recommendation_id=${recommendationId}`, { method: "POST" }
    ),
  generateRecommendations: (org: string) =>
    req<{ count: number }>(`/recommendations/generate?organization_id=${org}`, { method: "POST" }),
  companySuggest: (query: string) =>
    req<{ name: string; domain: string }[]>(`/company-suggest?query=${encodeURIComponent(query)}`),
  overview: (org: string) => req<Overview>(`/overview?organization_id=${org}`),
  usage: (org?: string) => req<UsageReport>(`/usage${org ? `?organization_id=${org}` : ""}`),
};
