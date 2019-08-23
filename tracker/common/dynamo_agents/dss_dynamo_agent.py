import os

from tracker.common.dynamo_agents.dynamo_agent import DynamoAgent
from tracker.common.dcp_agents.dss_agent import DSSAgent


class DSSDynamoAgent(DynamoAgent):

    def __init__(self):
        super().__init__()
        deployment_stage = os.environ["DEPLOYMENT_STAGE"]
        self.dynamo_table_name = f"dcp-data-dashboard-dss-info-{deployment_stage}"
        self.table_display_name = "dss-info"
        self.dss_agent = DSSAgent()

    def create_dynamo_payload(self, project_uuid):
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
