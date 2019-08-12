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

PAYLOAD_COUNT_EXPECTATIONS = {
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


class TestPayloadCreation(unittest.TestCase):

    def setUp(self):
        self.deployment_stage = os.environ['DEPLOYMENT_STAGE']
        self.project = PAYLOAD_COUNT_EXPECTATIONS[self.deployment_stage]['project']
        self.submission_id = self.project['submission_id']
        self.project_uuid = self.project['project_uuid']

    def test_ingest_payload(self):
        ingest_api_agent = IngestApiAgent(deployment=self.deployment_stage)
        envelope = SubmissionEnvelope.load_by_id(self.submission_id, ingest_api_agent=ingest_api_agent)
        ingest_dynamo_agent = IngestDynamoAgent()

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
        dss_dynamo_agent = DSSDynamoAgent()

        payload = dss_dynamo_agent.create_dynamo_payload(self.project_uuid)

        self.assertEqual(payload['project_uuid'], self.project_uuid)
        self.assertEqual(payload['aws_primary_bundle_count'], self.project['phases']['primary']['bundle_count_expected'])
        self.assertEqual(payload['gcp_primary_bundle_count'], self.project['phases']['primary']['bundle_count_expected'])
        self.assertEqual(payload['aws_analysis_bundle_count'], self.project['phases']['analysis']['bundle_count_expected'])
        self.assertEqual(payload['aws_analysis_bundle_count'], self.project['phases']['analysis']['bundle_count_expected'])

    def test_analysis_payload(self):
        analysis_dynamo_agent = AnalysisDynamoAgent()

        payload = analysis_dynamo_agent.create_dynamo_payload(self.submission_id, self.project_uuid)

        self.assertEqual(payload['project_uuid'], self.project_uuid)
        self.assertEqual(payload['succeeded_workflows'], self.project['phases']['analysis']['workflow_count_expected'])
        self.assertEqual(payload['total_workflows'], self.project['phases']['analysis']['workflow_count_expected'])
        self.assertEqual(payload['workflows_expected'], self.project['phases']['analysis']['workflows_expected'])

    def test_matrix_payload(self):
        matrix_dynamo_agent = MatrixDynamoAgent()

        payload = matrix_dynamo_agent.create_dynamo_payload(self.project_uuid)

        self.assertEqual(payload['project_uuid'], self.project_uuid)
        self.assertEqual(payload['analysis_bundle_count'], self.project['phases']['analysis']['bundle_count_expected'])
        self.assertEqual(payload['cell_count'], self.project['phases']['analysis']['cell_count_expected'])

    def test_azul_payload(self):
        azul_dynamo_agent = AzulDynamoAgent()

        payload = azul_dynamo_agent.create_dynamo_payload(self.project_uuid)

        self.assertEqual(payload['project_uuid'], self.project_uuid)
        self.assertEqual(payload['analysis_bundle_count'], self.project['phases']['analysis']['bundle_count_expected'])
        self.assertEqual(payload['primary_bundle_count'], self.project['phases']['primary']['bundle_count_expected'])
