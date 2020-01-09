terraform {
  required_version = "=0.11.13"

  backend "s3" {
    bucket  = "org-humancellatlas-data-tracker-infra"
    key     = "terraform/envs/integration/state.tfstate"
    encrypt = true
    region  = "us-east-1"
    profile = "hca"
  }
}

provider "aws" {
  version = ">= 1.31"
  region = "us-east-1"
  profile = "hca"
}

data "aws_caller_identity" "current" {}

module "data-monitoring" {
  source = "../../modules"
  deployment_stage =  var.deployment_stage
  analysis_gcp_creds =  var.analysis_gcp_creds
  allowed_subnet_ids =  var.allowed_subnet_ids
  security_group_id =  var.security_group_id
  account_id =  data.aws_caller_identity.current.account_id
  refresher_schedule_expression =  var.refresher_schedule_expression
  data_refresher_image =  var.data_refresher_image
  cloudfront_id =  var.cloudfront_id
  github_access_token =  var.github_access_token
}
