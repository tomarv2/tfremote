import argparse
import json
import logging
import os
import sys

import src.tf_azure as azure_state
from src.common import run_command
from src.conf import REQUIRED_VARIABLES
from src.logging import configure_logging

configure_logging()
logger = logging.getLogger()


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

        self.args, self.args_unknown = parser.parse_known_args()

    def configure_remotestate(self):
        logger.debug("configuring remote state")
        run_command.parse_vars(self.var_data, self.args)
        self.azure_path = run_command.build_tf_state_path(
            self.required_vars,
            self.var_data,
            "".join(vars(self.args)["state_key"]),
            vars(self.args)["workspace"],
        )
        self.configure(vars(self.args)["workspace"])
        if self.required_vars["prjid"] is None or self.required_vars["teamid"] is None:
            logger.error("required variables 'teamid' and 'prjid' not defined.")
            raise SystemExit
        else:
            set_remote_backend_status = self.set_remote_backend(
                self.required_vars["teamid"],
                self.required_vars["prjid"],
                vars(self.args)["workspace"],
                vars(self.args)["fips"],
                vars(self.args)["state_key"],
            )
        logger.info(
            "Remote State backend is configured: {}".format(
                set_remote_backend_status,
            ),
        )
        if set_remote_backend_status:
            logger.debug(sys.argv[1:])
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
            logger.info(f"AZURE command: {cmd}")
            ret_code = run_command.run_cmd(cmd)
            if ret_code == 0:
                exit(0)
            else:
                exit(1)
        else:
            raise Exception(
                "\nThere was an error setting the remote backend for Azure; aborting",
            )

    # set azure storage account details (get from env variables)
    def configure(self, workspace):
        self.azure_container_name = os.getenv("TF_AZURE_CONTAINER")
        self.azure_stg_acc_name = os.getenv("TF_AZURE_STORAGE_ACCOUNT")
        self.azure_access_key = os.getenv("ARM_ACCESS_KEY")
        if (self.azure_container_name is None) or (self.azure_container_name == ""):
            logger.error(
                "Please set the TF_AZURE_CONTAINER environment variable",
            )
            exit(1)
        if (self.azure_stg_acc_name is None) or (self.azure_stg_acc_name == ""):
            logger.error(
                "Please set the TF_AZURE_STORAGE_ACCOUNT environment variable",
            )
            exit(1)
        if (workspace is None) or (workspace == ""):
            logger.error("Please set the workspace using -workspace=<workspace_name>")
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

    def set_remote_backend(self, teamid, prjid, workspace, fips, state_key):
        """
        configure the Terraform remote state if necessary
        return True if remote state was successfully configured
        """
        logger.debug("configure remote state if necessary")
        key_path = teamid + "/" + prjid
        current_tf_state = {"backend": {}}
        current_tf_state["backend"]["config"] = {}
        current_tf_state["backend"]["config"]["storage_account_name"] = None
        current_tf_state["backend"]["config"]["key"] = None
        if "None" in self.azure_path:
            logger.error(
                """
                    Required values missing:
                    please specify: "teamid", "prjid", and "workspace"
                    "teamid", "prjid" can be specified using '-vars' or '-tfvars' e.g.
                        - tf -cloud azure plan -var='teamid=foo' -var='prjid=bar'
                        - tf -cloud azure plan -var-file /tmp/demo.tfvars
                    "workspace" can be specified using '-var' e.g.
                        - tf -cloud azure plan -workspace=demo-workspace
                """
            )
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
                        current_tf_state["backend"]["config"]["storage_account_name"]
                        == self.azure_stg_acc_name
                    )
                    and (
                        current_tf_state["backend"]["config"]["key"] == self.azure_path
                    )
                ):
                    logger.debug("No need to pull remote state")
                    return True
                else:
                    if os.path.isfile(".terraform/terraform.tfstate"):
                        os.unlink(".terraform/terraform.tfstate")
                        logger.debug("removed .terraform/terraform.tfstate")
                    cmd = 'echo "1" | TF_WORKSPACE={} terraform init -backend-config="storage_account_name={}" -backend-config="key={}" -backend-config="container_name={}"'.format(
                        workspace,
                        self.azure_stg_acc_name,
                        key_path,
                        self.azure_container_name,
                    )
                    logger.debug("init command: {}".format(cmd))
                    ret_code = run_command.run_cmd(cmd)
                    if ret_code == 0:
                        return True
                    else:
                        return False
