include common.mk
.PHONY: lint test unit-tests
MODULES=tracker

test: lint unit-tests

unit-tests:
	pytest -v --ignore tests/functional/

lint:
	flake8 $(MODULES) *.py

functional-tests:
	PYTHONWARNINGS=ignore:ResourceWarning python3 \
		-m unittest discover --start-directory tests/functional --top-level-directory . --verbose

deploy: deploy_api deploy_frontend

deploy_api:
	cd chalice && make deploy

deploy_frontend:
	cd frontend && make deploy
