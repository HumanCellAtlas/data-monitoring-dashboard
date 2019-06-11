include common.mk
.PHONY: lint test unit-tests
MODULES=tracker

test: lint

lint:
	flake8 $(MODULES) *.py

deploy:
	cd chalice && make deploy
	cd frontend && make deploy
	aws cloudfront create-invalidation --distribution-id E2Y2LM41A9RNBP --paths "/*" --profile hca-prod
