import { api } from "../api";
import { useAsync, useOrg } from "../state";
import { QuestionList } from "../components/QuestionList";
import { PageTitle, Card, Loading, ErrorMsg } from "./parts";

export function Prompts() {
  const { org } = useOrg();
  const { data, loading, error } = useAsync(api.probeLatest);
  if (loading) return <Loading />;
  if (error) return <ErrorMsg error={error} />;

  return (
    <div>
      <PageTitle title="Prompts" subtitle="What ChatGPT and Perplexity actually answered, question by question" />
      <Card>
        <QuestionList items={data?.questions ?? []} you={org?.name ?? "you"} />
      </Card>
    </div>
  );
}
