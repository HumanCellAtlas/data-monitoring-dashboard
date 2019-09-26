import os

from tracker.common.dynamo_agents.analysis_dynamo_agent import AnalysisDynamoAgent
from tracker.common.dynamo_agents.dynamo_agent import DynamoAgent
from tracker.common.dcp_agents.matrix_agent import MatrixAgent

# List of strings of species + method to be compared against populated bundle type counter
METHODS_SUPPORTED_FOR_MATRIX = [
    "10X 3' v2 sequencing homo sapiens",
    "10X 3' v2 sequencing paired-end homo sapiens",
    "10X v2 sequencing homo sapiens",
    "10X v2 sequencing paired-end homo sapiens",
    "10X v2 sequencing mus musculus",
    "10X v2 sequencing paired-end mus musculus",
    "Smart-seq2 paired-end homo sapiens"
]


class MatrixDynamoAgent(DynamoAgent):

    def __init__(self):
        super().__init__()
        deployment_stage = os.environ["DEPLOYMENT_STAGE"]
        self.dynamo_table_name = f"dcp-data-dashboard-matrix-info-{deployment_stage}"
        self.table_display_name = "matrix-info"
        self.agent = MatrixAgent()
        self.analysis_dynamo_agent = AnalysisDynamoAgent()

    def create_dynamo_payload(self, project_uuid, latest_analysis_bundles, azul_info):
        print(f"creating matrix info payload for {project_uuid}")
        payload = {}
        payload['project_uuid'] = project_uuid
        bundles_indexed = self.agent.get_bundles_for_project(project_uuid)
        matrix_bundles_expected = self._matrix_bundle_count_expected_for_project(azul_info)
        payload['analysis_bundle_count'] = len(bundles_indexed)
        payload['cell_count'] = self.agent.get_cell_count_for_project(project_uuid)
        payload['analysis_state'] = self._determine_state_of_analysis_data(bundles_indexed,
                                                                           latest_analysis_bundles,
                                                                           matrix_bundles_expected)
        return payload

    def _matrix_bundle_count_expected_for_project(self, azul_info):
        project_bundle_type_counter = azul_info['analysis_bundle_type_counter']
        matrix_bundles_expected = 0
        for method in METHODS_SUPPORTED_FOR_MATRIX:
            if project_bundle_type_counter.get(method.lower()):
                matrix_bundles_expected += project_bundle_type_counter[method.lower()]
        return matrix_bundles_expected

    def _determine_state_of_analysis_data(self, query_results, latest_analysis_bundles, matrix_bundles_expected):
        all_bundle_uuids_indexed = set()
        bundle_uuids_indexed_on_latest = set()
        for result in query_results:
            bundle_fqid = result[1]
            bundle_uuid = bundle_fqid.split('.')[0]
            bundle_version = bundle_fqid.split('.')[1]
            expected_bundle_version = latest_analysis_bundles.get(bundle_uuid, {}).get('version', 'N/A')
            if bundle_version == expected_bundle_version:
                bundle_uuids_indexed_on_latest.add(bundle_uuid)
            all_bundle_uuids_indexed.add(bundle_uuid)

        if matrix_bundles_expected == 0:
            return 'NOT_EXPECTED'
        elif len(all_bundle_uuids_indexed) != matrix_bundles_expected:
            return 'INCOMPLETE'
        elif len(bundle_uuids_indexed_on_latest) != matrix_bundles_expected:
            return 'OUT_OF_DATE'
        else:
            return 'COMPLETE'
