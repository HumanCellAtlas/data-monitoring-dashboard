[![Travis (.com) branch](https://img.shields.io/travis/com/HumanCellAtlas/data-monitoring-dashboard/master.svg?label=Unit%20Test%20on%20Travis%20CI%20&style=flat-square&logo=Travis)](https://travis-ci.com/HumanCellAtlas/data-monitoring-dashboard)
![Github](https://img.shields.io/badge/python-3.6%20%7C%203.7-green.svg?style=flat-square&logo=python&colorB=blue)

# data-monitoring-dashboard

## Currently deployed
prod: https://tracker.data.humancellatlas.org
staging: https://tracker.staging.data.humancellatlas.org
integration: https://tracker.integration.data.humancellatlas.org

## How to run the server locally for testing
1. `export DEPLOYMENT_STAGE=integration` (or `staging` or `prod`)
2. `make -C chalice build`
3. `scripts/run_local_server`

The front-end will be served on http://127.0.0.1:8000 and the API on http://127.0.0.1:9000.
Press Ctrl-C to quit the server.

## Technical Architecture Diagram
Coming soon

## How to set up dev environment
1. `git clone https://github.com/HumanCellAtlas/data-monitoring-dashboard.git`
2. `cd data-monitoring-dashboard`
3. `pip install -r requirements-dev.txt`

## How to run functional tests
1. `export DEPLOYMENT_STAGE=ENVNAME` where ENVNAME is the name of the environment you are running tests for
2. `source config/environment`
3. `make functional-tests`

## How to run integration tests
Coming soon

## How to run unit tests
Coming soon

## How to setup and deploy to a new environment
1. Setup new terraform dir at terraform/envs copying another environment. Replace environment references in main.tf and Makefile.
2. Create new terraform.tfvars following `terraform/envs/prod/terraform.tfvars.example`. Set `cloudfront_id` to `N/A`.
3. `make upload-vars` from `terraform/envs/ENVNAME`
3. `make apply` from `terraform/envs/ENVNAME`
4. `make deploy_api` from the repo root
5. Setup api cdn, route 53, and cloudfront following existing environment setup.
6. Replace `cloudfront_id` at `terraform/envs/ENVNAME/terraform.tfvars` with value from cloudfront setup from prior step.
7. `make upload-vars` from `terraform/envs/ENVNAME`
8. `make apply` from `terraform/envs/ENVNAME`
9. `make deploy_frontend` from repo root
10. check https://tracker.ENVNAME.data.humancellatlas.org

## How to deploy api and frontend to existing environment
1. `export DEPLOYMENT_STAGE=ENVNAME` where ENVNAME is the name of the environment you are deploying to
2. `source config/environment`
3. `make deploy`

## How to build and deploy data refresher docker image to existing environment
1. Follow the instructions at https://github.com/HumanCellAtlas/data-monitoring-dashboard/tree/master/docker-images/data-refresher to build and push a new image to dockerhub.
2. cd `terraform/envs/ENVNAME` where ENVNAME is the name of the environment you are deploying to
3. make `retrieve-vars`
4. Replace `data_refresher_image` in `terraform.tfvars` with new image you built and pushed in step 1
5. `make upload-vars`
6. `make apply`

## How to get test data for development
Coming soon
