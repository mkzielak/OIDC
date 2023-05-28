import sys
import re
import os
import jinja2
import boto3
from botocore.exceptions import ClientError
import json
import time

#terraformmainpath   = 'C:\\temp\\aws-A_000_EnvironmentVariablesTest_W00_Dev\\scripts\\main.tf'
#terraformmainnewpath= 'C:\\temp\\aws-A_000_EnvironmentVariablesTest_W00_Dev\\scripts\\main_new.tf'
#terraformmainoldpath= 'C:\\temp\\aws-A_000_EnvironmentVariablesTest_W00_Dev\\scripts\\main.tf.old'
#terraformtfvars     = 'C:\\temp\\aws-A_000_EnvironmentVariablesTest_W00_Dev\\scripts\\terraform.tfvars'
terraformmainpath   = './main.tf'
terraformmainnewpath= './main_new.tf'
terraformmainoldpath= './main.tf.old'
terraformtfvars     = './terraform.tfvars'
policyexists        = False
rolexists           = False  
S3account_number    =  '953689267850'   
rolearn ="arn:aws:iam::953689267850:role/CircleCI_Role"
# get the input string from command line arguments
if len(sys.argv) > 3:
    string  = sys.argv[1]
    jobname = sys.argv[2]
    circle_oidc_token = sys.argv[3] 
else:
    string  = sys.argv[1]
    jobname = sys.argv[2]


# split the string by '_' and get the last three elements
parts = string.split('_')
last_three = parts[-3:]
# join the last three elements back together using '_'
joined_string = '_'.join(last_three).lower()
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
if re.search(r'preparing-variable', jobname):
    with open("/root/project/env_account.var", "a") as f:
    # write the key-value pair in the format "KEY=VALUE" to the end of the file
        f.write(f"export {'ACCOUNT_NUMBER'}={account_number}\n")
    f.close()
     
# creating policy and role
if re.search(r'terraform-init-validate', jobname):
    # Open the input file in read mode
    #rename tfstate part
    with open(terraformmainpath, 'r') as input_file:
        # Open the output file in write mode
        with open(terraformmainnewpath, 'w') as output_file:
            # Loop over each line in the input file
            for line in input_file:
                # Check if this line contains the string you want to replace
                if re.search(r'key.*tfstate"$', line):
                    # Replace the line with the new string
                    substring = '= "' + joined_string + "/"
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
            RoleArn=rolearn,
            RoleSessionName='example-session',
            WebIdentityToken=circle_oidc_token,
        )
    except ClientError as e:
        print(e)
        exit()

    # Get temporary credentials
    credentials = assumed_role['Credentials']

    # Use the temporary credentials to access AWS resources
    iam_client = boto3.client(
        'iam',
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )

    #set s3 role name
    tfstaterolename        = 'S3Tfstate-' + joined_string + '-role'
    #set s3 policy name
    tfstatepolicyname   = 'S3Tfstate-' + joined_string +'-policy'
    #set s3 policy arn
    tfstatepolicyarn    = 'arn:aws:iam::'+ S3account_number + ':policy/' + tfstatepolicyname
    try:
            response_policy = iam_client.get_policy(PolicyArn=tfstatepolicyarn)
            policyexists = True
    except ClientError as e:
            print('Policy doesn\'t exists')
            policyexists = False  
    try:
        response_role = iam_client.get_role(RoleName=tfstaterolename)
        rolexists = True
    except ClientError as e:
            print('Role doesn\'t exists')
            rolexists = False
    if rolexists != False and policyexists !=False:
        # Delete the role
        # Detach the policy from the role
        try:
            iam_client.detach_role_policy(
            RoleName=tfstaterolename,
            PolicyArn=response_policy['Policy']['Arn']
            )    
            time.sleep(2)
            iam_client.delete_policy(PolicyArn=tfstatepolicyarn)
            iam_client.delete_role(RoleName=tfstaterolename)
            time.sleep(5)
            rolexists = False
        except ClientError as e:
            print(e)
            exit()
