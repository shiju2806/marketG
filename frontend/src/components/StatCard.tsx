export function StatCard({
  value,
  label,
  tone = "ink",
}: {
  value: string;
  label: string;
  tone?: "ink" | "good" | "warn" | "crit" | "accent";
}) {
  const toneClass = {
    ink: "text-ink",
    good: "text-good",
    warn: "text-warn",
    crit: "text-crit",
    accent: "text-accent",
  }[tone];
  return (
    <div className="rounded-xl border border-line bg-surface px-4 py-3.5">
      <div className={`text-2xl font-semibold tabular-nums tracking-tight ${toneClass}`}>{value}</div>
      <div className="mt-0.5 text-xs text-ink-faint">{label}</div>
    </div>
  );
}
