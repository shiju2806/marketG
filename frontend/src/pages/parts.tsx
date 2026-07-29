import type { ReactNode } from "react";

export function PageTitle({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-5 fade-in">
      <h2 className="text-xl font-bold tracking-tight">{title}</h2>
      {subtitle && <p className="mt-0.5 text-sm text-ink-faint">{subtitle}</p>}
    </div>
  );
}

export function Card({ title, children, className = "" }: { title?: string; children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-2xl border border-line bg-surface p-5 ${className}`}>
      {title && <h3 className="mb-3 font-mono text-xs uppercase tracking-widest text-ink-soft">{title}</h3>}
      {children}
    </div>
  );
}

export function Loading() {
  return (
    <div className="flex flex-col gap-3">
      <div className="skeleton h-24 w-full" />
      <div className="skeleton h-40 w-full" />
    </div>
  );
}

export function ErrorMsg({ error }: { error: string | null }) {
  if (!error) return null;
  return <div className="rounded-lg border border-crit bg-crit-soft px-4 py-2 text-sm text-crit">{error}</div>;
}
