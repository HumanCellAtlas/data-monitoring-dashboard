deploy:
	aws s3 sync . s3://hca-data-tracker-${DEPLOYMENT_STAGE}/ --profile hca-prod
	# TODO The distribution id and profile should not be hardcoded
	aws cloudfront create-invalidation --distribution-id E2Y2LM41A9RNBP --paths "/*" --profile hca-prod
