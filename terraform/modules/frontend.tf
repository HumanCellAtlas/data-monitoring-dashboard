# s3 Bucket with Website settings
resource "aws_s3_bucket" "site_bucket" {
  bucket = "hca-data-tracker-${var.deployment_stage}"
  acl = "public-read"
  website {
    index_document = "index.html"
  }
}

resource "aws_s3_bucket_policy" "site_bucket_policy" {
  bucket =  aws_s3_bucket.site_bucket.id

  policy = <<POLICY
{
  "Version":"2012-10-17",
  "Statement":[{
  "Sid":"PublicReadGetObject",
        "Effect":"Allow",
    "Principal": "*",
      "Action":["s3:GetObject"],
      "Resource":["arn:aws:s3:::hca-data-tracker-${var.deployment_stage}/*"
      ]
    }
  ]
}
POLICY
}
