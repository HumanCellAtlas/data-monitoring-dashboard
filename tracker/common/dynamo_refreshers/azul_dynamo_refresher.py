import os

from tracker.common.dynamo_refreshers.dynamo_refresher import DynamoRefresher
from tracker.common.dynamo_refreshers.ingest_dynamo_refresher import IngestDynamoRefresher
from tracker.common.agents.azul_agent import AzulAgent


class AzulDynamoRefresher(DynamoRefresher):

    def __init__(self):
        super().__init__()
        deployment_stage = os.environ["DEPLOYMENT_STAGE"]
        self.dynamo_table_name = f"dcp-data-dashboard-azul-info-{deployment_stage}"
        self.azul_agent = AzulAgent()
        self.ingest_dynamo_refresher = IngestDynamoRefresher()

    def create_and_save_dynamo_payload(self, submission_id):
        print(f"creating azul info payload for {submission_id}")
        ingest_project_info = self.ingest_dynamo_refresher.get_item_from_dynamo(key='submission_id', value=submission_id)
        project_key = ingest_project_info['project_key']
        bundles = self.azul_agent.get_entities_by_project('bundles', project_key)
        primary_bundle_count = 0
        analysis_bundle_count = 0
        for bundle in bundles:
            workflow = bundle['protocols'][0]['workflow']
            if workflow:
                analysis_bundle_count += 1
            else:
                primary_bundle_count += 1
        payload = {}
        payload['project_key'] = project_key
        payload['primary_bundle_count'] = primary_bundle_count
        payload['analysis_bundle_count'] = analysis_bundle_count
        self.write_item_to_dynamo(payload)
