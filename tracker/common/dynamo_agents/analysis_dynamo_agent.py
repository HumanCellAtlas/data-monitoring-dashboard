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

    def create_dynamo_payload(self, submission_id, project_uuid, latest_primary_bundles):
        print(f"creating analysis info payload for {project_uuid}")
        workflows = self.analysis_agent.get_workflows_for_project_uuid(project_uuid)
        methods = self.ingest_dynamo_agent.get_item_from_dynamo('submission_id', submission_id)['library_construction_methods']
        workflows_expected = self._are_workflows_expected_for_project(methods)
        wfs_count_by_status, wfs_count_by_version = self._aggregrate_workflow_stats(workflows)
        wfs_present_for_all_bundle_uuids, wfs_present_for_latest_bundle_versions = self._analyze_wfs(workflows, latest_primary_bundles)
        payload = {}
        payload['project_uuid'] = project_uuid
        for status, wf_count in wfs_count_by_status.items():
            payload[status.lower() + '_workflows'] = wf_count
        for version, wf_count in wfs_count_by_version.items():
            payload[version] = wf_count
        payload['total_workflows'] = len(workflows)
        payload['workflows_expected'] = workflows_expected
        payload['workflows_present_for_all_bundle_uuids'] = wfs_present_for_all_bundle_uuids
        payload['workflows_present_for_latest_bundle_versions'] = wfs_present_for_latest_bundle_versions
        return payload

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

    def _analyze_wfs(self, workflows, latest_primary_bundles):
        bundle_uuids_with_workflows_for_latest = set()
        input_bundle_uuids = set()
        for workflow in workflows:
            input_bundle_uuid = workflow['labels']['bundle-uuid']
            input_bundle_version = workflow['labels']['bundle-version']
            expected_bundle_version = latest_primary_bundles[input_bundle_uuid]['version']
            input_bundle_uuids.add(input_bundle_uuid)
            if expected_bundle_version in input_bundle_version:
                bundle_uuids_with_workflows_for_latest.add(input_bundle_uuid)

        workflows_present_for_latest_bundle_versions = False
        if len(bundle_uuids_with_workflows_for_latest) == len(latest_primary_bundles):
            workflows_present_for_latest_bundle_versions = True

        workflows_present_for_all_bundle_uuids = False
        if len(input_bundle_uuids) == len(latest_primary_bundles):
            workflows_present_for_all_bundle_uuids = True

        return workflows_present_for_all_bundle_uuids, workflows_present_for_latest_bundle_versions
