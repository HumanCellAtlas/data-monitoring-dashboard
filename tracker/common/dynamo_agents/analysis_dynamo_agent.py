import os
from collections import defaultdict

from tracker.common.dynamo_agents.dynamo_agent import DynamoAgent
from tracker.common.dcp_agents.analysis_agent import AnalysisAgent


class AnalysisDynamoAgent(DynamoAgent):

    def __init__(self):
        super().__init__()
        deployment_stage = os.environ["DEPLOYMENT_STAGE"]
        self.dynamo_table_name = f"dcp-data-dashboard-analysis-info-{deployment_stage}"
        self.table_display_name = "analysis-info"
        self.analysis_agent = AnalysisAgent()

    def create_and_save_dynamo_payload(self, project_uuid):
        print(f"creating analysis info payload for {project_uuid}")
        workflows = self.analysis_agent.get_workflows_for_project_uuid(project_uuid)
        workflow_count_by_status, workflow_count_by_version = self._count_workflows_by_status_and_version(workflows)
        payload = {}
        payload['project_uuid'] = project_uuid
        for status, wf_count in workflow_count_by_status.items():
            payload[status.lower()+'_workflows'] = wf_count
        for version, wf_count in workflow_count_by_version.items():
            payload[version] = wf_count
        payload['total_workflows'] = len(workflows)
        self.write_item_to_dynamo(payload)

    def _count_workflows_by_status_and_version(self, workflows):
        workflow_count_by_status = defaultdict(lambda: 0)
        workflow_count_by_version = defaultdict(lambda: 0)
        for workflow in workflows:
            wf_status = workflow['status']
            wf_version = workflow['labels']['workflow-version']
            workflow_count_by_status[wf_status] = workflow_count_by_status[wf_status] + 1
            workflow_count_by_version[wf_version] = workflow_count_by_version[wf_version] + 1
        return workflow_count_by_status, workflow_count_by_version
