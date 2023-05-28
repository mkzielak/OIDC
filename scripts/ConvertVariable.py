import sys
import re
import os
import jinja2
import boto3
from botocore.exceptions import ClientError
import json
import time

#terraformmainpath   = 'C:\\temp\\OIDC\\main.tf'
#terraformmainnewpath= 'C:\\temp\\aws-A_000_EnvironmentVariablesTest_W00_Dev\\scripts\\main_new.tf'
#terraformmainoldpath= 'C:\\temp\\aws-A_000_EnvironmentVariablesTest_W00_Dev\\scripts\\main.tf.old'
#terraformtfvars     = 'C:\\temp\\OIDC\\terraform.tfvars'
terraformmainpath   = './main.tf'
terraformmainnewpath= './main_new.tf'
terraformmainoldpath= './main.tf.old'
terraformtfvars     = './terraform.tfvars'
policyexists        = False
rolexists           = False  
rolearn_cfstackset ="arn:aws:iam::953689267850:role/CircleCI_Role"
# get the input string from command line arguments
if len(sys.argv) > 3:
    reponame  = sys.argv[1]
    jobname = sys.argv[2]
    circle_oidc_token = sys.argv[3] 

# split the string by '_' and get the last three elements
parts = reponame.split('_')
last_three_parts = parts[-3:]
# join the last three elements back together using '_'
project_name = '_'.join(last_three_parts).lower()
###########################################
#Get account number from terraform.tfvars
###########################################
with open(terraformtfvars, 'r') as f:
    #Get account value from terraform.tfvars
    for line in f:
        line = line.strip().lstrip()  # remove leading/trailing whitespace
        if line and re.search(r'aws_account_id',line):  # skip empty lines
            key, value = line.split('=')
            value_temp = re.sub(' +"', '',value)
            account_number = re.sub('"', '',value_temp)
            break
f.close()

with open(terraformmainpath, 'r') as input_file:
    # Open the output file in write mode
    with open(terraformmainnewpath, 'w') as output_file:
        # Loop over each line in the input file
        for line in input_file:
            # Check if this line contains the string you want to replace
            if re.search(r'key.*tfstate"$', line):
                # Replace the line with the new string
                substring = '= "' + project_name + "/"
                new_line = re.sub(r'\s=\s"', substring, line)
                output_file.write(new_line)
            else:
                # Write the original line to the output file
                output_file.write(line)
    output_file.close()
input_file.close()                
os.rename(terraformmainpath,terraformmainoldpath)
os.rename(terraformmainnewpath,terraformmainpath)
os.remove(terraformmainoldpath)



session = boto3.Session()
client = session.client('sts')
try:
    assumed_role = client.assume_role_with_web_identity(
        RoleArn=rolearn_cfstackset,
        RoleSessionName='AWS-KeyID',
        WebIdentityToken=circle_oidc_token,
    )
except ClientError as e:
    print(e)
    exit()

# Get temporary credentials
credentials = assumed_role['Credentials']

# Use the temporary credentials to access AWS resources
# iam_client = boto3.client(
#     'iam',
#     aws_access_key_id=credentials['AccessKeyId'],
#     aws_secret_access_key=credentials['SecretAccessKey'],
#     aws_session_token=credentials['SessionToken']
#     )
  
with open("/root/project/env_account.var", "a") as f:
   # write the key-value pair in the format "KEY=VALUE" to the end of the file
    f.write(f"export {'AWS_ACCESS_KEY_ID'}={credentials['AccessKeyId']}\n")
    f.write(f"export {'AWS_SECRET_ACCESS_KEY'}={credentials['SecretAccessKey']}\n")
    f.write(f"export {'AWS_SESSION_TOKEN'}={credentials['SessionToken']}\n")
f.close()