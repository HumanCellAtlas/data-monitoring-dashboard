import os
from collections import defaultdict

from tracker.common.dcp_agents.analysis_agent import AnalysisAgent
from tracker.common.dynamo_agents.dynamo_agent import DynamoAgent
from tracker.common.dynamo_agents.ingest_dynamo_agent import IngestDynamoAgent

METHODS_SUPPORTED_FOR_WORKFLOWS = ["10X 3' v2 sequencing", "10X v2 sequencing", "Smart-seq2"]


class AnalysisDynamoAgent(DynamoAgent):

    def __init__(self):
        super().__init__()
        deployment_stage = os.environ["DEPLOYMENT_STAGE"]
        self.dynamo_table_name = f"dcp-data-dashboard-analysis-info-{deployment_stage}"
        self.table_display_name = "analysis-info"
        self.analysis_agent = AnalysisAgent()
        self.ingest_dynamo_agent = IngestDynamoAgent()

    def create_dynamo_payload(self, submission_id, project_uuid):
        print(f"creating analysis info payload for {project_uuid}")
        workflows = self.analysis_agent.get_workflows_for_project_uuid(project_uuid)
        methods = self.ingest_dynamo_agent.get_item_from_dynamo('submission_id', submission_id)['library_construction_methods']
        workflows_expected = self._are_workflows_expected_for_project(methods)
        workflow_count_by_status, workflow_count_by_version = self._count_workflows_by_status_and_version(workflows)
        payload = {}
        payload['project_uuid'] = project_uuid
        for status, wf_count in workflow_count_by_status.items():
            payload[status.lower()+'_workflows'] = wf_count
        for version, wf_count in workflow_count_by_version.items():
            payload[version] = wf_count
        payload['total_workflows'] = len(workflows)
        payload['workflows_expected'] = workflows_expected
        return payload

    def _are_workflows_expected_for_project(self, project_methods):
        workflows_expected = False
        for method in METHODS_SUPPORTED_FOR_WORKFLOWS:
            if method in project_methods:
                workflows_expected = True
        return workflows_expected

    def _count_workflows_by_status_and_version(self, workflows):
        workflow_count_by_status = defaultdict(lambda: 0)
        workflow_count_by_version = defaultdict(lambda: 0)
        for workflow in workflows:
            wf_status = workflow['status']
            wf_version = workflow['labels']['workflow-version']
            workflow_count_by_status[wf_status] = workflow_count_by_status[wf_status] + 1
            workflow_count_by_version[wf_version] = workflow_count_by_version[wf_version] + 1
        return workflow_count_by_status, workflow_count_by_version
