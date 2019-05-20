import os

from hca import HCAConfig
from hca.dss import DSSClient
from hca.util.exceptions import SwaggerAPIException

# import requests

# from tracker.common.exceptions import TrackerException


class DSSAgent:
    DSS_SWAGGER_URL_TEMPLATE = "https://dss.{deployment}.data.humancellatlas.org/v1/swagger.json"
    DSS_PROD_SWAGGER_URL = "https://dss.data.humancellatlas.org/v1/swagger.json"

    def __init__(self):
        deployment = os.environ["DEPLOYMENT_STAGE"]
        if deployment == "prod":
            swagger_url = self.DSS_PROD_SWAGGER_URL
        else:
            swagger_url = self.DSS_SWAGGER_URL_TEMPLATE.format(deployment=deployment)

        dss_config = HCAConfig()
        dss_config['DSSClient'] = {}
        dss_config['DSSClient']['swagger_url'] = swagger_url
        self.client = DSSClient(config=dss_config)

    def primary_bundle_count_for_project(self, project_key, replica='aws'):
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "files.project_json.provenance.document_id": project_key
                            }
                        },
                        {
                            "bool": {
                                "must_not": {
                                    "match": {
                                        "files.analysis_process_json.type.text": "analysis"
                                    }
                                }
                            }
                        },
                        {
                            "bool": {
                                "must_not": {
                                    "match": {
                                        "files.analysis_process_json.process_type.text": "analysis"
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        }
        results = self.search(query, replica)
        total_hits = results['total_hits']
        return total_hits

    def total_bundle_count_for_project(self, project_key, replica='aws'):
        query = {
            "query": {
                "bool": {
                    "must": {
                        "match": {
                            "files.project_json.provenance.document_id": project_key
                        }
                    }
                }
            }
        }
        results = self.search(query, replica)
        if results and results.get('total_hits'):
            total_hits = results['total_hits']
        else:
            total_hits = 0
        return total_hits

    def search(self, query, replica='aws'):
        try:
            response = self.client.post_search(replica=replica, es_query=query)
            return response
        except SwaggerAPIException:
            return []
