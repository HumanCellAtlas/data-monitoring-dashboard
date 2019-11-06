from collections import defaultdict
from datetime import date, timedelta
import os
import requests

from tracker.common.cloudwatch_handler import CloudwatchHandler

TRACKER_URL_TEMPLATE = "https://tracker-api.{DEPLOYMENT_STAGE}.data.humancellatlas.org/"
DEPLOYMENT_STAGE = os.environ['DEPLOYMENT_STAGE']
if DEPLOYMENT_STAGE == 'prod':
    TRACKER_URL = "https://tracker-api.data.humancellatlas.org/"
else:
    TRACKER_URL = TRACKER_URL_TEMPLATE.replace('{DEPLOYMENT_STAGE}', DEPLOYMENT_STAGE)


class DataReport:

    def __init__(self):
        self.cloudwatch_handler = CloudwatchHandler()
        self.total_projects = 0
        self.total_primary_bundles = 0
        self.total_analysis_bundles = 0
        self.total_projects_analyzed = 0
        self.total_workflows = 0
        self.total_workflows_ninety_days = 0
        self.failed_workflows_ninety_days = 0
        self.projects_available_in_matrix_service = 0
        self.projects_with_processing_failure = 0
        self.total_cells = 0
        self.count_by_technology = defaultdict(int)
        self.new_projects_thirty_days = []
        self.new_projects_count_ninety_days = 0
        self.new_projects_count_ninety_days_with_failures = 0
        self.old_projects_with_issues = []

    def retrieve(self):
        projects_url = TRACKER_URL + 'v0/projects'
        response = requests.get(projects_url)
        payload = response.json()
        for project in payload:
            project_info = project['project-info'][0]
            first_ingest_info = self._get_first_submission(project['ingest-info'], project_info)
            last_ingest_info = self._get_last_submission(project['ingest-info'], project_info)
            dss_info = project['dss-info'][0]
            matrix_info = project['matrix-info'][0]
            azul_info = project['azul-info'][0]
            analysis_info = project['analysis-info'][0]
            primary_bundle_count = dss_info['aws_primary_bundle_count']
            analysis_bundle_count = dss_info['aws_analysis_bundle_count']
            total_cells = matrix_info['cell_count']
            methods = azul_info['library_construction_methods']
            submission_date = first_ingest_info['submission_date']
            project_status = project_info['project_state']
            failures_present = project_info['failures_present']
            if primary_bundle_count > 0:
                self.total_projects += 1
                self.total_primary_bundles += primary_bundle_count
                self.total_analysis_bundles += analysis_bundle_count
                self.total_workflows += analysis_info['total_workflows']
                if analysis_bundle_count > 0:
                    self.total_projects_analyzed += 1
                if total_cells > 0:
                    self.total_cells += total_cells
                    self.projects_available_in_matrix_service += 1
                for method in methods:
                    self.count_by_technology[method] += 1
                thirty_days_prior_timestamp = (date.today() - timedelta(days=30)).isoformat()
                if submission_date > thirty_days_prior_timestamp:
                    self.new_projects_thirty_days.append(project)
                elif project_status != 'COMPLETE':
                    self.old_projects_with_issues.append(project)

                ninety_days_prior_timestamp = (date.today() - timedelta(days=30)).isoformat()
                if last_ingest_info['submission_date'] > ninety_days_prior_timestamp:
                    self.total_workflows_ninety_days += analysis_info['total_workflows']
                    if analysis_info.get('failed_workflows'):
                        self.failed_workflows_ninety_days += analysis_info['failed_workflows']
                    self.new_projects_count_ninety_days += 1
                    if failures_present:
                        self.new_projects_count_ninety_days_with_failures += 1

    def _get_first_submission(self, ingest_submissions, project_info):
        for submission in ingest_submissions:
            if submission['submission_id'] == project_info['initial_submission_id']:
                return submission

    def _get_last_submission(self, ingest_submissions, project_info):
        for submission in ingest_submissions:
            if submission['submission_id'] == project_info['latest_submission_id']:
                return submission

    def post_to_cloudwatch(self):
        self.cloudwatch_handler.put_metric_data('total_projects', self.total_projects)
        self.cloudwatch_handler.put_metric_data('total_primary_bundles', self.total_primary_bundles)
        self.cloudwatch_handler.put_metric_data('total_analysis_bundles', self.total_analysis_bundles)
        bundles_analyzed_percentage = float(self.total_analysis_bundles) / float(self.total_primary_bundles) * 100
        self.cloudwatch_handler.put_metric_data('bundles_analyzed_percentage', bundles_analyzed_percentage)
        projects_analyzed_percentage = float(self.total_projects_analyzed) / float(self.total_projects) * 100
        self.cloudwatch_handler.put_metric_data('projects_analyzed_percentage', projects_analyzed_percentage)
        matrix_available_percentage = float(self.projects_available_in_matrix_service) / float(self.total_projects) * 100
        self.cloudwatch_handler.put_metric_data('matrix_available_percentage', matrix_available_percentage)
        self.cloudwatch_handler.put_metric_data('total_cells', self.total_cells)
        project_failure_percentage = float(self.new_projects_count_ninety_days_with_failures) / float(self.new_projects_count_ninety_days) * 100
        self.cloudwatch_handler.put_metric_data('project_failure_percentage', project_failure_percentage)
        self.cloudwatch_handler.put_metric_data('total_workflows', self.total_workflows)
        failed_workflows_percentage = float(self.failed_workflows_ninety_days) / float(self.total_workflows_ninety_days) * 100
        self.cloudwatch_handler.put_metric_data('failed_workflow_percentage', failed_workflows_percentage)

    def print(self):
        print(f"Total Projects: {self.total_projects}")
        print(f"Total Primary Bundles: {self.total_primary_bundles}")
        print(f"Total Analysis Bundles: {self.total_analysis_bundles}")
        print(f"Total Projects Analyzed: {self.total_projects_analyzed}")
        print(f"Total Projects Available in Matrix Service: {self.projects_available_in_matrix_service}")
        print(f"Total Cells Available: {self.total_cells}")
        print(f"Count By Technology: {self.count_by_technology}")
        print(f"New Project Count: {len(self.new_projects_thirty_days)}")
        print("New Projects: ")
        for project in self.new_projects_thirty_days:
            print('\n')
            latest_submission = self._get_last_submission(project['ingest-info'], project['project-info'][0])
            print(latest_submission['project_title'])
            print(f"Wrangler: {project['ingest-info'][0]['data_curator']}")
            print(f"Species: {project['azul-info'][0]['species']}")
            print(f"Methods: {project['azul-info'][0]['library_construction_methods']}")
            print(f"Overall project state: {project['project-info'][0]['project_state']}")
            print(f"Primary data available: {project['project-info'][0]['primary_state']}")
            print(f"Analysis data available: {project['project-info'][0]['analysis_state']}")
            print(f"Matrix data available: {project['project-info'][0]['matrix_state']}")
            print(f"DCP repo linked issue: {project['project-info'][0]['github_issue']}")

        print(f"Old Projects with Issues Count: {len(self.old_projects_with_issues)}")
        print("Old Projects with Issues: ")
        for project in self.old_projects_with_issues:
            print('\n')
            latest_submission = self._get_last_submission(project['ingest-info'], project['project-info'][0])
            print(latest_submission['project_title'])
            print(f"Wrangler: {project['ingest-info'][0]['data_curator']}")
            print(f"Species: {project['azul-info'][0]['species']}")
            print(f"Methods: {project['azul-info'][0]['library_construction_methods']}")
            print(f"Overall project state: {project['project-info'][0]['project_state']}")
            print(f"Primary data available: {project['project-info'][0]['primary_state']}")
            print(f"Analysis data available: {project['project-info'][0]['analysis_state']}")
            print(f"Matrix data available: {project['project-info'][0]['matrix_state']}")
            print(f"DCP repo linked issue: {project['project-info'][0]['github_issue']}")
            print('\n')

if __name__ == '__main__':
    report = DataReport()
    report.retrieve()
    report.print()
