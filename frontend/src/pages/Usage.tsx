import { api } from "../api";
import { useAsync } from "../state";
import { UsagePanel } from "../components/UsagePanel";
import { PageTitle, Loading, ErrorMsg } from "./parts";

export function Usage() {
  const { data, loading, error } = useAsync((org) => api.usage(org));
  if (loading) return <Loading />;
  if (error) return <ErrorMsg error={error} />;
  if (!data) return null;
  return (
    <div>
      <PageTitle title="Usage & cost" subtitle="LLM spend per analysis — incremental re-runs skip unchanged pages" />
      <UsagePanel data={data} />
    </div>
  );
}
