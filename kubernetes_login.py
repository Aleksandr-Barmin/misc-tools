from kubernetes import client, config

config.load_config()
v1_client = client.CoreV1Api()

v1_client.list_namespace()