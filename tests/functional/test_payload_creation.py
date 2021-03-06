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
from tracker.common.dynamo_agents.project_dynamo_agent import ProjectDynamoAgent

ingest_dynamo_agent = IngestDynamoAgent()
dss_dynamo_agent = DSSDynamoAgent()
analysis_dynamo_agent = AnalysisDynamoAgent()
matrix_dynamo_agent = MatrixDynamoAgent()
azul_dynamo_agent = AzulDynamoAgent()
project_dynamo_agent = ProjectDynamoAgent()


PROJECT_FIXTURE = {
    'prod': {
        'project': {
            'submission_id': '5d30e0c49be88c0008a9b236',
            'project_uuid': '091cf39b-01bc-42e5-9437-f419a66c8a45',
            'project_short_name': 'Human Hematopoietic Profiling',
            'project_title': 'Profiling of CD34+ cells from human bone marrow to understand hematopoiesis',
            'submission_status': 'Complete',
            'submission_date': '2019-07-18T21:12:36.392Z',
            'species': ['homo sapiens'],
            'library_construction_methods': ['10x v2 sequencing'],
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
            'project_uuid': '116965f3-f094-4769-9d28-ae675c1b569c',
            'submission_id': '5d95d36b71fe4a0008e0c82f',
            'phases': {
                'primary': {
                    'bundle_fqids_count_expected': 6,
                    'latest_bundle_count_expected': 3,
                },
                'analysis': {
                    'bundle_fqids_count_expected': 6,
                    'latest_bundle_count_expected': 3
                }
            }
        }
    }
}


