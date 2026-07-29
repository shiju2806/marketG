import { api } from "../api";
import { useAsync } from "../state";
import { CitedSources } from "../components/CitedSources";
import { PageTitle, Card, Loading, ErrorMsg } from "./parts";

export function Sources() {
  const { data, loading, error } = useAsync(api.citedSources);
  if (loading) return <Loading />;
  if (error) return <ErrorMsg error={error} />;
  if (!data) return null;
  return (
    <div>
      <PageTitle title="Sources" subtitle="The sources AI trusts for your market — and whether your site is among them" />
      <Card><CitedSources data={data} /></Card>
    </div>
  );
}
