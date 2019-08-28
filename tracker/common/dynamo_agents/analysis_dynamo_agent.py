import os
from collections import defaultdict

from tracker.common.dcp_agents.analysis_agent import AnalysisAgent
from tracker.common.dynamo_agents.dynamo_agent import DynamoAgent
from tracker.common.dynamo_agents.ingest_dynamo_agent import IngestDynamoAgent

# List of strings of species + method to be compared against populated bundle type counter
METHODS_SUPPORTED_FOR_WORKFLOWS = [
    "10X 3' v2 sequencing homo sapiens",
    "10X 3' v2 sequencing paired-end homo sapiens",
    "10X v2 sequencing homo sapiens",
    "10X v2 sequencing paired-end homo sapiens",
    "10X v2 sequencing mus musculus",
    "10X v2 sequencing paired-end mus musculus",
    "10X 3' v2 sequencing mus musculus",
    "10X 3' v2 sequencing paired-end mus musculus",
    "Smart-seq2 paired-end homo sapiens",
]


class AnalysisDynamoAgent(DynamoAgent):

    def __init__(self):
        super().__init__()
        deployment_stage = os.environ["DEPLOYMENT_STAGE"]
        self.dynamo_table_name = f"dcp-data-dashboard-analysis-info-{deployment_stage}"
        self.table_display_name = "analysis-info"
        self.analysis_agent = AnalysisAgent()
        self.ingest_dynamo_agent = IngestDynamoAgent()

    def create_dynamo_payload(self, envelope, latest_primary_bundles, azul_project_info):
        project_uuid = envelope.project().uuid
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
        payload['analysis_state'] = self._determine_state_of_workflows(workflows,
                                                                       latest_primary_bundles,
                                                                       envelope,
                                                                       project_uuid,
                                                                       azul_project_info)
        return payload

    def _determine_state_of_workflows(self, workflows, latest_primary_bundles, envelope, project_uuid, azul_info):
        workflows_expected = self._workflow_count_expected_for_project(azul_info)
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

        # This is a patch for where failing workflows still produced bundles or incorrect workflows ran
        if (project_uuid == 'f83165c5-e2ea-4d15-a5cf-33f3550bffde' and
                workflows_expected == 7628 and
                len(latest_input_bundle_versions_with_successful_workflows)) == 7611:
            return 'COMPLETE'
        elif (project_uuid == 'f8aa201c-4ff1-45a4-890e-840d63459ca2' and
                workflows_expected == 10 and
                len(latest_input_bundle_versions_with_successful_workflows) == 17):
            return 'COMPLETE'

        if workflows_expected == 0:
            return 'NOT_EXPECTED'
        elif len(input_bundle_uuids_with_successful_workflows) != workflows_expected:
            return 'INCOMPLETE'
        elif len(latest_input_bundle_versions_with_successful_workflows) != workflows_expected:
            return 'OUT_OF_DATE'
        else:
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

    def _workflow_count_expected_for_project(self, azul_info):
        project_bundle_type_counter = azul_info['primary_bundle_type_counter']
        workflows_expected = 0
        for method in METHODS_SUPPORTED_FOR_WORKFLOWS:
            if project_bundle_type_counter.get(method.lower()):
                workflows_expected += project_bundle_type_counter[method.lower()]
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
