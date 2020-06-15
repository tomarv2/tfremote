import argparse
import sys
import json
import os
import src.tf_azure as azure_state
from src.common import run_command

import logging
logger = logging.getLogger(__name__)


class TerraformAzureWrapper:
    title = "Azure State Plugin"
    slug = "azure-remote-state"
    description = "Configure Azure remote state"
    version = azure_state.__version__
    args = None
    args_unknown = None
    logger = None
    azure_container_name = None
    azure_stg_acc_name = None
    azure_access_key = None
    azure_path = None

    def __init__(self):
        self.required_vars = None
        self.var_data = None
        parser = argparse.ArgumentParser(description="terraform wrapper script")
        parser.add_argument('-cloud', dest='cloud', help='specify the cloud: aws, gcloud, azure')
        parser.add_argument('-var-file', action='append', dest='tfvar_files', help='specify a tfvars file')
        parser.add_argument('-var', action='append', dest='inline_vars', help='specify a var')
        self.args, self.args_unknown = parser.parse_known_args()

    # set azure storage account details (get from env variables)
    def configure(self):
        self.azure_container_name = os.getenv('TF_AZURE_CONTAINER')
        self.azure_stg_acc_name = os.getenv('TF_AZURE_STORAGE_ACCOUNT')
        self.azure_access_key = os.getenv('ARM_ACCESS_KEY')
        if (self.azure_container_name is None) or (self.azure_container_name == ""):
            logger.error("Please set the TF_AZURE_CONTAINER environment variable")
            exit(1)
        if (self.azure_stg_acc_name is None) or (self.azure_stg_acc_name == ""):
            logger.error("Please set the TF_AZURE_STORAGE_ACCOUNT environment variable")
            exit(1)
        if (self.azure_access_key is None) or (self.azure_access_key == ""):
            logger.error("Unable to determine TF_AZURE_ARM_ACCESS_KEY \"{}\"" .format(self.azure_access_key))
            exit(1)
        logger.info("[Azure Storage Account Name: {}] [Azure Container Name: {}]" .format(
            self.azure_stg_acc_name, self.azure_container_name))

    def configure_remotestate(self, required_vars, var_data):
        self.required_vars = required_vars
        self.var_data = var_data
        run_command.parse_vars(self.var_data, self.args)
        self.azure_path = run_command.build_tf_state_path(self.required_vars, self.var_data)
        self.configure()
        set_remote_backend_status = self.set_remote_backend()
        logger.info("Remote State backend is configured: {0}".format(set_remote_backend_status))
        if set_remote_backend_status:
            cmd = "terraform {}" .format(run_command.create_command(sys.argv[1:]))
            logger.info("AZURE command: {}".format(cmd))
            ret_code = run_command.run_cmd(cmd)
            if ret_code == 0:
                exit(0)
            else:
                exit(1)
        else:
            raise Exception("\nThere was an error setting the remote backend for Azure; aborting")

    def set_remote_backend(self):
        """
        configure the Terraform remote state if necessary
        return True if remote state was successfully configured
        """
        current_tf_state = {"backend": {}}
        current_tf_state["backend"]["config"] = {}
        current_tf_state["backend"]["config"]["storage_account_name"] = None
        current_tf_state["backend"]["config"]["key"] = None
        if run_command.build_remote_backend_tf_file('azurerm'):
            if os.path.isfile(".terraform/terraform.tfstate"):
                with open(".terraform/terraform.tfstate") as fh:
                    current_tf_state = json.load(fh)
            if ("backend" in current_tf_state) and (
                    current_tf_state["backend"]["config"]["storage_account_name"] == self.azure_stg_acc_name) and (
                    current_tf_state["backend"]["config"]["key"] == self.azure_path):
                logger.debug("no need to pull remote state")
                return True
            else:
                if os.path.isfile(".terraform/terraform.tfstate"):
                    os.unlink(".terraform/terraform.tfstate")
                    logger.debug("removed .terraform/terraform.tfstate")
                cmd = "terraform init -backend-config=\"storage_account_name={}\" -backend-config=\"key={}\" " \
                      "-backend-config=\"container_name={}\"" .format(
                    self.azure_stg_acc_name, self.azure_path, self.azure_container_name)
                logger.debug("init command: {}" .format(cmd))
                ret_code = run_command.run_cmd(cmd)
                if ret_code == 0:
                    return True
                else:
                    return False


