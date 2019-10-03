resource "aws_dynamodb_table" "ingest-analysis-envelopes" {
  name           = "dcp-data-dashboard-ingest-analysis-envelopes-info-${var.deployment_stage}"
  read_capacity  = 25
  write_capacity = 25
  hash_key       = "submission_id"

  attribute {
    name = "submission_id"
    type = "S"
  }
}

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
  hash_key       = "project_uuid"

  attribute {
    name = "project_uuid"
    type = "S"
  }
}

resource "aws_dynamodb_table" "azul_tracking_stats" {
  name           = "dcp-data-dashboard-azul-info-${var.deployment_stage}"
  read_capacity  = 25
  write_capacity = 25
  hash_key       = "project_uuid"

  attribute {
    name = "project_uuid"
    type = "S"
  }
}

resource "aws_dynamodb_table" "analysis_tracking_stats" {
  name           = "dcp-data-dashboard-analysis-info-${var.deployment_stage}"
  read_capacity  = 25
  write_capacity = 25
  hash_key       = "project_uuid"

  attribute {
    name = "project_uuid"
    type = "S"
  }
}

resource "aws_dynamodb_table" "dss_tracking_stats" {
  name           = "dcp-data-dashboard-dss-info-${var.deployment_stage}"
  read_capacity  = 25
  write_capacity = 25
  hash_key       = "project_uuid"

  attribute {
    name = "project_uuid"
    type = "S"
  }
}

resource "aws_dynamodb_table" "overall_project_stats" {
  name           = "dcp-data-dashboard-project-info-${var.deployment_stage}"
  read_capacity  = 25
  write_capacity = 25
  hash_key       = "project_uuid"

  attribute {
    name = "project_uuid"
    type = "S"
  }
}
