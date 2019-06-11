from collections import defaultdict

from tracker.common.dynamo_agents.ingest_dynamo_agent import IngestDynamoAgent
from tracker.common.dynamo_agents.dss_dynamo_agent import DSSDynamoAgent
from tracker.common.dynamo_agents.matrix_dynamo_agent import MatrixDynamoAgent
from tracker.common.dynamo_agents.analysis_dynamo_agent import AnalysisDynamoAgent
from tracker.common.dynamo_agents.azul_dynamo_agent import AzulDynamoAgent

DYNAMO_REFRESHERS = [IngestDynamoAgent, DSSDynamoAgent, MatrixDynamoAgent, AnalysisDynamoAgent, AzulDynamoAgent]


def get_projects():
    projects = defaultdict(dict)
    for dynamo_agent in DYNAMO_REFRESHERS:
        dynamo_handler = dynamo_agent()
        payload = dynamo_handler.get_all_items()
        projects = _parse_by_project_uuid(projects, payload['records'], payload['table_name'])
    return projects


def _parse_by_project_uuid(target_project_dict, source_records_list, table_name):
    for record in source_records_list:
        project_uuid = record['project_uuid']
        target_project_dict[project_uuid][table_name] = record
    return target_project_dict
