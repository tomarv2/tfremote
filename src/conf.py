VERSION = "0.0.8"
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
   - tf -cloud gcloud plan -var='teamid=foo' -var='prjid=bar'
   - tf -cloud gcloud plan -var-file demo.tfvars
- 'workspace' can be defined using -workspace='<workspace_name>'
- 'cloud' can be defined using -cloud='aws' (supported values: gcloud, aws, or azure)

e.g: tf plan -cloud=gcloud -var=teamid=demo-team -var=prjid=demo-app -workspace=demo-workspace
------------------------------------------
"""
