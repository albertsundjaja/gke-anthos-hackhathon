# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

.-PHONY: cluster deploy deploy-continuous logs checkstyle check-env

CLUSTER=bank-of-anthos
E2E_PATH=${PWD}/.github/workflows/ui-tests/

cluster: check-env
	gcloud container clusters create ${CLUSTER} \
		--project=${PROJECT_ID} --zone=${ZONE} \
		--machine-type=e2-standard-4 --num-nodes=4 \
		--enable-stackdriver-kubernetes --subnetwork=default \
		--labels csm=

deploy: check-env
	echo ${CLUSTER}
	gcloud container clusters get-credentials --project ${PROJECT_ID} ${CLUSTER} --zone ${ZONE}
	skaffold run --default-repo=us-central1-docker.pkg.dev/${PROJECT_ID}/bank-of-anthos -l skaffold.dev/run-id=${CLUSTER}-${PROJECT_ID}-${ZONE}

deploy-continuous: check-env
	gcloud container clusters get-credentials --project ${PROJECT_ID} ${CLUSTER} --zone ${ZONE}
	skaffold dev --default-repo=us-central1-docker.pkg.dev/${PROJECT_ID}/bank-of-anthos

monolith-fw-rule: check-env
	export CLUSTER_POD_CIDR="$(shell gcloud container clusters describe ${CLUSTER} --format="value(clusterIpv4Cidr)" --project ${PROJECT_ID} --zone=${ZONE})" && \
	gcloud compute firewall-rules create monolith-gke-cluster --allow=TCP:8080 --project=${PROJECT_ID} --source-ranges=$${CLUSTER_POD_CIDR} --target-tags=monolith

monolith: check-env
ifndef GCS_BUCKET
	# GCS_BUCKET is undefined
	# ATTENTION: Deployment proceeding with canonical pre-built monolith artifacts
endif
	# build and deploy Bank of Anthos along with a monolith backend service
	mvn -f src/ledgermonolith/ package
	src/ledgermonolith/scripts/build-artifacts.sh
	src/ledgermonolith/scripts/deploy-monolith.sh
	sed -i 's/\[PROJECT_ID\]/${PROJECT_ID}/g' src/ledgermonolith/config.yaml
	gcloud container clusters get-credentials --project ${PROJECT_ID} ${CLUSTER} --zone ${ZONE}
	kubectl apply -f src/ledgermonolith/config.yaml
	kubectl apply -f extras/jwt/jwt-secret.yaml
	kubectl apply -f kubernetes-manifests/accounts-db.yaml
	kubectl apply -f kubernetes-manifests/userservice.yaml
	kubectl apply -f kubernetes-manifests/contacts.yaml
	kubectl apply -f kubernetes-manifests/frontend.yaml
	kubectl apply -f kubernetes-manifests/loadgenerator.yaml

monolith-build: check-env
ifndef GCS_BUCKET
	$(error GCS_BUCKET is undefined; specify a Google Cloud Storage bucket to store your build artifacts)
endif
	# build the artifacts for the ledgermonolith service 
	mvn -f src/ledgermonolith/ package
	src/ledgermonolith/scripts/build-artifacts.sh

monolith-deploy: check-env
ifndef GCS_BUCKET
	# GCS_BUCKET is undefined
	# ATTENTION: Deployment proceeding with canonical pre-built monolith artifacts
endif
	# deploy the ledgermonolith service to a GCE VM
	src/ledgermonolith/scripts/deploy-monolith.sh

