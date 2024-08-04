registry := "ghcr.io/wrossmorrow"
image_name := "scheduled-api-call"
image_tag := "local"
chart := "helm/scheduled-api-call"

# list all targets and exit
default: 
    just --list

# install python dependencies (in venv, via poetry)
install: 
    poetry install

# update python dependencies (in venv, via poetry)
update: 
    poetry update

# format python code
format:
    poetry run isort .
    poetry run black .

# lint python code
lint:
    poetry run flake8 .

# type python code
types:
    poetry run mypy .

# format, lint, and type check python code
validate: format lint types

# test python code
test *flags="":
    poetry run python -m pytest test/unitish -vvv {{flags}}

# run module
run *flags="":
    poetry run python -m caller {{flags}}

# run locally with mongodb using docker-compose
up *FLAGS: 
    docker-compose up --build {{FLAGS}}

# teardown docker-compose
down: 
    docker-compose down --volumes

# template kubernetes manifests
template *flags="":
    helm template caller scheduled-api-call {{flags}}

# deploy manifests to kubernetes
deploy:
    helm upgrade --install caller scheduled-api-call --values helm/test.values.yaml

# build image (local arch)
build tag=image_tag:
    docker build . -f Dockerfile -t {{registry}}/{{image_name}}:{{tag}}

# build and push image (multi-arch)
docker-publish tag=image_tag:
    docker buildx build . -f Dockerfile -t {{registry}}/{{image_name}}:{{tag}} \
        --platform linux/amd64,linux/arm64 --push

# publish helm chart
helm-publish:
    #!/bin/bash
    VERSION=$( yq -r '.version' {{chart}}/Chart.yaml )
    helm package --version ${VERSION} {{chart}}
    helm push {{chart}}-${VERSION}.tgz oci://{{registry}}/scheduled-api-call
    rm {{chart}}-${VERSION}.tgz
