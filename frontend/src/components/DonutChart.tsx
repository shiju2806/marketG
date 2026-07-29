import type { ShareOfVoice } from "../api";

// Inline-SVG donut of share of voice (you highlighted). No chart lib.
const PALETTE = ["#5b8cff", "#34c77b", "#e5a93a", "#f0605f", "#9b8cff", "#3ac0d0", "#c77b34", "#8a93a6"];

export function DonutChart({ data }: { data: ShareOfVoice[] }) {
  const items = data.filter((d) => d.mentions > 0).slice(0, 8);
  const total = items.reduce((s, d) => s + d.mentions, 0) || 1;
  const r = 60, c = 2 * Math.PI * r;
  let offset = 0;
  const segs = items.map((d, i) => {
    const frac = d.mentions / total;
    const seg = { d, color: d.is_you ? "var(--accent)" : PALETTE[(i % PALETTE.length)], frac, offset };
    offset += frac;
    return seg;
  });
  const you = items.find((d) => d.is_you);

  return (
    <div className="flex flex-wrap items-center gap-6">
      <svg viewBox="0 0 160 160" width="160" height="160" className="shrink-0 -rotate-90">
        {segs.map((s, i) => (
          <circle key={i} cx="80" cy="80" r={r} fill="none" strokeWidth="20"
            stroke={s.d.is_you ? "var(--accent)" : PALETTE[i % PALETTE.length]}
            strokeDasharray={`${s.frac * c} ${c}`} strokeDashoffset={-s.offset * c} />
        ))}
        <text x="80" y="76" textAnchor="middle" className="rotate-90"
          style={{ transformOrigin: "80px 80px" }} fontSize="22" fontWeight="700" fill="var(--ink)">
          {you ? `${Math.round(you.share * 100)}%` : "—"}
        </text>
        <text x="80" y="94" textAnchor="middle" className="rotate-90"
          style={{ transformOrigin: "80px 80px" }} fontSize="9" fill="var(--ink-faint)">
          you
        </text>
      </svg>
      <ul className="flex flex-col gap-1.5">
        {segs.map((s, i) => (
          <li key={i} className="flex items-center gap-2 text-sm">
            <span className="h-2.5 w-2.5 rounded-sm" style={{
              background: s.d.is_you ? "var(--accent)" : PALETTE[i % PALETTE.length],
            }} />
            <span className={s.d.is_you ? "font-semibold text-ink" : "text-ink-soft"}>{s.d.brand}</span>
            <span className="font-mono text-xs text-ink-faint">{Math.round(s.d.share * 100)}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
