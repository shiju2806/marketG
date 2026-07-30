import { useState, type FormEvent } from "react";
import { api } from "./api";
import { useOrg } from "./state";

// Best-guess domain from a company name: "General Motors" -> "generalmotors.com".
function guessWebsite(name: string): string {
  const slug = name.toLowerCase().replace(/[^a-z0-9]/g, "");
  return slug ? `${slug}.com` : "";
}

export function AnalyzeModal({ onClose }: { onClose: () => void }) {
  const { refreshOrgs, setOrgId } = useOrg();
  const [name, setName] = useState("");
  // null = "not manually edited" -> website is DERIVED from the name (bulletproof:
  // can't be desynced by a stray onChange/autofill).
  const [manualWebsite, setManualWebsite] = useState<string | null>(null);
  const [stage, setStage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const website = manualWebsite ?? guessWebsite(name);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!name || !website) return;
    setError(null);
    try {
      const { job_id, organization_id } = await api.analyze({ name, website });
      setStage("starting…");
      const poll = async (): Promise<void> => {
        const s = await api.analyzeStatus(job_id);
        setStage(s.stage ?? s.status);
        if (s.status === "done") {
          await refreshOrgs();
          setOrgId(organization_id);
          onClose();
          return;
        }
        if (s.status === "failed") { setError(s.error ?? "analysis failed"); setStage(null); return; }
        setTimeout(poll, 2500);
      };
      setTimeout(poll, 2500);
    } catch (err) { setError(String(err)); setStage(null); }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div className="w-full max-w-md rounded-2xl border border-line bg-surface p-6" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-lg font-semibold">Analyze a website</h2>
        <p className="mt-1 text-sm text-ink-faint">See how AI describes a company when buyers research its market.</p>
        <p className="mt-1 text-xs italic text-accent">✨ Type the company — the website fills in for you (edit if needed).</p>
        <form onSubmit={submit} autoComplete="off" className="mt-4 flex flex-col gap-3">
          <div className="flex flex-col gap-1">
            <label htmlFor="analyze-company" className="text-xs text-ink-faint">Company</label>
            <input id="analyze-company" value={name} autoComplete="off"
              onChange={(e) => setName(e.target.value)}
              placeholder="Rivian" disabled={stage !== null} autoFocus
              className="rounded-lg border border-line bg-bg px-3 py-2 text-sm outline-none focus:border-accent" />
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="analyze-website" className="text-xs text-ink-faint">Website
              {manualWebsite === null && website && <span className="ml-1 text-ink-faint/70">· suggested, edit if needed</span>}
            </label>
            <input id="analyze-website" value={website} autoComplete="off"
              onChange={(e) => setManualWebsite(e.target.value)}
              placeholder="rivian.com" disabled={stage !== null}
              className="rounded-lg border border-line bg-bg px-3 py-2 text-sm outline-none focus:border-accent" />
          </div>
          {error && <p className="text-sm text-crit">{error}</p>}
          {stage ? (
            <div className="text-sm text-accent"><span className="inline-block animate-pulse">●</span> {stage} — this takes a minute or two…</div>
          ) : (
            <div className="mt-1 flex justify-end gap-2">
              <button type="button" onClick={onClose} className="rounded-lg border border-line px-3 py-2 text-sm text-ink-soft">Cancel</button>
              <button type="submit" disabled={!name || !website}
                className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-40">Analyze</button>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
