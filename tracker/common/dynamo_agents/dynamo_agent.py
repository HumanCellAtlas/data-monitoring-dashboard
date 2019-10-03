import os
from collections import defaultdict
from datetime import datetime

import boto3

DYNAMO = boto3.resource("dynamodb", region_name=os.environ['AWS_DEFAULT_REGION'])


class DynamoAgent:

    def __init__(self):
        # Variables set by child class
        self.dynamo_table_name = None
        self.table_display_name = None

    def write_item_to_dynamo(self, payload):
        print(f"saving payload {payload} to {self.dynamo_table_name}")
        now = datetime.utcnow()
        payload['updated_at'] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        table = DYNAMO.Table(self.dynamo_table_name)
        table.put_item(Item=payload)
        print(f"saved payload {payload} to {self.dynamo_table_name}")

    def get_item_from_dynamo(self, key, value):
        table = DYNAMO.Table(self.dynamo_table_name)
        table_key = {key: value}
        item = table.get_item(
            Key=table_key,
            ConsistentRead=True
        )['Item']
        payload = {'record': item, 'table_name': self.table_display_name}
        return payload

    def get_all_items(self):
        all_results = []
        table = DYNAMO.Table(self.dynamo_table_name)
        scan_results = table.scan()
        all_results = all_results + scan_results['Items']
        while scan_results.get('LastEvaluatedKey'):
            scan_results = table.scan(ExclusiveStartKey=scan_results['LastEvaluatedKey'])
            all_results = all_results + scan_results['Items']
        payload = {'records': all_results, 'table_name': self.table_display_name}
        return payload

    def create_project_map(self):
        project_map = defaultdict(list)
        records = self.get_all_items()['records']
        for record in records:
            project_uuid = record['project_uuid']
            project_map[project_uuid].append(record)
        return project_map

    def create_dynamo_payload(self, *args, **kwargs):
        raise Exception("func create_dynamo_payload not implemented in child class")
