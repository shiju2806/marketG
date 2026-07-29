import { api } from "../api";
import { useAsync, useOrg } from "../state";
import { AskTwin } from "../components/AskTwin";
import { PageTitle, Card, Loading, ErrorMsg } from "./parts";

export function Twin() {
  const { orgId } = useOrg();
  const conflicts = useAsync(api.conflicts);

  return (
    <div>
      <PageTitle title="Ask the twin" subtitle="Query your own knowledge graph — grounded answers, no hallucination" />
      <Card title="Ask a question" className="mb-4"><AskTwin orgId={orgId} /></Card>

      <Card title="Contradictions in your content">
        {conflicts.loading ? <Loading /> : <ErrorMsg error={conflicts.error} />}
        {conflicts.data && conflicts.data.length === 0 && (
          <p className="text-sm text-ink-faint">No contradictions detected.</p>
        )}
        {conflicts.data && conflicts.data.length > 0 && (
          <ul className="flex flex-col gap-2">
            {conflicts.data.map((c) => (
              <li key={c.conflict_id} className="rounded-lg border border-warn/40 bg-warn-soft px-3 py-2 text-sm text-ink">
                {c.description}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
