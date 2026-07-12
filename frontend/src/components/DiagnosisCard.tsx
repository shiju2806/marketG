import type { CrawlDiagnosis } from "../api";

const tone = {
  readable: { border: "border-good", bg: "bg-good-soft", text: "text-good", icon: "✓" },
  blocked: { border: "border-crit", bg: "bg-crit-soft", text: "text-crit", icon: "✕" },
  thin: { border: "border-warn", bg: "bg-warn-soft", text: "text-warn", icon: "!" },
  unreachable: { border: "border-crit", bg: "bg-crit-soft", text: "text-crit", icon: "✕" },
} as const;

export function DiagnosisCard({ data }: { data: CrawlDiagnosis }) {
  const d = data.diagnosis;
  if (!d) return null;
  const t = tone[d.status] ?? tone.thin;
  return (
    <div className={`rounded-2xl border ${t.border} ${t.bg} p-5`}>
      <div className="flex items-start gap-3">
        <span className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border ${t.border} ${t.text} text-sm font-bold`}>
          {t.icon}
        </span>
        <div>
          <h2 className={`text-base font-semibold ${t.text}`}>{d.headline}</h2>
          <p className="mt-1.5 text-sm leading-relaxed text-ink">{d.detail}</p>
          <p className="mt-2 font-mono text-[11px] text-ink-faint">
            Read {d.pages_read} of {d.pages_attempted} pages
            {d.pages_blocked > 0 && ` · ${d.pages_blocked} blocked`}
            {" · "}robots {d.ai_allowed_in_robots ? "allows AI" : "restricts AI"}
            {" · "}structured data {d.has_structured_data ? "present" : "missing"}
          </p>
        </div>
      </div>
    </div>
  );
}
