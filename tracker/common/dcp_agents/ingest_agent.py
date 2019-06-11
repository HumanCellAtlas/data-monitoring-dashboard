import os

import requests
from hca.util.pool import ThreadPool

STATUSES_TO_EXCLUDE_FROM_TRACKER = ['Invalid', 'Draft', 'Valid', 'Pending', 'Validating']
PROJECT_NAME_STRINGS_TO_EXCLUDE_FROM_TRACKER = [
    'prod/optimus/',
    'prod/Smart-seq2/',
    'prod/10x/',
    'SS2 1 Cell Integration Test',
    'ss2_prod_test_',
    '10x_prod_test_',
    'DCP_Infrastructure_Test_Do_Not_Use',
    'Q4_DEMO-project',
    'Glioblastoma_small',
]


class IngestAgent:

    INGEST_API_URL_TEMPLATE = "https://api.ingest.{}.data.humancellatlas.org"
    INGEST_API_PROD_URL = "https://api.ingest.data.humancellatlas.org"

    def __init__(self):
        self.deployment = os.environ["DEPLOYMENT_STAGE"]
        if self.deployment == "prod":
            self.base_url = self.INGEST_API_PROD_URL
        else:
            self.base_url = self.INGEST_API_URL_TEMPLATE.format(self.deployment)

    def get_envelope(self, submission_id):
        url = f"{self.base_url}/submissionEnvelopes/{submission_id}"
        response = requests.get(url)
        response.raise_for_status()
        envelope = response.json()
        return envelope

    def get_project(self, submission_id):
        envelope = self.get_envelope(submission_id)
        project_url = envelope['_links']['projects']['href']
        response = requests.get(project_url)
        response.raise_for_status()
        body = response.json()
        if not body.get('_embedded'):
            return None
        project = body['_embedded']['projects'][0]
        return project

    def get_bundle_manifest_count(self, submission_id):
        envelope = self.get_envelope(submission_id)
        bundle_manifest_url = envelope['_links']['bundleManifests']['href']
        response = requests.get(bundle_manifest_url)
        response.raise_for_status()
        bundle_manifest_count = response.json()['page']['totalElements']
        if submission_id == '5cda8757d96dad000856d2ae':
            bundle_manifest_count = '3514'
        return bundle_manifest_count

    def get_all_primary_submission_envelopes(self):
        all_envelopes = []
        url = f"{self.base_url}/submissionEnvelopes?size=100"
        while True:
            response = requests.get(url)
            response.raise_for_status()
            body = response.json()
            envelopes = body['_embedded']['submissionEnvelopes']
            all_envelopes.extend(envelopes)
            print(f"Envelopes paged through: {len(all_envelopes)}")
            links = body['_links']
            next_link = links.get('next')
            if not next_link:
                break
            url = next_link['href']
        primary_submission_envelopes = self._parse_primary_envelopes_from_envelopes(all_envelopes)
        return primary_submission_envelopes

    def get_submission_id_from_envelope(self, envelope):
        submission_id = envelope['_links']['self']['href'].split('/')[-1]
        return submission_id

    def get_project_short_name_from_project(self, project):
        project_core = project['content']['project_core']
        if project_core.get('project_short_name'):
            project_short_name = project['content']['project_core']['project_short_name']
        else:
            project_short_name = project['content']['project_core']['project_shortname']
        return project_short_name

    def get_project_title_from_project(self, project):
        project_core = project['content']['project_core']
        project_title = project_core['project_title']
        return project_title

    def _project_short_name_in_exclusion_list(self, project_short_name):
        excluded = False
        for name in PROJECT_NAME_STRINGS_TO_EXCLUDE_FROM_TRACKER:
            if name in project_short_name:
                excluded = True
        return excluded

    def _parse_primary_envelopes_from_envelopes(self, envelopes):
        primary_submission_envelopes = []
        pool = ThreadPool()
        for envelope in envelopes:
            submission_status = envelope['submissionState']
            if submission_status not in STATUSES_TO_EXCLUDE_FROM_TRACKER:
                pool.add_task(self._append_to_input_list_if_project_present_for_envelope, envelope, primary_submission_envelopes)
        pool.wait_for_completion()
        return primary_submission_envelopes

    def _append_to_input_list_if_project_present_for_envelope(self, envelope, primary_submission_envelopes):
        submission_id = self.get_submission_id_from_envelope(envelope)
        project = self.get_project(submission_id)
        if project:
            project_short_name = self.get_project_short_name_from_project(project)
            if not self._project_short_name_in_exclusion_list(project_short_name):
                primary_submission_envelopes.append(envelope)
                print(f"Primary Submission Envelopes found: {len(primary_submission_envelopes)}({project_short_name})")
