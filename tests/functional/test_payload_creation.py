import json
import os
import unittest

from dcplib.component_agents import IngestApiAgent
from dcplib.component_entities.ingest_entities import SubmissionEnvelope

from tracker.common.dynamo_agents.ingest_dynamo_agent import IngestDynamoAgent
from tracker.common.dynamo_agents.dss_dynamo_agent import DSSDynamoAgent
from tracker.common.dynamo_agents.matrix_dynamo_agent import MatrixDynamoAgent
from tracker.common.dynamo_agents.azul_dynamo_agent import AzulDynamoAgent
from tracker.common.dynamo_agents.analysis_dynamo_agent import AnalysisDynamoAgent

ingest_dynamo_agent = IngestDynamoAgent()
dss_dynamo_agent = DSSDynamoAgent()
analysis_dynamo_agent = AnalysisDynamoAgent()
matrix_dynamo_agent = MatrixDynamoAgent()
azul_dynamo_agent = AzulDynamoAgent()


PROJECT_FIXTURE = {
    'prod': {
        'project': {
            'submission_id': '5d30e0c49be88c0008a9b236',
            'project_uuid': '091cf39b-01bc-42e5-9437-f419a66c8a45',
            'project_short_name': 'Human Hematopoietic Profiling',
            'project_title': 'Profiling of CD34+ cells from human bone marrow to understand hematopoiesis',
            'submission_status': 'Complete',
            'submission_date': '2019-07-18T21:12:36.392Z',
            'species': ['Homo sapiens'],
            'library_construction_methods': ['10X v2 sequencing'],
            'primary_investigator': "Dana,, Pe'er; ",
            'data_curator': 'Parisa,, Nejad; ',
            'phases': {
                'primary': {
                    'bundle_count_expected': 9
                },
                'analysis': {
                    'workflows_expected': True,
                    'bundle_count_expected': 9,
                    'workflow_count_expected': 9,
                    'cell_count_expected': 41331
                }
            }
        }
    }
}

PROJECT_UPDATE_FIXTURE = {
    'prod': {
        'project': {
            'project_uuid': 'abe1a013-af7a-45ed-8c26-f3793c24a1f4',
            'submission_id': '5d51692a1a249400085ac36a',
            'phases': {
                'primary': {
                    'bundle_count_expected': 94,
                    'latest_bundle_count_expected': 47
                }
            }
        }
    }
}


