import os
from collections import defaultdict

from tracker.common.dynamo_agents.dynamo_agent import DynamoAgent
from tracker.common.dcp_agents.analysis_agent import AnalysisAgent


class AnalysisDynamoAgent(DynamoAgent):

    def __init__(self):
        super().__init__()
        deployment_stage = os.environ["DEPLOYMENT_STAGE"]
        self.dynamo_table_name = f"dcp-data-dashboard-analysis-info-{deployment_stage}"
        self.analysis_agent = AnalysisAgent()

    def create_and_save_dynamo_payload(self, project_uuid):
        print(f"creating analysis info payload for {project_uuid}")
        workflows = self.analysis_agent.get_workflows_for_project_uuid(project_uuid)
        workflows_by_status = self._separate_workflows_by_status(workflows)
        payload = {}
        payload['project_uuid'] = project_uuid
        for k, v in workflows_by_status.items():
            payload[k.lower()+'_workflows'] = len(v)
        payload['total_workflows'] = len(workflows)
        self.write_item_to_dynamo(payload)

    def _separate_workflows_by_status(self, workflows):
        workflows_by_status = defaultdict(list)
        for workflow in workflows:
            workflows_by_status[workflow['status']].append(workflow)
        return workflows_by_status