checkstyle:
	mvn checkstyle:check
	# disable warnings: import loading, todos, function members, duplicate code, public methods
	pylint --rcfile=./.pylintrc ./src/*/*.py

test-e2e:
	E2E_URL="http://$(shell kubectl get service frontend -o jsonpath='{.status.loadBalancer.ingress[0].ip}')" && \
	docker run -it -v ${E2E_PATH}:/e2e -w /e2e -e CYPRESS_baseUrl=$${E2E_URL} cypress/included:5.0.0 $(E2E_FLAGS)

test-unit:
	mvn test
	for SERVICE in "contacts" "userservice"; \
	do \
		pushd src/$$SERVICE;\
			python3 -m venv $$HOME/venv-$$SERVICE; \
			source $$HOME/venv-$$SERVICE/bin/activate; \
			pip install -r requirements.txt; \
			python -m pytest -v -p no:warnings; \
			deactivate; \
		popd; \
	done

check-env:
ifndef PROJECT_ID
	$(error PROJECT_ID is undefined)
else ifndef ZONE
	$(error ZONE is undefined)
endif

build-cs-agent:
	docker build -t us-central1-docker.pkg.dev/gke-hackathon-472001/bank-of-anthos-gke/cs-agent:latest -f src/cs-agent/Dockerfile src/cs-agent/

build-anthos-mcp:
	docker build -t us-central1-docker.pkg.dev/gke-hackathon-472001/bank-of-anthos-gke/anthos-mcp:latest -f src/anthos-mcp/Dockerfile src/anthos-mcp/

build-promotion-db:
	docker build -t us-central1-docker.pkg.dev/gke-hackathon-472001/bank-of-anthos-gke/promotion-db:latest -f src/promotion/promotion-db/Dockerfile src/promotion/promotion-db/

build-promotion-agent:
	docker build -t us-central1-docker.pkg.dev/gke-hackathon-472001/bank-of-anthos-gke/promotion-agent:latest -f src/promotion/agent/Dockerfile src/promotion/agent/

build-db-poller:
	docker build -t us-central1-docker.pkg.dev/gke-hackathon-472001/bank-of-anthos-gke/db-poller:latest -f src/db-poller/Dockerfile src/db-poller/

build-nats-subscriber:
	docker build -t us-central1-docker.pkg.dev/gke-hackathon-472001/bank-of-anthos-gke/nats-subscriber:latest -f src/promotion/nats-subscriber/Dockerfile src/promotion/nats-subscriber/

kind-update-promotion-db:
	kind load docker-image us-central1-docker.pkg.dev/gke-hackathon-472001/bank-of-anthos-gke/promotion-db:latest --name bank-of-anthos

kind-update-promotion-agent:
	kind load docker-image us-central1-docker.pkg.dev/gke-hackathon-472001/bank-of-anthos-gke/promotion-agent:latest --name bank-of-anthos

kind-update-anthos-mcp:
	kind load docker-image us-central1-docker.pkg.dev/gke-hackathon-472001/bank-of-anthos-gke/anthos-mcp:latest --name bank-of-anthos

kind-update-cs-agent:
	kind load docker-image us-central1-docker.pkg.dev/gke-hackathon-472001/bank-of-anthos-gke/cs-agent:latest --name bank-of-anthos

kind-update-db-poller:
	kind load docker-image us-central1-docker.pkg.dev/gke-hackathon-472001/bank-of-anthos-gke/db-poller:latest --name bank-of-anthos

kind-update-nats-subscriber:
	kind load docker-image us-central1-docker.pkg.dev/gke-hackathon-472001/bank-of-anthos-gke/nats-subscriber:latest --name bank-of-anthos

kind-deploy-nats-subscriber:
	kubectl apply -f kubernetes-manifests/nats-subscriber.yaml

kind-deploy-promotion-db:
	kubectl apply -f kubernetes-manifests/promotion-db.yaml

kind-deploy-promotion-agent:
	kubectl apply -f kubernetes-manifests/promotion-agent.yaml

kind-deploy-anthos-mcp:
	kubectl apply -f kubernetes-manifests/anthos-mcp.yaml

kind-deploy-cs-agent:
	kubectl apply -f kubernetes-manifests/cs-agent.yaml

kind-deploy-db-poller:
	kubectl apply -f kubernetes-manifests/db-poller.yaml

restart-cs-agent:
	kubectl delete deployment cs-agent
	envsubst < kubernetes-manifests/cs-agent.yaml | kubectl apply -f -

restart-promotion-agent:
	kubectl delete deployment promotion-agent
	envsubst < kubernetes-manifests/promotion-agent.yaml | kubectl apply -f -

restart-nats-subscriber:
	kubectl delete deployment nats-subscriber
	envsubst < kubernetes-manifests/nats-subscriber.yaml | kubectl apply -f -

build-local: build-cs-agent build-anthos-mcp build-promotion-db build-promotion-agent build-db-poller build-nats-subscriber
kind-update: kind-update-cs-agent kind-update-anthos-mcp kind-update-promotion-db kind-update-promotion-agent kind-update-db-poller kind-update-nats-subscriber
kind-rebuild: build-local kind-update
kind-redeploy: kind-stop kind-deploy
kind-redeploy-cs-agent: build-cs-agent kind-update-cs-agent restart-cs-agent port-forward-cs-agent
kind-redeploy-promotion-agent: build-promotion-agent kind-update-promotion-agent restart-promotion-agent port-forward-promotion-agent
kind-redeploy-nats-subscriber: build-nats-subscriber kind-update-nats-subscriber restart-nats-subscriber
kind-deploy:
	kubectl apply -f extras/jwt/jwt-secret.yaml
	for file in kubernetes-manifests/*.yaml; do \
		echo "Processing $$file..."; \
		if [ "$$file" = "kubernetes-manifests/loadgenerator.yaml" ]; then \
			continue; \
		fi; \
		envsubst < "$$file" | kubectl apply -f -; \
	done
	# Force restart all deployments to pick up latest images
	kubectl get deployments -o name | xargs -I {} kubectl rollout restart {} || true
kind-stop:
	kubectl delete -f kubernetes-manifests/

port-forward-cs-agent:
	kubectl port-forward deployment/cs-agent 8080:8080

port-forward-anthos-mcp:
	kubectl port-forward deployment/anthos-mcp 8000:8080

port-forward-frontend:
	kubectl port-forward deployment/frontend 8081:8080

port-forward-promotion-agent:
	kubectl port-forward deployment/promotion-agent 8082:8080


# --- Push targets for custom images ---
configure-docker:
	gcloud auth configure-docker us-central1-docker.pkg.dev

push-cs-agent:
	docker push us-central1-docker.pkg.dev/gke-hackathon-472001/bank-of-anthos-gke/cs-agent:latest

push-anthos-mcp:
	docker push us-central1-docker.pkg.dev/gke-hackathon-472001/bank-of-anthos-gke/anthos-mcp:latest

push-promotion-db:
	docker push us-central1-docker.pkg.dev/gke-hackathon-472001/bank-of-anthos-gke/promotion-db:latest

push-promotion-agent:
	docker push us-central1-docker.pkg.dev/gke-hackathon-472001/bank-of-anthos-gke/promotion-agent:latest

push-db-poller:
	docker push us-central1-docker.pkg.dev/gke-hackathon-472001/bank-of-anthos-gke/db-poller:latest

push-nats-subscriber:
	docker push us-central1-docker.pkg.dev/gke-hackathon-472001/bank-of-anthos-gke/nats-subscriber:latest

# Push all custom images (ensure you built them first)
push-local: push-cs-agent push-anthos-mcp push-promotion-db push-promotion-agent push-db-poller push-nats-subscriber
