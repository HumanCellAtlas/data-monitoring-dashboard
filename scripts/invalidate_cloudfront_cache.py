import os
import sys
from time import time
sys.path.append(os.environ['PROJECT_ROOT'])

import boto3

from tracker.common.config import TrackerInfraConfig

client = boto3.client('cloudfront')


def main():
    """
    Invalidate cloudfront cache entry for tracker environment specified in ENV VAR 'DEPLOYMENT_STAGE'
    """
    cloudfront_id = TrackerInfraConfig().cloudfront_id
    response = client.create_invalidation(
        DistributionId=cloudfront_id,
        InvalidationBatch={
            'Paths': {
                'Quantity': 1,
                'Items': ['/*'],
            },
            'CallerReference': str(time()).replace(".", "")
        }
    )


if __name__ == '__main__':
    main()
