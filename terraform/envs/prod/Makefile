DEPLOYMENT_STAGE=prod
TF_STATE_BUCKET=org-humancellatlas-data-dashboard-prod-infra
S3_TFVARS_FILE=s3://$(TF_STATE_BUCKET)/terraform/envs/$(DEPLOYMENT_STAGE)/terraform.tfvars

default: plan

init:
	terraform init

plan:
	terraform plan -detailed-exitcode

apply:
	terraform apply --backup=-

destroy:
	terraform destroy --backup=-
