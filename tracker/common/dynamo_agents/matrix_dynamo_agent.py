import os

from tracker.common.dynamo_agents.dynamo_agent import DynamoAgent
from tracker.common.dcp_agents.matrix_agent import MatrixAgent


class MatrixDynamoAgent(DynamoAgent):

    def __init__(self):
        super().__init__()
        deployment_stage = os.environ["DEPLOYMENT_STAGE"]
        self.dynamo_table_name = f"dcp-data-dashboard-matrix-info-{deployment_stage}"
        self.table_display_name = "matrix-info"
        self.matrix_agent = MatrixAgent()

    def create_dynamo_payload(self, project_uuid):
        print(f"creating matrix info payload for {project_uuid}")
        payload = {}
        payload['project_uuid'] = project_uuid
        payload['analysis_bundle_count'] = self.matrix_agent.get_bundle_count_for_project(project_uuid)
        payload['cell_count'] = self.matrix_agent.get_cell_count_for_project(project_uuid)
        return payload
