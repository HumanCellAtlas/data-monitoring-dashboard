import os

from tracker.common.dynamo_agents.dynamo_agent import DynamoAgent
from tracker.common.dcp_agents.azul_agent import AzulAgent


class AzulDynamoAgent(DynamoAgent):

    def __init__(self):
        super().__init__()
        deployment_stage = os.environ["DEPLOYMENT_STAGE"]
        self.dynamo_table_name = f"dcp-data-dashboard-azul-info-{deployment_stage}"
        self.table_display_name = "azul-info"
        self.azul_agent = AzulAgent()

    def create_dynamo_payload(self, project_uuid):
        print(f"creating azul info payload for {project_uuid}")
        bundles = self.azul_agent.get_entities_by_project('bundles', project_uuid)
        primary_bundle_count = 0
        analysis_bundle_count = 0
        for bundle in bundles:
            workflow = bundle['protocols'][0]['workflow']
            if workflow:
                analysis_bundle_count += 1
            else:
                primary_bundle_count += 1
        payload = {}
        payload['project_uuid'] = project_uuid
        payload['primary_bundle_count'] = primary_bundle_count
        payload['analysis_bundle_count'] = analysis_bundle_count
        return payload
