import os

from tracker.common.dynamo_agents.dynamo_agent import DynamoAgent
from tracker.common.dcp_agents.azul_agent import AzulAgent


class AzulDynamoAgent(DynamoAgent):

    def __init__(self):
        super().__init__()
        deployment_stage = os.environ["DEPLOYMENT_STAGE"]
        self.dynamo_table_name = f"dcp-data-dashboard-azul-info-{deployment_stage}"
        self.table_display_name = "azul-info"
        self.azul_agent = AzulAgent()

    def create_dynamo_payload(self, project_uuid, latest_primary_bundles, latest_analysis_bundles):
        print(f"creating azul info payload for {project_uuid}")
        bundles = self.azul_agent.get_entities_by_project('bundles', project_uuid)
        primary_bundles_indexed = []
        analysis_bundles_indexed = []
        for bundle in bundles:
            bundle_info = bundle['bundles'][0]
            workflow = bundle['protocols'][0]['workflow']
            if workflow:
                analysis_bundles_indexed.append(bundle_info)
            else:
                primary_bundles_indexed.append(bundle_info)
        payload = {}
        payload['project_uuid'] = project_uuid
        payload['primary_bundle_count'] = len(primary_bundles_indexed)
        payload['analysis_bundle_count'] = len(analysis_bundles_indexed)
        payload['primary_state'] = self._determine_phase_state(primary_bundles_indexed, latest_primary_bundles)
        payload['analysis_state'] = self._determine_phase_state(analysis_bundles_indexed, latest_analysis_bundles)
        return payload

    def _determine_phase_state(self, bundles_indexed, latest_bundles):
        all_bundle_uuids_indexed = set()
        bundle_uuids_indexed_on_latest = set()
        for bundle in bundles_indexed:
            bundle_uuid = bundle['bundleUuid']
            bundle_version = bundle['bundleVersion']
            expected_bundle_version = latest_bundles[bundle_uuid]['version']
            if expected_bundle_version in bundle_version:
                bundle_uuids_indexed_on_latest.add(bundle_uuid)
            all_bundle_uuids_indexed.add(bundle_uuid)

        if len(latest_bundles) == 0:
            state = 'NOT_EXPECTED'
        elif len(all_bundle_uuids_indexed) != len(latest_bundles):
            state = 'INCOMPLETE'
        elif len(bundle_uuids_indexed_on_latest) != len(latest_bundles):
            state = 'OUT_OF_DATE'
        else:
            state = 'COMPLETE'

        return state
