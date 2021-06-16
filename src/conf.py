VERSION = "0.0.23"
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
Required argument(s)
 missing: 'teamid', 'prjid or invalid 'workspace' provided:
- 'teamid', 'prjid' can be defined using '-var' or '-var-file' e.g.
   - tf -c=gcloud plan -var='teamid=foo' -var='prjid=bar'
   - tf -c=gcloud plan -var-file=demo.tfvars
- 'workspace' can be defined using '-w' (if no workspace is provided 'default' workspace is used).
  Supported workspace are parsed from TF_WORKSPACE_FILE_LOCATION

e.g: tf plan -c=gcloud -var=teamid=demo-team -var=prjid=demo-app -w=demo-workspace

(more information: https://github.com/tomarv2/tfremote)
------------------------------------------
"""
ARGS_REMOVED = (
    "-c",
    "-w",
    "default",
    "-s",
    "-nf",
    "-f",
)
PACKAGE_DESCRIPTION = """
Terraform remote state wrapper package
--------------------------------------
Usage: Set below env variables to begin (more information: https://github.com/tomarv2/tfremote):
TF_WORKSPACE_FILE_LOCATION
aws: TF_AWS_BUCKET, TF_AWS_PROFILE or , TF_AWS_BUCKET_REGION=us-west-2
azure: TF_AZURE_STORAGE_ACCOUNT, TF_AZURE_CONTAINER, ARM_ACCESS_KEY
gcloud: TF_GCLOUD_BUCKET, TF_GCLOUD_CREDENTIALS
"""
REQUIRED_GCLOUD_ENV_VARIABLES = [
    "TF_GCLOUD_BUCKET",
    "TF_GCLOUD_CREDENTIALS",
]
REQUIRED_AWS_ENV_VARIABLES = [
    "TF_AWS_BUCKET",
    "TF_AWS_BUCKET_REGION",
]
REQUIRED_AWS_PROFILE_ENV_VARIABLES = [
    "TF_AWS_PROFILE",
]
REQUIRED_AWS_KEY_ENV_VARIABLES = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
REQUIRED_AZURE_ENV_VARIABLES = [
    "TF_AZURE_STORAGE_ACCOUNT",
    "TF_AZURE_CONTAINER",
    "ARM_ACCESS_KEY",
]

WORKSPACES_YML = """
aws:
  - name: "aws-demo"
    account_id: "123456789012"
    workspaces: ["aws-demo.us-west-2.prod", "aws-demo.us-west-2.dev", "aws-demo.us-west-2.staging"]

  - name: "aws-test"
    account_id: "987654321012"
    workspaces: ["aws-test.us-west-2.prod", "aws-test.us-west-2.dev", "aws-test.us-west-2.staging"]
"""
