<p align="center">
    <a href="https://github.com/tomarv2/tfremote/actions/workflows/checks.yml" alt="Check">
        <img src="https://github.com/tomarv2/tfremote/actions/workflows/checks.yml/badge.svg?branch=main" /></a>
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

# Terraform Remote State Manager([tfremote](https://pypi.org/project/tfremote/))

**tf** is a python package for managing terraform remote state for: Google(GCP), AWS, and Azure.
It sets a defined structure for all cloud providers by removing the overheard of configuring and managing the path in storage buckets.

It works with:

:point_right: Google Storage Bucket

:point_right: AWS S3

:point_right: Azure Storage

> ❗️ **Note** Best practice is to make sure buckets are versioned.

## Install package

```
pip install tfremote --upgrade
```

## Environment setup

- Install Python 3.8+

- Using virtualenv is strongly recommended:

```
python3 -m venv <venv name>
```

- Terraform 0.14.0 and above (download: https://www.terraform.io/downloads.html)

Default log level is `WARNING`, to change:

`export TF_LOG_LEVEL` to any of these: `'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'`

> ❗️ **Important** - Three variables are required for using `tf` package:
>
> - teamid
> - prjid
> - workspace
>
> Three variables are required to set backend path in the remote storage: `teamid`, `prjid`, and `workspace`
>
> `teamid` and `prjid` can be defined using:
>
> - As `inline variables` e.g.: `-var='teamid=demo-team' -var='prjid=demo-project'`
> - Inside `.tfvars` file e.g.: `-var-file=<tfvars file location> `
>
> `workspace` can be defined using:
>
> - `-workspace=<workspace_name>`
>
> For more information refer to [Terraform documentation](https://www.terraform.io/docs/language/values/variables.html)

## Setup environment variables

### AWS

> ❗️ **Important** - s3 bucket for remote state should reside in `us-west-2`

Set below env variables:

```
export TF_AWS_BUCKET=<your_remote_state_bucket_name>
export TF_AWS_PROFILE=default
export TF_AWS_BUCKET_REGION=us-west-2
```

### Azure

To create storage for remote state there is handy script.

Run `scripts/remote_state.sh` (fill in the required information)

Set below env variables:

```
export TF_AZURE_STORAGE_ACCOUNT=tfstatexxxxx # Output of remote_state.sh
export TF_AZURE_CONTAINER=tfstate # Output of remote_state.sh
export ARM_ACCESS_KEY=xxxxxxxxxx # Output of remote_state.sh
```

### GCP(Gcloud)

https://cloud.google.com/community/tutorials/managing-gcp-projects-with-terraform

Set below env variables:

```
# Google storage bucket name
export TF_GCLOUD_BUCKET= # change it to right value
# Path to google service account file
export TF_GCLOUD_CREDENTIALS= # change it to right value
```

## How to use

### For Gcloud:

```
tf plan -cloud=gcloud -var=teamid=demo-team -var=prjid=demo-app -workspace=demo-workspace
```

The structure in Google Storage Bucket:

![alt text](docs/images/google_tf.png)

### For AWS:

```
tf plan -cloud=aws -var=teamid=demo-team -var=prjid=demo-app -workspace=demo-workspace
```

The structure in AWS S3:

![alt text](docs/images/aws_tf.png)

If you need to specify `state_key` in S3, specify `-state_key=tryme-key`

### For Azure:

```
tf plan -cloud=azure -var=teamid=demo-team -var=prjid=demo-app -workspace=demo-workspace
```

The structure in Azure Storage:

![alt text](docs/images/azure_tf.png)

### For more available options:

```
tf -h
usage: tf [-h] [-var-file] [-var] [-cloud] [-workspace] [-state_key] [-fips] [-no-fips] [-v]

Terraform remote state wrapper package

optional arguments:
  -h, --help     show this help message and exit
  -var-file      specify .tfvars file(s)
  -var           specify inline variable(s)
  -cloud         specify cloud provider (default: 'aws'). Supported values: gcloud, aws, or azure)
  -workspace     workspace name
  -state_key     file name in remote state(default: 'terraform.tfstate')
  -fips          enable FIPS endpoints(default: True)
  -no-fips       disable FIPS endpoints
  -v, --version  show program's version number and exit

```
