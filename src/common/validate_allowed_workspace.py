import logging
import os
import sys

from ruamel.yaml import YAML
from ruamel.yaml.scanner import ScannerError

from src.conf import WORKSPACES_YML
from src.logging import configure_logging

configure_logging()
logger = logging.getLogger()


def allowed_workspace(workspace_directory, workspace, fips):
    """
    Check if the workspace specified by user in the approved list
    """
    logger.debug(
        f"workspace_directory: [{workspace_directory}] workspace: [{workspace}]"
    )
    if workspace == "default":
        return True
    if os.getenv("TF_WORKSPACE_FILE_LOCATION"):
        file_location = os.getenv("TF_WORKSPACE_FILE_LOCATION")
        try:
            with open(os.path.expanduser(file_location), "r") as f:
                try:
                    data = YAML().load(f)
                    for i in data[workspace_directory]:
                        if workspace in i["workspaces"]:
                            return workspace, i["account_id"]
                except ScannerError as e:
                    logger.error(
                        "Error parsing yaml of configuration file "
                        "{}: {}".format(
                            e.problem_mark,
                            e.problem,
                        )
                    )
                    sys.exit(1)
        except FileNotFoundError:
            logger.error("Error opening configuration file {}".format(file_location))
            sys.exit(1)
    else:
        logger.info("Using default workspaces file")
        try:
            data = YAML().load(WORKSPACES_YML)
            out_list = []
            for i in data[workspace_directory]:
                if workspace in i["workspaces"]:
                    out_list.append(workspace)
                    out_list.append(i["account_id"])
            if out_list:
                return out_list
            else:
                logger.error(
                    f"{workspace} workspace does not exist in default workspaces file"
                )
        except ScannerError as e:
            logger.error(
                "Error parsing yaml of configuration file "
                "{}: {}".format(
                    e.problem_mark,
                    e.problem,
                )
            )
            sys.exit(1)
