import { api } from "../api";
import { useAsync } from "../state";
import { CitedSources } from "../components/CitedSources";
import { PageTitle, Loading, ErrorMsg } from "./parts";

export function Sources() {
  const { data, loading, error } = useAsync(api.citedSources);
  return (
    <div>
      <PageTitle title="Sources" subtitle="The sources AI trusts for your market — and whether your site is among them" />
      {loading && <Loading />}
      <ErrorMsg error={error} />
      {data && <CitedSources data={data} />}
    </div>
  );
}
