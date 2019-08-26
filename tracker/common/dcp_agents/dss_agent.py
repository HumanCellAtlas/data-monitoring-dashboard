import os

from hca import HCAConfig
from hca.dss import DSSClient
from hca.util.exceptions import SwaggerAPIException


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

    def get_primary_bundles_for_project(self, project_uuid, replica):
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "files.project_json.provenance.document_id": project_uuid
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
        bundles = self._search_and_return_full_bundle_payload(query, replica)
        return bundles

    def get_analysis_bundles_for_project(self, project_uuid, replica):
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "files.project_json.provenance.document_id": project_uuid
                            }
                        },
                        {
                            "bool": {
                                "should": [
                                    {
                                        "match": {
                                            "files.analysis_process_json.type.text": "analysis"
                                        }
                                    },
                                    {
                                        "match": {
                                            "files.analysis_process_json.process_type.text": "analysis"
                                        }
                                    }
                                ],
                                "minimum_number_should_match": 1
                            }
                        }
                    ]
                }
            }
        }
        bundles = self._search_and_return_full_bundle_payload(query, replica)
        return bundles

    def _search_and_return_full_bundle_payload(self, query, replica):
        bundles = []
        for result in self.search(query, replica):
            bundle = {}
            bundle_fqid = result['bundle_fqid']
            bundle['fqid'] = bundle_fqid
            bundle['uuid'] = bundle_fqid.split('.')[0]
            bundle['version'] = bundle_fqid.split('.')[1]
            bundles.append(bundle)
        return bundles

    def search(self, query, replica='aws'):
        try:
            response = self.client.post_search.iterate(replica=replica, es_query=query)
            return response
        except SwaggerAPIException:
            return []
