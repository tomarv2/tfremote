import argparse
import sys
import json
import os
import subprocess
import src.tf_aws as aws_state
from src.common import run_command

import logging
logger = logging.getLogger(__name__)


class TerraformAWSWrapper:
    title = "AWS State Plugin"
    slug = "aws-remote-state"
    description = "Configure AWS remote state"
    version = aws_state.__version__
    args = None
    args_unknown = None
    logger = None
    s3_path = None
    s3_bucket = None
    s3_region = None
    aws_profile = None

    def __init__(self):
        self.required_vars = None
        self.var_data = None
        parser = argparse.ArgumentParser(description="terraform wrapper script")
        parser.add_argument('-cloud', dest='cloud', help='specify the cloud: aws, gcloud, azure')
        parser.add_argument('-var-file', action='append', dest='tfvar_files', help='specify a tfvars file')
        parser.add_argument('-var', action='append', dest='inline_vars', help='specify a var')
        self.args, self.args_unknown = parser.parse_known_args()

    # set bucket details (get from env variables)
    def configure(self):
        self.aws_profile = os.getenv('TF_AWS_PROFILE')
        self.s3_bucket = os.getenv('TF_AWS_BUCKET')
        self.s3_region = os.getenv('TF_AWS_BUCKET_REGION')
        if (self.aws_profile is None) or (self.aws_profile == ""):
            logger.error("Please set the TF_AWS_PROFILE environment variable")
            exit(1)
        if (self.s3_bucket is None) or (self.s3_bucket == ""):
            logger.error("Please set the TF_AWS_BUCKET environment variable")
            exit(1)
        # TODO: fixed to use 'us-west-2', to be made global
        if (self.s3_region is None) or (self.s3_region == ""):
            p = subprocess.Popen(
                ['aws', 's3api', 'get-bucket-location', '--output', 'text', '--profile', self.aws_profile, '--bucket',
                 self.s3_bucket], stdout=subprocess.PIPE)
            self.s3_region = p.communicate()[0]
            if (self.s3_region is None) or (self.s3_region == ""):
                logger.error("unable to determine S3 bucket \"{}\" location.  AWS profile used is \"{}\"" .format(
                    self.s3_bucket, self.aws_profile))
                exit(1)
        logger.info("[S3 bucket: {}] [AWS profile: {}] [AWS region: {}]" .format(self.s3_bucket, self.aws_profile,
                                                                                 self.s3_region))

    def configure_remotestate(self, required_vars, var_data):
        self.required_vars = required_vars
        self.var_data = var_data
        run_command.parse_vars(self.var_data, self.args)
        self.s3_path = run_command.build_tf_state_path(self.required_vars, self.var_data)
        self.configure()
        set_remote_backend_status = self.set_remote_backend()
        logger.info("Remote State backend is configured: {0}" .format(set_remote_backend_status))
        if set_remote_backend_status:
            cmd = "terraform {}" .format(run_command.create_command(sys.argv[1:]))
            logger.info("AWS command: {}" .format(cmd))
            ret_code = run_command.run_cmd(cmd)
            if ret_code == 0:
                exit(0)
            else:
                exit(1)
        else:
            raise Exception("\nThere was an error setting the remote backend for AWS; aborting")

    def set_remote_backend(self):
        """
        configure the Terraform remote state if necessary
        return True if remote state was successfully configured
        """
        current_tf_state = {"backend": {}}
        current_tf_state["backend"]["config"] = {}
        current_tf_state["backend"]["config"]["bucket"] = None
        current_tf_state["backend"]["config"]["key"] = None
        if run_command.build_remote_backend_tf_file('s3'):
            if os.path.isfile(".terraform/terraform.tfstate"):
                with open(".terraform/terraform.tfstate") as fh:
                    current_tf_state = json.load(fh)
            if ("backend" in current_tf_state) and (
                    current_tf_state["backend"]["config"]["bucket"] == self.s3_bucket) and (
                    current_tf_state["backend"]["config"]["key"] == self.s3_path):
                logger.debug("No need to pull remote state")
                return True
            else:
                if os.path.isfile(".terraform/terraform.tfstate"):
                    os.unlink(".terraform/terraform.tfstate")
                    logger.debug("Removed .terraform/terraform.tfstate")
                cmd = "terraform init -backend-config=\"bucket={}\" -backend-config=\"region={}\" -backend-config=" \
                      "\"key={}\" -backend-config=\"acl=bucket-owner-full-control\" -backend-config=\"profile={}\"" \
                    .format(self.s3_bucket, 'us-west-2', self.s3_path, self.aws_profile)
                logger.debug("init command: {}" .format(cmd))
                ret_code = run_command.run_cmd(cmd)
                if ret_code == 0:
                    return True
                else:
                    return False
