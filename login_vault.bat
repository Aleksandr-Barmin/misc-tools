@echo on

@REM Logging in into AWS with different roles
@REM python aws_login.py sirius-dev-vault-secret-manager credentials.json
python aws_login.py sirius-dev-eks-limited credentials.json
@REM python aws_login.py sirius-codeartifact credentials.json

set HTTPS_PROXY=http://dia2.santanderuk.gs.corp:80
set HTTP_PROXY=http://dia2.santanderuk.gs.corp:80
set NO_PROXY=.corp,sts.santander.co.uk

@REM Parameter needed for aws scripts
set AWS_CA_BUNDLE=C:\Users\C0284773\Documents\dev-code\aws-auth\cacert.pem

@REM Parameter needed for vault_login.py
set DEFAULT_CA_BUNDLE_PATH=C:\Users\C0284773\Documents\dev-code\aws-auth\cacert.pem

@REM Reading secrets from the DB
@REM TODO: to be parameterized
@REM python vault_login.py 

@REM Logging into EKS, creating config for kubectl
@REM set AWS_CA_BUNDLE=C:\Users\C0284773\Documents\dev-code\aws-auth\cacert.pem
@REM aws eks update-kubeconfig --profile sirius-dev-eks-limited --name sirius-eks-main-dev

@REM Login into ECS
@REM set HELM_EXPERIMENTAL_OCI=1
@REM aws ecr get-login-password --region eu-west-2 --profile sirius-codeartifact | helm registry login --username AWS --password-stdin 590455736492.dkr.ecr.eu-west-2.amazonaws.com 
@REM rd /s /q .\chart
@REM mkdir chart
@REM helm pull oci://590455736492.dkr.ecr.eu-west-2.amazonaws.com/helm/ssm-connector --version v0.11.0 --destination .\chart
@REM 7z x -o.\chart .\chart\ssm-connector-v0.11.0.tgz
@REM 7z x -o.\chart .\chart\ssm-connector-v0.11.0.tar
helm install -n ssm-connector --set environment=dev --set service=customer-service --set service_port=5432 --set db_type=postgres test-chart .\chart\ssm-connector-v0.11.0.tgz
@REM kubectl wait --for=condition=Ready --timeout=45s pod --selector=job-name=test-chart -n ssm-connector

@REM Get latest version of the SSM Helm
@REM aws ecr --profile sirius-codeartifact --output json describe-images --registry-id 590455736492 --repository-name helm/ssm-connector --query "imageDetails[*].imageTags[]" | jq "sort_by(. | split(\".\") | map(sub(\"^v\"; \"\") | tonumber ))[-1]" --raw-output > helm_latest_version.txt
@REM set /p LATEST_VERSION=<helm_latest_version.txt

@REM kubectl get pods --namespace ssm-connector

@REM Logging in into HashiCorp Vault
@REM set VAULT_ADDR=https://vault.dev.sirius.tlzproject.com
@REM set AWS_PROFILE=sirius-dev-vault-secret-manager
@REM vault login -method=aws region=eu-west-2 role=secretmanager

@REM Retrieving credentials for DB
@REM vault read -format=json database/creds/customer-service-dev
