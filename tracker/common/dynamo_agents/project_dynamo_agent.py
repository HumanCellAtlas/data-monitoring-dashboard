import os

from tracker.common.dynamo_agents.dynamo_agent import DynamoAgent


class ProjectDynamoAgent(DynamoAgent):

    def __init__(self):
        super().__init__()
        deployment_stage = os.environ["DEPLOYMENT_STAGE"]
        self.dynamo_table_name = f"dcp-data-dashboard-project-info-{deployment_stage}"
        self.table_display_name = "project-info"

    def create_dynamo_payload(self, ingest_info, dss_info, azul_info, analysis_info, matrix_info):
        payload = {}
        payload['project_uuid'] = ingest_info['project_uuid']

        primary_state = self._determine_project_primary_state(ingest_info, dss_info, azul_info)
        analysis_state = self._determine_project_analysis_state(primary_state, dss_info, analysis_info, azul_info)
        matrix_state = matrix_info['analysis_state']
        project_state = self._determine_project_overall_state(primary_state, analysis_state, matrix_state)

        payload['primary_state'] = primary_state
        payload['analysis_state'] = analysis_state
        payload['matrix_state'] = matrix_state
        payload['project_state'] = project_state

        return payload

    def _determine_project_primary_state(self, ingest_info, dss_info, azul_info):
        if ingest_info['primary_state'] == 'INCOMPLETE' or dss_info['primary_state'] == 'INCOMPLETE' or azul_info['primary_state'] == 'INCOMPLETE':
            return 'INCOMPLETE'
        elif azul_info['primary_state'] == 'OUT_OF_DATE':
            return 'OUT_OF_DATE'
        else:
            return 'COMPLETE'

    def _determine_project_analysis_state(self, primary_state, dss_info, analysis_info, azul_info):
        if primary_state == 'OUT_OF_DATE' or primary_state == 'INCOMPLETE':
            return primary_state
        elif (analysis_info['analysis_state'] == 'INCOMPLETE' or
                dss_info['analysis_state'] == 'INCOMPLETE' or
                azul_info['analysis_state'] == 'INCOMPLETE'):
            return 'INCOMPLETE'
        elif analysis_info['analysis_state'] == 'OUT_OF_DATE' or azul_info['analysis_state'] == 'OUT_OF_DATE':
            return 'OUT_OF_DATE'
        else:
            return 'COMPLETE'

    def _determine_project_overall_state(self, primary_state, analysis_state, matrix_state):
        if primary_state == 'INCOMPLETE' or analysis_state == 'INCOMPLETE' or matrix_state == 'INCOMPLETE':
            return 'INCOMPLETE'
        elif primary_state == 'OUT_OF_DATE' or analysis_state == 'OUT_OF_DATE' or matrix_state == 'OUT_OF_DATE':
            return 'OUT_OF_DATE'
        else:
            return 'COMPLETE'
