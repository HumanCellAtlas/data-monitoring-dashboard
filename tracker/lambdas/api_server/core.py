from collections import defaultdict

from tracker.common.dynamo_refreshers.ingest_dynamo_refresher import IngestDynamoRefresher
from tracker.common.dynamo_refreshers.dss_dynamo_refresher import DSSDynamoRefresher
from tracker.common.dynamo_refreshers.matrix_dynamo_refresher import MatrixDynamoRefresher
from tracker.common.dynamo_refreshers.pipeline_dynamo_refresher import PipelineDynamoRefresher
from tracker.common.dynamo_refreshers.azul_dynamo_refresher import AzulDynamoRefresher


def get_projects():
    projects = defaultdict(dict)
    dynamo_refreshers = [IngestDynamoRefresher, DSSDynamoRefresher, MatrixDynamoRefresher, PipelineDynamoRefresher, AzulDynamoRefresher]
    for dynamo_refresher in dynamo_refreshers:
        dynamo_handler = dynamo_refresher()
        payload = dynamo_handler.get_all_items()
        projects = _parse_by_project_key(projects, payload['records'], payload['table_name'])
    return projects


def _parse_by_project_key(target_project_dict, source_records_list, table_name):
    for record in source_records_list:
        project_key = record['project_key']
        del record['project_key']
        target_project_dict[project_key][table_name] = record
    return target_project_dict
