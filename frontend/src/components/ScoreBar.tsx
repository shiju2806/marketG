function toneFor(score: number | null): string {
  if (score === null) return "bg-ink-faint";
  if (score >= 70) return "bg-good";
  if (score >= 45) return "bg-warn";
  return "bg-crit";
}

export function ScoreBar({
  label,
  score,
  hint,
}: {
  label: string;
  score: number | null;
  hint?: string;
}) {
  const width = score === null ? 0 : Math.max(2, Math.min(100, score));
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-baseline justify-between font-mono text-xs uppercase tracking-wide text-ink-soft">
        <span>{label}</span>
        <span className="text-ink">{score === null ? "—" : score}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-surface-2">
        <div className={`h-full rounded-full ${toneFor(score)}`} style={{ width: `${width}%` }} />
      </div>
      {hint && <div className="text-[11px] text-ink-faint">{hint}</div>}
    </div>
  );
}
