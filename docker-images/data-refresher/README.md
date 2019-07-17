# Data refresh docker image

Purpose: This directory builds the data refresh docker image that is deployed via ecs + fargate. The instructions in this image refresh the statistics for all projects x components.

## How to test locally
1) make build
2) source config/environment in repo root or set DEPLOYMENT_STAGE env variable manually
3) make test
