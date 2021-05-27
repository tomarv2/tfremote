import json
import logging
import os

from src.logging import configure_logging

configure_logging()
logger = logging.getLogger()

if os.getenv("WORKSPACE_FILE_LOCATION"):
    file_location = os.getenv("WORKSPACE_FILE_LOCATION")
else:
    logger.error(f"Please set WORKSPACE_FILE_LOCATION environment variable")


def allowed_workspace(cloud, workspace, fips):
    try:
        with open(file_location) as f:
            data = json.load(f)
            for i in data[cloud]["workspaces"]:
                if (i["name"]) == workspace:
                    return True
    except:
        logger.error(
            f"Unable to open workspace file, please set WORKSPACE_FILE_LOCATION environment variable"
        )
