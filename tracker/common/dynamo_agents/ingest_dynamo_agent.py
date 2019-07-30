import os

from tracker.common.dynamo_agents.dynamo_agent import DynamoAgent
from tracker.common.dcp_agents.ingest_agent import IngestAgent


class IngestDynamoAgent(DynamoAgent):

    def __init__(self):
        super().__init__()
        deployment_stage = os.environ["DEPLOYMENT_STAGE"]
        self.dynamo_table_name = f"dcp-data-dashboard-ingest-info-{deployment_stage}"
        self.table_display_name = "ingest-info"
        self.ingest_agent = IngestAgent()

    def create_and_save_dynamo_payload(self, submission_id):
        print(f"creating ingest info payload for {submission_id}")
        payload = {}
        envelope = self.ingest_agent.get_envelope(submission_id)
        project = self.ingest_agent.get_project(submission_id)
        biomaterials = self.ingest_agent.get_biomaterials(submission_id)
        protocols = self.ingest_agent.get_protocols(submission_id)
        bundle_manifest_count = self.ingest_agent.get_bundle_manifest_count(submission_id)
        project_uuid = project['uuid']['uuid']
        payload['submission_id'] = submission_id
        payload['submission_date'] = envelope['submissionDate']
        payload['project_uuid'] = project_uuid
        payload['project_short_name'] = self.ingest_agent.get_project_short_name_from_project(project)
        payload['project_title'] = self.ingest_agent.get_project_title_from_project(project)
        payload['submission_status'] = envelope['submissionState']
        payload['submission_bundles_exported_count'] = bundle_manifest_count
        payload['species'] = self.ingest_agent.get_unique_species_set_from_biomaterials(biomaterials)
        payload['library_construction_methods'] = self.ingest_agent.get_unique_library_construction_methods_from_protocols(protocols)
        primary_investigator, data_curator = self.ingest_agent.get_primary_investigator_and_data_curator_from_project(project)
        payload['primary_investigator'] = primary_investigator
        payload['data_curator'] = data_curator
        self.write_item_to_dynamo(payload)
        return project_uuid
