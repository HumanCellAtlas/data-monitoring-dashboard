import os

import requests
from hca.util.pool import ThreadPool


DEPLOYMENT_STAGE = os.environ['DEPLOYMENT_STAGE']
STATUSES_TO_EXCLUDE_FROM_TRACKER = ['Invalid', 'Draft', 'Valid', 'Pending', 'Validating', 'Submitted']
PROJECT_NAME_STRINGS_TO_EXCLUDE_FROM_TRACKER = [
    f'{DEPLOYMENT_STAGE}/optimus/',
    f'{DEPLOYMENT_STAGE}/Smart-seq2/',
    f'{DEPLOYMENT_STAGE}/10x/',
    'integration/10x/',
    'integration/Smart-seq2',
    'SS2 1 Cell Integration Test',
    f'ss2_{DEPLOYMENT_STAGE}_test_',
    f'10x_{DEPLOYMENT_STAGE}_test_',
    'DCP_Infrastructure_Test_Do_Not_Use',
    'Q4_DEMO-project',
    'Glioblastoma_small'
]


class IngestAgent:

    INGEST_API_URL_TEMPLATE = "https://api.ingest.{}.data.humancellatlas.org"
    INGEST_API_PROD_URL = "https://api.ingest.data.humancellatlas.org"

    def __init__(self):
        if DEPLOYMENT_STAGE == "prod":
            self.base_url = self.INGEST_API_PROD_URL
        else:
            self.base_url = self.INGEST_API_URL_TEMPLATE.format(DEPLOYMENT_STAGE)

    def get_envelope(self, submission_id):
        url = f"{self.base_url}/submissionEnvelopes/{submission_id}"
        response = requests.get(url)
        response.raise_for_status()
        envelope = response.json()
        return envelope

    def get_project(self, submission_id):
        envelope = self.get_envelope(submission_id)
        project_url = envelope['_links']['projects']['href']
        response = requests.get(project_url)
        response.raise_for_status()
        body = response.json()
        if not body.get('_embedded'):
            return None
        project = body['_embedded']['projects'][0]
        return project

    # TODO consolidate logic in get_biomaterials and get_protocols
    def get_biomaterials(self, submission_id):
        biomaterials = []
        envelope = self.get_envelope(submission_id)
        biomaterials_url = f"{envelope['_links']['biomaterials']['href']}/?size=1000"
        while True:
            response = requests.get(biomaterials_url)
            response.raise_for_status()
            body = response.json()
            if not body.get('_embedded'):
                break
            biomaterials = biomaterials + body['_embedded']['biomaterials']
            links = body['_links']
            next_link = links.get('next')
            if not next_link:
                break
            biomaterials_url = next_link['href']
        return biomaterials

    # TODO consolidate logic in get_biomaterials and get_protocols
    def get_protocols(self, submission_id):
        protocols = []
        envelope = self.get_envelope(submission_id)
        protocols_url = f"{envelope['_links']['protocols']['href']}/?size=1000"
        while True:
            response = requests.get(protocols_url)
            response.raise_for_status()
            body = response.json()
            if not body.get('_embedded'):
                break
            protocols = protocols + body['_embedded']['protocols']
            links = body['_links']
            next_link = links.get('next')
            if not next_link:
                break
            protocols_url = next_link['href']
        return protocols

    def get_bundle_manifest_count(self, submission_id):
        envelope = self.get_envelope(submission_id)
        bundle_manifest_url = envelope['_links']['bundleManifests']['href']
        response = requests.get(bundle_manifest_url)
        response.raise_for_status()
        bundle_manifest_count = response.json()['page']['totalElements']
        return bundle_manifest_count

    def get_all_primary_submission_envelopes(self):
        all_envelopes = []
        url = f"{self.base_url}/submissionEnvelopes?size=1000"
        while True:
            response = requests.get(url)
            response.raise_for_status()
            body = response.json()
            envelopes = body['_embedded']['submissionEnvelopes']
            all_envelopes.extend(envelopes)
            print(f"Envelopes paged through: {len(all_envelopes)}")
            links = body['_links']
            next_link = links.get('next')
            if not next_link:
                break
            url = next_link['href']
        primary_submission_envelopes = self._parse_primary_envelopes_from_envelopes(all_envelopes)
        return primary_submission_envelopes

    # TODO Does not belong in ingest agent/dcplib. Move to ingest utils and write test.
    def get_submission_id_from_envelope(self, envelope):
        submission_id = envelope['_links']['self']['href'].split('/')[-1]
        return submission_id

    # TODO Does not belong in ingest agent/dcplib. Move to ingest utils and write test.
    def get_project_short_name_from_project(self, project):
        project_core = project['content']['project_core']
        if project_core.get('project_short_name'):
            project_short_name = project['content']['project_core']['project_short_name']
        else:
            project_short_name = project['content']['project_core']['project_shortname']
        return project_short_name

    # TODO Does not belong in ingest agent/dcplib. Move to ingest utils and write test.
    def get_project_title_from_project(self, project):
        project_core = project['content']['project_core']
        project_title = project_core['project_title']
        return project_title

    # TODO Does not belong in ingest agent/dcplib. Move to ingest utils and write test.
    def get_unique_species_set_from_biomaterials(self, biomaterials):
        project_species = set()
        for biomaterial in biomaterials:
            content = biomaterial['content']
            if content.get('genus_species'):
                genus_species = content['genus_species']
                for species in genus_species:
                    if species.get('ontology_label'):
                        project_species.add(species['ontology_label'])
                    elif species.get('text'):
                        project_species.add(species['text'])
        if len(project_species) == 0:
            raise Exception('No species found from biomaterials in this project')
        return sorted(project_species)

    # TODO Does not belong in ingest agent/dcplib. Move to ingest utils and write test.
    def get_unique_library_construction_methods_from_protocols(self, protocols):
        project_library_construction_methods = set()
        for protocol in protocols:
            content = protocol['content']
            if content.get('library_construction_method'):
                library_construction_method = content['library_construction_method']
                if library_construction_method.get('ontology_label'):
                    project_library_construction_methods.add(library_construction_method['ontology_label'])
                elif library_construction_method.get('text'):
                    project_library_construction_methods.add(library_construction_method['text'])
            elif content.get('library_construction_approach'):
                library_construction_approach = content['library_construction_approach']
                if library_construction_approach.get('ontology_label'):
                    project_library_construction_methods.add(library_construction_approach['ontology_label'])
                elif library_construction_approach.get('text'):
                    project_library_construction_methods.add(library_construction_approach['text'])
        if len(project_library_construction_methods) == 0:
            raise Exception('No library construction methods found from protocols in this project')
        return sorted(project_library_construction_methods)

    # TODO Does not belong in ingest agent/dcplib. Move to ingest utils and write test.
    def _project_short_name_in_exclusion_list(self, project_short_name):
        excluded = False
        for name in PROJECT_NAME_STRINGS_TO_EXCLUDE_FROM_TRACKER:
            if name in project_short_name:
                excluded = True
        return excluded

    # TODO Does not belong in ingest agent/dcplib. Move to ingest utils and write test.
    def get_primary_investigator_and_data_curator_from_project(self, project):
        primary_investigator = ''
        data_curator = ''
        contributors = project['content']['contributors']
        for contributor in contributors:
            project_role = contributor.get('project_role')
            if project_role:
                if contributor.get('contact_name'):
                    name = contributor['contact_name']
                else:
                    name = contributor['name']
                if type(project_role) == str:
                    role_ontology_label = project_role
                else:
                    role_ontology_label = project_role.get('ontology_label')
                if role_ontology_label == "principal investigator":
                    primary_investigator += f"{name}; "
                elif role_ontology_label == "data curator" or role_ontology_label == "Human Cell Atlas wrangler":
                    data_curator += f"{name}; "
        if primary_investigator == '':
            primary_investigator = 'N/A'
        if data_curator == '':
            data_curator = 'N/A'
        return primary_investigator, data_curator

    # TODO Does not belong in ingest agent/dcplib. Move to ingest utils and write test.
    def _parse_primary_envelopes_from_envelopes(self, envelopes):
        primary_submission_envelopes = []
        pool = ThreadPool()
        for envelope in envelopes:
            submission_status = envelope['submissionState']
            if submission_status not in STATUSES_TO_EXCLUDE_FROM_TRACKER:
                pool.add_task(self._append_to_input_list_if_project_present_for_envelope,
                              envelope, primary_submission_envelopes)
        pool.wait_for_completion()
        return primary_submission_envelopes

    # TODO Does not belong in ingest agent/dcplib. Move to ingest utils and write test.
    def _append_to_input_list_if_project_present_for_envelope(self, envelope, primary_submission_envelopes):
        submission_id = self.get_submission_id_from_envelope(envelope)
        project = self.get_project(submission_id)
        if project:
            project_short_name = self.get_project_short_name_from_project(project)
            if not self._project_short_name_in_exclusion_list(project_short_name):
                primary_submission_envelopes.append(envelope)
                print(f"Primary Submission Envelopes found: {len(primary_submission_envelopes)}({project_short_name})")
