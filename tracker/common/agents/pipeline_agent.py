import logging
import os
import json

from cromwell_tools import api as cwm_api
from cromwell_tools import cromwell_auth as cwm_auth

from tracker.common.entities.analysis_entities import Workflow


class PipelineAgent:
    def __init__(self):
        deployment = os.environ['DEPLOYMENT_STAGE']
        self.cromwell_url = 'https://cromwell.caas-prod.broadinstitute.org'
        self.cromwell_collection = 'lira-test' if deployment == 'integration' else f'lira-{deployment}'
        gcp_credentials_file_for_analysis = os.environ.get('GCP_ACCOUNT_ANALYSIS_INFO')
        if gcp_credentials_file_for_analysis:
            with open(gcp_credentials_file_for_analysis, 'r') as f:
                service_account_key = json.load(f)
            self.auth = self._get_auth(service_account_key)

    def _get_auth(self, service_account_key):
        """Helper function to generate the auth object to talk to Secondary-analysis service."""
        return cwm_auth.CromwellAuth.harmonize_credentials(service_account_key=service_account_key,
                                                           url=self.cromwell_url)

    def get_workflows_for_project_uuid(self, project_uuid, with_labels=True):
        query_dict = {
            "label": {
                "project_uuid": project_uuid
            }
        }
        if with_labels:
            query_dict['additionalQueryResultFields'] = ['labels']
        query_dict['label']['caas-collection-name'] = self.cromwell_collection

        response = cwm_api.query(query_dict=query_dict, auth=self.auth)
        response.raise_for_status()
        result = response.json()
        all_workflows = [Workflow(wf) for wf in result['results']]
        return all_workflows
