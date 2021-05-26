"""
This package allows multiple teams to collaborate on Terraform deployments by maintaining centralized remote state.

- aws
- azure
- gcloud
- alicloud in-progress

It needs two variables: teamid and prjid to structure files in storage
"""
import argparse
import logging
import re
import subprocess
import sys
from distutils.version import StrictVersion as V

from src.common import pass_through_list, run_command
from src.conf import REQUIRED_VARIABLES
from src.tf_aws import plugin as aws_plugin
from src.tf_azure import plugin as azure_plugin
from src.tf_gcloud import plugin as gcloud_plugin

from .logging import configure_logging

logger = logging.getLogger(__name__)
configure_logging()

MIN_TERRAFORM_V = "0.14.0"


# verifying version of terraform installed
def valid_terraform_version(min_supported_ver):
    """
    :param min_supported_ver: v14
    """
    cmd_output = subprocess.check_output("terraform version", shell=True)
    detected_ver = re.search(
        r"\d+\.\d+\.\d+",
        cmd_output.decode("utf-8"),
    ).group(0)
    if V(detected_ver) >= V(min_supported_ver):
        return True
    else:
        logger.error(
            "Installed terraform version: {}, is not supported by the tf wrapper script. \
        \nTerraform version must be >= {}".format(
                detected_ver,
                min_supported_ver,
            ),
        )
        return False


class TerraformWrapper:
    var_data = {}
    args = None
    args_unknown = None
    required_vars = REQUIRED_VARIABLES
    logger = None

    def __init__(self):
        parser = argparse.ArgumentParser(
            description="terraform wrapper script",
        )
        parser.add_argument("apply", help="terraform subcommand")
        parser.add_argument(
            "-cloud",
            dest="cloud",
            help="specify cloud provider (e.g. gcloud, aws, or azure)",
        )
        parser.add_argument("-version", action="version", version="%(prog)s 0.1")
        self.args, self.args_unknown = parser.parse_known_args()

    def main(self):
        if vars(self.args)["apply"] in pass_through_list.deny_list():
            logger.error(
                "subcommand '{}' should not be used with this wrapper script as it may break things ".format(
                    vars(self.args)["apply"],
                ),
            )
            exit(1)
        elif vars(self.args)["apply"] in pass_through_list.allow_list():
            argument = "".join(vars(self.args)["apply"])
            cmd = "terraform " + argument
            logging.debug("terraform command: {}", cmd)
            ret_code = run_command.run_cmd(cmd)
            if ret_code == 0:
                exit(0)
            else:
                exit(1)
        else:
            if vars(self.args)["cloud"] is None:
                logger.error(
                    "Please specify cloud provider with -cloud argument(-cloud gcloud, aws, or azure)",
                )
                raise SystemExit
            cloud_env = vars(self.args)["cloud"].lower()
            if cloud_env == "aws":
                logger.debug("configuring aws")
                aws_plugin.configure_remotestate()
            elif cloud_env == "azure":
                logger.debug("configuring azure")
                azure_plugin.configure_remotestate()
            elif cloud_env == "gcloud":
                logger.debug("configuring gcloud")
                gcloud_plugin.configure_remotestate()
            else:
                logger.error(
                    "Incorrect cloud provider entered (e.g. gcloud, aws, or azure)",
                )
                raise SystemExit


def entrypoint():
    if not valid_terraform_version(MIN_TERRAFORM_V):
        exit(1)
    else:
        TerraformWrapper().main()


if __name__ == "__main__":
    entrypoint()
