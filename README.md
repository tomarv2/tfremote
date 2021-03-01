<p align="center">
    <a href="https://github.com/tomarv2/tfremote/actions/workflows/unit_test.yml" alt="GitHub tag">
        <img src="https://github.com/tomarv2/tfremote/actions/workflows/unit_test.yml/badge.svg?branch=main" /></a>
    <a href="https://www.apache.org/licenses/LICENSE-2.0" alt="GitHub tag">
        <img src="https://img.shields.io/github/license/tomarv2/tfremote" /></a>
    <a href="https://github.com/tomarv2/tfremote/tags" alt="GitHub tag">
        <img src="https://img.shields.io/github/v/tag/tomarv2/tfremote" /></a>
    <a href="https://github.com/tomarv2/tfremote/pulse" alt="Activity">
        <img src="https://img.shields.io/github/commit-activity/m/tomarv2/tfremote" /></a>
    <a href="https://stackoverflow.com/users/6679867/tomarv2" alt="Stack Exchange reputation">
        <img src="https://img.shields.io/stackexchange/stackoverflow/r/6679867"></a>
    <a href="https://discord.gg/XH975bzN" alt="chat on Discord">
        <img src="https://img.shields.io/discord/813961944443912223?logo=discord"></a>
    <a href="https://twitter.com/intent/follow?screen_name=varuntomar2019" alt="follow on Twitter">
        <img src="https://img.shields.io/twitter/follow/varuntomar2019?style=social&logo=twitter"></a>
</p>
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

## To run tox:

#### Update Sphinx documentation
tox -e docs