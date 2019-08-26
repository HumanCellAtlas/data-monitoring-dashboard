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
        payload['analysis_bundle_count'] = len(bundles_indexed)
        payload['cell_count'] = self.agent.get_cell_count_for_project(project_uuid)
        payload['analysis_state'] = self._determine_state_of_analysis_data(bundles_indexed, latest_analysis_bundles)
        return payload

    def _determine_state_of_analysis_data(self, query_results, latest_analysis_bundles):
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

        if len(latest_analysis_bundles) == 0:
            return 'NOT_EXPECTED'
        elif len(all_bundle_uuids_indexed) != len(latest_analysis_bundles):
            return 'INCOMPLETE'
        elif len(bundle_uuids_indexed_on_latest) != len(latest_analysis_bundles):
            return 'OUT_OF_DATE'
        else:
            return 'COMPLETE'
