resource "aws_secretsmanager_secret" "tracker_secrets" {
  name = "dcp/tracker/${var.deployment_stage}/infra"
}

resource "aws_secretsmanager_secret_version" "tracker_secrets" {
  secret_id = "${aws_secretsmanager_secret.tracker_secrets.id}"
  secret_string = <<SECRETS_JSON
{
  "analysis_gcp_creds": "${var.analysis_gcp_creds}"
}
SECRETS_JSON
}
