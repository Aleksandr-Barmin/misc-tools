#!/usr/bin/python3

from pydoc import cli
import hvac
import os
from os.path import expanduser
import configparser

# Here I need to get name of the AWS Profile
profile_name = "sirius-dev-vault-secret-manager"
vault_url = "https://vault.dev.sirius.tlzproject.com"

# Reading values from .aws/credentials file
credentials_file_path = os.path.join(expanduser("~"), ".aws", "credentials")
if not os.path.exists(credentials_file_path):
    print("AWS credentials file does not exist, more likely, you are not logged it")
    print(f"Expected location is {credentials_file_path}")
    exit()

# Reading parameters from profile
credentials_config = configparser.ConfigParser()
credentials_config.read(credentials_file_path)
if not credentials_config.has_section(profile_name):
    print(f"You have not logged with {profile_name} profile to AWS")
    print("Login again")
    exit()

access_key_id = credentials_config[profile_name]["aws_access_key_id"]
secret_access_key = credentials_config[profile_name]["aws_secret_access_key"]
session_token = credentials_config[profile_name]["aws_session_token"]

# Trying to login to the Vault
client = hvac.Client(url=vault_url)
client.auth.aws.iam_login(
    access_key = access_key_id, 
    secret_key = secret_access_key, 
    session_token = session_token, 
    role = "secretmanager", 
    region = "eu-west-2"
)

if not client.is_authenticated:
    print("Client is not authenticated")
    exit()

r = client.read('database/creds/customer-service-dev')
print(r)