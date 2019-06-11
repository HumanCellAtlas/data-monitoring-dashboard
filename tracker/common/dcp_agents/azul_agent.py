import os

from urllib3 import Retry
from six.moves.urllib.parse import urlencode

import requests

class AzulAgent:
    AZUL_URL_TEMPLATE = 'https://service.{deployment}.explore.data.humancellatlas.org'
    AZUL_PROD_URL = 'https://service.explore.data.humancellatlas.org'

    def __init__(self):
        deployment = os.environ['DEPLOYMENT_STAGE']
        if deployment == "prod":
            self.azul_url = self.AZUL_PROD_URL
        else:
            self.azul_url = self.AZUL_URL_TEMPLATE.format(deployment=deployment)
        self.https_session = requests.Session()
        azul_retries = Retry(status_forcelist=(500, 502, 503, 504))
        azul_adapter = requests.adapters.HTTPAdapter(max_retries=azul_retries)
        self.https_session.mount('https://', azul_adapter)

    def get_entities_by_project(self, entity_type, project_uuid):
        filters = {'file': {'projectId': {'is': [project_uuid]}}}
        entities = []
        size = 100
        # Yes, the value of the filters parameter is a Python literal, not JSON.
        # https://github.com/DataBiosphere/azul/issues/537
        params = dict(filters=str(filters), size=str(size))
        while True:
            url = self.azul_url + f'/repository/{entity_type}?' + urlencode(params, safe="{}/'")
            response = self.https_session.request('GET', url)
            response.raise_for_status()
            body = response.json()
            hits = body['hits']
            entities.extend(hits)
            pagination = body['pagination']
            search_after = pagination['search_after']
            if search_after is None:
                break
            params['search_after'] = search_after
            params['search_after_uid'] = pagination['search_after_uid']
        return entities
