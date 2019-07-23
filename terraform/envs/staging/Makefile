DEPLOYMENT_STAGE=staging
TF_STATE_BUCKET=org-humancellatlas-data-tracker-infra
S3_TFVARS_FILE=s3://$(TF_STATE_BUCKET)/terraform/envs/$(DEPLOYMENT_STAGE)/terraform.tfvars

default: plan

init:
	terraform init

plan:
	make retrieve-vars
	terraform plan -detailed-exitcode

apply:
	make retrieve-vars
	terraform apply --backup=-

destroy:
	terraform destroy --backup=-

retrieve-vars:
	aws s3 cp $(S3_TFVARS_FILE) terraform.tfvars

upload-vars:
	aws s3 cp terraform.tfvars $(S3_TFVARS_FILE)
