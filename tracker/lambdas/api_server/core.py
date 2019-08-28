from collections import defaultdict

from tracker.common.dynamo_agents.ingest_dynamo_agent import IngestDynamoAgent
from tracker.common.dynamo_agents.dss_dynamo_agent import DSSDynamoAgent
from tracker.common.dynamo_agents.matrix_dynamo_agent import MatrixDynamoAgent
from tracker.common.dynamo_agents.analysis_dynamo_agent import AnalysisDynamoAgent
from tracker.common.dynamo_agents.azul_dynamo_agent import AzulDynamoAgent
from tracker.common.dynamo_agents.project_dynamo_agent import ProjectDynamoAgent

DYNAMO_REFRESHERS = [ProjectDynamoAgent, IngestDynamoAgent, DSSDynamoAgent, MatrixDynamoAgent, AnalysisDynamoAgent, AzulDynamoAgent]


def get_projects():
    projects_dict = defaultdict(dict)
    projects_list = []
    for dynamo_agent in DYNAMO_REFRESHERS:
        dynamo_handler = dynamo_agent()
        payload = dynamo_handler.get_all_items()
        projects_dict = _parse_by_project_uuid(projects_dict, payload['records'], payload['table_name'])
    for project_uuid, project_info_dict in projects_dict.items():
        project_info_dict['project_uuid'] = project_uuid
        projects_list.append(project_info_dict)
    return projects_list


def get_project(project_uuid):
    project_payload = {}
    project_payload['project_uuid'] = project_uuid
    for dynamo_agent in DYNAMO_REFRESHERS:
        dynamo_handler = dynamo_agent()
        payload = dynamo_handler.get_item_from_dynamo('project_uuid', project_uuid)
        record = payload['record']
        del record['project_uuid']
        table_name = payload['table_name']
        project_payload[table_name] = record
    return project_payload


def _parse_by_project_uuid(target_project_dict, source_records_list, table_name):
    for record in source_records_list:
        project_uuid = record['project_uuid']
        target_project_dict[project_uuid][table_name] = record

    return target_project_dict
