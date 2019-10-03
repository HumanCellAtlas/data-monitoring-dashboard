from collections import defaultdict
import os

from tracker.common.dynamo_agents.dynamo_agent import DynamoAgent


class IngestAnalysisDynamoAgent(DynamoAgent):

    def __init__(self):
        super().__init__()
        deployment_stage = os.environ["DEPLOYMENT_STAGE"]
        self.dynamo_table_name = f"dcp-data-dashboard-ingest-analysis-envelopes-info-{deployment_stage}"
        self.table_display_name = "dcp-data-dashboard-ingest-analysis-envelopes-info"

    def create_dynamo_payload(self, envelope):
        print(f"creating ingest analysis envelope info payload for {envelope.submission_id}")
        payload = {}
        payload['submission_id'] = envelope.submission_id
        payload['submission_date'] = envelope.submission_date
        payload['update_date'] = envelope.update_date
        payload['submission_status'] = envelope.status
        payload['failures_present'] = len(envelope.submission_errors()) > 0
        payload['input_bundle_uuids'] = self._get_input_bundles(envelope)
        payload['submission_bundles_exported_count'] = envelope.bundle_count()
        return payload

    def create_analysis_envelopes_bundle_map(self):
        analysis_envelopes_map = defaultdict(list)
        analysis_envelopes = self.get_all_items()['records']
        for envelope in analysis_envelopes:
            input_bundle_uuids = envelope['input_bundle_uuids']
            for bundle_uuid in input_bundle_uuids:
                analysis_envelopes_map[bundle_uuid].append(envelope)
        return analysis_envelopes_map

    def _get_input_bundles(self, envelope):
        input_bundle_uuids = []
        processes = envelope.processes()
        for process in processes:
            input_bundles = process.input_bundles
            for bundle in input_bundles:
                input_bundle_uuids.append(bundle)
        return input_bundle_uuids
