import sys
import re
import os
import jinja2
import boto3
from botocore.exceptions import ClientError
import json
import time

terraformmainpath   = './main.tf'
terraformmainnewpath= './main_new.tf'
terraformmainoldpath= './main.tf.old'
terraformtfvars     = './terraform.tfvars'
rolearn_tfstate_account ="arn:aws:iam::038297232438:role/CircleciRole"
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
            rolearn_provisioned_account = "arn:aws:iam::"+ account_number + ":role/CircleciRole"
            break
f.close()

with open(terraformmainpath, 'r') as input_file:
    # Open the output file in write mode
    with open(terraformmainnewpath, 'w') as output_file:
        # Loop over each line in the input file
        for line in input_file:
            # Check if this line contains the string you want to replace
            if re.search(r'key.*tfstate\"$', line):
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



session_provisioned_account = boto3.Session()
client_provisioned_account = session_provisioned_account.client('sts')
try:
    assumed_role = client_provisioned_account.assume_role_with_web_identity(
        RoleArn=rolearn_provisioned_account,
        RoleSessionName='AWS-KeyID',
        WebIdentityToken=circle_oidc_token,
    )
except ClientError as e:
    print(e)
    exit()

# Get temporary credentials
credentials_provisioned_account = assumed_role['Credentials']

with open("./env_var.env", "w") as f:
   # write the key-value pair in the format "KEY=VALUE" to the end of the file
    f.write(f"export {'AWS_ACCESS_KEY_ID'}={credentials_provisioned_account['AccessKeyId']}\n")
    f.write(f"export {'AWS_SECRET_ACCESS_KEY'}={credentials_provisioned_account['SecretAccessKey']}\n")
    f.write(f"export {'AWS_SESSION_TOKEN'}={credentials_provisioned_account['SessionToken']}\n")
f.close()

session_tfstate_account = boto3.Session()
client_tfstate_account = session_tfstate_account.client('sts')
try:
    assumed_role = client_tfstate_account.assume_role_with_web_identity(
        RoleArn=rolearn_tfstate_account,
        RoleSessionName='AWS-KeyID',
        WebIdentityToken=circle_oidc_token,
    )
except ClientError as e:
    print(e)
    exit()

# Get temporary credentials for tfstate account
credentials_tfstate_account = assumed_role['Credentials']
   # Open the input file in read mode
    #rename tfstate part
with open(terraformmainpath, 'r') as input_file:
    # Open the output file in write mode
    with open(terraformmainnewpath, 'w') as output_file:
        # Loop over each line in the input file
        for line in input_file:
            if re.search(r'\s+backend*\"s3\"\s+{$',line):
                substring = '{\n\taccess_key  = "' + credentials_tfstate_account['AccessKeyId'] + '"' + '\n\tsecret_key = "' + credentials_tfstate_account['SecretAccessKey'] + '"'
                new_line = re.sub(r'\s{', substring, line)
                output_file.write(new_line)
                print(credentials_tfstate_account['AccessKeyId'])
                print(credentials_tfstate_account['SecretAccessKey'])
            else:
                # Write the original line to the output file
                output_file.write(line)
    output_file.close()
input_file.close()                
os.rename(terraformmainpath,terraformmainoldpath)
os.rename(terraformmainnewpath,terraformmainpath)
os.remove(terraformmainoldpath)