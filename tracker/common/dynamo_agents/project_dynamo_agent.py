import requests

from datetime import datetime
from decimal import Decimal
import os

from tracker.common.dynamo_agents.dynamo_agent import DynamoAgent
from tracker.common.github_agent import GithubAgent


class ProjectDynamoAgent(DynamoAgent):

    def __init__(self):
        super().__init__()
        self.deployment_stage = os.environ["DEPLOYMENT_STAGE"]
        self.dynamo_table_name = f"dcp-data-dashboard-project-info-{self.deployment_stage}"
        self.table_display_name = "project-info"
        self.github_agent = GithubAgent()
        if self.deployment_stage == 'prod':
            self.tracker_api_url = "https://tracker-api.data.humancellatlas.org"
            self.tracker_ui_url = "https://tracker.data.humancellatlas.org"
        else:
            self.tracker_api_url = f"https://tracker-api.{self.deployment_stage}.data.humancellatlas.org"
            self.tracker_ui_url = f"https://tracker.{self.deployment_stage}.data.humancellatlas.org"

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
        payload['expected_workflows'] = analysis_record['expected_workflows']
        payload['total_workflows'] = analysis_record['total_workflows']
        payload['project_title'] = last_ingest_record['project_title']
        payload['wranglers'] = last_ingest_record['data_curator']
        payload['primary_investigators'] = last_ingest_record['primary_investigator']
        payload['methods'] = azul_record['library_construction_methods']
        payload['species'] = azul_record['species']
        payload['aws_dss_primary_bundle_count'] = dss_record['aws_primary_bundle_count']

        if self.deployment_stage == 'prod':
            prior_saved_payload = self.get_prior_payload_from_tracker_api(payload['project_uuid'])
            github_issue_number = self.create_or_comment_on_github_issue(payload, prior_saved_payload)
            if github_issue_number:
                payload['github_issue'] = int(github_issue_number)

        return payload

    def get_prior_payload_from_tracker_api(self, project_uuid):
        try:
            project_api_url = f"{self.tracker_api_url}/v0/project/{project_uuid}"
            response = requests.get(project_api_url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {}

    def _get_tracker_ui_project_url(self, project_uuid):
        return f"{self.tracker_ui_url}/?projectUUID={project_uuid}"

    def _format_github_issue_title(self, payload):
        return f"{payload['project_title']} ({payload['project_uuid']})"

    def _format_github_issue_body(self, payload):
        body = ''
        body += f"<b>Project Title:</b> {payload['project_title']}<br>"
        # PROJECT SHORTNAME
        body += f"<b>Project UUID:</b> {payload['project_uuid']}<br>"
        body += f"<b>Wrangler/s:</b> {payload['wranglers']}<br>"
        body += f"<b>PI/s:</b> {payload['primary_investigators']}<br>"
        body += f"<b>Species:</b> {payload['species']}<br>"
        body += f"<b>Methods:</b> {payload['methods']}<br>"
        # Original Submission UUID
        # Original Submission Date
        # Latest Submission UUID
        # Latest Submission Date
        body += f"<b>Tracker URL:</b> {self._get_tracker_ui_project_url(payload['project_uuid'])}<br>"
        return body

    def _format_github_state_comment(self, payload):
        body = ''
        body += "State of this project has changed: <br><br>"
        body += f"<b>Overall Project State:</b> {payload['project_state']}<br>"
        body += f"<b>Primary State:</b> {payload['primary_state']}<br>"
        body += f"<b>Analysis State:</b> {payload['analysis_state']}<br>"
        body += f"<b>Matrix State:</b> {payload['matrix_state']}<br><br>"
        body += f"cc @HumanCellAtlas/data-ops"
        return body

    def _determine_diff_and_comment_on_issue(self, github_issue_number, payload, prior_saved_payload):
        prior_project_info = prior_saved_payload.get('project-info', [{}])[0]
        state_changed = self._has_project_state_changed(payload, prior_project_info)
        if state_changed:
            self.github_agent.comment_on_issue(github_issue_number, self._format_github_state_comment(payload))
        if payload['project_state'] == 'COMPLETE':
            self.github_agent.edit_issue_state(github_issue_number, 'closed')
        else:
            self.github_agent.edit_issue_state(github_issue_number, 'open')

    def _has_project_state_changed(self, payload, prior_project_info):
        state_changed = False
        if payload['primary_state'] != prior_project_info.get('primary_state'):
            state_changed = True
        elif payload['analysis_state'] != prior_project_info.get('analysis_state'):
            state_changed = True
        elif payload['matrix_state'] != prior_project_info.get('matrix_state'):
            state_changed = True
        elif payload['project_state'] != prior_project_info.get('project_state'):
            state_changed = True
        return state_changed

    def create_or_comment_on_github_issue(self, payload, prior_saved_payload):
        github_issue_number = prior_saved_payload.get('project-info', [{}])[0].get('github_issue')
        if not github_issue_number:
            if payload['aws_dss_primary_bundle_count'] > 0:
                issue = self.github_agent.create_issue(title=self._format_github_issue_title(payload),
                                                       body=self._format_github_issue_body(payload),
                                                       label='hca-project')
                github_issue_number = int(issue.number)
        if github_issue_number:
            self._determine_diff_and_comment_on_issue(github_issue_number, payload, prior_saved_payload)
            # edit body
        return github_issue_number

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
