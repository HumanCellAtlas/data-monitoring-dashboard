resource "aws_dynamodb_table" "ingest_tracking_stats" {
  name           = "dcp-data-dashboard-ingest-info-${var.deployment_stage}"
  read_capacity  = 25
  write_capacity = 25
  hash_key       = "submission_id"

  attribute {
    name = "submission_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "matrix_tracking_stats" {
  name           = "dcp-data-dashboard-matrix-info-${var.deployment_stage}"
  read_capacity  = 25
  write_capacity = 25
  hash_key       = "project_key"

  attribute {
    name = "project_key"
    type = "S"
  }
}

resource "aws_dynamodb_table" "azul_tracking_stats" {
  name           = "dcp-data-dashboard-azul-info-${var.deployment_stage}"
  read_capacity  = 25
  write_capacity = 25
  hash_key       = "project_key"

  attribute {
    name = "project_key"
    type = "S"
  }
}

resource "aws_dynamodb_table" "pipeline_tracking_stats" {
  name           = "dcp-data-dashboard-pipeline-info-${var.deployment_stage}"
  read_capacity  = 25
  write_capacity = 25
  hash_key       = "project_key"

  attribute {
    name = "project_key"
    type = "S"
  }
}

resource "aws_dynamodb_table" "dss_tracking_stats" {
  name           = "dcp-data-dashboard-dss-info-${var.deployment_stage}"
  read_capacity  = 25
  write_capacity = 25
  hash_key       = "project_key"

  attribute {
    name = "project_key"
    type = "S"
  }
}
