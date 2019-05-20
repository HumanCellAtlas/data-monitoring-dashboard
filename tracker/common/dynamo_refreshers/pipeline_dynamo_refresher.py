import os
from collections import defaultdict

from tracker.common.dynamo_refreshers.dynamo_refresher import DynamoRefresher
from tracker.common.dynamo_refreshers.ingest_dynamo_refresher import IngestDynamoRefresher
from tracker.common.agents.pipeline_agent import PipelineAgent


class PipelineDynamoRefresher(DynamoRefresher):

    def __init__(self):
        super().__init__()
        deployment_stage = os.environ["DEPLOYMENT_STAGE"]
        self.dynamo_table_name = f"dcp-data-dashboard-pipeline-info-{deployment_stage}"
        self.pipeline_agent = PipelineAgent()
        self.ingest_dynamo_refresher = IngestDynamoRefresher()

    def create_and_save_dynamo_payload(self, submission_id):
        print(f"creating pipeline info payload for {submission_id}")
        ingest_project_info = self.ingest_dynamo_refresher.get_item_from_dynamo(key='submission_id', value=submission_id)
        project_key = ingest_project_info['project_key']
        workflows = self.pipeline_agent.get_workflows_for_project_uuid(project_key)
        workflows_by_status = self._separate_workflows_by_status(workflows)
        payload = {}
        payload['project_key'] = project_key
        for k, v in workflows_by_status.items():
            payload[k.lower()+'_workflows'] = len(v)
        payload['total_workflows'] = len(workflows)
        self.write_item_to_dynamo(payload)

    def _separate_workflows_by_status(self, workflows):
        workflows_by_status = defaultdict(list)
        for workflow in workflows:
            workflows_by_status[workflow.status].append(workflow)
        return workflows_by_status
