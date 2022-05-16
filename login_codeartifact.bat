@echo off

python aws_login.py sirius-codeartifact credentials.json

set DEFAULT_CA_BUNDLE_PATH=C:\Users\C0284773\Documents\dev-code\aws-auth\cacert.pem
set HTTPS_PROXY=http://dia2.santanderuk.gs.corp:80
set HTTP_PROXY=http://dia2.santanderuk.gs.corp:80
set NO_PROXY=.corp,sts.santander.co.uk
set AWS_CA_BUNDLE=C:\Users\C0284773\Documents\dev-code\aws-auth\cacert.pem

FOR /F "tokens=*" %%g IN ('aws --profile sirius-codeartifact codeartifact get-authorization-token --domain sirius --domain-owner 590455736492 --query authorizationToken --output text') do (python maven_install_settings.py %%g)