terraform {
  required_version = "=0.11.11"

  backend "s3" {
    bucket  = "org-humancellatlas-data-dashboard-prod-infra"
    key     = "terraform/envs/prod/state.tfstate"
    encrypt = true
    region  = "us-east-1"
    profile = "hca-prod"
  }
}

provider "aws" {
  version = ">= 1.31"
  region = "us-east-1"
  profile = "hca-prod"
}

module "data-monitoring" {
  source = "../../modules"
  deployment_stage = "${var.deployment_stage}"
}
