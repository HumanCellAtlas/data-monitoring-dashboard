from hca.util.pool import ThreadPool

from tracker.common.dcp_agents.ingest_agent import IngestAgent
from tracker.common.dynamo_agents.ingest_dynamo_agent import IngestDynamoAgent
from tracker.common.dynamo_agents.dss_dynamo_agent import DSSDynamoAgent
from tracker.common.dynamo_agents.matrix_dynamo_agent import MatrixDynamoAgent
from tracker.common.dynamo_agents.azul_dynamo_agent import AzulDynamoAgent
from tracker.common.dynamo_agents.analysis_dynamo_agent import AnalysisDynamoAgent

ingest_agent = IngestAgent()
ingest_dynamo_agent = IngestDynamoAgent()
dss_dynamo_agent = DSSDynamoAgent()
analysis_dynamo_agent = AnalysisDynamoAgent()
matrix_dynamo_agent = MatrixDynamoAgent()
azul_dynamo_agent = AzulDynamoAgent()


def track_envelope_data_moving_through_dcp(submission_id, failures={}):
    try:
        project_uuid = ingest_dynamo_agent.create_and_save_dynamo_payload(submission_id)
        dss_dynamo_agent.create_and_save_dynamo_payload(project_uuid)
        analysis_dynamo_agent.create_and_save_dynamo_payload(submission_id, project_uuid)
        matrix_dynamo_agent.create_and_save_dynamo_payload(project_uuid)
        azul_dynamo_agent.create_and_save_dynamo_payload(project_uuid)
    except Exception as e:
        failures[submission_id] = e
        print(f"Submission_id {submission_id} failed with error: {e} ")


def main():
    failures = {}
    ingest_agent = IngestAgent()
    primary_envelopes = ingest_agent.get_all_primary_submission_envelopes()
    pool = ThreadPool()
    for envelope in primary_envelopes:
        submission_id = ingest_agent.get_submission_id_from_envelope(envelope)
        pool.add_task(track_envelope_data_moving_through_dcp, submission_id, failures)
    pool.wait_for_completion()
    print(f"{len(failures)} projects failed during refresh")
    if len(failures) > 0:
        raise Exception(failures)

if __name__ == '__main__':
    main()
