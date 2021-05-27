VERSION = "0.0.9"
SUPPORTED_CLOUD_PROVIDERS = ["aws", "azure", "gcloud"]
DEFAULT_AWS_BUCKET_REGION = "us-west-2"
LIST_OF_VARIABLES_FILES = ["vars.tf", "variable.tf", "variables.tf"]
REQUIRED_VARIABLES = {"teamid": None, "prjid": None}
# FIPS endpoints
AWS_FIPS_US_WEST2_ENDPOINT = "s3-fips.us-west-2.amazonaws.com"
AZURE_FIPS_WESTUS2_ENDPOINT = ""
GCP_FIPS_WESTUS2_ENDPOINT = ""
# Error messages
MISSING_VARS = """
------------------------------------------
Required argument(s) missing: 'teamid', 'prjid', or 'workspace'
- 'teamid', 'prjid' can be defined using '-var' or '-var-file' e.g.
   - tf -c=gcloud plan -var='teamid=foo' -var='prjid=bar'
   - tf -c=gcloud plan -var-file=demo.tfvars
- 'workspace' can be defined using -w/--workspace='<workspace_name>'
- 'cloud' can be defined using -c/--cloud='aws' (supported values: gcloud, aws, or azure)

e.g: tf plan -c=gcloud -var=teamid=demo-team -var=prjid=demo-app -w=demo-workspace

(more information: https://github.com/tomarv2/tfremote)
------------------------------------------
"""
ARGS_REMOVED = (
    "-c",
    "--cloud",
    "-w",
    "--workspace",
    "default",
    "-s",
    "--state_key",
    "-nf",
    "--no-fips",
    "-f",
    "--fips",
)
PACKAGE_DESCRIPTION = """
Terraform remote state wrapper package
--------------------------------------
Usage: Set below env variables to begin (more information: https://github.com/tomarv2/tfremote):
TF_WORKSPACE_FILE_LOCATION
aws: TF_AWS_BUCKET, TF_AWS_PROFILE, TF_AWS_BUCKET_REGION=us-west-2
azure: TF_AZURE_STORAGE_ACCOUNT, TF_AZURE_CONTAINER, ARM_ACCESS_KEY
gcloud: TF_GCLOUD_BUCKET, TF_GCLOUD_CREDENTIALS
"""
