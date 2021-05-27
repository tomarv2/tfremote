# import os
#
# from src.common.validate_allowed_workspace import allowed_workspace
#
#
# def test_allowed_workspace():
#     dirname = os.path.dirname(__file__)
#     filename = os.path.join(dirname, "../scripts/workspaces.json")
#     os.environ["TF_WORKSPACE_FILE_LOCATION"] = filename
#
#     cloud = "gcloud"
#     workspace = "demo-workspace"
#     fips = True
#
#     output = allowed_workspace(cloud, workspace, fips)
#     assert output == True
