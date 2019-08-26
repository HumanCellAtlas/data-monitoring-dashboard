import os
import signal
import time

from hca.util.pool import ThreadPool
from dcplib.component_agents import IngestApiAgent
from dcplib.component_entities.ingest_entities import SubmissionEnvelope

from tracker.common.dynamo_agents.ingest_dynamo_agent import IngestDynamoAgent
from tracker.common.dynamo_agents.dss_dynamo_agent import DSSDynamoAgent
from tracker.common.dynamo_agents.matrix_dynamo_agent import MatrixDynamoAgent
from tracker.common.dynamo_agents.azul_dynamo_agent import AzulDynamoAgent
from tracker.common.dynamo_agents.analysis_dynamo_agent import AnalysisDynamoAgent
from tracker.common.dynamo_agents.project_dynamo_agent import ProjectDynamoAgent

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
project_dynamo_agent = ProjectDynamoAgent()


class Statistics:

    REPORT_EVERY_X_SECONDS = 5

    statistics = {
        'envelopes_retrieved': 0,
        'envelope_not_ready': 0,
        'envelope_has_no_project': 0,
        'envelope_too_old': 0,
        'project_is_excluded': 0,
        'error_while_tracking': 0,
        'successfully_tracked': 0
    }

    time_of_last_report = None

    @classmethod
    def increment(cls, stat):
        cls.statistics[stat] += 1
        cls.report()

    @classmethod
    def report(cls, force=False):
        if force or not cls.time_of_last_report or time.time() - cls.time_of_last_report > cls.REPORT_EVERY_X_SECONDS:
            print(cls.statistics)
            cls.time_of_last_report = time.time()


def track_envelope_data_moving_through_dcp(envelope, failures={}):
    if envelope.submission_date < '2019-05-10T00:00:00.000Z':
        Statistics.increment('envelope_too_old')
        return

    if envelope.is_unprocessed:
        Statistics.increment('envelope_not_ready')
        return

    try:
        project = envelope.project()
    except RuntimeError:
        Statistics.increment('envelope_has_no_project')
        return

    if _is_excluded_project(project):
        Statistics.increment('project_is_excluded')
        return

    try:
        ingest_submission_payload = ingest_dynamo_agent.create_dynamo_payload(envelope)
        latest_primary_bundles, latest_analysis_bundles = dss_dynamo_agent.latest_primary_and_analysis_bundles_for_project(project.uuid)
        analysis_project_payload = analysis_dynamo_agent.create_dynamo_payload(envelope.submission_id, project.uuid, latest_primary_bundles, envelope)
        dss_project_payload = dss_dynamo_agent.create_dynamo_payload(project.uuid, envelope)
        matrix_project_payload = matrix_dynamo_agent.create_dynamo_payload(project.uuid, latest_analysis_bundles)
        azul_project_payload = azul_dynamo_agent.create_dynamo_payload(project.uuid, latest_primary_bundles, latest_analysis_bundles)
        project_payload = project_dynamo_agent.create_dynamo_payload(ingest_submission_payload,
                                                                     dss_project_payload,
                                                                     azul_project_payload,
                                                                     analysis_project_payload,
                                                                     matrix_project_payload)

        ingest_dynamo_agent.write_item_to_dynamo(ingest_submission_payload)
        analysis_dynamo_agent.write_item_to_dynamo(analysis_project_payload)
        dss_dynamo_agent.write_item_to_dynamo(dss_project_payload)
        matrix_dynamo_agent.write_item_to_dynamo(matrix_project_payload)
        azul_dynamo_agent.write_item_to_dynamo(azul_project_payload)
        project_dynamo_agent.write_item_to_dynamo(project_payload)
        Statistics.increment('successfully_tracked')

    except Exception as e:
        failures[envelope.submission_id] = e
        print(f"Submission {envelope.submission_id} failed with error: {e}")
        Statistics.increment('error_while_tracking')


def _is_excluded_project(project):
    for exclude_name in PROJECT_NAME_STRINGS_TO_EXCLUDE_FROM_TRACKER:
        if exclude_name in project.short_name:
            return True
    return False


def _exit_on_signal(sig, frame):
    Statistics.report(force=True)
    exit(1)


def main():
    failures = {}
    signal.signal(signal.SIGINT, _exit_on_signal)
    ingest_agent = IngestApiAgent(deployment=DEPLOYMENT_STAGE)
    pool = ThreadPool()
    for envelope in SubmissionEnvelope.iter_submissions(ingest_api_agent=ingest_agent, page_size=1000, sort_by=None):
        Statistics.increment('envelopes_retrieved')
        pool.add_task(track_envelope_data_moving_through_dcp, envelope, failures)
    pool.wait_for_completion()
    Statistics.report(force=True)
    print(f"{len(failures)} projects failed during refresh")
    if len(failures) > 0:
        raise Exception(failures)


if __name__ == '__main__':
    main()
