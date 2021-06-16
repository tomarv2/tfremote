"""
This package allows multiple teams to collaborate on Terraform deployments by maintaining centralized remote state.

- aws
- azure
- gcloud
- alicloud in-progress

It needs three variables: teamid, prjid and workspace to structure files in backend storage
"""
import argparse
import logging
import re
import subprocess
from distutils.version import StrictVersion as V

from src.common import pass_through_list
from src.common import plugin as common_plugin
from src.common import run_command

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
    logger = None

    def __init__(self):
        parser = argparse.ArgumentParser(
            description="Terraform wrapper script",
        )
        parser.add_argument("plan, apply, or destroy", help="terraform command")

        self.args, self.args_unknown = parser.parse_known_args()

    def main(self):
        if vars(self.args)["plan, apply, or destroy"] in pass_through_list.deny_list():
            logger.error(
                "subcommand '{}' should not be used with this wrapper script as it may break things ".format(
                    vars(self.args)["plan, apply, or destroy"],
                ),
            )
            exit(1)
        elif (
            vars(self.args)["plan, apply, or destroy"] in pass_through_list.allow_list()
        ):
            argument = "".join(vars(self.args)["plan, apply, or destroy"])
            cmd = "terraform " + argument
            logging.debug(f"terraform command: {cmd}")
            ret_code = run_command.run_cmd(cmd)
            if ret_code == 0:
                exit(0)
            else:
                exit(1)
        else:
            common_plugin.configure_remotestate()


def entrypoint():
    if not valid_terraform_version(MIN_TERRAFORM_V):
        exit(1)
    else:
        TerraformWrapper().main()


if __name__ == "__main__":
    entrypoint()
