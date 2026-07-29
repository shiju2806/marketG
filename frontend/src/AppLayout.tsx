import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useOrg, useTheme } from "./state";
import { AnalyzeModal } from "./AnalyzeModal";

const NAV = [
  { to: "/", label: "Overview", end: true },
  { to: "/competitors", label: "Competitors" },
  { to: "/prompts", label: "Prompts" },
  { to: "/sources", label: "Sources" },
  { to: "/opportunities", label: "Opportunities" },
  { to: "/twin", label: "Ask the twin" },
  { to: "/usage", label: "Usage" },
];

export function AppLayout() {
  const { orgs, orgId, setOrgId, org } = useOrg();
  const [theme, toggleTheme] = useTheme();
  const [analyzing, setAnalyzing] = useState(false);
  const location = useLocation();

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="flex w-56 shrink-0 flex-col border-r border-line bg-surface px-3 py-5">
        <div className="px-2 text-lg font-bold tracking-tight">market<span className="text-accent">G</span></div>
        <div className="mt-1 px-2 font-mono text-[10px] uppercase tracking-widest text-ink-faint">AI Visibility</div>

        <button onClick={() => setAnalyzing(true)}
          className="mt-5 rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white hover:opacity-90">
          + Analyze a website
        </button>

        <nav className="mt-5 flex flex-col gap-0.5">
          {NAV.map((n) => (
            <NavLink key={n.to} to={n.to} end={n.end}
              className={({ isActive }) =>
                `rounded-lg px-3 py-2 text-sm ${isActive ? "bg-accent-soft font-medium text-accent" : "text-ink-soft hover:bg-surface-2"}`}>
              {n.label}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto flex flex-col gap-2 px-1">
          <button onClick={toggleTheme}
            className="rounded-lg border border-line px-3 py-1.5 text-left text-sm text-ink-soft hover:border-accent">
            {theme === "dark" ? "☀ Light" : "☾ Dark"}
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-x-hidden">
        <header className="flex items-center justify-between gap-3 border-b border-line px-6 py-3">
          <div>
            <h1 className="text-lg font-semibold capitalize leading-tight">{org?.name ?? "Select a company"}</h1>
            {org?.website && <div className="text-xs text-ink-faint">{org.website}</div>}
          </div>
          {orgs.length > 0 && (
            <select value={orgId} onChange={(e) => setOrgId(e.target.value)}
              className="rounded-lg border border-line bg-surface px-2.5 py-1.5 text-sm text-ink-soft">
              {orgs.map((o) => <option key={o.organization_id} value={o.organization_id}>{o.name}</option>)}
            </select>
          )}
        </header>

        <div key={location.pathname} className="fade-in px-6 py-6">
          {orgId ? <Outlet /> : (
            <div className="mt-16 text-center">
              <p className="text-sm text-ink-faint">No company analyzed yet.</p>
              <button onClick={() => setAnalyzing(true)}
                className="mt-3 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white">Analyze a website</button>
            </div>
          )}
        </div>
      </main>

      {analyzing && <AnalyzeModal onClose={() => setAnalyzing(false)} />}
    </div>
  );
}
