from collections import Counter
import os

from tracker.common.dynamo_agents.dynamo_agent import DynamoAgent


class IngestDynamoAgent(DynamoAgent):

    def __init__(self):
        super().__init__()
        deployment_stage = os.environ["DEPLOYMENT_STAGE"]
        self.dynamo_table_name = f"dcp-data-dashboard-ingest-info-{deployment_stage}"
        self.table_display_name = "ingest-info"

    def create_dynamo_payload(self, envelope, latest_primary_bundles, analysis_envelopes_map={}):
        print(f"creating ingest info payload for {envelope.submission_id}")
        payload = {}
        project = envelope.project()
        payload['submission_id'] = envelope.submission_id
        payload['submission_date'] = envelope.submission_date
        payload['project_uuid'] = project.uuid
        payload['project_short_name'] = project.short_name
        payload['project_title'] = project.title
        payload['submission_status'] = envelope.status
        payload['submission_bundles_exported_count'] = envelope.bundle_count()
        payload['species'] = self._get_project_species(envelope)
        payload['library_construction_methods'] = self._get_project_library_construction_methods(envelope)
        payload['primary_investigator'] = project.primary_investigator
        payload['data_curator'] = project.data_curator
        primary_state = self._determine_state_of_primary_data(envelope.status)
        payload['primary_state'] = primary_state
        envelope_statuses_count = self._aggregrate_analysis_envelopes_status_count(latest_primary_bundles, analysis_envelopes_map)
        for status, count in envelope_statuses_count.items():
            status_string = status + '_envelopes'
            payload[status_string] = count
        return payload

    def _aggregrate_analysis_envelopes_status_count(self, latest_primary_bundles, analysis_envelopes_map):
        envelope_statuses_count = Counter()
        for uuid, bundle in latest_primary_bundles.items():
            statuses = analysis_envelopes_map.get(uuid, [])
            for status in statuses:
                envelope_statuses_count[status] += 1
                envelope_statuses_count['Total'] += 1
        return envelope_statuses_count

    def _determine_state_of_primary_data(self, envelope_status):
        if envelope_status != 'Complete':
            primary_state = 'INCOMPLETE'
        else:
            primary_state = 'COMPLETE'
        return primary_state

    def _get_project_library_construction_methods(self, envelope):
        project_library_construction_methods = set()
        for protocol in envelope.protocols():
            method = protocol.library_construction_method
            if method:
                project_library_construction_methods.add(method.lower())
        return sorted(project_library_construction_methods)

    def _get_project_species(self, envelope):
        project_species = set()
        for biomaterial in envelope.biomaterials():
            for species in biomaterial.species:
                project_species.add(species.lower())
        return sorted(project_species)
