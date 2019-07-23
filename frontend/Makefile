deploy:
	aws s3 sync . s3://hca-data-tracker-${DEPLOYMENT_STAGE}/
	python ${PROJECT_ROOT}/scripts/invalidate_cloudfront_cache.py
