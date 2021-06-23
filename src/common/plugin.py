import argparse
import json
import logging
import os
import subprocess
import sys

import src.common as state
from src.common import run_command, validate_allowed_workspace
from src.conf import (
    ARGS_REMOVED,
    DEFAULT_AWS_BUCKET_REGION,
    MISSING_VARS,
    PACKAGE_DESCRIPTION,
    REQUIRED_AWS_ENV_VARIABLES,
    REQUIRED_AWS_KEY_ENV_VARIABLES,
    REQUIRED_AWS_PROFILE_ENV_VARIABLES,
    REQUIRED_AZURE_ENV_VARIABLES,
    REQUIRED_GCLOUD_ENV_VARIABLES,
    REQUIRED_VARIABLES,
    SUPPORTED_CLOUD_PROVIDERS,
    VERSION,
)
from src.logging import configure_logging

configure_logging()
logger = logging.getLogger()


class TerraformCommonWrapper:
    title = "Remote State Plugin"
    slug = "remote-state-management"
    description = "Configure Terraform remote state for GCP, AWS, and Azure"
    version = state.__version__
    args = None
    args_unknown = None
    logger = None
    storage_path = None
    s3_bucket = None
    s3_region = None
    aws_profile = None
    workspace_key_prefix = None
    var_data = {}
    required_vars = None

    def __init__(self):
        self.required_vars = REQUIRED_VARIABLES
        self.var_data = {}
        parser = argparse.ArgumentParser(
            description=PACKAGE_DESCRIPTION,
            formatter_class=argparse.RawTextHelpFormatter,
            add_help=True,
        )
        parser.add_argument(
            "-var",
            action="append",
            metavar="",
            dest="inline_vars",
            help="""Set Terraform configuration variable. This flag can be set multiple times""",
        )
        parser.add_argument(
            "-var-file",
            action="append",
            metavar="",
            dest="tfvar_files",
            help="""Set Terraform configuration variables from a file. This flag can be set multiple times""",
        )
        parser.add_argument(
            "-c",
            dest="cloud",
            default="aws",
            metavar="",
            help="Specify cloud provider (default: 'aws'). Supported values: gcloud, aws, or azure",
        )
        parser.add_argument(
            "-w",
            dest="workspace",
            default="default",
            metavar="",
            help="Specify existing workspace name(default: 'default')",
        )
        parser.add_argument(
            "-s",
            dest="state_key",
            default="terraform",
            metavar="",
            help="File name in remote state (default: 'terraform.tfstate')",
        )
        parser.add_argument(
            "-f",
            dest="fips",
            action="store_true",
            help="Enable FIPS endpoints (default: True)",
        )
        parser.add_argument(
            "-nf",
            dest="fips",
            action="store_false",
            help="Disable FIPS endpoints",
        )
        parser.set_defaults(fips=True)

        parser.add_argument(
            "-v",
            action="version",
            version="%(prog)s {version}".format(version=VERSION),
        )
        self.args, self.args_unknown = parser.parse_known_args()

    def configure_remotestate(self):
        """
        Configuring remote state
        """
        logger.debug("configuring remote state")
        run_command.parse_vars(self.var_data, self.args)
        state_key = "".join(vars(self.args)["state_key"])
        cloud = "".join(vars(self.args)["cloud"]).lower()
        if cloud not in SUPPORTED_CLOUD_PROVIDERS:
            logger.error("Incorrect cloud provider specified")
            raise SystemExit
        if cloud == "gcloud":
            for env_var in REQUIRED_GCLOUD_ENV_VARIABLES:
                if not os.getenv(env_var):
                    logger.error(
                        f"Required env. variables missing: {REQUIRED_GCLOUD_ENV_VARIABLES}"
                    )
                    raise SystemExit
        if cloud == "aws":
            for env_var in REQUIRED_AWS_ENV_VARIABLES:
                if not os.getenv(env_var):
                    logger.error(
                        f"Required environment variable(s) missing: {REQUIRED_AWS_ENV_VARIABLES} and {REQUIRED_AWS_PROFILE_ENV_VARIABLES} or {REQUIRED_AWS_KEY_ENV_VARIABLES}"
                    )
                    raise SystemExit

            creds_list = []
            for env_var in REQUIRED_AWS_PROFILE_ENV_VARIABLES:
                creds_list.append(env_var)
            for env_var in REQUIRED_AWS_KEY_ENV_VARIABLES:
                creds_list.append(env_var)

            if not creds_list:
                logger.error(
                    f"Required environment variable(s) missing: {REQUIRED_AWS_ENV_VARIABLES}, {REQUIRED_AWS_ENV_VARIABLES} or {REQUIRED_AWS_KEY_ENV_VARIABLES}"
                )
                raise SystemExit
        if cloud == "azure":
            for env_var in REQUIRED_AZURE_ENV_VARIABLES:
                if not os.getenv(env_var):
                    logger.error(
                        f"Required environment variable(s) missing: {REQUIRED_AZURE_ENV_VARIABLES}"
                    )
                    raise SystemExit
        fips = vars(self.args)["fips"]
        workspace = vars(self.args)["workspace"]
        if workspace is None or workspace == "":
            logger.error(MISSING_VARS)
            raise SystemExit
        else:
            if not validate_allowed_workspace.allowed_workspace(cloud, workspace, fips):
                logger.error(MISSING_VARS)
                raise SystemExit
        if not state_key.endswith(".tfstate"):
            state_key = state_key + ".tfstate"
        self.storage_path = run_command.build_tf_state_path(
            self.required_vars,
            self.var_data,
            state_key,
            workspace,
        )
        self.configure(workspace, cloud)
        if self.required_vars["prjid"] is None or self.required_vars["teamid"] is None:
            logger.error(MISSING_VARS)
            raise SystemExit
        else:
            set_remote_backend_status = self.set_remote_backend(
                self.required_vars["teamid"],
                self.required_vars["prjid"],
                workspace,
                fips,
                state_key,
                cloud,
            )
        logger.info(
            "Remote State backend is configured: {}".format(
                set_remote_backend_status,
            ),
        )
        if set_remote_backend_status:
            new_cmd = [x for x in sys.argv[1:] if not x.startswith(ARGS_REMOVED)]
            cmd = "terraform {}".format(
                run_command.create_command(new_cmd),
            )
            logger.info("Command: {}".format(cmd))
            ret_code = run_command.run_cmd(cmd)
            if ret_code == 0:
                exit(0)
            else:
                exit(1)
        else:
            raise Exception(
                "\nThere was an error setting the remote backend for AWS; aborting",
            )

    # set bucket details (get from env variables)
    def configure(self, workspace, cloud):
        """
        Configure bucket
        """
        logger.debug("Configure bucket")
        if cloud == "aws":
            logger.debug(f"Configuring remote state for {cloud}")
            self.aws_profile = os.getenv("TF_AWS_PROFILE")
            self.s3_bucket = os.getenv("TF_AWS_BUCKET")
            self.s3_region = os.getenv("TF_AWS_BUCKET_REGION")
            if (self.aws_profile is None) or (self.aws_profile == ""):
                if (
                    (os.getenv("AWS_ACCESS_KEY_ID") is None)
                    or (os.getenv("AWS_ACCESS_KEY_ID") == "")
                    and (os.getenv("AWS_SECRET_ACCESS_KEY") is None)
                    or (os.getenv("AWS_SECRET_ACCESS_KEY") == "")
                ):
                    logger.error(
                        "Please set TF_AWS_PROFILE or AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variable"
                    )
                    exit(1)
            if (self.s3_bucket is None) or (self.s3_bucket == ""):
                logger.error("Please set TF_AWS_BUCKET environment variable")
                exit(1)
            if (workspace is None) or (workspace == ""):
                logger.error(MISSING_VARS)
                exit(1)
            # TODO: fixed to use 'us-west-2', to be made global
            if (self.s3_region is None) or (self.s3_region == ""):
                if (self.aws_profile is None) or (self.aws_profile == ""):
                    p = subprocess.Popen(
                        [
                            "aws",
                            "s3api",
                            "get-bucket-location",
                            "--output",
                            "text",
                            "--bucket",
                            self.s3_bucket,
                        ],
                        stdout=subprocess.PIPE,
                    )
                else:
                    p = subprocess.Popen(
                        [
                            "aws",
                            "s3api",
                            "get-bucket-location",
                            "--output",
                            "text",
                            "--profile",
                            self.aws_profile,
                            "--bucket",
                            self.s3_bucket,
                        ],
                        stdout=subprocess.PIPE,
                    )
                self.s3_region = p.communicate()[0]
                if (self.s3_region is None) or (self.s3_region == ""):
                    logger.error(
                        'Unable to determine S3 bucket "{}" location.\nAWS profile used is "{}"'.format(
                            self.s3_bucket,
                            self.aws_profile,
                        ),
                    )
                    exit(1)
            logger.info(
                "[S3 bucket: {}] [AWS profile: {}] [AWS region: {}]".format(
                    self.s3_bucket,
                    self.aws_profile,
                    self.s3_region,
                ),
            )
        elif cloud == "azure":
            logger.debug(f"Configuring remote state for {cloud}")
            self.azure_container_name = os.getenv("TF_AZURE_CONTAINER")
            self.azure_stg_acc_name = os.getenv("TF_AZURE_STORAGE_ACCOUNT")
            self.azure_access_key = os.getenv("ARM_ACCESS_KEY")
            if (self.azure_container_name is None) or (self.azure_container_name == ""):
                logger.error(
                    "Please set TF_AZURE_CONTAINER environment variable",
                )
                exit(1)
            if (self.azure_stg_acc_name is None) or (self.azure_stg_acc_name == ""):
                logger.error(
                    "Please set TF_AZURE_STORAGE_ACCOUNT environment variable",
                )
                exit(1)
            if (workspace is None) or (workspace == ""):
                logger.error(MISSING_VARS)
                exit(1)
            if (self.azure_access_key is None) or (self.azure_access_key == ""):
                logger.error(
                    'Unable to determine TF_AZURE_ARM_ACCESS_KEY "{}"'.format(
                        self.azure_access_key,
                    ),
                )
                exit(1)
            logger.info(
                "[Azure Storage Account Name: {}] [Azure Container Name: {}]".format(
                    self.azure_stg_acc_name,
                    self.azure_container_name,
                ),
            )
        else:
            logger.debug(f"Configuring remote state for {cloud}")
            self.gcloud_bucket_name = os.getenv("TF_GCLOUD_BUCKET")
            self.gcloud_credentials = os.getenv("TF_GCLOUD_CREDENTIALS")
            if (self.gcloud_bucket_name is None) or (self.gcloud_bucket_name == ""):
                logger.error(
                    "Please set TF_GCLOUD_BUCKET environment variable",
                )
                exit(1)
            # different credentials for different env
            if (self.gcloud_credentials is None) or (self.gcloud_credentials == ""):
                logger.error(
                    "Please set TF_GCLOUD_CREDENTIALS environment variable",
                )
                exit(1)
            if (workspace is None) or (workspace == ""):
                logger.error(MISSING_VARS)
                exit(1)
            logger.info(
                "[gcloud bucket: {}] [gcloud credentials file path: {}]".format(
                    self.gcloud_bucket_name,
                    self.gcloud_credentials,
                ),
            )

    def set_remote_backend(self, teamid, prjid, workspace, fips, state_key, cloud):
        """
        Configure the Terraform remote state if necessary
        return True if remote state was successfully configured
        """
        logger.debug("configure remote state if necessary")
        if cloud == "aws":
            key_path = teamid + "/" + prjid
            current_tf_state = {"backend": {}}
            current_tf_state["backend"]["config"] = {}
            current_tf_state["backend"]["config"]["bucket"] = None
            current_tf_state["backend"]["config"]["key"] = None
            if "None" in self.storage_path:
                logger.error(MISSING_VARS)
                raise SystemExit
            else:
                if run_command.build_remote_backend_tf_file(
                    "s3", teamid, fips, state_key
                ):
                    if os.path.isfile(".terraform/terraform.tfstate"):
                        with open(".terraform/terraform.tfstate") as fh:
                            current_tf_state = json.load(fh)
                    if (
                        ("backend" in current_tf_state)
                        and (
                            current_tf_state["backend"]["config"]["bucket"]
                            == self.s3_bucket
                        )
                        and (
                            current_tf_state["backend"]["config"]["key"]
                            == self.storage_path
                        )
                        and (
                            current_tf_state["backend"]["config"][
                                "workspace_key_prefix"
                            ]
                            == workspace
                        )
                    ):
                        logger.debug("No need to pull remote state")
                        return True
                    else:
                        if os.path.isfile(".terraform/terraform.tfstate"):
                            os.unlink(".terraform/terraform.tfstate")
                            logger.debug("Removed .terraform/terraform.tfstate")

                        logger.info("Switching to using existing workspace")
                        if self.aws_profile is not None:
                            cmd = (
                                'terraform init -backend-config="bucket={}" '
                                '-backend-config="region={}" -backend-config="key={}" '
                                '-backend-config="workspace_key_prefix={}" -backend-config="acl=bucket-owner-full-control" '
                                '-backend-config="profile={}"'.format(
                                    self.s3_bucket,
                                    DEFAULT_AWS_BUCKET_REGION,
                                    self.storage_path,
                                    key_path,
                                    self.aws_profile,
                                )
                            )
                        else:
                            cmd = (
                                'terraform init -backend-config="bucket={}" '
                                '-backend-config="region={}" -backend-config="key={}" '
                                '-backend-config="workspace_key_prefix={}" -backend-config="acl=bucket-owner-full-control" '.format(
                                    self.s3_bucket,
                                    DEFAULT_AWS_BUCKET_REGION,
                                    self.storage_path,
                                    key_path,
                                )
                            )
                        logger.debug("init command: {}".format(cmd))
                        ret_code = run_command.run_cmd(cmd)
                        if ret_code == 0:
                            logger.info(f"Selecting/Creating Workspce {workspace}")
                            if (
                                run_command.run_cmd(
                                    f"terraform workspace select {workspace} || terraform workspace new {workspace}"
                                )
                                == 0
                            ):
                                return True
                        else:
                            return False
        elif cloud == "azure":
            logger.debug("Configure remote state if necessary")
            key_path = teamid + "/" + prjid
            current_tf_state = {"backend": {}}
            current_tf_state["backend"]["config"] = {}
            current_tf_state["backend"]["config"]["storage_account_name"] = None
            current_tf_state["backend"]["config"]["key"] = None
            if "None" in self.storage_path:
                logger.error(MISSING_VARS)
                raise SystemExit
            else:
                if run_command.build_remote_backend_tf_file(
                    "azurerm", teamid, fips, state_key
                ):
                    if os.path.isfile(".terraform/terraform.tfstate"):
                        with open(".terraform/terraform.tfstate") as fh:
                            current_tf_state = json.load(fh)
                    if (
                        ("backend" in current_tf_state)
                        and (
                            current_tf_state["backend"]["config"][
                                "storage_account_name"
                            ]
                            == self.azure_stg_acc_name
                        )
                        and (
                            current_tf_state["backend"]["config"]["key"]
                            == self.storage_path
                        )
                    ):
                        logger.debug("No need to pull remote state")
                        return True
                    else:
                        if os.path.isfile(".terraform/terraform.tfstate"):
                            os.unlink(".terraform/terraform.tfstate")
                            logger.debug("removed .terraform/terraform.tfstate")
                        cmd = 'terraform init -backend-config="storage_account_name={}" ' '-backend-config="key={}" -backend-config="container_name={}"'.format(
                            self.azure_stg_acc_name,
                            key_path + "/" + workspace + "/" + state_key,
                            self.azure_container_name,
                        )
                        logger.debug("init command: {}".format(cmd))
                        ret_code = run_command.run_cmd(cmd)
                        if ret_code == 0:
                            return True
                        else:
                            return False
        else:
            logger.debug("Setting remote state backend")
            key_path = teamid + "/" + prjid + "/" + workspace
            current_tf_state = {"backend": {}}
            current_tf_state["backend"]["config"] = {}
            current_tf_state["backend"]["config"]["bucket"] = None
            current_tf_state["backend"]["config"]["credentials"] = None
            if run_command.build_remote_backend_tf_file(
                "gcs", key_path, fips, state_key
            ):
                if os.path.isfile(".terraform/terraform.tfstate"):
                    with open(".terraform/terraform.tfstate") as fh:
                        current_tf_state = json.load(fh)
                if (
                    ("backend" in current_tf_state)
                    and (
                        current_tf_state["backend"]["config"]["bucket"]
                        == self.gcloud_bucket_name
                    )
                    and (
                        current_tf_state["backend"]["config"]["credentials"]
                        == self.gcloud_credentials
                    )
                    and (current_tf_state["backend"]["config"]["prefix"] == workspace)
                ):
                    logger.debug("No need to pull remote state")
                    return True
                else:
                    if os.path.isfile(".terraform/terraform.tfstate"):
                        os.unlink(".terraform/terraform.tfstate")
                        logger.debug("Removed .terraform/terraform.tfstate")
                    storage_path = self.storage_path.rsplit("/", 1)[0]
                    if "None" in storage_path:
                        logger.error(MISSING_VARS)
                        raise SystemExit
                    cmd = 'echo "1" | terraform init -backend-config="bucket={}" -backend-config="credentials={}" ' '-backend-config="prefix={}"'.format(
                        self.gcloud_bucket_name,
                        self.gcloud_credentials,
                        key_path,
                    )
                    logger.debug(f"Terraform init command: {cmd}")

                    # TODO: if 'prefix=' in cmd:
                    # verify contents of backend file

                    ret_code = run_command.run_cmd(cmd)
                    if ret_code == 0:
                        return True
                    else:
                        return False
