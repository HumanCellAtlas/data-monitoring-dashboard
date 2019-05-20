import os

from tracker.common.dynamo_refreshers.dynamo_refresher import DynamoRefresher
from tracker.common.dynamo_refreshers.ingest_dynamo_refresher import IngestDynamoRefresher
from tracker.common.agents.dss_agent import DSSAgent


class DSSDynamoRefresher(DynamoRefresher):

    def __init__(self):
        super().__init__()
        deployment_stage = os.environ["DEPLOYMENT_STAGE"]
        self.dynamo_table_name = f"dcp-data-dashboard-dss-info-{deployment_stage}"
        self.dss_agent = DSSAgent()
        self.ingest_dynamo_refresher = IngestDynamoRefresher()

    def create_and_save_dynamo_payload(self, submission_id):
        print(f"creating dss info payload for {submission_id}")
        ingest_project_info = self.ingest_dynamo_refresher.get_item_from_dynamo(key='submission_id', value=submission_id)
        project_key = ingest_project_info['project_key']
        total_aws_bundle_count = self.dss_agent.total_bundle_count_for_project(project_key, 'aws')
        primary_aws_bundle_count = self.dss_agent.primary_bundle_count_for_project(project_key, 'aws')
        analysis_aws_bundle_count = total_aws_bundle_count - primary_aws_bundle_count
        total_gcp_bundle_count = self.dss_agent.total_bundle_count_for_project(project_key, 'gcp')
        primary_gcp_bundle_count = self.dss_agent.primary_bundle_count_for_project(project_key, 'gcp')
        analysis_gcp_bundle_count = total_gcp_bundle_count - primary_gcp_bundle_count
        payload = {}
        payload['project_key'] = project_key
        payload['aws_primary_bundle_count'] = primary_aws_bundle_count
        payload['aws_analysis_bundle_count'] = analysis_aws_bundle_count
        payload['gcp_primary_bundle_count'] = primary_gcp_bundle_count
        payload['gcp_analysis_bundle_count'] = analysis_gcp_bundle_count
        self.write_item_to_dynamo(payload)
