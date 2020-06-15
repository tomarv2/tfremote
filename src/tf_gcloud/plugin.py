import argparse
import sys
import json
import os
import src.tf_gcloud as gcloud_state
from src.common import run_command

import logging
logger = logging.getLogger(__name__)


class TerraformGcloudWrapper:
    title = "Gcloud State Plugin"
    slug = "gcloud-remote-state"
    description = "Configure Gcloud remote state"
    version = gcloud_state.__version__
    args = None
    args_unknown = None
    logger = None
    gcloud_path = None
    gcloud_bucket_name = None
    gcloud_credentials = None
    gcloud_prefix = None

    def __init__(self):
        self.required_vars = None
        self.var_data = None
        parser = argparse.ArgumentParser(description="terraform wrapper script")
        parser.add_argument('-cloud', dest='cloud', help='specify the cloud: aws, gcloud, azure')
        parser.add_argument('-var-file', action='append', dest='tfvar_files', help='specify a tfvars file')
        parser.add_argument('-var', action='append', dest='inline_vars', help='specify a var')
        self.args, self.args_unknown = parser.parse_known_args()

    # set google storage account details (get from env variables)
    def configure(self):
        self.gcloud_prefix = os.getenv('TF_GCLOUD_PREFIX')
        self.gcloud_bucket_name = os.getenv('TF_GCLOUD_BUCKET')
        self.gcloud_credentials = os.getenv('TF_GCLOUD_CREDENTIALS')
        if (self.gcloud_prefix is None) or (self.gcloud_prefix == ""):
            logger.error("Please set the TF_GCLOUD_PREFIX environment variable")
            exit(1)
        if (self.gcloud_bucket_name is None) or (self.gcloud_bucket_name == ""):
            logger.error("Please set the TF_GCLOUD_BUCKET environment variable")
            exit(1)
        # different credentials for different env
        if (self.gcloud_credentials is None) or (self.gcloud_credentials == ""):
            logger.error("Please set the TF_GCLOUD_CREDENTIALS environment variable")
            exit(1)
        logger.info("[gcloud bucket: {}] [gcloud credentials file path: {}]" .format(self.gcloud_bucket_name,
                                                                                     self.gcloud_credentials))

    def configure_remotestate(self, required_vars, var_data):
        self.required_vars = required_vars
        self.var_data = var_data
        run_command.parse_vars(self.var_data, self.args)
        self.gcloud_path = run_command.build_tf_state_path(self.required_vars, self.var_data)
        self.configure()
        set_remote_backend_status = self.set_remote_backend()
        logger.info("set_remote_backend_status: {}".format(set_remote_backend_status))
        if set_remote_backend_status:
            cmd = "terraform {}" .format(run_command.create_command(sys.argv[1:]))
            logger.info("GCLOUD command: {}".format(cmd))
            ret_code = run_command.run_cmd(cmd)
            if ret_code == 0:
                exit(0)
            else:
                exit(1)
        else:
            raise Exception("\nThere was an error setting the remote backend for gcloud; aborting")

    def set_remote_backend(self):
        """
        configure the Terraform remote state if necessary
        return True if remote state was successfully configured
        """
        current_tf_state = {"backend": {}}
        current_tf_state["backend"]["config"] = {}
        current_tf_state["backend"]["config"]["bucket"] = None
        current_tf_state["backend"]["config"]["credentials"] = None
        if run_command.build_remote_backend_tf_file('gcs'):
            if os.path.isfile(".terraform/terraform.tfstate"):
                with open(".terraform/terraform.tfstate") as fh:
                    current_tf_state = json.load(fh)
            if ("backend" in current_tf_state) and (
                    current_tf_state["backend"]["config"]["bucket"] == self.gcloud_bucket_name) and (
                    current_tf_state["backend"]["config"]["credentials"] == self.gcloud_credentials):
                logger.debug("no need to pull remote state")
                return True
            else:
                if os.path.isfile(".terraform/terraform.tfstate"):
                    os.unlink(".terraform/terraform.tfstate")
                    logger.debug("removed .terraform/terraform.tfstate")
                gcloud_path = self.gcloud_path.rsplit('/', 1)[0]
                cmd = "terraform init -backend-config=\"bucket={}\" -backend-config=\"credentials={}\" " \
                      "-backend-config=\"prefix={}\"".format(self.gcloud_bucket_name, self.gcloud_credentials,
                                                             gcloud_path)
                logger.debug("init command: {}".format(cmd))

                # TODO: if 'prefix=' in cmd:
                # verify contents of backend file

                ret_code = run_command.run_cmd(cmd)
                if ret_code == 0:
                    return True
                else:
                    return False

