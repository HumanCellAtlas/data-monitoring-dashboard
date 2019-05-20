import os

from tracker.common.dynamo_refreshers.dynamo_refresher import DynamoRefresher
from tracker.common.dynamo_refreshers.ingest_dynamo_refresher import IngestDynamoRefresher
from tracker.common.agents.matrix_agent import MatrixAgent


class MatrixDynamoRefresher(DynamoRefresher):

    def __init__(self):
        super().__init__()
        deployment_stage = os.environ["DEPLOYMENT_STAGE"]
        self.dynamo_table_name = f"dcp-data-dashboard-matrix-info-{deployment_stage}"
        self.matrix_agent = MatrixAgent()
        self.ingest_dynamo_refresher = IngestDynamoRefresher()

    def create_and_save_dynamo_payload(self, submission_id):
        print(f"creating matrix info payload for {submission_id}")
        ingest_project_info = self.ingest_dynamo_refresher.get_item_from_dynamo(key='submission_id', value=submission_id)
        project_key = ingest_project_info['project_key']
        payload = {}
        payload['project_key'] = project_key
        payload['analysis_bundle_count'] = self.matrix_agent.get_bundle_count_for_project(project_key)
        payload['cell_count'] = self.matrix_agent.get_cell_count_for_project(project_key)
        self.write_item_to_dynamo(payload)
