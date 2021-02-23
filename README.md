[![](https://img.shields.io/badge/license-Apache%202-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)
# Terraform Remote State Manager

A Python package for managing Terraform remote state for: AWS, Azure, and Gcloud(GCP).

To install package run: 
```
pip install tfremote  --upgrade
```

## Environment setup

- Install Python 3.6+

- Using virtualenv is strongly recommended:
```
python3 -m venv <venv name>
```

- Terraform 0.12.0 and above (download: https://www.terraform.io/downloads.html)


Default log level is `WARNING`, to change:

`export TF_LOG_LEVEL` to any of these: `'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'`

## Setup environment variables

### AWS

s3 bucket for remote state should reside in `us-west-2` (best practice is to have it versioned)

Set these env variables:

```
export TF_AWS_BUCKET=<your_remote_state_bucket_name>
export TF_AWS_PROFILE=default
export TF_AWS_BUCKET_REGION=us-west-2 
export PATH=$PATH:/usr/local/bin/
```

### Azure

To create storage for remote state there is handy script.

Run `remote_state.sh` scripts located under `scripts` (fill in the required information)

Set these env variables:

```
export TF_AZURE_STORAGE_ACCOUNT=tfstatexxxxx # Output of remote_state.sh
export TF_AZURE_CONTAINER=tfstate # Output of remote_state.sh
export ARM_ACCESS_KEY=xxxxxxxxxx # Output of remote_state.sh
```

### Gcloud

https://cloud.google.com/community/tutorials/managing-gcp-projects-with-terraform

Set these env variables:

```
# Google storage bucket name
export TF_GCLOUD_BUCKET= # change it to right value
# Folders inside the bucket
export TF_GCLOUD_PREFIX= # change it to right value
# Path to google service account file
export TF_GCLOUD_CREDENTIALS= # change it to right value
```

## How to use

Once environment variables are configured, run:

### For aws:
```
tf -cloud aws plan -var-file ../custom.tfvars 

or 

tf plan -var-file ../demo.tfvars -var 'foo=bar'  -var 'john=doe' -cloud aws
```

### For azure:
```
tf plan -var-file ../custom.tfvars -cloud azure 

or

tf plan -var-file ../custom.tfvars -var 'foo=bar' -var 'john=doe' -cloud azure
```

### For gcloud:
```
tf plan -var-file ../custom.tfvars -cloud gcloud 

or

tf plan -var-file ../custom.tfvars -var 'foo=bar' -cloud gcloud -var 'john=doe' 
```