####################################################################    
    # define the trust relationship policy document
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": "arn:aws:iam::"+account_number+":role/CircleCI_Role"
                },
                "Action": "sts:AssumeRole",
                "Condition": {}
            },
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": "arn:aws:sts::"+account_number+":assumed-role/CircleCI_Role/AWS-KeyID"
                },
                "Action": "sts:AssumeRole",
                "Condition": {}
            }
        ]
    }
    custom_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowS3",
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:DeleteObject"
                ],
                "Resource": "arn:aws:s3:::/raxhlag-aws-org-terraform-state-backend/*"
            },
            {
                "Sid": "AllowListBucket",
                "Effect": "Allow",
                "Action": "s3:ListBucket",
                "Resource": [
                    "arn:aws:s3:::raxhlag-aws-org-terraform-state-backend",
                    "arn:aws:s3:::raxhlag-aws-org-terraform-state-backend/*"
                ]
            },
            {
                "Sid": "PutObjectS3",
                "Effect": "Allow",
                "Action": "s3:PutObject",
                "Resource": [
                    "arn:aws:s3:::raxhlag-aws-org-terraform-state-backend/*"
                ]
            },
            {
            "Effect": "Allow",
            "Action": [
                "s3:*",
                "s3-object-lambda:*"
            ],
            "Resource": "*"
            }
        ]
    }

    if rolexists == False:
        # create IAM role with the trust relationship policy
        role_name = tfstaterolename
        response_role = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument = json.dumps(trust_policy)
        )
        policy_description  = 'This is S3nbucket access policy for tfstate'
        response_policy     = iam_client.create_policy(
            PolicyName      = tfstatepolicyname,
            PolicyDocument  = json.dumps(custom_policy),
            Description     = policy_description
        )
        time.sleep(2)
        iam_client.attach_role_policy(
            PolicyArn=response_policy['Policy']['Arn'],
            RoleName=tfstaterolename
        )
    # modifing arn role
    # Open the input file in read mode
    with open(terraformmainpath, 'r') as input_file:
        # Open the output file in write mode
        with open(terraformmainnewpath, 'w') as output_file:
            # Loop over each line in the input file
            for line in input_file:
                # Check if this line contains the string you want to replace
                if re.search(r'"arn:aws:iam::<account_number>:role/<rolename>"', line):
                    # Replace the line with the new string
                    substring = '"' + response_role['Role']['Arn'] + '"'
                    new_line = re.sub(r'"arn:aws:iam::<account_number>:role/<rolename>"', substring, line)
                    output_file.write(new_line)
                else:
                    # Write the original line to the output file
                    output_file.write(line)
        output_file.close()
    input_file.close()                
    os.rename(terraformmainpath,terraformmainoldpath)
    os.rename(terraformmainnewpath,terraformmainpath)
    os.remove(terraformmainoldpath)
    time.sleep(15)

# deleting policy and role
if re.search(r'terraform-apply', jobname):
    session = boto3.Session()
    client = session.client('sts')
    try:
        assumed_role = client.assume_role_with_web_identity(
            RoleArn=rolearn,
            RoleSessionName='example-session',
            WebIdentityToken=circle_oidc_token,
        )
    except ClientError as e:
        print(e)
        exit()

    # Get temporary credentials
    credentials = assumed_role['Credentials']

    # Use the temporary credentials to access AWS resources
    iam_client = boto3.client(
        'iam',
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )
    #set s3 role name
    tfstaterolename     = 'S3Tfstate-' + joined_string + '-role'
    #set s3 policy name
    tfstatepolicyname   = 'S3Tfstate-' + joined_string +'-policy'
    #set s3 policy arn
    tfstatepolicyarn    = 'arn:aws:iam::'+ S3account_number + ':policy/' + tfstatepolicyname
    try:
        response_policy = iam_client.get_policy(PolicyArn=tfstatepolicyarn)
        policyexists = True
    except ClientError as e:
            print('Policy doesn\'t exists')
            policyexists = False  
    try:
        response_role = iam_client.get_role(RoleName=tfstaterolename)
        rolexists = True
    except ClientError as e:
            print('Role doesn\'t exists')
            rolexists = False
    if rolexists != False:
        # Delete the role
        # Detach the policy from the role
        iam_client.detach_role_policy(
            RoleName=tfstaterolename,
            PolicyArn=response_policy['Policy']['Arn']
        )
        time.sleep(2)
        iam_client.delete_policy(PolicyArn=tfstatepolicyarn)
        iam_client.delete_role(RoleName=tfstaterolename)
        
