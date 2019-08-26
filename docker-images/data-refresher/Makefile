HUB_ORG=humancellatlas
IMAGE=data-monitoring-data-refresher
VERSION=$(shell cat VERSION)

# Modus operandi for testing and releasing changes.
# --------------
# make bump_version
# make build
# make test
#	test image locally. Expects target env var DEPLOYMENT_STAGE to be set.
# make push

build:
	mkdir -p code
	cp -R ../../requirements.txt code/
	cp -R ../../tracker code/
	cp load.py code
	docker build -t $(IMAGE):$(VERSION) .
	rm -rf code/

push:
	$(eval VERSION=$(shell cat VERSION))
	docker tag $(IMAGE):$(VERSION) $(HUB_ORG)/$(IMAGE):$(VERSION)
	docker push $(HUB_ORG)/$(IMAGE):$(VERSION)

bump_version:
	expr `cat VERSION` + 1 > VERSION

test:
	docker run -e DEPLOYMENT_STAGE=${DEPLOYMENT_STAGE} -e AWS_DEFAULT_REGION=us-east-1 -v ~/.aws:/root/.aws -e AWS_PROFILE=hca-prod --rm -it $(IMAGE):$(VERSION)

.phony: build bump_version promote push
