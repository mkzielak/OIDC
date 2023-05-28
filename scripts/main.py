import csv
import git
import sys
import jinja2
import os
import re

#pipeline_temp_path  = "C:\\temp\\aws-A_000_EnvironmentVariablesTest_W00_Dev\\scripts\\config_tmpl.yml"
#pipeline_out_path   = "C:\\temp\\aws-A_000_EnvironmentVariablesTest_W00_Dev\\scripts\\generated_config.yml"
#terraformtfvars     = "C:\\temp\\aws-A_000_EnvironmentVariablesTest_W00_Dev\\layers\\000base\\terraform.tfvars"
#workingdir          = "00base"
pipeline_temp_path   = "./scripts/pipe_template.yml"
pipeline_out_path    =  "./.circleci/generated_config.yml"
workingdir           = sys.argv[1]
terraformtfvars      = "./layers/" + workingdir + "/terraform.tfvars"           

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

        # Load the template from the file
with open(pipeline_temp_path, 'r') as f:
    template = jinja2.Template(f.read())
    # Render the template with the variables
    config_data = template.render(debug=True, account_number=account_number, workingdir=workingdir)
    # Write thpipeline_out_path, "a") as conf:
    with open(pipeline_out_path, "a") as conf:
        conf.write(config_data)
    conf.close()
f.close()
       

#-------------------------- TO DELETE
with open(pipeline_out_path, 'r') as f:
    print(f.read())


