# Terraform remote state management for AWS, Azure, GCP

A Python package to manage Terraform remote state across AWS, Azure, and GCP.

To install package run: `pip install tfremote`


## Google slides
https://docs.google.com/presentation/d/1ZX_56ChDopA3qDVMVRvdH8z6pvi6IO9WwKwUtsN78nY


## Environment setup

- Using virtualenv is strongly recommended
- Install Python 3.6+
- Terraform 0.12.0 and above (download: https://www.terraform.io/downloads.html)


Default loglevel is `WARNING`, to change it using:
`export TF_LOG_LEVEL`

## Setup environment variables

### AWS

s3 bucket for remotestate should reside in `us-west-2` (best practice is to have it versioned)

Set these env variables:

```
export TF_AWS_BUCKET=<your_remote_state_bucket_name>
export TF_AWS_PROFILE=default
export TF_AWS_BUCKET_REGION=us-west-2 
export PATH=$PATH:/usr/local/bin/
```

### Azure

Run remote_state.sh script located under `Azure` -> `_scripts` -> `remote_state.sh` (fill in the required information)

Set these env variables:

```
export TF_AZURE_STORAGE_ACCOUNT=tfstatexxxxx # Output of remote_state.sh
export TF_AZURE_CONTAINER=tfstate # Output of remote_state.sh
export ARM_ACCESS_KEY=xxxxxxxxxx # Output of remote_state.sh
```

### GCP

https://cloud.google.com/community/tutorials/managing-gcp-projects-with-terraform

Set these env variables:

```
export TF_GCLOUD_BUCKET=XXXX # change it to right value
export TF_GCLOUD_PREFIX=# change it to right value
export TF_GCLOUD_CRENDETIALS=<path to service account .json credentials file>
```

## How to use

Once environment variables are configured run for the cloud provider, run:

```
tfremote -cloud aws plan -var-file ../custom.tfvars
```

## NOTE: 
The module have been tested with python 3.8