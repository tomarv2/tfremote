"""
- Build remote state path
- Parse vars
- Create command
"""
import json
import logging
import os
import re
import subprocess
from typing import List

import hcl

from src.conf import (
    AWS_FIPS_US_WEST2_ENDPOINT,
    LIST_OF_VARIABLES_FILES,
    MISSING_VARS,
    SUPPORTED_CLOUD_PROVIDERS,
)
from src.logging import configure_logging

configure_logging()
logger = logging.getLogger()


def run_cmd(cmd):
    p = subprocess.Popen(cmd, shell=True)
    p.wait()
    return p.returncode


def create_command(arguments_entered: List[str]) -> str:
    """
    :param arguments_entered: storage path, tfvars file
    :return: command generated
    """
    logger.debug(f"arguments_entered: {arguments_entered}")
    if "-cloud" in arguments_entered:
        arguments_entered.remove("-cloud")
    for i in SUPPORTED_CLOUD_PROVIDERS:
        if i in arguments_entered:
            arguments_entered.remove(i)
    return " ".join(arguments_entered)


def build_remote_backend_tf_file(storage_type, workspace_key_prefix, fips, state_key):
    """
    function to create remote_backend.tf file
    """
    logger.debug("creating remote_backend.tf file")
    if os.path.exists("remote_backend.tf"):
        logger.info("remote_backend.tf exists, deleting existing backend file")
        os.remove("remote_backend.tf")
    logger.debug(f"storage_type: {storage_type}")
    try:
        with open("remote_backend.tf", "w") as f:
            f.write("# file generated by wrapper script to configure backend\n")
            f.write("# do not edit or delete!\n")
            f.write("\n")
            if fips and storage_type == "s3":
                f.write(
                    'terraform {{\n\tbackend "{}" {{\n\t\tendpoint = "{}"\n\t\tworkspace_key_prefix = "{}"\n\t}}\n}}\n'.format(
                        storage_type, AWS_FIPS_US_WEST2_ENDPOINT, workspace_key_prefix
                    )
                )
            elif storage_type == "azurerm":
                f.write(
                    'terraform {{\n\tbackend "{}" {{\n\t\tkey = "{}"\n\t}}\n}}\n'.format(
                        storage_type, state_key
                    )
                )
            elif storage_type == "gcs":
                f.write(
                    'terraform {{\n\tbackend "{}" {{\n\t\tprefix = "{}"\n\t}}\n}}\n'.format(
                        storage_type, workspace_key_prefix
                    )
                )
            else:
                f.write(
                    'terraform {{\n\tbackend "{}" {{\n\tworkspace_key_prefix = "{}"\n\t}}\n}}\n'.format(
                        storage_type, workspace_key_prefix
                    )
                )
        return True
    except OSError:
        logger.error("error creating file: {}".format("remote_backend.tf"))


def build_tf_state_path(required_vars, var_data, state_key, workspace):
    """
    function to build tf state path
    """
    logger.debug("build tf state path")
    for var in required_vars:
        logger.debug("checking if required variables are provided")
        logger.debug("checking required vars in inline vars")
        if var in var_data["inline_vars"]:
            required_vars[var] = var_data["inline_vars"][var]
        elif var_data["tfvars"] is not None:
            logger.debug("checking required vars in tfvars")
            if var in var_data["tfvars"]:
                required_vars[var] = var_data["tfvars"][var]
        elif "variables_tf" in var_data:
            logger.debug("checking required vars in variables file")
            if var in var_data["variables_tf"]:
                logger.debug("checking required vars in variables.tf file")
                if var_data["variables_tf"][var] != "":
                    required_vars[var] = var_data["variables_tf"][var]
                else:
                    raise Exception(MISSING_VARS)
        else:
            raise Exception(MISSING_VARS)

    else:
        if workspace != "default":
            path = "{}".format(state_key)
            logger.debug("terraform path: %s" % path)
            return path
        else:
            path = "terraform/{}/{}/terraform.tfstate".format(
                required_vars["teamid"],
                required_vars["prjid"],
            )
            logger.debug("terraform path: %s" % path)
            return path


def parse_vars(var_data, args):
    """
    function to parse variables
    """
    logger.debug("parsing variables")
    var_data["inline_vars"] = parse_inline_vars(args)
    var_data["tfvars"] = parse_tfvar_files(args)
    for file in LIST_OF_VARIABLES_FILES:
        if os.path.isfile(file):
            var_data["variables_tf"] = parse_var_file(file)
            logger.debug(
                "parsed variables: %s"
                % (
                    json.dumps(
                        var_data,
                        indent=2,
                        sort_keys=True,
                    )
                ),
            )


def parse_inline_vars(args):
    """
    parse variables defined on the command line (-var foo=bar)
    """
    logger.debug("parsing inline vars")
    results = {}
    if vars(args)["inline_vars"] is None:
        return results
    for var in vars(args)["inline_vars"]:
        match = re.split(r"\s*=\s*", var, maxsplit=1)
        key = match[0]
        value = match[1]
        results[key] = value
    return results


def parse_tfvar_files(args):
    """
    parse variables defined in:
     - terraform.tfvars
     - file(s) defined in command line (-var-file foo.tfvars)
    """
    logger.debug("inside parse_tfvar_files function")
    tfvar_files = vars(args)["tfvar_files"]
    if tfvar_files is not None:
        if (os.path.isfile("terraform.tfvars")) and (
            "terraform.tfvars" not in tfvar_files
        ):
            tfvar_files.insert(0, "terraform.tfvars")
        for file in tfvar_files:
            with open(file) as fh:
                obj = hcl.load(fh)
                return obj
    else:
        logger.debug("no tfvars provided")


def parse_var_file(file):
    """
    parse the variables defined in .tf file
        eg:
            variable name {
                foo = "bar"

    }
    """
    logger.debug("parsing tfvars file")
    results = {}
    with open(file) as fh:
        data = hcl.load(fh)
    for var in data["variable"]:
        if "default" in data["variable"][var]:
            results[var] = data["variable"][var]["default"]
    return results
