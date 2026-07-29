import { api } from "../api";
import { useAsync } from "../state";
import { GapMatrix } from "../components/GapMatrix";
import { RecommendationList } from "../components/RecommendationList";
import { PageTitle, Card, Loading, ErrorMsg } from "./parts";

export function Opportunities() {
  const delta = useAsync(api.delta);
  const recs = useAsync(api.recommendations);

  if (delta.loading) return <Loading />;
  if (delta.error) return <ErrorMsg error={delta.error} />;

  return (
    <div>
      <PageTitle title="Opportunities" subtitle="Where you're losing — and the fixes, generated from your own site" />
      {delta.data && (
        <Card title="Content gap — what you have vs. what buyers ask AI" className="mb-4">
          <GapMatrix data={delta.data} />
        </Card>
      )}
      <Card title="How to improve">
        <RecommendationList items={recs.data ?? []} />
      </Card>
    </div>
  );
}
