// Animated circular progress ring — the hero "AI visibility" score.
export function ScoreRing({ value, label, size = 108 }: { value: number | null; label: string; size?: number }) {
  const v = value ?? 0;
  const stroke = 9;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const tone = v >= 60 ? "var(--good)" : v >= 40 ? "var(--warn)" : "var(--crit)";
  return (
    <div className="flex items-center gap-4">
      <svg width={size} height={size} className="-rotate-90 shrink-0">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--surface-2)" strokeWidth={stroke} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={tone} strokeWidth={stroke}
          strokeLinecap="round" strokeDasharray={c}
          strokeDashoffset={value == null ? c : c * (1 - v / 100)}
          style={{ transition: "stroke-dashoffset 0.9s cubic-bezier(0.2,0.7,0.2,1)" }} />
        <text x="50%" y="50%" dy="0.05em" textAnchor="middle" className="rotate-90"
          style={{ transformOrigin: "center" }} fontSize={size * 0.28} fontWeight="700" fill="var(--ink)">
          {value ?? "—"}
        </text>
      </svg>
      <div>
        <div className="text-sm font-medium text-ink">{label}</div>
        <div className="mt-0.5 text-xs text-ink-faint">
          {v >= 60 ? "Strong presence" : v >= 40 ? "Room to grow" : "Largely invisible"}
        </div>
      </div>
    </div>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton ${className}`} />;
}
