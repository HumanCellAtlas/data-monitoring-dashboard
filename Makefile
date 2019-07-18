include common.mk
.PHONY: lint test unit-tests
MODULES=tracker

test: lint

lint:
	flake8 $(MODULES) *.py

deploy: deploy_api deploy_frontend

deploy_api:
	cd chalice && make deploy

deploy_frontend:
	cd frontend && make deploy
