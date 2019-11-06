import base64
import logging
import os
import json

import cromwell_tools
from typing import List, Dict

from tracker.common.config import TrackerInfraConfig


class AnalysisAgent:
    def __init__(self) -> None:
        """Interacts with the HCA DCP Pipelines Execution Service."""
        deployment = os.environ['DEPLOYMENT_STAGE']
        self.cromwell_url = 'https://cromwell.caas-prod.broadinstitute.org'
        self.cromwell_collection = 'lira-int' if deployment == 'integration' else f'lira-{deployment}'
        self.auth = cromwell_tools.cromwell_auth.CromwellAuth.harmonize_credentials(service_account_key=self.analysis_gcp_creds,
                                                                                    url=self.cromwell_url)

    # TODO FIGURE OUT HOW TO PASS IN CREDS ONCE THIS AGENT IS MOVED TO DCPLIB
    @property
    def analysis_gcp_creds(self):
        return json.loads(base64.b64decode(TrackerInfraConfig().analysis_gcp_creds).decode())

    def get_workflows_for_project_uuid(self, project_uuid: str, with_labels: bool = True) -> List[Dict[str, str]]:
        """Query the workflows in secondary analysis by project uuid.

        Args:
            project_uuid: The UUID of an ingested HCA DCP data project.
            with_labels: Whether to include all workflow labels information in the result. Note
                setting this to True will put some extra stress on the secondary analysis service
                and might be slower to query.
        Returns:
            result: A list of workflow metadata blocks that matched the query.
        """
        # Note: this query dict automatically filters out any workflows that
        # labeled with the key:values pairs in the `excludeLabelOr` list. 
        # the labeling mechanism is fully relying on the analysis component 
        # and the data operations team
        query_dict = {
            "label": {
                "project_uuid": project_uuid
            },
        'excludeLabelOr': ['comment:erased'],
        }
        if with_labels:
            query_dict['additionalQueryResultFields'] = ['labels']

        # to only query within the collection that associated with the current deployment
        query_dict['label']['caas-collection-name'] = self.cromwell_collection

        response = cromwell_tools.api.query(query_dict=query_dict, auth=self.auth, raise_for_status=True)
        result = response.json()['results']
        return result
