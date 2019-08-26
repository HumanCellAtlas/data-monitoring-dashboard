import os

from dcplib.config import Config
try:
    import psycopg2 as pg
except:
    print("Skipping import of psycopg2")


class MatrixRedshiftConfig(Config):

    def __init__(self, *args, **kwargs):
        super().__init__(component_name='matrix', secret_name='database', **kwargs)


class MatrixAgent:

    def __init__(self):
        self.deployment = os.environ["DEPLOYMENT_STAGE"]
        self.redshift_config = MatrixRedshiftConfig()

    def get_cell_count_for_project(self, project_uuid):
        query = f"select count(*) from cell where projectkey = '{project_uuid}'"
        results = self._run_query(query)
        cell_count = results[0][0]
        return cell_count

    def get_bundles_for_project(self, project_uuid):
        query = f"select * from (select distinct(analysis.analysiskey), analysis.bundle_fqid \
            from analysis LEFT OUTER JOIN cell on analysis.analysiskey = cell.analysiskey \
            where cell.projectkey = '{project_uuid}');"
        results = self._run_query(query)
        return results

    @property
    def readonly_database_uri(self):
        return self.redshift_config.readonly_database_uri

    def _run_query(self, query):
        conn = pg.connect(self.readonly_database_uri)
        results = []
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        conn.commit()
        conn.close()
        return results
