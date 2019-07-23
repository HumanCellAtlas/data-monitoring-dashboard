variable "deployment_stage" {
  type = "string"
}

variable "analysis_gcp_creds" {
  type = "string"
}

variable "allowed_subnet_ids" {
  type = "string"
}

variable "security_group_id" {
  type = "string"
}

variable "refresher_schedule_expression" {
  type = "string"
}

variable "data_refresher_image" {
  type = "string"
}

variable "cloudfront_id" {
  type = "string"
}
