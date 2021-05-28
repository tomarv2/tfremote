import json
import logging
import os

from src.logging import configure_logging

configure_logging()
logger = logging.getLogger()


def allowed_workspace(cloud, workspace, fips):
    """
    check if the workspace specified by user in the approved list
    """
    if os.getenv("TF_WORKSPACE_FILE_LOCATION"):
        file_location = os.getenv("TF_WORKSPACE_FILE_LOCATION")
        with open(file_location) as f:
            try:
                data = json.load(f)
                for i in data[cloud]["workspaces"]:
                    if (i["name"]) == workspace:
                        return True
            except Exception as e:
                logger.error(
                    f"Not a valid json file provided for env variable: TF_WORKSPACE_FILE_LOCATION\n"
                    f"{os.getenv('TF_WORKSPACE_FILE_LOCATION')}: {str(e)}"
                )
                raise SystemExit
    else:
        logger.error(
            f"Unable to open workspace list file, please set TF_WORKSPACE_FILE_LOCATION environment variable"
        )
        raise SystemExit
