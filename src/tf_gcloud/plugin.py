import argparse
import json
import logging
import os
import sys

import src.tf_gcloud as gcloud_state
from src.common import run_command
from src.conf import REQUIRED_VARIABLES
from src.logging import configure_logging

configure_logging()
logger = logging.getLogger()


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
            help="specify tfvars file(s)",
        )
        parser.add_argument(
            "-var",
            action="append",
            metavar="",
            dest="inline_vars",
            help="specify inline variables",
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
        # self.required_vars = required_vars
        # self.var_data = var_data
        run_command.parse_vars(self.var_data, self.args)
        self.gcloud_path = run_command.build_tf_state_path(
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
            logger.info(f"GCLOUD command: {cmd}")
            ret_code = run_command.run_cmd(cmd)
            if ret_code == 0:
                exit(0)
            else:
                exit(1)
        else:
            raise Exception(
                "\nThere was an error setting the remote backend for gcloud; aborting",
            )

    # set google storage account details (get from env variables)
    def configure(self, workspace):
        logger.debug("configuring remote state")
        self.gcloud_bucket_name = os.getenv("TF_GCLOUD_BUCKET")
        self.gcloud_credentials = os.getenv("TF_GCLOUD_CREDENTIALS")
        if (self.gcloud_bucket_name is None) or (self.gcloud_bucket_name == ""):
            logger.error(
                "Please set the TF_GCLOUD_BUCKET environment variable",
            )
            exit(1)
        # different credentials for different env
        if (self.gcloud_credentials is None) or (self.gcloud_credentials == ""):
            logger.error(
                "Please set the TF_GCLOUD_CREDENTIALS environment variable",
            )
            exit(1)
        if (workspace is None) or (workspace == ""):
            logger.error("Please set the workspace using -workspace=<workspace_name>")
            exit(1)
        logger.info(
            "[gcloud bucket: {}] [gcloud credentials file path: {}]".format(
                self.gcloud_bucket_name,
                self.gcloud_credentials,
            ),
        )

    def set_remote_backend(self, teamid, prjid, workspace, fips, state_key):
        """
        configure the Terraform remote state if necessary
        return True if remote state was successfully configured
        """
        logger.debug("inside set_remote_backend")
        key_path = teamid + "/" + prjid + "/" + workspace
        current_tf_state = {"backend": {}}
        current_tf_state["backend"]["config"] = {}
        current_tf_state["backend"]["config"]["bucket"] = None
        current_tf_state["backend"]["config"]["credentials"] = None
        if run_command.build_remote_backend_tf_file("gcs", key_path, fips, state_key):
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
                logger.debug("no need to pull remote state")
                return True
            else:
                if os.path.isfile(".terraform/terraform.tfstate"):
                    os.unlink(".terraform/terraform.tfstate")
                    logger.debug("removed .terraform/terraform.tfstate")
                gcloud_path = self.gcloud_path.rsplit("/", 1)[0]
                if "None" in gcloud_path:
                    logger.error(
                        """
                             Required values missing:
                             please specify: "teamid" & "prjid"
                             values can be specified using '-vars' or '-tfvars'
                             e.g. tf -cloud gcloud plan -var='teamid=foo' -var='prjid=bar'
                             tf -cloud gcloud plan -var-file /tmp/demo.tfvars
                             "workspace" can be specified using '-var' e.g.
                                 - tf -cloud azure plan -workspace=demo-workspace"""
                    )
                    raise SystemExit
                cmd = 'echo "1" | terraform init -backend-config="bucket={}" -backend-config="credentials={}" -backend-config="prefix={}"'.format(
                    # workspace,
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