class TestPayloadCreation(unittest.TestCase):

    def setUp(self):
        self.deployment_stage = os.environ['DEPLOYMENT_STAGE']
        self.ingest_api_agent = IngestApiAgent(deployment=self.deployment_stage)

        self.project = PROJECT_FIXTURE[self.deployment_stage]['project']
        self.submission_id = self.project['submission_id']
        self.project_uuid = self.project['project_uuid']
        self.envelope = SubmissionEnvelope.load_by_id(self.submission_id, ingest_api_agent=self.ingest_api_agent)

        self.updated_project = PROJECT_UPDATE_FIXTURE[self.deployment_stage]['project']
        self.updated_project_uuid = self.updated_project['project_uuid']
        self.updated_submission_id = self.updated_project['submission_id']
        self.updated_envelope = SubmissionEnvelope.load_by_id(self.updated_submission_id, ingest_api_agent=self.ingest_api_agent)

    def test_ingest_payload(self):
        latest_primary_bundles, latest_analysis_bundles = dss_dynamo_agent.latest_primary_and_analysis_bundles_for_project(self.project_uuid)
        payload = ingest_dynamo_agent.create_dynamo_payload(self.envelope, latest_primary_bundles)

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
        self.assertEqual(payload['primary_state'], 'COMPLETE')
        self.assertEqual(payload['failures_present'], False)

    def test_dss_payload(self):
        latest_primary_bundles, latest_analysis_bundles = dss_dynamo_agent.latest_primary_and_analysis_bundles_for_project(self.project_uuid)
        ingest_payload = ingest_dynamo_agent.create_dynamo_payload(self.envelope, latest_primary_bundles)
        payload = dss_dynamo_agent.create_dynamo_payload(self.envelope, ingest_payload)

        self.assertEqual(payload['project_uuid'], self.project_uuid)
        self.assertEqual(payload['aws_primary_bundle_count'], self.project['phases']['primary']['bundle_count_expected'])
        self.assertEqual(payload['gcp_primary_bundle_count'], self.project['phases']['primary']['bundle_count_expected'])
        self.assertEqual(payload['aws_analysis_bundle_count'], self.project['phases']['analysis']['bundle_count_expected'])
        self.assertEqual(payload['aws_analysis_bundle_count'], self.project['phases']['analysis']['bundle_count_expected'])
        self.assertEqual(payload['aws_primary_bundle_fqids_count'], self.project['phases']['primary']['bundle_count_expected'])
        self.assertEqual(payload['gcp_primary_bundle_fqids_count'], self.project['phases']['primary']['bundle_count_expected'])
        self.assertEqual(payload['aws_analysis_bundle_fqids_count'], self.project['phases']['analysis']['bundle_count_expected'])
        self.assertEqual(payload['aws_analysis_bundle_fqids_count'], self.project['phases']['analysis']['bundle_count_expected'])
        self.assertEqual(payload['primary_state'], 'COMPLETE')
        self.assertEqual(payload['analysis_state'], 'COMPLETE')

    def test_analysis_payload(self):
        latest_primary_bundles, latest_analysis_bundles = dss_dynamo_agent.latest_primary_and_analysis_bundles_for_project(self.project_uuid)
        azul_payload = azul_dynamo_agent.create_dynamo_payload(self.project_uuid, latest_primary_bundles, latest_analysis_bundles, {})

        payload = analysis_dynamo_agent.create_dynamo_payload(self.envelope, latest_primary_bundles, azul_payload)

        self.assertEqual(payload['project_uuid'], self.project_uuid)
        self.assertEqual(payload['succeeded_workflows'], self.project['phases']['analysis']['workflow_count_expected'])
        self.assertEqual(payload['total_workflows'], self.project['phases']['analysis']['workflow_count_expected'])
        self.assertEqual(payload['analysis_state'], 'COMPLETE')
        self.assertEqual(payload['failures_present'], False)

    def test_matrix_payload(self):
        latest_primary_bundles, latest_analysis_bundles = dss_dynamo_agent.latest_primary_and_analysis_bundles_for_project(self.project_uuid)
        azul_payload = azul_dynamo_agent.create_dynamo_payload(self.project_uuid, latest_primary_bundles, latest_analysis_bundles, {})

        payload = matrix_dynamo_agent.create_dynamo_payload(self.project_uuid, latest_analysis_bundles, azul_payload)

        self.assertEqual(payload['project_uuid'], self.project_uuid)
        self.assertEqual(payload['analysis_bundle_count'], self.project['phases']['analysis']['bundle_count_expected'])
        self.assertEqual(payload['cell_count'], self.project['phases']['analysis']['cell_count_expected'])
        self.assertEqual(payload['analysis_state'], 'COMPLETE')
        self.assertEqual(payload['project_matrices'], 3)

    def test_azul_payload(self):
        latest_primary_bundles, latest_analysis_bundles = dss_dynamo_agent.latest_primary_and_analysis_bundles_for_project(self.project_uuid)

        payload = azul_dynamo_agent.create_dynamo_payload(self.project_uuid, latest_primary_bundles, latest_analysis_bundles, {})

        self.assertEqual(payload['project_uuid'], self.project_uuid)
        self.assertEqual(payload['analysis_bundle_count'], self.project['phases']['analysis']['bundle_count_expected'])
        self.assertEqual(payload['primary_bundle_count'], self.project['phases']['primary']['bundle_count_expected'])
        self.assertEqual(payload['species'], self.project['species'])
        self.assertEqual(payload['library_construction_methods'], self.project['library_construction_methods'])
        self.assertEqual(payload['primary_state'], 'COMPLETE')
        self.assertEqual(payload['analysis_state'], 'COMPLETE')

    def test_project_payload(self):
        latest_primary_bundles, latest_analysis_bundles = dss_dynamo_agent.latest_primary_and_analysis_bundles_for_project(self.project_uuid)
        ingest_payload = ingest_dynamo_agent.create_dynamo_payload(self.envelope, latest_primary_bundles)
        azul_payload = azul_dynamo_agent.create_dynamo_payload(self.project_uuid, latest_primary_bundles, latest_analysis_bundles, {})
        dss_payload = dss_dynamo_agent.create_dynamo_payload(self.envelope, ingest_payload)
        analysis_payload = analysis_dynamo_agent.create_dynamo_payload(self.envelope, latest_primary_bundles, azul_payload)
        matrix_payload = matrix_dynamo_agent.create_dynamo_payload(self.project_uuid, latest_analysis_bundles, azul_payload)

        project_payload = project_dynamo_agent.create_dynamo_payload([ingest_payload], dss_payload, azul_payload, analysis_payload, matrix_payload)

        self.assertEqual(project_payload['project_uuid'], self.project_uuid)
        self.assertEqual(project_payload['project_state'], 'COMPLETE')
        self.assertEqual(project_payload['primary_state'], 'COMPLETE')
        self.assertEqual(project_payload['analysis_state'], 'COMPLETE')
        self.assertEqual(project_payload['matrix_state'], 'COMPLETE')
        self.assertEqual(project_payload['failures_present'], False)

    def test_latest_primary_and_analysis_bundles_for_project__dss(self):
        latest_primary_bundles, latest_analysis_bundles = dss_dynamo_agent.latest_primary_and_analysis_bundles_for_project(self.updated_project_uuid)
        ingest_payload = ingest_dynamo_agent.create_dynamo_payload(self.updated_envelope, latest_primary_bundles)
        dss_payload = dss_dynamo_agent.create_dynamo_payload(self.updated_envelope, ingest_payload)

        self.assertEqual(dss_payload['project_uuid'], self.updated_project['project_uuid'])
        self.assertEqual(dss_payload['aws_primary_bundle_count'], self.updated_project['phases']['primary']['latest_bundle_count_expected'])
        self.assertEqual(dss_payload['gcp_primary_bundle_count'], self.updated_project['phases']['primary']['latest_bundle_count_expected'])
        self.assertEqual(dss_payload['aws_analysis_bundle_count'], self.updated_project['phases']['analysis']['latest_bundle_count_expected'])
        self.assertEqual(dss_payload['gcp_analysis_bundle_count'], self.updated_project['phases']['analysis']['latest_bundle_count_expected'])
        self.assertEqual(dss_payload['aws_primary_bundle_fqids_count'], self.updated_project['phases']['primary']['bundle_fqids_count_expected'])
        self.assertEqual(dss_payload['gcp_primary_bundle_fqids_count'], self.updated_project['phases']['primary']['bundle_fqids_count_expected'])
        self.assertEqual(dss_payload['aws_analysis_bundle_fqids_count'], self.updated_project['phases']['analysis']['bundle_fqids_count_expected'])
        self.assertEqual(dss_payload['gcp_analysis_bundle_fqids_count'], self.updated_project['phases']['analysis']['bundle_fqids_count_expected'])
        self.assertEqual(len(latest_primary_bundles), self.updated_project['phases']['primary']['latest_bundle_count_expected'])

    def test_latest_primary_and_analysis_bundles_for_project__azul(self):
        latest_primary_bundles, latest_analysis_bundles = dss_dynamo_agent.latest_primary_and_analysis_bundles_for_project(self.updated_project_uuid)
        azul_payload = azul_dynamo_agent.create_dynamo_payload(self.updated_project_uuid, latest_primary_bundles, latest_analysis_bundles, {})

        self.assertEqual(azul_payload['primary_state'], 'COMPLETE')
        self.assertEqual(azul_payload['analysis_state'], 'COMPLETE')

    def test_latest_primary_and_analysis_bundles_for_project__analysis(self):
        latest_primary_bundles, latest_analysis_bundles = dss_dynamo_agent.latest_primary_and_analysis_bundles_for_project(self.updated_project_uuid)
        azul_payload = azul_dynamo_agent.create_dynamo_payload(self.updated_project_uuid, latest_primary_bundles, latest_analysis_bundles, {})

        analysis_payload = analysis_dynamo_agent.create_dynamo_payload(self.updated_envelope, latest_primary_bundles, azul_payload)

        self.assertEqual(analysis_payload['analysis_state'], 'COMPLETE')
        self.assertEqual(analysis_payload['failures_present'], False)

    def test_latest_primary_and_analysis_bundles_for_project__matrix(self):
        latest_primary_bundles, latest_analysis_bundles = dss_dynamo_agent.latest_primary_and_analysis_bundles_for_project(self.updated_project_uuid)
        azul_payload = azul_dynamo_agent.create_dynamo_payload(self.updated_project_uuid, latest_primary_bundles, latest_analysis_bundles, {})

        matrix_payload = matrix_dynamo_agent.create_dynamo_payload(self.updated_project_uuid, latest_analysis_bundles, azul_payload)

        self.assertEqual(matrix_payload['analysis_state'], 'INCOMPLETE')
        self.assertEqual(matrix_payload['project_matrices'], 0)