class TestPayloadCreation(unittest.TestCase):

    def setUp(self):
        self.deployment_stage = os.environ['DEPLOYMENT_STAGE']
        self.project = PROJECT_FIXTURE[self.deployment_stage]['project']
        self.updated_project = PROJECT_UPDATE_FIXTURE[self.deployment_stage]['project']
        self.submission_id = self.project['submission_id']
        self.project_uuid = self.project['project_uuid']

    def test_ingest_payload(self):
        ingest_api_agent = IngestApiAgent(deployment=self.deployment_stage)
        envelope = SubmissionEnvelope.load_by_id(self.submission_id, ingest_api_agent=ingest_api_agent)

        payload = ingest_dynamo_agent.create_dynamo_payload(envelope)

        self.assertEqual(payload['submission_id'], self.submission_id)
        self.assertEqual(payload['submission_date'], self.project['submission_date'])
        self.assertEqual(payload['project_uuid'], self.project_uuid)
        self.assertEqual(payload['project_short_name'], self.project['project_short_name'])
        self.assertEqual(payload['project_title'], self.project['project_title'])
        self.assertEqual(payload['submission_status'], self.project['submission_status'])
        self.assertEqual(payload['submission_bundles_exported_count'], self.project['phases']['primary']['bundle_count_expected'])
        self.assertEqual(payload['species'], self.project['species'])
        self.assertEqual(payload['library_construction_methods'], self.project['library_construction_methods'])
        self.assertEqual(payload['primary_investigator'], self.project['primary_investigator'])
        self.assertEqual(payload['data_curator'], self.project['data_curator'])

    def test_dss_payload(self):
        payload = dss_dynamo_agent.create_dynamo_payload(self.project_uuid)

        self.assertEqual(payload['project_uuid'], self.project_uuid)
        self.assertEqual(payload['aws_primary_bundle_count'], self.project['phases']['primary']['bundle_count_expected'])
        self.assertEqual(payload['gcp_primary_bundle_count'], self.project['phases']['primary']['bundle_count_expected'])
        self.assertEqual(payload['aws_analysis_bundle_count'], self.project['phases']['analysis']['bundle_count_expected'])
        self.assertEqual(payload['aws_analysis_bundle_count'], self.project['phases']['analysis']['bundle_count_expected'])

    def test_analysis_payload(self):
        latest_primary_bundles, latest_analysis_bundles = dss_dynamo_agent.latest_primary_and_analysis_bundles_for_project(self.project_uuid)
        payload = analysis_dynamo_agent.create_dynamo_payload(self.submission_id, self.project_uuid, latest_primary_bundles)

        self.assertEqual(payload['project_uuid'], self.project_uuid)
        self.assertEqual(payload['succeeded_workflows'], self.project['phases']['analysis']['workflow_count_expected'])
        self.assertEqual(payload['total_workflows'], self.project['phases']['analysis']['workflow_count_expected'])
        self.assertEqual(payload['workflows_expected'], self.project['phases']['analysis']['workflows_expected'])

    def test_matrix_payload(self):
        latest_primary_bundles, latest_analysis_bundles = dss_dynamo_agent.latest_primary_and_analysis_bundles_for_project(self.project_uuid)

        payload = matrix_dynamo_agent.create_dynamo_payload(self.project_uuid, latest_analysis_bundles)

        self.assertEqual(payload['project_uuid'], self.project_uuid)
        self.assertEqual(payload['analysis_bundle_count'], self.project['phases']['analysis']['bundle_count_expected'])
        self.assertEqual(payload['cell_count'], self.project['phases']['analysis']['cell_count_expected'])

    def test_azul_payload(self):
        latest_primary_bundles, latest_analysis_bundles = dss_dynamo_agent.latest_primary_and_analysis_bundles_for_project(self.project_uuid)

        payload = azul_dynamo_agent.create_dynamo_payload(self.project_uuid, latest_primary_bundles, latest_analysis_bundles)

        self.assertEqual(payload['project_uuid'], self.project_uuid)
        self.assertEqual(payload['analysis_bundle_count'], self.project['phases']['analysis']['bundle_count_expected'])
        self.assertEqual(payload['primary_bundle_count'], self.project['phases']['primary']['bundle_count_expected'])

    def test_latest_primary_and_analysis_bundles_for_project__dss(self):
        updated_project_uuid = self.updated_project['project_uuid']

        dss_payload = dss_dynamo_agent.create_dynamo_payload(updated_project_uuid)
        latest_primary_bundles, latest_analysis_bundles = dss_dynamo_agent.latest_primary_and_analysis_bundles_for_project(updated_project_uuid)

        self.assertEqual(dss_payload['project_uuid'], self.updated_project['project_uuid'])
        self.assertEqual(dss_payload['aws_primary_bundle_count'], self.updated_project['phases']['primary']['bundle_count_expected'])
        self.assertEqual(dss_payload['gcp_primary_bundle_count'], self.updated_project['phases']['primary']['bundle_count_expected'])
        self.assertEqual(len(latest_primary_bundles), self.updated_project['phases']['primary']['latest_bundle_count_expected'])

    def test_latest_primary_and_analysis_bundles_for_project__azul(self):
        updated_project_uuid = self.updated_project['project_uuid']

        latest_primary_bundles, latest_analysis_bundles = dss_dynamo_agent.latest_primary_and_analysis_bundles_for_project(updated_project_uuid)
        azul_payload = azul_dynamo_agent.create_dynamo_payload(updated_project_uuid, latest_primary_bundles, latest_analysis_bundles)

        self.assertEqual(azul_payload['primary_complete'], True)
        self.assertEqual(azul_payload['primary_on_latest'], True)
        self.assertEqual(azul_payload['analysis_complete'], True)
        self.assertEqual(azul_payload['analysis_on_latest'], True)

    def test_latest_primary_and_analysis_bundles_for_project__analysis(self):
        updated_project_uuid = self.updated_project['project_uuid']
        updated_submission_id = self.updated_project['submission_id']

        latest_primary_bundles, latest_analysis_bundles = dss_dynamo_agent.latest_primary_and_analysis_bundles_for_project(updated_project_uuid)
        analysis_payload = analysis_dynamo_agent.create_dynamo_payload(updated_submission_id, updated_project_uuid, latest_primary_bundles)

        self.assertEqual(analysis_payload['workflows_present_for_all_bundle_uuids'], True)
        self.assertEqual(analysis_payload['workflows_present_for_latest_bundle_versions'], True)

    def test_latest_primary_and_analysis_bundles_for_project__matrix(self):
        updated_project_uuid = self.updated_project['project_uuid']

        latest_primary_bundles, latest_analysis_bundles = dss_dynamo_agent.latest_primary_and_analysis_bundles_for_project(updated_project_uuid)
        matrix_payload = matrix_dynamo_agent.create_dynamo_payload(updated_project_uuid, latest_analysis_bundles)

        self.assertEqual(matrix_payload['results_complete'], False)
        self.assertEqual(matrix_payload['indexed_on_latest'], False)
