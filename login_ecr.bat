@echo off

python aws_login.py sirius-codeartifact credentials.json

set HTTP_PROXY=
set HTTPS_PROXY=
set NO_PROXY=amazonaws.com

aws ecr get-login-password --region eu-west-2 --profile sirius-codeartifact | docker login --username AWS --password-stdin 590455736492.dkr.ecr.eu-west-2.amazonaws.com