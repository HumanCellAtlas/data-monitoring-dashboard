from datetime import datetime
from decimal import Decimal
import os

from tracker.common.dynamo_agents.dynamo_agent import DynamoAgent


class ProjectDynamoAgent(DynamoAgent):

    def __init__(self):
        super().__init__()
        deployment_stage = os.environ["DEPLOYMENT_STAGE"]
        self.dynamo_table_name = f"dcp-data-dashboard-project-info-{deployment_stage}"
        self.table_display_name = "project-info"

    def create_dynamo_payload(self, ingest_records, dss_record, azul_record, analysis_record, matrix_record):
        payload = {}
        payload['project_uuid'] = dss_record['project_uuid']

        first_ingest_record, last_ingest_record, primary_time, analysis_time = self._parse_ingest_records_and_project_lead_times(ingest_records)

        primary_state = self._determine_project_primary_state(last_ingest_record, dss_record, azul_record)
        analysis_state = self._determine_project_analysis_state(primary_state, dss_record, analysis_record, azul_record)
        matrix_state = matrix_record['analysis_state']
        project_state = self._determine_project_overall_state(primary_state, analysis_state, matrix_state)

        payload['primary_state'] = primary_state
        payload['analysis_state'] = analysis_state
        payload['matrix_state'] = matrix_state
        payload['project_state'] = project_state
        payload['latest_submission_id'] = last_ingest_record['submission_id']
        payload['initial_submission_id'] = first_ingest_record['submission_id']
        payload['primary_lead_time'] = int(primary_time)
        payload['analysis_lead_time'] = int(analysis_time)
        payload['failures_present'] = self._determine_if_failures_present(ingest_records, analysis_record)

        return payload

    def _parse_ingest_records_and_project_lead_times(self, ingest_records):
        last_submission_date = ingest_records[0]['submission_date']
        last_record = ingest_records[0]
        first_submission_date = ingest_records[0]['submission_date']
        first_record = ingest_records[0]
        for record in ingest_records:
            submission_date = record['submission_date']
            if submission_date > last_submission_date:
                last_record = record
                last_submission_date = submission_date
            elif submission_date <= first_submission_date:
                first_record = record
                first_submission_date = submission_date
        primary_submission_date = first_record['submission_date']
        primary_submission_dt = datetime.strptime(primary_submission_date, "%Y-%m-%dT%H:%M:%S.%fZ")
        primary_update_date = first_record['update_date']
        primary_update_dt = datetime.strptime(primary_update_date, "%Y-%m-%dT%H:%M:%S.%fZ")
        last_analysis_update_date = first_record.get('latest_analysis_envelope_update_date')
        primary_lead_time = (primary_update_dt - primary_submission_dt).total_seconds()
        if last_analysis_update_date != 'N/A':
            last_analysis_update_dt = datetime.strptime(last_analysis_update_date, "%Y-%m-%dT%H:%M:%S.%fZ")
            analysis_lead_time = (last_analysis_update_dt - primary_submission_dt).total_seconds()
        else:
            analysis_lead_time = 0
        return first_record, last_record, primary_lead_time, analysis_lead_time

    def _determine_if_failures_present(self, ingest_records, analysis_record):
        failures_present = False
        for record in ingest_records:
            if record['failures_present']:
                failures_present = True
        if analysis_record['failures_present']:
            failures_present = True
        return failures_present

    def _determine_project_primary_state(self, ingest_record, dss_record, azul_record):
        if (ingest_record['primary_state'] == 'INCOMPLETE' or
                dss_record['primary_state'] == 'INCOMPLETE' or
                azul_record['primary_state'] == 'INCOMPLETE'):
            return 'INCOMPLETE'
        elif azul_record['primary_state'] == 'OUT_OF_DATE':
            return 'OUT_OF_DATE'
        else:
            return 'COMPLETE'

    def _determine_project_analysis_state(self, primary_state, dss_record, analysis_record, azul_record):
        if analysis_record['analysis_state'] == 'NOT_EXPECTED':
            return 'NOT_EXPECTED'
        elif (analysis_record['analysis_state'] == 'INCOMPLETE' or
                dss_record['analysis_state'] == 'INCOMPLETE' or
                azul_record['analysis_state'] == 'INCOMPLETE'):
            return 'INCOMPLETE'
        elif analysis_record['analysis_state'] == 'OUT_OF_DATE' or azul_record['analysis_state'] == 'OUT_OF_DATE':
            return 'OUT_OF_DATE'
        else:
            return 'COMPLETE'

    def _determine_project_overall_state(self, primary_state, analysis_state, matrix_state):
        if primary_state == 'INCOMPLETE' or analysis_state == 'INCOMPLETE' or matrix_state == 'INCOMPLETE':
            return 'INCOMPLETE'
        elif primary_state == 'OUT_OF_DATE' or analysis_state == 'OUT_OF_DATE' or matrix_state == 'OUT_OF_DATE':
            return 'OUT_OF_DATE'
        else:
            return 'COMPLETE'
