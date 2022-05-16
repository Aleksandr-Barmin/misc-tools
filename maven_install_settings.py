from posixpath import expanduser
import sys
import os
from os.path import expanduser

# Checking if the token is available
if len(sys.argv) != 2:
    print("No token provided")
    print("Usage: python maven_install_settings.py <token>")
    exit()

token = sys.argv[1]

# Checking if the basic settings file is available
template_file_path = os.path.join(".", "maven", "settings.xml")
if not os.path.exists(template_file_path):
    print("Template file is not available")
    print(f"Expected location {template_file_path}")
    exit()

target_file_path = os.path.join(expanduser("~"), ".m2", "settings.xml")
if os.path.exists(target_file_path):
    os.remove(target_file_path)

# Creating a new file
to_replace = "${env.CODEARTIFACT_AUTH_TOKEN}"
with open(template_file_path, "r") as template_file: 
    with open(target_file_path, "w") as target_file: 
        while True:
            line = template_file.readline()
            if not line:
                break
            if to_replace in line:
                line = line.replace(to_replace, token)
            target_file.write(line)