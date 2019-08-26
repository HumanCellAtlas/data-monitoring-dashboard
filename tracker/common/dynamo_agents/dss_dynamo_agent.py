import os

from tracker.common.dynamo_agents.dynamo_agent import DynamoAgent
from tracker.common.dcp_agents.dss_agent import DSSAgent
from tracker.common.dynamo_agents.ingest_dynamo_agent import IngestDynamoAgent
from tracker.common.dynamo_agents.analysis_dynamo_agent import AnalysisDynamoAgent


class DSSDynamoAgent(DynamoAgent):

    def __init__(self):
        super().__init__()
        deployment_stage = os.environ["DEPLOYMENT_STAGE"]
        self.dynamo_table_name = f"dcp-data-dashboard-dss-info-{deployment_stage}"
        self.table_display_name = "dss-info"
        self.dss_agent = DSSAgent()
        self.ingest_dynamo_agent = IngestDynamoAgent()
        self.analysis_dynamo_agent = AnalysisDynamoAgent()

    def create_dynamo_payload(self, project_uuid, envelope):
        print(f"creating dss info payload for {project_uuid}")
        primary_aws_bundles = self.dss_agent.get_primary_bundles_for_project(project_uuid, 'aws')
        analysis_aws_bundles = self.dss_agent.get_analysis_bundles_for_project(project_uuid, 'aws')
        primary_gcp_bundles = self.dss_agent.get_primary_bundles_for_project(project_uuid, 'gcp')
        analysis_gcp_bundles = self.dss_agent.get_analysis_bundles_for_project(project_uuid, 'gcp')
        payload = {}
        payload['project_uuid'] = project_uuid
        payload['aws_primary_bundle_count'] = len(primary_aws_bundles)
        payload['aws_analysis_bundle_count'] = len(analysis_aws_bundles)
        payload['gcp_primary_bundle_count'] = len(primary_gcp_bundles)
        payload['gcp_analysis_bundle_count'] = len(analysis_gcp_bundles)
        payload['primary_state'] = self._determine_primary_state(project_uuid, payload, envelope)
        payload['analysis_state'] = self._determine_analysis_state(project_uuid, payload, envelope)
        return payload

    def latest_primary_and_analysis_bundles_for_project(self, project_uuid, replica='aws'):
        latest_primary_bundles = {}
        latest_analysis_bundles = {}
        primary_bundles = self.dss_agent.get_primary_bundles_for_project(project_uuid, replica)
        analysis_bundles = self.dss_agent.get_analysis_bundles_for_project(project_uuid, replica)

        for bundle in primary_bundles:
            latest_primary_bundle = latest_primary_bundles.get(bundle['uuid'])
            if latest_primary_bundle:
                if latest_primary_bundle['version'] < bundle['version']:
                    latest_primary_bundles[bundle['uuid']] = bundle
            else:
                latest_primary_bundles[bundle['uuid']] = bundle

        for bundle in analysis_bundles:
            latest_analysis_bundle = latest_analysis_bundles.get(bundle['uuid'])
            if latest_analysis_bundle:
                if latest_analysis_bundle['version'] < bundle['version']:
                    latest_analysis_bundles[bundle['uuid']] = bundle
            else:
                latest_analysis_bundles[bundle['uuid']] = bundle

        return latest_primary_bundles, latest_analysis_bundles

    def _determine_primary_state(self, project_uuid, payload, envelope):
        if payload['aws_primary_bundle_count'] != payload['gcp_primary_bundle_count']:
            primary_state = 'INCOMPLETE'
        else:
            primary_state = 'COMPLETE'
        return primary_state

    def _determine_analysis_state(self, project_uuid, payload, envelope):
        methods = self.ingest_dynamo_agent._get_project_library_construction_methods(envelope)
        workflows_expected = self.analysis_dynamo_agent._are_workflows_expected_for_project(methods)
        analysis_bundles_expected = len(self.analysis_dynamo_agent._bundle_uuids_with_successful_workflows(project_uuid))

        if not workflows_expected:
            analysis_state = 'NOT_EXPECTED'
        elif payload['aws_analysis_bundle_count'] != analysis_bundles_expected:
            analysis_state = 'INCOMPLETE'
        elif payload['aws_analysis_bundle_count'] != payload['gcp_analysis_bundle_count']:
            analysis_state = 'INCOMPLETE'
        else:
            analysis_state = 'COMPLETE'

        return analysis_state
