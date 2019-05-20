import os

from tracker.common.dynamo_refreshers.dynamo_refresher import DynamoRefresher
from tracker.common.agents.ingest_agent import IngestAgent


class IngestDynamoRefresher(DynamoRefresher):

    def __init__(self):
        super().__init__()
        deployment_stage = os.environ["DEPLOYMENT_STAGE"]
        self.dynamo_table_name = f"dcp-data-dashboard-ingest-info-{deployment_stage}"
        self.ingest_agent = IngestAgent()

    def create_and_save_dynamo_payload(self, submission_id):
        print(f"creating ingest info payload for {submission_id}")
        payload = {}
        envelope = self.ingest_agent.get_envelope(submission_id)
        project = self.ingest_agent.get_project(submission_id)
        bundle_manifest_count = self.ingest_agent.get_bundle_manifest_count(submission_id)
        payload['submission_id'] = submission_id
        payload['submission_date'] = envelope['submissionDate']
        payload["project_key"] = project['uuid']['uuid']
        payload["project_short_name"] = self.ingest_agent.get_project_short_name_from_project(project)
        payload["submission_status"] = envelope['submissionState']
        payload["submission_bundles_exported_count"] = bundle_manifest_count
        self.write_item_to_dynamo(payload)
