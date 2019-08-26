resource "aws_ecs_task_definition" "data_refresher" {
  family                = "data-monitoring-data-refresher-${var.deployment_stage}"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn = "${aws_iam_role.task_executor.arn}"
  task_role_arn = "${aws_iam_role.data_refresher.arn}"
  cpu = "4096"
  memory = "8192"
  network_mode = "awsvpc"
  container_definitions = <<DEFINITION
[
  {
    "environment": [
      {
        "name": "DEPLOYMENT_STAGE",
        "value": "${var.deployment_stage}"
      }
    ],
    "image": "${var.data_refresher_image}",
    "name": "data-monitoring-data-refresher-${var.deployment_stage}",
    "essential": true,
    "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "${aws_cloudwatch_log_group.data_refresher.name}",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
    }
  }
]
DEFINITION
}

resource "aws_cloudwatch_log_group" "data_refresher" {
  name              = "/aws/service/data-monitoring-data-refresher-${var.deployment_stage}"
  retention_in_days = 1827
}

resource "aws_iam_role" "task_executor" {
  name = "data-monitoring-task-execution-role-${var.deployment_stage}"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "ecs.amazonaws.com",
          "ecs-tasks.amazonaws.com",
          "events.amazonaws.com"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "task_executor_ecs" {
  role = "${aws_iam_role.task_executor.name}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "AWS-Events-Invoke" {
  name = "data-monitoring-refresher-event-invoke-${var.deployment_stage}"
  role = "${aws_iam_role.task_executor.id}"
  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecs:RunTask"
            ],
            "Resource": [
                "arn:aws:ecs:*:${var.account_id}:task-definition/data-monitoring-data-refresher-${var.deployment_stage}:*"
            ],
            "Condition": {
                "ArnLike": {
                    "ecs:cluster": "arn:aws:ecs:*:${var.account_id}:cluster/data-monitoring-data-refresher-${var.deployment_stage}"
                }
            }
        },
        {
            "Effect": "Allow",
            "Action": "iam:PassRole",
            "Resource": [
                "*"
            ],
            "Condition": {
                "StringLike": {
                    "iam:PassedToService": "ecs-tasks.amazonaws.com"
                }
            }
        }
    ]
}
EOF
}

resource "aws_iam_role" "data_refresher" {
  name = "data-monitoring-data-refresher-${var.deployment_stage}"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "ecs-tasks.amazonaws.com"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "data_refresher" {
  name = "data-monitoring-data-refresher-policy-${var.deployment_stage}"
  role = "${aws_iam_role.data_refresher.id}"
  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "${aws_cloudwatch_log_group.data_refresher.arn}:*",
            "Effect": "Allow"
        },
        {
            "Effect": "Allow",
            "Action": "logs:CreateLogGroup",
            "Resource": "${aws_cloudwatch_log_group.data_refresher.arn}"
        },
        {
          "Effect": "Allow",
          "Action": [
            "secretsmanager:DescribeSecret",
            "secretsmanager:GetSecretValue"
          ],
          "Resource": [
            "arn:aws:secretsmanager:us-east-1:${var.account_id}:secret:dcp/matrix/${var.deployment_stage}/*",
            "arn:aws:secretsmanager:us-east-1:${var.account_id}:secret:dcp/tracker/${var.deployment_stage}/*"
          ]
        },
        {
          "Sid": "DynamoPolicy",
          "Effect": "Allow",
          "Action": [
            "dynamodb:UpdateItem",
            "dynamodb:GetItem",
            "dynamodb:PutItem"
          ],
          "Resource": [
            "arn:aws:dynamodb:us-east-1:${var.account_id}:table/dcp-data-dashboard-ingest-info-${var.deployment_stage}",
            "arn:aws:dynamodb:us-east-1:${var.account_id}:table/dcp-data-dashboard-matrix-info-${var.deployment_stage}",
            "arn:aws:dynamodb:us-east-1:${var.account_id}:table/dcp-data-dashboard-azul-info-${var.deployment_stage}",
            "arn:aws:dynamodb:us-east-1:${var.account_id}:table/dcp-data-dashboard-analysis-info-${var.deployment_stage}",
            "arn:aws:dynamodb:us-east-1:${var.account_id}:table/dcp-data-dashboard-dss-info-${var.deployment_stage}",
            "arn:aws:dynamodb:us-east-1:${var.account_id}:table/dcp-data-dashboard-project-info-${var.deployment_stage}"
          ]
        }
    ]
}
EOF
}

resource "aws_ecs_cluster" "data_refresher" {
  name = "data-monitoring-data-refresher-${var.deployment_stage}"
}

# allow events role to be assumed by events service 
data "aws_iam_policy_document" "events_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
  }
}

resource "aws_cloudwatch_event_rule" "data_refresher" {
  name                = "tracker-data-refresher-cron-rule-${var.deployment_stage}"
  description         = "Runs fargate task data monitoring data tracker refresher with a cron rule"
  schedule_expression = "${var.refresher_schedule_expression}"
}

resource "aws_cloudwatch_event_target" "scheduled_task" {
  rule      = "${aws_cloudwatch_event_rule.data_refresher.name}"
  arn       = "${aws_ecs_cluster.data_refresher.arn}"
  role_arn  = "${aws_iam_role.task_executor.arn}"

  ecs_target = {
    task_count          = 1
    task_definition_arn = "${aws_ecs_task_definition.data_refresher.arn}"
    launch_type         = "FARGATE"
    platform_version    = "LATEST"

    network_configuration {
      security_groups = ["${var.security_group_id}"]
      subnets         = ["${var.allowed_subnet_ids}"]
      assign_public_ip = true
    }
  }
}
