import argparse
import json
import logging
import os
import subprocess
import sys

import src.tf_aws as aws_state
from src.common import run_command
from src.conf import DEFAULT_AWS_BUCKET_REGION, REQUIRED_VARIABLES
from src.logging import configure_logging

configure_logging()
logger = logging.getLogger()


class TerraformAWSWrapper:
    title = "AWS State Plugin"
    slug = "aws-remote-state"
    description = "Configure AWS remote state"
    version = aws_state.__version__
    aws_args = None
    args_unknown = None
    logger = None
    s3_path = None
    s3_bucket = None
    s3_region = None
    aws_profile = None
    workspace_key_prefix = None
    var_data = {}
    required_vars = REQUIRED_VARIABLES

    def __init__(self):
        self.required_vars = REQUIRED_VARIABLES
        self.var_data = {}
        parser = argparse.ArgumentParser(
            description="Terraform remote state wrapper package", add_help=True
        )
        parser.add_argument(
            "-var-file",
            action="append",
            metavar="",
            dest="tfvar_files",
            help="specify .tfvars file(s)",
        )
        parser.add_argument(
            "-var",
            action="append",
            metavar="",
            dest="inline_vars",
            help="specify inline variable(s)",
        )
        # parser.add_argument(
        #     "-cloud",
        #     dest="cloud",
        #     metavar="",
        #     help="specify the cloud provider: gcloud, aws, or azure",
        # )
        parser.add_argument(
            "-workspace",
            dest="workspace",
            metavar="",
            help="workspace name",
        )
        parser.add_argument(
            "-state_key",
            dest="state_key",
            default="terraform",
            metavar="",
            help="file name in remote state(default: 'terraform.tfstate')",
        )
        parser.add_argument(
            "-fips",
            dest="fips",
            action="store_true",
            help="enable FIPS endpoints(default: True)",
        )
        parser.add_argument(
            "-no-fips", dest="fips", action="store_false", help="disable FIPS endpoints"
        )
        parser.set_defaults(fips=True)

        parser.add_argument("-version", action="version", version="%(prog)s 0.1")

        self.aws_args, self.aws_args_unknown = parser.parse_known_args()

    def configure_remotestate(self):
        logger.debug("configuring remote state")
        run_command.parse_vars(self.var_data, self.aws_args)
        self.s3_path = run_command.build_tf_state_path(
            self.required_vars,
            self.var_data,
            "".join(vars(self.aws_args)["state_key"]),
            vars(self.aws_args)["workspace"],
        )
        self.configure(vars(self.aws_args)["workspace"])
        if self.required_vars["prjid"] is None or self.required_vars["teamid"] is None:
            logger.error("required variables 'teamid' and 'prjid' not defined.")
            raise SystemExit
        else:
            set_remote_backend_status = self.set_remote_backend(
                self.required_vars["teamid"],
                self.required_vars["prjid"],
                vars(self.aws_args)["workspace"],
                vars(self.aws_args)["fips"],
                vars(self.aws_args)["state_key"],
            )
        logger.info(
            "Remote State backend is configured: {}".format(
                set_remote_backend_status,
            ),
        )
        if set_remote_backend_status:
            new_cmd = [
                x
                for x in sys.argv[1:]
                if not x.startswith(
                    ("-workspace", "default", "-state_key", "-no-fips", "-fips")
                )
            ]
            cmd = "terraform {}".format(
                run_command.create_command(new_cmd),
            )
            logger.info("AWS command: {}".format(cmd))
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
    def configure(self, workspace):
        logger.debug("configuring backend")
        self.aws_profile = os.getenv("TF_AWS_PROFILE")
        self.s3_bucket = os.getenv("TF_AWS_BUCKET")
        self.s3_region = os.getenv("TF_AWS_BUCKET_REGION")
        if (self.aws_profile is None) or (self.aws_profile == ""):
            logger.error("Please set the TF_AWS_PROFILE environment variable")
            exit(1)
        if (self.s3_bucket is None) or (self.s3_bucket == ""):
            logger.error("Please set the TF_AWS_BUCKET environment variable")
            exit(1)
        if (workspace is None) or (workspace == ""):
            logger.error("Please set the workspace using -workspace=<workspace_name>")
            exit(1)
        # TODO: fixed to use 'us-west-2', to be made global
        if (self.s3_region is None) or (self.s3_region == ""):
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
                    'unable to determine S3 bucket "{}" location.  AWS profile used is "{}"'.format(
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

    def set_remote_backend(self, teamid, prjid, workspace, fips, state_key):
        """
        configure the Terraform remote state if necessary
        return True if remote state was successfully configured
        """
        logger.debug("configure remote state if necessary")
        key_path = teamid + "/" + prjid
        current_tf_state = {"backend": {}}
        current_tf_state["backend"]["config"] = {}
        current_tf_state["backend"]["config"]["bucket"] = None
        current_tf_state["backend"]["config"]["key"] = None
        if "None" in self.s3_path:
            logger.error(
                """
                    Required values missing:
                    please specify: "teamid", "prjid", and "workspace"
                    "teamid", "prjid" can be specified using '-vars' or '-tfvars' e.g.
                        - tf -cloud aws plan -var='teamid=foo' -var='prjid=bar'
                        - tf -cloud aws plan -var-file /tmp/demo.tfvars
                    "workspace" can be specified using '-var' e.g.
                        - tf -cloud aws plan -workspace=demo-workspace
                """
            )
            raise SystemExit
        else:
            if run_command.build_remote_backend_tf_file("s3", teamid, fips, state_key):
                if os.path.isfile(".terraform/terraform.tfstate"):
                    with open(".terraform/terraform.tfstate") as fh:
                        current_tf_state = json.load(fh)
                if (
                    ("backend" in current_tf_state)
                    and (
                        current_tf_state["backend"]["config"]["bucket"]
                        == self.s3_bucket
                    )
                    and (current_tf_state["backend"]["config"]["key"] == self.s3_path)
                    and (
                        current_tf_state["backend"]["config"]["workspace_key_prefix"]
                        == workspace
                    )
                ):
                    logger.debug("No need to pull remote state")
                    return True
                else:
                    if os.path.isfile(".terraform/terraform.tfstate"):
                        os.unlink(".terraform/terraform.tfstate")
                        logger.debug("Removed .terraform/terraform.tfstate")

                    cmd = 'echo "1" | TF_WORKSPACE={} terraform init -backend-config="bucket={}" -backend-config="region={}" -backend-config="key={}" -backend-config="workspace_key_prefix={}" -backend-config="acl=bucket-owner-full-control" -backend-config="profile={}"'.format(
                        workspace,
                        self.s3_bucket,
                        DEFAULT_AWS_BUCKET_REGION,
                        self.s3_path,
                        key_path,
                        self.aws_profile,
                    )
                    logger.debug("init command: {}".format(cmd))
                    ret_code = run_command.run_cmd(cmd)
                    if ret_code == 0:
                        return True
                    else:
                        return False
