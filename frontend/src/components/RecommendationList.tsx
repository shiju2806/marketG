import { useState } from "react";
import { api, type Artifact, type Recommendation } from "../api";
import { FixPanel } from "./FixPanel";

const impactTone: Record<string, string> = {
  high: "text-crit border-crit",
  medium: "text-warn border-warn",
  low: "text-ink-soft border-line",
};

// gap types that have a page/copy artifact worth generating
const GENERATABLE = new Set(["citation", "content", "hidden", "missing", "word", "design"]);

export function RecommendationList({ items }: { items: Recommendation[] }) {
  if (items.length === 0) {
    return <p className="text-sm text-ink-faint">No recommendations yet — run an analysis first.</p>;
  }
  return (
    <div className="flex flex-col gap-2.5">
      {items.map((r) => <RecRow key={r.recommendation_id} r={r} />)}
    </div>
  );
}

function RecRow({ r }: { r: Recommendation }) {
  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function generate() {
    setBusy(true);
    setErr(null);
    try {
      const res = await api.remediate(r.recommendation_id);
      setArtifact(res.artifact);
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-xl border border-line p-4">
      <div className="flex items-start justify-between gap-3">
        <h4 className="text-sm font-medium text-ink">{r.title}</h4>
        <span className={`shrink-0 rounded-md border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide ${impactTone[r.expected_impact]}`}>
          {r.expected_impact}
        </span>
      </div>
      <p className="mt-1 text-sm text-ink-soft">{r.missing_detail}</p>
      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        {r.affects.map((a) => (
          <span key={a} className="rounded bg-surface-2 px-2 py-0.5 font-mono text-[10px] text-ink-faint">{a}</span>
        ))}
        {GENERATABLE.has(r.missing_type) && (
          <button onClick={generate} disabled={busy}
            className="ml-auto rounded-lg border border-accent px-2.5 py-1 text-xs text-accent hover:bg-accent-soft disabled:opacity-40">
            {busy ? "Generating…" : artifact ? "Regenerate fix" : "Generate fix"}
          </button>
        )}
      </div>
      {err && <p className="mt-2 text-xs text-crit">{err}</p>}
      {artifact && <FixPanel artifact={artifact} />}
    </div>
  );
}
