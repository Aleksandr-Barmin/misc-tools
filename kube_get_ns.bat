@echo on

python aws_login.py sirius-dev-eks-limited credentials.json

set HTTPS_PROXY=http://dia2.santanderuk.gs.corp:80
set HTTP_PROXY=http://dia2.santanderuk.gs.corp:80
set NO_PROXY=.corp,sts.santander.co.uk
set DEFAULT_CA_BUNDLE_PATH=C:\Users\C0284773\Documents\dev-code\aws-auth\cacert.pem
set AWS_CA_BUNDLE=C:\Users\C0284773\Documents\dev-code\aws-auth\cacert.pem

aws eks update-kubeconfig --profile sirius-dev-eks-limited --name sirius-eks-main-dev
kubectl get pods --namespace oba