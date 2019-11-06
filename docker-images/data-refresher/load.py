from collections import defaultdict
import os
import multiprocessing
import signal
import time

from hca.util.pool import ThreadPool
from dcplib.component_agents import IngestApiAgent
from dcplib.component_entities.ingest_entities import SubmissionEnvelope

from tracker.data_report import DataReport
from tracker.common.dynamo_agents.ingest_dynamo_agent import IngestDynamoAgent
from tracker.common.dynamo_agents.ingest_analysis_dynamo_agent import IngestAnalysisDynamoAgent
from tracker.common.dynamo_agents.dss_dynamo_agent import DSSDynamoAgent
from tracker.common.dynamo_agents.matrix_dynamo_agent import MatrixDynamoAgent
from tracker.common.dynamo_agents.azul_dynamo_agent import AzulDynamoAgent
from tracker.common.dynamo_agents.analysis_dynamo_agent import AnalysisDynamoAgent
from tracker.common.dynamo_agents.project_dynamo_agent import ProjectDynamoAgent

ANALYSIS_ENVELOPE_COLLECTION_JOB = os.environ.get('ANALYSIS_ENVELOPE_COLLECTION_JOB')
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
SUBMISSION_DATE_CUTOFF = '2019-05-10T00:00:00.000Z'

ingest_dynamo_agent = IngestDynamoAgent()
ingest_analysis_dynamo_agent = IngestAnalysisDynamoAgent()
dss_dynamo_agent = DSSDynamoAgent()
analysis_dynamo_agent = AnalysisDynamoAgent()
matrix_dynamo_agent = MatrixDynamoAgent()
azul_dynamo_agent = AzulDynamoAgent()
project_dynamo_agent = ProjectDynamoAgent()
data_report = DataReport()


class Statistics:

    REPORT_EVERY_X_SECONDS = 5

    statistics = {
        'envelopes_retrieved': 0,
        'envelope_not_ready': 0,
        'envelope_has_no_project': 0,
        'envelope_too_old': 0,
        'project_is_excluded': 0,
        'error_while_tracking': 0,
        'successfully_tracked': 0,
        'analysis_envelope': 0
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


def track_envelope_data_moving_through_dcp(envelope, analysis_envelopes_map, bundle_map, failures):
    if envelope.submission_date < SUBMISSION_DATE_CUTOFF:
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
        latest_primary_bundles, latest_analysis_bundles = dss_dynamo_agent.latest_primary_and_analysis_bundles_for_project(project.uuid)
        ingest_submission_payload = ingest_dynamo_agent.create_dynamo_payload(envelope, latest_primary_bundles, analysis_envelopes_map)
        azul_project_payload = azul_dynamo_agent.create_dynamo_payload(project.uuid,
                                                                       latest_primary_bundles,
                                                                       latest_analysis_bundles,
                                                                       bundle_map)
        analysis_project_payload = analysis_dynamo_agent.create_dynamo_payload(envelope,
                                                                               latest_primary_bundles,
                                                                               azul_project_payload)
        dss_project_payload = dss_dynamo_agent.create_dynamo_payload(envelope, ingest_submission_payload)
        matrix_project_payload = matrix_dynamo_agent.create_dynamo_payload(project.uuid, latest_analysis_bundles, azul_project_payload)

        ingest_dynamo_agent.write_item_to_dynamo(ingest_submission_payload)
        analysis_dynamo_agent.write_item_to_dynamo(analysis_project_payload)
        dss_dynamo_agent.write_item_to_dynamo(dss_project_payload)
        matrix_dynamo_agent.write_item_to_dynamo(matrix_project_payload)
        azul_dynamo_agent.write_item_to_dynamo(azul_project_payload)
        Statistics.increment('successfully_tracked')

    except Exception as e:
        failures[envelope.submission_id] = e
        print(f"Submission {envelope.submission_id} failed with error: {e}")
        Statistics.increment('error_while_tracking')


def track_analysis_envelope(envelope, failures):
    if envelope.submission_date < SUBMISSION_DATE_CUTOFF:
        Statistics.increment('envelope_too_old')
        return

    try:
        envelope.project()
        return
    except RuntimeError:
        Statistics.increment('analysis_envelope')

    try:
        ingest_analysis_envelope_payload = ingest_analysis_dynamo_agent.create_dynamo_payload(envelope)
        ingest_analysis_dynamo_agent.write_item_to_dynamo(ingest_analysis_envelope_payload)
        Statistics.increment('successfully_tracked')

    except Exception as e:
        failures[envelope.submission_id] = e
        print(f"Analysis submission {envelope.submission_id} failed with error: {e}")
        Statistics.increment('error_while_tracking')


def create_overall_project_payloads():
    primary_envelopes_project_map = ingest_dynamo_agent.create_project_map()
    dss_project_map = dss_dynamo_agent.create_project_map()
    analysis_project_map = analysis_dynamo_agent.create_project_map()
    matrix_project_map = matrix_dynamo_agent.create_project_map()
    azul_project_map = azul_dynamo_agent.create_project_map()
    for project_uuid, ingest_records in primary_envelopes_project_map.items():
        project_payload = project_dynamo_agent.create_dynamo_payload(ingest_records,
                                                                     dss_project_map[project_uuid][0],
                                                                     azul_project_map[project_uuid][0],
                                                                     analysis_project_map[project_uuid][0],
                                                                     matrix_project_map[project_uuid][0])
        project_dynamo_agent.write_item_to_dynamo(project_payload)


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
    bundle_map = defaultdict(dict)
    signal.signal(signal.SIGINT, _exit_on_signal)
    ingest_agent = IngestApiAgent(deployment=DEPLOYMENT_STAGE)
    analysis_envelopes_map = ingest_analysis_dynamo_agent.create_analysis_envelopes_bundle_map()
    pool = ThreadPool(multiprocessing.cpu_count() * 4)

    for envelope in SubmissionEnvelope.iter_submissions(ingest_api_agent=ingest_agent, page_size=1000, sort_by=None):
        Statistics.increment('envelopes_retrieved')
        if ANALYSIS_ENVELOPE_COLLECTION_JOB:
            # ONLY SAVE PAYLOADS CORRESPONDING WITH ENVELOPES FOR WORKFLOWS. WILL RUN TWICE A DAY.
            pool.add_task(track_analysis_envelope, envelope, failures)
        else:
            # REFRESH DATA FROM ALL COMPONENTS FOR ALL EXISTING AND NEW PROJECTS. RUNS ONCE AN HOUR.
            pool.add_task(track_envelope_data_moving_through_dcp,
                          envelope,
                          analysis_envelopes_map,
                          bundle_map,
                          failures)
    pool.wait_for_completion()

    if not ANALYSIS_ENVELOPE_COLLECTION_JOB:
        create_overall_project_payloads()
        data_report.retrieve()
        data_report.post_to_cloudwatch()

    Statistics.report(force=True)
    print(f"{len(failures)} projects failed during refresh")
    if len(failures) > 0:
        raise Exception(failures)


if __name__ == '__main__':
    main()
