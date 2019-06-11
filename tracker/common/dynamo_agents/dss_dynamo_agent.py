import os

from tracker.common.dynamo_agents.dynamo_agent import DynamoAgent
from tracker.common.dcp_agents.dss_agent import DSSAgent


class DSSDynamoAgent(DynamoAgent):

    def __init__(self):
        super().__init__()
        deployment_stage = os.environ["DEPLOYMENT_STAGE"]
        self.dynamo_table_name = f"dcp-data-dashboard-dss-info-{deployment_stage}"
        self.dss_agent = DSSAgent()

    def create_and_save_dynamo_payload(self, project_uuid):
        print(f"creating dss info payload for {project_uuid}")
        total_aws_bundle_count = self.dss_agent.total_bundle_count_for_project(project_uuid, 'aws')
        primary_aws_bundle_count = self.dss_agent.primary_bundle_count_for_project(project_uuid, 'aws')
        analysis_aws_bundle_count = total_aws_bundle_count - primary_aws_bundle_count
        total_gcp_bundle_count = self.dss_agent.total_bundle_count_for_project(project_uuid, 'gcp')
        primary_gcp_bundle_count = self.dss_agent.primary_bundle_count_for_project(project_uuid, 'gcp')
        analysis_gcp_bundle_count = total_gcp_bundle_count - primary_gcp_bundle_count
        payload = {}
        payload['project_uuid'] = project_uuid
        payload['aws_primary_bundle_count'] = primary_aws_bundle_count
        payload['aws_analysis_bundle_count'] = analysis_aws_bundle_count
        payload['gcp_primary_bundle_count'] = primary_gcp_bundle_count
        payload['gcp_analysis_bundle_count'] = analysis_gcp_bundle_count
        self.write_item_to_dynamo(payload)
