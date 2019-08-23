import os

from tracker.common.dynamo_agents.dynamo_agent import DynamoAgent
from tracker.common.dcp_agents.matrix_agent import MatrixAgent


class MatrixDynamoAgent(DynamoAgent):

    def __init__(self):
        super().__init__()
        deployment_stage = os.environ["DEPLOYMENT_STAGE"]
        self.dynamo_table_name = f"dcp-data-dashboard-matrix-info-{deployment_stage}"
        self.table_display_name = "matrix-info"
        self.agent = MatrixAgent()

    def create_dynamo_payload(self, project_uuid, latest_analysis_bundles):
        print(f"creating matrix info payload for {project_uuid}")
        payload = {}
        payload['project_uuid'] = project_uuid
        bundles_indexed = self.agent.get_bundles_for_project(project_uuid)
        results_complete, indexed_on_latest = self._analyze_results(bundles_indexed, latest_analysis_bundles)
        payload['analysis_bundle_count'] = len(bundles_indexed)
        payload['cell_count'] = self.agent.get_cell_count_for_project(project_uuid)
        payload['results_complete'] = results_complete
        payload['indexed_on_latest'] = indexed_on_latest
        return payload

    def _analyze_results(self, query_results, latest_analysis_bundles):
        all_bundle_uuids_indexed = set()
        bundle_uuids_indexed_on_latest = set()
        for result in query_results:
            bundle_fqid = result[1]
            bundle_uuid = bundle_fqid.split('.')[0]
            bundle_version = bundle_fqid.split('.')[1]
            expected_bundle_version = latest_analysis_bundles[bundle_uuid]['version']
            if bundle_version == expected_bundle_version:
                bundle_uuids_indexed_on_latest.add(bundle_uuid)
            all_bundle_uuids_indexed.add(bundle_uuid)

        results_complete = False
        if len(all_bundle_uuids_indexed) == len(latest_analysis_bundles):
            results_complete = True

        indexed_on_latest = False
        if len(bundle_uuids_indexed_on_latest) == len(latest_analysis_bundles):
            indexed_on_latest = True

        return results_complete, indexed_on_latest
