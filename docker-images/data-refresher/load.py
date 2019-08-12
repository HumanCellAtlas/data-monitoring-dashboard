import os

from hca.util.pool import ThreadPool
from dcplib.component_agents import IngestApiAgent
from dcplib.component_entities.ingest_entities import SubmissionEnvelope

from tracker.common.dynamo_agents.ingest_dynamo_agent import IngestDynamoAgent
from tracker.common.dynamo_agents.dss_dynamo_agent import DSSDynamoAgent
from tracker.common.dynamo_agents.matrix_dynamo_agent import MatrixDynamoAgent
from tracker.common.dynamo_agents.azul_dynamo_agent import AzulDynamoAgent
from tracker.common.dynamo_agents.analysis_dynamo_agent import AnalysisDynamoAgent

DEPLOYMENT_STAGE = os.environ['DEPLOYMENT_STAGE']
PROJECT_NAME_STRINGS_TO_EXCLUDE_FROM_TRACKER = [
    f'{DEPLOYMENT_STAGE}/optimus/',
    f'{DEPLOYMENT_STAGE}/Smart-seq2/',
    f'{DEPLOYMENT_STAGE}/10x/',
    'integration/10x/',
    'integration/Smart-seq2',
    'SS2 1 Cell Integration Test',
    f'ss2_{DEPLOYMENT_STAGE}_test_',
    f'10x_{DEPLOYMENT_STAGE}_test_',
    'DCP_Infrastructure_Test_Do_Not_Use',
    'Q4_DEMO-project',
    'Glioblastoma_small'
]

ingest_dynamo_agent = IngestDynamoAgent()
dss_dynamo_agent = DSSDynamoAgent()
analysis_dynamo_agent = AnalysisDynamoAgent()
matrix_dynamo_agent = MatrixDynamoAgent()
azul_dynamo_agent = AzulDynamoAgent()


def track_envelope_data_moving_through_dcp(envelope, failures={}):
    try:
        if envelope.is_unprocessed:
            print(f"Submission {envelope.submission_id} is unprocessed ({envelope.status})")
            return
        project = envelope.project()
        if _is_excluded_project(project):
            print(f"Submission {envelope.submission_id} is excluded (project {project.short_name})")
            return
        # Create project payloads
        ingest_submission_payload = ingest_dynamo_agent.create_dynamo_payload(envelope)
        dss_project_payload = dss_dynamo_agent.create_dynamo_payload(project.uuid)
        analysis_project_payload = analysis_dynamo_agent.create_dynamo_payload(envelope.submission_id, project.uuid)
        matrix_project_payload = matrix_dynamo_agent.create_dynamo_payload(project.uuid)
        azul_project_payload = azul_dynamo_agent.create_dynamo_payload(project.uuid)

        # Save project payloads once all created
        ingest_dynamo_agent.write_item_to_dynamo(ingest_submission_payload)
        dss_dynamo_agent.write_item_to_dynamo(dss_project_payload)
        analysis_dynamo_agent.write_item_to_dynamo(analysis_project_payload)
        matrix_dynamo_agent.write_item_to_dynamo(matrix_project_payload)
        azul_dynamo_agent.write_item_to_dynamo(azul_project_payload)
    except Exception as e:
        failures[envelope.submission_id] = e
        print(f"Submission {envelope.submission_id} failed with error: {e}")


def _is_excluded_project(project):
    for exclude_name in PROJECT_NAME_STRINGS_TO_EXCLUDE_FROM_TRACKER:
        if exclude_name in project.short_name:
            return True
    return False


def main():
    failures = {}
    ingest_agent = IngestApiAgent(deployment=DEPLOYMENT_STAGE)
    pool = ThreadPool()
    for envelope in SubmissionEnvelope.iter_submissions(ingest_api_agent=ingest_agent, page_size=1000):
        pool.add_task(track_envelope_data_moving_through_dcp, envelope, failures)
    pool.wait_for_completion()
    print(f"{len(failures)} projects failed during refresh")
    if len(failures) > 0:
        raise Exception(failures)


if __name__ == '__main__':
    main()
