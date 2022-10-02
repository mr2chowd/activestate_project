import boto3
from datetime import datetime, timezone
resource_name= 'RDSCluster'
# aws lambda invoke --function-name GetRdsSnapshot response.json

today = (datetime.today()).date()
print(today)
rds_client = boto3.client('rds')
snapshots = rds_client.describe_db_cluster_snapshots(DBClusterIdentifier='database-1',MaxRecords=20)

list=[]
for x in snapshots['DBClusterSnapshots']:
    list.append(x['SnapshotCreateTime'])

latestsnapshottime=max(list)

for x in snapshots['DBClusterSnapshots']:
    if x['SnapshotCreateTime'] == latestsnapshottime:
        arnname=x['DBClusterSnapshotArn']
        print(arnname)
    
import yaml
# from ansible import from_yaml
import io
from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode
s3 = boto3.client('s3')
s3.download_file('activestatebucket', 'ephemeralenv.yml','ephemeralenv.yml')

def construct_vault_encrypted_unicode(loader, node):
    value = loader.construct_scalar(node)
    return AnsibleVaultEncryptedUnicode(value)

with open("ephemeralenv.yml", "r") as stream:
    data = yaml.safe_load(stream) 
    data['Resources']['RDSCluster']['Properties']['SnapshotIdentifier'] = arnname    
    print(data)

with io.open('final.yaml', 'w', encoding='utf8') as outfile:
    yaml.dump(data, outfile, default_flow_style=False, allow_unicode=True, sort_keys=False)
    s3.upload_file("final.yaml", "activestatebucket", "final.yaml")