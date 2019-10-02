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
        payload['update_date'] = envelope.update_date
        payload['project_uuid'] = project.uuid
        payload['project_short_name'] = project.short_name
        payload['project_title'] = project.title
        payload['submission_status'] = envelope.status
        payload['submission_bundles_exported_count'] = envelope.bundle_count()
        # This submission has the incorrect bundle count but has been resolved. Manually overriding.
        if envelope.submission_id == '5cda8757d96dad000856d2ae':
            payload['submission_bundles_exported_count'] = '3514'
        payload['species'] = self._get_project_species(envelope)
        payload['library_construction_methods'] = self._get_project_library_construction_methods(envelope)
        payload['primary_investigator'] = project.primary_investigator
        payload['data_curator'] = project.data_curator
        payload['failures_present'] = len(envelope.submission_errors()) > 0
        primary_state = self._determine_state_of_primary_data(envelope.status)
        payload['primary_state'] = primary_state
        envelope_statuses_count, latest_analysis_envelope_update_date = self._aggregrate_analysis_envelopes_stats(latest_primary_bundles,
                                                                                                                  analysis_envelopes_map)
        for status, count in envelope_statuses_count.items():
            status_string = status + '_envelopes'
            payload[status_string] = count
        payload['latest_analysis_envelope_update_date'] = latest_analysis_envelope_update_date
        return payload

    def _aggregrate_analysis_envelopes_stats(self, latest_primary_bundles, analysis_envelopes_map):
        latest_analysis_envelope_update_date = ''
        envelope_statuses_count = Counter()
        envelope_statuses_count['Total'] = 0
        for uuid, bundle in latest_primary_bundles.items():
            envelopes = analysis_envelopes_map.get(uuid, [])
            for envelope in envelopes:
                if envelope['update_date'] > latest_analysis_envelope_update_date:
                    latest_analysis_envelope_update_date = envelope['update_date']
                status = envelope['submission_status']
                envelope_statuses_count[status] += 1
                envelope_statuses_count['Total'] += 1
        if latest_analysis_envelope_update_date == '':
            latest_analysis_envelope_update_date = 'N/A'
        return envelope_statuses_count, latest_analysis_envelope_update_date

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
