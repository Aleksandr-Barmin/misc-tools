#!/usr/bin/python3

import sys
import boto.sts
import boto.s3
import requests
import configparser
import base64
import json
import xml.etree.ElementTree as ET
import re
import os
import sys
from bs4 import BeautifulSoup
from os.path import expanduser
from urllib.parse import urlparse, urlunparse

# Checking if profile is provided
if (len(sys.argv) != 3):
    print("Not all the args provided")
    print("Usage: aws_login.py <profile> <credentials file>")
    exit()

# Checking if configuration file exists
config_file_path = os.path.join(expanduser("~"), ".aws", "config")
if not os.path.exists(config_file_path):
    print("AWS Config file does not exist")
    print(f"Expected location is {config_file_path}")
    exit()

# Checking if the profile exists in the config
profile_name = sys.argv[1]
section_name = f"profile {profile_name}"
profiles_config = configparser.ConfigParser()
profiles_config.read(config_file_path)
if not profiles_config.has_section(section_name):
    print(f"AWS Config has no section with name {profile_name}")
    exit()

# Checking the profile props
props_should_exist = [
    "region", 
    "adfs_role_arn",
    "adfs_login_url"
]
profile_has_errors = False
for prop in props_should_exist:
    if not prop in profiles_config[section_name]:
        print(f"Configuration file should have {prop} property in the {section_name} section")
        profile_has_errors = True
if profile_has_errors:
    exit()   

# Checking the credentials file
credentials_file_path = os.path.join(".", sys.argv[2])
if not os.path.exists(credentials_file_path):
    print("No file with credentials")
    print(f"Path was checked {credentials_file_path}")

# Reading the credentials file
with open(credentials_file_path, "r") as credentials_file:
    credentials = json.load(credentials_file)
    username = credentials["username"]
    password = credentials["password"]

# Configuring and running everything    
region = profiles_config[section_name]["region"]
idpentryurl = profiles_config[section_name]["adfs_login_url"]
assuming_role = profiles_config[section_name]["adfs_role_arn"]

# awsconfigfile: The file where this script will store the temp
# credentials under the saml profile
awsconfigfile = '/.aws/credentials'
outputformat = 'json'

# Checking if the .aws/credentials file exists
home = expanduser("~")
aws_config_default = home + awsconfigfile
if (not os.path.exists(aws_config_default)):
    with open(aws_config_default, "x") as aws_config_file:
        aws_config_file.write("[default]\n")
        aws_config_file.write(f"output={outputformat}\n")
        aws_config_file.write(f"region={region}\n")
        aws_config_file.write("aws_access_key_id=\n")
        aws_config_file.write("aws_secret_access_key=\n")

# SSL certificate verification: Whether or not strict certificate
# verification is done, False should only be used for dev/test
sslverification = True

# Initiate session handler
session = requests.Session()

# Programmatically get the SAML assertion
# Opens the initial IdP url and follows all of the HTTP302 redirects, and
# gets the resulting login page
formresponse = session.get(idpentryurl, verify=sslverification)
# Capture the idpauthformsubmiturl, which is the final url after all the 302s
idpauthformsubmiturl = formresponse.url

# Parse the response and extract all the necessary values
# in order to build a dictionary of all of the form values the IdP expects
formsoup = BeautifulSoup(formresponse.text, features='lxml')
payload = {}

for inputtag in formsoup.find_all(re.compile('(INPUT|input)')):
    name = inputtag.get('name','')
    value = inputtag.get('value','')
    if "user" in name.lower():
        #Make an educated guess that this is the right field for the username
        payload[name] = username
    elif "email" in name.lower():
        #Some IdPs also label the username field as 'email'
        payload[name] = username
    elif "pass" in name.lower():
        #Make an educated guess that this is the right field for the password
        payload[name] = password
    else:
        #Simply populate the parameter with the existing value (picks up hidden fields in the login form)
        payload[name] = value

# Some IdPs don't explicitly set a form action, but if one is set we should
# build the idpauthformsubmiturl by combining the scheme and hostname 
# from the entry url with the form action target
# If the action tag doesn't exist, we just stick with the 
# idpauthformsubmiturl above
for inputtag in formsoup.find_all(re.compile('(FORM|form)')):
    action = inputtag.get('action')
    if action:
        parsedurl = urlparse(idpentryurl)
        idpauthformsubmiturl = parsedurl.scheme + "://" + parsedurl.netloc + action

# Fix for SNTD
idpauthformsubmiturl = idpauthformsubmiturl[27:]

# Performs the submission of the IdP login form with the above post data
response = session.post(
    idpauthformsubmiturl, data=payload, verify=sslverification)

# Decode the response and extract the SAML assertion
soup = BeautifulSoup(response.text, features='lxml')
assertion = ''

# Look for the SAMLResponse attribute of the input tag (determined by
# analyzing the debug print lines above)
for inputtag in soup.find_all('input'):
    if(inputtag.get('name') == 'SAMLResponse'):
        assertion = inputtag.get('value')

# Better error handling is required for production use.
if (assertion == ''):
    print('Response did not contain a valid SAML assertion')
    sys.exit(0)

# Parse the returned assertion and extract the authorized roles
awsroles = []
root = ET.fromstring(base64.b64decode(assertion))
for saml2attribute in root.iter('{urn:oasis:names:tc:SAML:2.0:assertion}Attribute'):
    if (saml2attribute.get('Name') == 'https://aws.amazon.com/SAML/Attributes/Role'):
        for saml2attributevalue in saml2attribute.iter('{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue'):
            awsroles.append(saml2attributevalue.text)

# Note the format of the attribute value should be role_arn,principal_arn
# but lots of blogs list it as principal_arn,role_arn so let's reverse
# them if needed
for awsrole in awsroles:
    chunks = awsrole.split(',')
    if'saml-provider' in chunks[0]:
        newawsrole = chunks[1] + ',' + chunks[0]
        index = awsroles.index(awsrole)
        awsroles.insert(index, newawsrole)
        awsroles.remove(awsrole)

# Selecting a role, based on the configuration file
assuming_role_exists = False
for role in awsroles:
    aws_role = role.split(",")[0]
    if aws_role == assuming_role:
        assuming_role_exists = True
        role_arn = role.split(",")[0]
        principal_arn = role.split(",")[1]

if not assuming_role_exists:
    print(f"Role {assuming_role} does not exist")
    print("The following roles are available: ")
    for role in awsroles:
        role_arn = role.split(",")[0]
        print(f"- {role_arn}")
    exit()

# Use the assertion to get an AWS STS token using Assume Role with SAML
conn = boto.sts.connect_to_region(region)
token = conn.assume_role_with_saml(role_arn, principal_arn, assertion)

# Write the AWS STS token into the AWS credential file
home = expanduser("~")
filename = home + awsconfigfile

# Read in the existing config file
config = configparser.RawConfigParser()
config.read(filename)

# Put the credentials into a saml specific section instead of clobbering
# the default credentials
if not config.has_section(profile_name):
    config.add_section(profile_name)

config.set(profile_name, 'output', outputformat)
config.set(profile_name, 'region', region)
config.set(profile_name, 'aws_access_key_id', token.credentials.access_key)
config.set(profile_name, 'aws_secret_access_key', token.credentials.secret_key)
config.set(profile_name, 'aws_session_token', token.credentials.session_token)

# Write the updated config file
with open(filename, 'w+') as configfile:
    config.write(configfile)