import type { VisibilityTrend } from "../api";

// A small SVG sparkline of share-of-voice over probe runs.
export function TrendChart({ data }: { data: VisibilityTrend }) {
  const pts = data.points.filter((p) => p.your_share !== null);
  if (pts.length < 2) {
    return (
      <p className="text-sm text-ink-faint">
        Trend appears after your second analysis — re-run periodically to track movement over time.
      </p>
    );
  }

  const w = 520;
  const h = 120;
  const pad = 24;
  const vals = pts.map((p) => p.your_share as number);
  const maxV = Math.max(...vals, 10);
  const x = (i: number) => pad + (i / (pts.length - 1)) * (w - 2 * pad);
  const y = (v: number) => h - pad - (v / maxV) * (h - 2 * pad);
  const line = pts.map((p, i) => `${i === 0 ? "M" : "L"} ${x(i)} ${y(p.your_share as number)}`).join(" ");
  const area = `${line} L ${x(pts.length - 1)} ${h - pad} L ${x(0)} ${h - pad} Z`;

  const first = vals[0];
  const last = vals[vals.length - 1];
  const change = last - first;

  return (
    <div>
      <div className="mb-2 flex items-baseline gap-3">
        <span className="text-2xl font-semibold tabular-nums">{last}%</span>
        <span className="text-sm text-ink-faint">share of voice now</span>
        <span className={`text-sm font-medium ${change > 0 ? "text-good" : change < 0 ? "text-crit" : "text-ink-faint"}`}>
          {change > 0 ? "▲" : change < 0 ? "▼" : "→"} {Math.abs(change)} pts since first run
        </span>
      </div>
      <div className="w-full overflow-x-auto">
        <svg viewBox={`0 0 ${w} ${h}`} className="w-full" style={{ maxWidth: w }}>
          <path d={area} fill="var(--accent)" opacity="0.10" />
          <path d={line} fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinejoin="round" />
          {pts.map((p, i) => (
            <circle key={i} cx={x(i)} cy={y(p.your_share as number)} r="3" fill="var(--accent)" />
          ))}
        </svg>
      </div>
      <div className="mt-1 font-mono text-[10px] text-ink-faint">
        {pts.length} analyses · {new Date(pts[0].date).toLocaleDateString()} → {new Date(pts[pts.length - 1].date).toLocaleDateString()}
      </div>
    </div>
  );
}
