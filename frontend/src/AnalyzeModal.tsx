import { useEffect, useRef, useState, type FormEvent } from "react";
import { api } from "./api";
import { useOrg } from "./state";

type Suggestion = { name: string; domain: string };

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
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [showSuggest, setShowSuggest] = useState(false);
  const debounce = useRef<ReturnType<typeof setTimeout>>();

  const website = manualWebsite ?? guessWebsite(name);

  // Debounced real-company autocomplete as the user types the company name.
  useEffect(() => {
    clearTimeout(debounce.current);
    const q = name.trim();
    if (q.length < 2) { setSuggestions([]); return; }
    debounce.current = setTimeout(async () => {
      try {
        const s = await api.companySuggest(q);
        setSuggestions(s);
        setShowSuggest(s.length > 0);
      } catch { setSuggestions([]); }
    }, 220);
    return () => clearTimeout(debounce.current);
  }, [name]);

  function pick(s: Suggestion) {
    setName(s.name);
    setManualWebsite(s.domain);
    setShowSuggest(false);
  }

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
        <p className="mt-1 text-xs italic text-accent">✨ Start typing — pick your company from the list to auto-fill its website.</p>
        <form onSubmit={submit} autoComplete="off" className="mt-4 flex flex-col gap-3">
          <div className="relative flex flex-col gap-1">
            <label htmlFor="analyze-company" className="text-xs text-ink-faint">Company</label>
            <input id="analyze-company" value={name} autoComplete="off"
              onChange={(e) => { setName(e.target.value); setManualWebsite(null); }}
              onFocus={() => setShowSuggest(suggestions.length > 0)}
              placeholder="Start typing a company…" disabled={stage !== null} autoFocus
              className="rounded-lg border border-line bg-bg px-3 py-2 text-sm outline-none focus:border-accent" />
            {showSuggest && suggestions.length > 0 && (
              <ul className="absolute left-0 right-0 top-full z-10 mt-1 max-h-56 overflow-auto rounded-lg border border-line bg-surface shadow-lg">
                {suggestions.map((s) => (
                  <li key={s.domain}>
                    <button type="button" onClick={() => pick(s)}
                      className="flex w-full items-center gap-2.5 px-3 py-2 text-left text-sm hover:bg-surface-2">
                      <img src={`https://www.google.com/s2/favicons?domain=${s.domain}&sz=32`} alt=""
                        width={18} height={18} className="shrink-0 rounded"
                        onError={(e) => (e.currentTarget.style.visibility = "hidden")} />
                      <span className="truncate text-ink">{s.name}</span>
                      <span className="ml-auto shrink-0 font-mono text-xs text-ink-faint">{s.domain}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
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
