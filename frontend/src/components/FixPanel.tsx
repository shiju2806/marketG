import { useState } from "react";
import type { Artifact } from "../api";

function download(filename: string, content: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function FixPanel({ artifact }: { artifact: Artifact }) {
  const [tab, setTab] = useState<"page" | "schema" | "notes">("page");
  const [copied, setCopied] = useState(false);
  const schemaStr = JSON.stringify(artifact.schema_jsonld ?? {}, null, 2);

  const tabs: { id: typeof tab; label: string }[] = [
    { id: "page", label: "Draft page" },
    { id: "schema", label: "Schema (JSON-LD)" },
    { id: "notes", label: "Why" },
  ];

  const copy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  };

  return (
    <div className="mt-3 rounded-xl border border-accent bg-accent-soft p-3">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        {tabs.map((t) => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`rounded-md px-2.5 py-1 text-xs ${tab === t.id ? "bg-accent text-white" : "text-ink-soft hover:text-ink"}`}>
            {t.label}
          </button>
        ))}
        <div className="ml-auto flex gap-1.5">
          {tab === "page" && (
            <>
              <button onClick={() => copy(artifact.body_markdown)} className="rounded-md border border-line px-2 py-1 text-xs text-ink-soft">
                {copied ? "Copied" : "Copy"}
              </button>
              <button onClick={() => download("page.md", artifact.body_markdown, "text/markdown")} className="rounded-md border border-line px-2 py-1 text-xs text-ink-soft">.md</button>
              <button onClick={() => download("page.html", artifact.body_html, "text/html")} className="rounded-md border border-line px-2 py-1 text-xs text-ink-soft">.html</button>
            </>
          )}
          {tab === "schema" && (
            <>
              <button onClick={() => copy(schemaStr)} className="rounded-md border border-line px-2 py-1 text-xs text-ink-soft">{copied ? "Copied" : "Copy"}</button>
              <button onClick={() => download("schema.json", schemaStr, "application/json")} className="rounded-md border border-line px-2 py-1 text-xs text-ink-soft">.json</button>
            </>
          )}
        </div>
      </div>

      {tab === "page" && (
        <pre className="max-h-80 overflow-auto whitespace-pre-wrap rounded-lg bg-surface p-3 text-xs text-ink">
          {artifact.body_markdown || "(empty — try re-generating)"}
        </pre>
      )}
      {tab === "schema" && (
        <pre className="max-h-80 overflow-auto rounded-lg bg-surface p-3 font-mono text-[11px] text-ink">
          {schemaStr}
        </pre>
      )}
      {tab === "notes" && <p className="p-1 text-sm text-ink">{artifact.notes || "—"}</p>}
    </div>
  );
}
