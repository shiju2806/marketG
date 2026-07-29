import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, type Organization } from "./api";

interface OrgState {
  orgs: Organization[];
  orgId: string;
  setOrgId: (id: string) => void;
  refreshOrgs: () => Promise<Organization[]>;
  org?: Organization;
}

const Ctx = createContext<OrgState | null>(null);

export function OrgProvider({ children }: { children: ReactNode }) {
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [orgId, setOrgIdState] = useState<string>(() => localStorage.getItem("orgId") ?? "");

  function setOrgId(id: string) {
    setOrgIdState(id);
    localStorage.setItem("orgId", id);
  }

  async function refreshOrgs() {
    const list = await api.listOrganizations();
    setOrgs(list);
    // Keep a valid selection.
    if (list.length && !list.some((o) => o.organization_id === orgId)) {
      setOrgId(list[0].organization_id);
    }
    return list;
  }

  useEffect(() => { refreshOrgs().catch(() => {}); }, []);

  const org = orgs.find((o) => o.organization_id === orgId);
  return <Ctx.Provider value={{ orgs, orgId, setOrgId, refreshOrgs, org }}>{children}</Ctx.Provider>;
}

export function useOrg(): OrgState {
  const v = useContext(Ctx);
  if (!v) throw new Error("useOrg must be used within OrgProvider");
  return v;
}

// Theme (light/dark via CSS vars, persisted).
export function useTheme(): ["light" | "dark", () => void] {
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    const saved = localStorage.getItem("theme");
    if (saved === "light" || saved === "dark") return saved;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("theme", theme);
  }, [theme]);
  return [theme, () => setTheme((t) => (t === "dark" ? "light" : "dark"))];
}

// Shared hook: load a per-page resource for the current org.
export function useAsync<T>(fn: (org: string) => Promise<T>, deps: unknown[] = []) {
  const { orgId } = useOrg();
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (!orgId) return;
    let live = true;
    setLoading(true);
    setError(null);
    fn(orgId)
      .then((d) => live && setData(d))
      .catch((e) => live && setError(String(e)))
      .finally(() => live && setLoading(false));
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId, ...deps]);
  return { data, loading, error };
}
