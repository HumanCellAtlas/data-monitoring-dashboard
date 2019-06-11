import os
from datetime import datetime

import boto3

DYNAMO = boto3.resource("dynamodb", region_name=os.environ['AWS_DEFAULT_REGION'])


class DynamoAgent:

    def __init__(self):
        # Dynamo table name set by child class
        self.dynamo_table_name = None

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
        return item

    def get_all_items(self):
        table = DYNAMO.Table(self.dynamo_table_name)
        results = table.scan()
        if table.item_count > len(results['Items']):
            raise Exception(f"Table scan for {self.dynamo_table_name} did not retrieve complete results")
        payload = {'records': results['Items'], 'table_name': self.dynamo_table_name}
        return payload

    def create_dynamo_payload(self, submission_id):
        raise Exception("func create_dynamo_payload not implemented in child class")
