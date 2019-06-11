include ../common.mk

export EXPORT_ENV_VARS_TO_LAMBDA=DEPLOYMENT_STAGE \
			API_HOST \
			XDG_CONFIG_HOME

clean:
	git clean -df .

clobber: clean
	git checkout .chalice/*.json

build:
	cp ../requirements.txt .
	mkdir -p chalicelib/tracker/common chalicelib/tracker/lambdas
	cp -R ../tracker/__init__.py \
		  ../tracker/common \
		chalicelib/tracker
	cp -R ../tracker/lambdas/__init__.py \
		  ../tracker/lambdas/api_server \
		chalicelib/tracker/lambdas
	mkdir -p chalicelib/config
	envsubst '$$API_HOST' < ../config/tracker-api.yml > chalicelib/config/tracker-api.yml
	shopt -s nullglob; for wheel in vendor.in/*/*.whl; do unzip -q -o -d vendor $$wheel; done

deploy: clean build
	@echo -e "\n\n#########################################################"
	@echo -e "########## Deploying to $(DEPLOYMENT_STAGE) environment"
	@echo -e "#########################################################\n"
	./build_deploy_config.sh $(DEPLOYMENT_STAGE)
	chalice deploy --no-autogen-policy --stage $(DEPLOYMENT_STAGE) --api-gateway-stage $(DEPLOYMENT_STAGE)

