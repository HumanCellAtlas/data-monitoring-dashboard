from hca.util.pool import ThreadPool

from tracker.common.agents.ingest_agent import IngestAgent
from tracker.common.dynamo_refreshers.ingest_dynamo_refresher import IngestDynamoRefresher
from tracker.common.dynamo_refreshers.dss_dynamo_refresher import DSSDynamoRefresher
from tracker.common.dynamo_refreshers.matrix_dynamo_refresher import MatrixDynamoRefresher
from tracker.common.dynamo_refreshers.azul_dynamo_refresher import AzulDynamoRefresher
from tracker.common.dynamo_refreshers.pipeline_dynamo_refresher import PipelineDynamoRefresher


def track_envelope_data_moving_through_dcp(submission_id, failures):
    try:
        ingest_dynamo_refresher = IngestDynamoRefresher()
        ingest_dynamo_refresher.create_and_save_dynamo_payload(submission_id)
        dss_dynamo_refresher = DSSDynamoRefresher()
        dss_dynamo_refresher.create_and_save_dynamo_payload(submission_id)
        pipeline_dynamo_refresher = PipelineDynamoRefresher()
        pipeline_dynamo_refresher.create_and_save_dynamo_payload(submission_id)
        matrix_dynamo_refresher = MatrixDynamoRefresher()
        matrix_dynamo_refresher.create_and_save_dynamo_payload(submission_id)
        azul_dynamo_refresher = AzulDynamoRefresher()
        azul_dynamo_refresher.create_and_save_dynamo_payload(submission_id)
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
    print("Failures:")
    print(failures)

if __name__ == '__main__':
    main()
