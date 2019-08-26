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

    def create_dynamo_payload(self, submission_id, project_uuid, latest_primary_bundles, envelope):
        print(f"creating analysis info payload for {project_uuid}")
        workflows = self.analysis_agent.get_workflows_for_project_uuid(project_uuid)
        wfs_count_by_status, wfs_count_by_version = self._aggregrate_workflow_stats(workflows)
        payload = {}
        payload['project_uuid'] = project_uuid
        for status, wf_count in wfs_count_by_status.items():
            payload[status.lower() + '_workflows'] = wf_count
        for version, wf_count in wfs_count_by_version.items():
            payload[version] = wf_count
        payload['total_workflows'] = len(workflows)
        payload['analysis_state'] = self._determine_state_of_workflows(workflows, latest_primary_bundles, envelope)
        return payload

    def _determine_state_of_workflows(self, workflows, latest_primary_bundles, envelope):
        methods = self.ingest_dynamo_agent._get_project_library_construction_methods(envelope)
        if not self._are_workflows_expected_for_project(methods):
            return 'NOT_EXPECTED'

        latest_input_bundle_versions_with_successful_workflows = set()
        input_bundle_uuids_with_successful_workflows = set()
        for workflow in workflows:
            input_bundle_uuid = workflow['labels']['bundle-uuid']
            input_bundle_version = workflow['labels']['bundle-version']
            workflow_status = workflow['status']
            latest_bundle_version = latest_primary_bundles[input_bundle_uuid]['version']
            if workflow_status == 'Succeeded':
                input_bundle_uuids_with_successful_workflows.add(input_bundle_uuid)
                if latest_bundle_version in input_bundle_version:
                    latest_input_bundle_versions_with_successful_workflows.add(input_bundle_uuid)

        if len(input_bundle_uuids_with_successful_workflows) != len(latest_primary_bundles):
            return 'INCOMPLETE'

        if len(latest_input_bundle_versions_with_successful_workflows) != len(latest_primary_bundles):
            return 'OUT_OF_DATE'

        return 'COMPLETE'

    def _bundle_uuids_with_successful_workflows(self, project_uuid):
        workflows = self.analysis_agent.get_workflows_for_project_uuid(project_uuid)
        input_bundle_uuids_with_successful_workflows = set()
        for workflow in workflows:
            workflow_status = workflow['status']
            input_bundle_uuid = workflow['labels']['bundle-uuid']
            if workflow_status == 'Succeeded':
                input_bundle_uuids_with_successful_workflows.add(input_bundle_uuid)
        return input_bundle_uuids_with_successful_workflows

    def _are_workflows_expected_for_project(self, project_methods):
        workflows_expected = False
        for method in METHODS_SUPPORTED_FOR_WORKFLOWS:
            if method in project_methods:
                workflows_expected = True
        return workflows_expected

    def _aggregrate_workflow_stats(self, workflows):
        workflow_count_by_status = defaultdict(lambda: 0)
        workflow_count_by_version = defaultdict(lambda: 0)
        for workflow in workflows:
            wf_status = workflow['status']
            wf_version = workflow['labels']['workflow-version']
            workflow_count_by_status[wf_status] = workflow_count_by_status[wf_status] + 1
            workflow_count_by_version[wf_version] = workflow_count_by_version[wf_version] + 1
        return workflow_count_by_status, workflow_count_by_version
