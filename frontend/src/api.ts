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

export interface CompetitiveSummary {
  summary: string | null;
  actions: string[];
  leaders: string[];
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
  probeLatest: (org: string) => req<ProbeReport>(`/probe/latest?organization_id=${org}`),
  runProbe: (org: string) =>
    req<{ citation: number }>(`/probe?organization_id=${org}`, { method: "POST" }),
  competitiveSummary: (org: string) =>
    req<CompetitiveSummary>(`/competitive-summary?organization_id=${org}`),
  recommendations: (org: string) => req<Recommendation[]>(`/recommendations?organization_id=${org}`),
  generateRecommendations: (org: string) =>
    req<{ count: number }>(`/recommendations/generate?organization_id=${org}`, { method: "POST" }),
};
